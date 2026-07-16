from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Prestamo, Devolucion

@receiver(post_save, sender=Prestamo)
def cambiar_estado_prestamo(sender, instance, created, **kwargs):
    if created:
        equipo = instance.equipo
        equipo.estado = 'Prestado'
        equipo.save()


@receiver(post_save, sender=Devolucion)
def cambiar_estado_devolucion(sender, instance, created, **kwargs):
    if created:
        equipo = instance.prestamo.equipo
        equipo.estado = 'Disponible'
        equipo.save()