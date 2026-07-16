from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# =========================================================================
# 1. CATEGORÍAS & EQUIPOS
# =========================================================================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    ESTADOS = [
        ('Disponible', 'Disponible'),
        ('Prestado', 'Prestado'),
        ('Mantenimiento', 'Mantenimiento'),
    ]

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="equipos"
    )

    codigo = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100, blank=True, default="")

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Disponible'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def save(self, *args, **kwargs):
        # 1. Guardamos los cambios del equipo en la base de datos
        super().save(*args, **kwargs)
        
        # 2. Si el estado del equipo cambió a 'Disponible', cerramos sus préstamos activos
        if self.estado == 'Disponible':
            # Se importa aquí adentro para evitar problemas de "importación circular"
            from prestamo.models import Prestamo 
            
            # Busca los préstamos de este equipo que sigan "Activos" y los cambia a "Devuelto"
            Prestamo.objects.filter(equipo=self, estado='Activo').update(estado='Devuelto')


# =========================================================================
# 2. PERFIL BIOMÉTRICO DE USUARIO (NUEVO)
# =========================================================================

class Perfil(models.Model):
    """
    Extiende el usuario básico de Django para almacenar su firma facial.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rostro_biometrico = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


# =========================================================================
# 3. SEÑALES (Crea el Perfil automáticamente al registrar usuarios)
# =========================================================================

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
    else:
        Perfil.objects.create(usuario=instance)