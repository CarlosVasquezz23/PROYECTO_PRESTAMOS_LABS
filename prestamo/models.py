from django.db import models
from inventario.models import Equipo
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Prestamo(models.Model):
    ESTADOS = [
        ('Activo', 'Activo'),
        ('Devuelto', 'Devuelto'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    fecha_prestamo = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Activo')

    def __str__(self):
        return f"{self.usuario.username} - {self.equipo.nombre}"

    def clean(self):
        super().clean()
        # Validar que la fecha de devolución no sea anterior a la de préstamo
        if self.fecha_prestamo and self.fecha_devolucion:
            if self.fecha_devolucion < self.fecha_prestamo:
                raise ValidationError({
                    'fecha_devolucion': 'La fecha de devolución no puede ser anterior a la fecha del préstamo.'
                })

    def save(self, *args, **kwargs):
        # 1. Guardamos el préstamo primero
        super().save(*args, **kwargs)

        # 2. Inmediatamente después, sincronizamos el estado del equipo
        if self.estado == "Activo":
            self.equipo.estado = "Prestado"
            self.equipo.save()
        elif self.estado == "Devuelto":
            self.equipo.estado = "Disponible"
            self.equipo.save()


class Devolucion(models.Model):
    prestamo = models.OneToOneField(Prestamo, on_delete=models.CASCADE)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    def clean(self):
        if self.pk is None and Devolucion.objects.filter(prestamo=self.prestamo).exists():
            raise ValidationError("Este préstamo ya tiene una devolución registrada.")

    def save(self, *args, **kwargs):
        # 1. Guardamos la devolución
        super().save(*args, **kwargs)

        # 2. Cambiamos automáticamente el estado del préstamo
        # (Esto a su vez disparará el save() de Prestamo que acabamos de arreglar arriba,
        # haciendo que el Equipo vuelva automáticamente a "Disponible")
        self.prestamo.estado = "Devuelto"
        self.prestamo.save()

    def __str__(self):
        return f"Devolución de {self.prestamo.equipo.nombre}"