from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

from .models import Prestamo, Devolucion
from .forms import PrestamoForm, DevolucionForm


@login_required
def lista_prestamos(request):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado: Esta área es solo para el personal del laboratorio.")
        return redirect("dashboard")

    buscar = request.GET.get("buscar", "")
    estado = request.GET.get("estado", "")

    prestamos = Prestamo.objects.select_related("usuario", "equipo").all().order_by('-fecha_prestamo')

    if buscar:
        prestamos = prestamos.filter(
            Q(usuario__username__icontains=buscar) |
            Q(usuario__first_name__icontains=buscar) |
            Q(usuario__last_name__icontains=buscar) |
            Q(equipo__nombre__icontains=buscar) |
            Q(equipo__codigo__icontains=buscar)
        )

    if estado:
        prestamos = prestamos.filter(estado=estado)

    context = {
        "prestamos": prestamos,
        "buscar": buscar,
        "estado": estado
    }

    return render(request, "prestamo/lista_prestamos.html", context)


@login_required
def procesar_devolucion(request, prestamo_id):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado: Solo el personal de laboratorio puede registrar devoluciones.")
        return redirect("dashboard")
        
    if request.method == "POST":
        prestamo = get_object_or_404(Prestamo, id=prestamo_id)
        
        if prestamo.estado == "Activo":
            Devolucion.objects.create(
                prestamo=prestamo, 
                observaciones="Equipo recibido desde el panel de control rápido."
            )
            
            prestamo.estado = "Devuelto"
            prestamo.save()
            
            prestamo.equipo.estado = "Disponible"
            prestamo.equipo.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True, 
                    "message": "Equipo marcado como devuelto."
                })
            
            messages.success(request, f"Equipo {prestamo.equipo.codigo} marcado como devuelto correctamente y liberado en el inventario.")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False, 
                    "message": "Este préstamo ya ha sido devuelto anteriormente."
                })
            messages.warning(request, "Este préstamo ya ha sido devuelto anteriormente.")
            
    return redirect("prestamo:lista_prestamos")


@login_required
def crear_prestamo(request):
    if request.method == "POST":
        form = PrestamoForm(request.POST)

        if form.is_valid():
            prestamo = form.save(commit=False)
            prestamo.usuario = request.user
            prestamo.save()

            prestamo.equipo.estado = "Prestado"
            prestamo.equipo.save()

            # Corregido con los espacios de nombres del proyecto
            if request.user.groups.filter(name="Usuario").exists():
                return redirect("prestamo:mis_prestamos")
            else:
                return redirect("prestamo:lista_prestamos")
    else:
        form = PrestamoForm()

    return render(request, "prestamo/crear_prestamo.html", {
        "form": form
    })


@login_required
def mis_prestamos(request):
    prestamos = Prestamo.objects.filter(usuario=request.user).order_by('-fecha_prestamo')
    ahora = timezone.now()
    
    for pr in prestamos:
        if pr.estado == 'Activo' and pr.fecha_devolucion:
            if pr.fecha_devolucion > ahora:
                diferencia = pr.fecha_devolucion - ahora
                segundos_totales = int(diferencia.total_seconds())
                horas = segundos_totales // 3600
                minutos = (segundos_totales % 3600) // 60
                
                if horas > 0:
                    pr.tiempo_restante = f"Te quedan {horas}h {minutos}m"
                else:
                    pr.tiempo_restante = f"Te quedan {minutos} min"
                
                pr.alerta_clase = "warning" if horas == 0 and minutos < 30 else "info"
            else:
                diferencia = ahora - pr.fecha_devolucion
                segundos_totales = int(diferencia.total_seconds())
                horas = segundos_totales // 3600
                minutos = (segundos_totales % 3600) // 60
                
                if horas > 0:
                    pr.tiempo_restante = f"Vencido hace {horas}h {minutos}m"
                else:
                    pr.tiempo_restante = f"Vencido hace {minutos} min"
                
                pr.alerta_clase = "danger"
        else:
            pr.tiempo_restante = "Completado"
            pr.alerta_clase = "success"
    
    return render(
        request, 
        'prestamo/mis_prestamos.html',
        {'prestamos': prestamos}
    )


@login_required
def crear_devolucion(request):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado: Solo el personal puede registrar devoluciones.")
        return redirect("dashboard")

    if request.method == "POST":
        form = DevolucionForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("prestamo:lista_prestamos")
    else:
        form = DevolucionForm()

    return render(request, "prestamo/crear_devolucion.html", {
        "form": form
    })


@login_required
def reporte_prestamos_pdf(request):
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_prestamos_UNEMI.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    azul_unemi = colors.HexColor("#002D62")

    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(azul_unemi)
    p.drawCentredString(width / 2, 750, "UNIVERSIDAD ESTATAL DE MILAGRO")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.darkgrey)
    p.drawCentredString(width / 2, 735, "Facultad de Ciencias e Ingenierías - Laboratorios")

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawCentredString(width / 2, 715, "REPORTE OFICIAL DE PRÉSTAMOS DE EQUIPOS")

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    p.setFont("Helvetica", 9)
    p.drawString(440, 695, f"Fecha Emisión: {fecha}")

    p.setStrokeColor(azul_unemi)
    p.setLineWidth(2)
    p.line(50, 685, 550, 685)

    p.setFillColor(azul_unemi)
    p.rect(50, 660, 500, 20, fill=1, stroke=0)

    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.white)
    p.drawString(55, 666, "Usuario")
    p.drawString(145, 666, "Equipo")
    p.drawString(295, 666, "F. Préstamo")      
    p.drawString(400, 666, "F. Devolución")    
    p.drawString(505, 666, "Estado")

    y = 640
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.black)

    prestamos = Prestamo.objects.select_related("usuario", "equipo").all().order_by('-fecha_prestamo')

    for pr in prestamos:
        fecha_prestamo_limpia = pr.fecha_prestamo.strftime('%Y-%m-%d %H:%M') if pr.fecha_prestamo else "---"
        fecha_devolucion_limpia = pr.fecha_devolucion.strftime('%Y-%m-%d %H:%M') if pr.fecha_devolucion else "---"

        p.drawString(55, y, str(pr.usuario.username).capitalize())
        
        nombre_equipo = str(pr.equipo.nombre).capitalize()
        if len(nombre_equipo) > 22:
            nombre_equipo = Galbraith = nombre_equipo[:20] + "..."
            
        p.drawString(145, y, nombre_equipo)
        p.drawString(295, y, fecha_prestamo_limpia)
        p.drawString(400, y, fecha_devolucion_limpia)
        
        estado = str(pr.estado)
        if estado == "Activo":
            p.setFillColor(colors.HexColor("#198754")) 
        elif estado == "Devuelto":
            p.setFillColor(colors.HexColor("#0d6efd"))
        else:
            p.setFillColor(colors.darkgrey)
            
        p.drawString(505, y, estado)
        p.setFillColor(colors.black)

        p.setStrokeColor(colors.lightgrey)
        p.setLineWidth(0.5)
        p.line(50, y - 5, 550, y - 5)

        y -= 20

        if y < 50:
            p.showPage()
            y = 750
            p.setFont("Helvetica", 9)
            p.setFillColor(colors.black)

    p.save()
    return response


@login_required
def dashboard(request):
    is_admin = request.user.groups.filter(name="Administrador").exists()
    is_usuario = request.user.groups.filter(name="Usuario").exists()
    ahora = timezone.now()

    if "user" in request.path or not is_admin:
        mis_prestamos = Prestamo.objects.filter(usuario=request.user).order_by('-fecha_prestamo')
        
        for pr in mis_prestamos:
            pr.devuelto = (pr.estado == 'Devuelto')

        cant_activos = mis_prestamos.filter(estado='Activo').count()
        cant_espera = mis_prestamos.filter(estado__icontains='espera').count()

        prestamos_recortados = mis_prestamos[:5]

        context = {
            "is_admin": is_admin,
            "is_usuario": is_usuario,
            "prestamos": prestamos_recortados,
            "cant_activos": cant_activos,
            "cant_espera": cant_espera if cant_espera > 0 else 1,
        }
        return render(request, "dashboard_user.html", context)

    else:
        total_solicitudes = Prestamo.objects.count()
        prestamos_activos = Prestamo.objects.filter(estado='Activo').count()
        prestamos_vencidos = Prestamo.objects.filter(
            estado='Activo', 
            fecha_devolucion__lt=ahora
        ).count()

        context = {
            "is_admin": is_admin,
            "is_usuario": is_usuario,
            "metric_activos": prestamos_activos,
            "metric_vencidos": prestamos_vencidos,
            "metric_total": total_solicitudes,
        }
        return render(request, "dashboard_admin.html", context)


@login_required
def api_mis_prestamos(request):
    prestamos = Prestamo.objects.filter(usuario=request.user).select_related('equipo')
    ahora = timezone.now()
    data = []

    for pr in prestamos:
        tiempo_restante = "Completado"
        alerta_clase = "success"

        if pr.estado == 'Activo' and pr.fecha_devolucion:
            if pr.fecha_devolucion > ahora:
                diferencia = pr.fecha_devolucion - ahora
                segundos_totales = int(diferencia.total_seconds())
                horas = segundos_totales // 3600
                minutos = (segundos_totales % 3600) // 60
                tiempo_restante = f"Te quedan {horas}h {minutos}m" if horas > 0 else f"Te quedan {minutos} min"
                # Corregido: 'minutes' cambiado a 'minutos'
                alerta_clase = "warning" if horas == 0 and minutos < 30 else "info"
            else:
                diferencia = ahora - pr.fecha_devolucion
                segundos_totales = int(diferencia.total_seconds())
                horas = segundos_totales // 3600
                minutos = (segundos_totales % 3600) // 60
                tiempo_restante = f"Vencido hace {horas}h {minutos}m" if horas > 0 else f"Vencido hace {minutos} min"
                alerta_clase = "danger"

        data.append({
            'id': pr.id,
            'equipo': pr.equipo.nombre,
            'estado': pr.estado,
            'tiempo_restante': tiempo_restante,
            'alerta_clase': alerta_clase
        })
    
    return JsonResponse(data, safe=False)