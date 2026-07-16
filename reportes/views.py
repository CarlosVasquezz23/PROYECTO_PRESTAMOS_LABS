from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from inventario.models import Equipo
from prestamo.models import Prestamo
from django.contrib.auth.models import User


@login_required
def estadisticas(request):

    context = {
        "total_equipos": Equipo.objects.count(),
        "disponibles": Equipo.objects.filter(estado="Disponible").count(),
        "prestados": Equipo.objects.filter(estado="Prestado").count(),
        "mantenimiento": Equipo.objects.filter(estado="Mantenimiento").count(),
        "prestamos_activos": Prestamo.objects.filter(estado="Activo").count(),
        "total_usuarios": User.objects.count(),
    }

    return render(request, "reportes/estadisticas.html", context)