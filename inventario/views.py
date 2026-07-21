import os
import cv2
import json
import numpy as np
import base64
try:
    import face_recognition
except ImportError:
    face_recognition = None

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Para la generación del PDF de reporte
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Modelos y Formularios locales de inventario
from .models import Equipo, Categoria 
from .forms import EquipoForm


# =========================================================================
# 1. BIOMETRÍA FACIAL & PROCESAMIENTO DE IMAGEN
# =========================================================================

def normalizar_iluminacion_rostro(imagen_cv2):
    """
    Convierte la imagen de formato BGR (OpenCV) a RGB nativo (Face Recognition).
    Evita alterar excesivamente el contraste para conservar las características faciales reales.
    """
    imagen_rgb = cv2.cvtColor(imagen_cv2, cv2.COLOR_BGR2RGB)
    return imagen_rgb


@csrf_exempt
def vista_login_pagina(request):
    """
    Controlador unificado para la pantalla de inicio de sesión visual tradicional.
    """
    if request.method == "POST":
        username = request.POST.get("username") or request.POST.get("username_admin") or request.POST.get("username_usuario")
        password = request.POST.get("password") or request.POST.get("password_admin") or request.POST.get("password_usuario")

        if not username or not password:
            messages.error(request, "Por favor, introduce tu usuario y contraseña.")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"¡Bienvenido, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "login.html")

    return render(request, "login.html")


@csrf_exempt
def login_facial(request):
    """
    Endpoint para procesar el inicio de sesión por biometría compatible con FormData y Base64.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

    if face_recognition is None:
        return JsonResponse({"success": False, "message": "El módulo face_recognition no está instalado en el servidor."}, status=500)

    try:
        archivo_imagen = request.FILES.get('image')
        
        if archivo_imagen:
            filestr = archivo_imagen.read()
            np_arr = np.frombuffer(filestr, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        else:
            uri_imagen = None
            if request.content_type == 'application/json' or request.body:
                try:
                    data = json.loads(request.body)
                    uri_imagen = data.get("imagen") or data.get("image")
                except json.JSONDecodeError:
                    pass
            
            if not uri_imagen:
                uri_imagen = request.POST.get("imagen") or request.POST.get("image")

            if not uri_imagen:
                return JsonResponse({"success": False, "message": "No se recibió ninguna captura de la cámara."})

            if "," in uri_imagen:
                header, encoded = uri_imagen.split(",", 1)
            else:
                encoded = uri_imagen
                
            datos_binarios = base64.b64decode(encoded)
            np_arr = np.frombuffer(datos_binarios, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return JsonResponse({"success": False, "message": "No se pudo procesar la captura de la cámara."})

        img_procesada = normalizar_iluminacion_rostro(img_bgr)
        rostros_actuales = face_recognition.face_encodings(img_procesada)
        
        if len(rostros_actuales) == 0:
            return JsonResponse({
                "success": False, 
                "message": "No se detectó un rostro claro. Por favor, enfoca bien tu cámara y evita contraluces."
            })

        rostro_actual_codificado = rostros_actuales[0]
        usuarios = User.objects.all()
        usuario_encontrado = None

        for usuario in usuarios:
            rostro_guardado_str = None
            try:
                if hasattr(usuario, 'perfil') and usuario.perfil and getattr(usuario.perfil, 'rostro_biometrico', None):
                    rostro_guardado_str = usuario.perfil.rostro_biometrico
                elif getattr(usuario, 'rostro_biometrico', None):
                    rostro_guardado_str = usuario.rostro_biometrico
            except Exception:
                continue

            if rostro_guardado_str:
                try:
                    rostro_guardado = np.array(json.loads(rostro_guardado_str))
                    distancia = face_recognition.face_distance([rostro_guardado], rostro_actual_codificado)[0]

                    if distancia <= 0.45:
                        usuario_encontrado = usuario
                        break
                except Exception:
                    continue

        if usuario_encontrado is not None:
            login(request, usuario_encontrado)

            # Consumir mensajes previos residuales
            storage = messages.get_messages(request)
            for _ in storage:
                pass

            messages.success(request, f"¡Autenticación facial exitosa! Bienvenido, {usuario_encontrado.username}.")
            redirect_url = "/dashboard/admin/" if usuario_encontrado.is_staff or usuario_encontrado.is_superuser else "/dashboard/user/"
            return JsonResponse({"success": True, "redirect_url": redirect_url})
        else:
            return JsonResponse({
                "success": False, 
                "message": "Rostro no reconocido. Asegúrate de estar en un lugar iluminado o vuelve a registrar tu rostro."
            })

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error del sistema: {str(e)}"})


@csrf_exempt
@login_required
def registrar_rostro(request):
    """
    API para registrar el rostro maestro del usuario autenticado.
    """
    if request.method != "POST":
        return render(request, "inventario/registrar_facial.html")

    if face_recognition is None:
        return JsonResponse({"success": False, "message": "Módulo de biometría no disponible en el servidor."}, status=500)

    try:
        archivo_imagen = request.FILES.get('image')
        
        if archivo_imagen:
            filestr = archivo_imagen.read()
            np_arr = np.frombuffer(filestr, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        else:
            uri_imagen = None
            if request.content_type == 'application/json' or request.body:
                try:
                    data = json.loads(request.body)
                    uri_imagen = data.get("imagen") or data.get("image")
                except json.JSONDecodeError:
                    pass
            
            if not uri_imagen:
                uri_imagen = request.POST.get("imagen") or request.POST.get("image")

            if not uri_imagen:
                return JsonResponse({"success": False, "message": "Imagen de registro faltante."})
            
            if "," in uri_imagen:
                header, encoded = uri_imagen.split(",", 1)
            else:
                encoded = uri_imagen
                
            datos_binarios = base64.b64decode(encoded)
            np_arr = np.frombuffer(datos_binarios, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            return JsonResponse({"success": False, "message": "La imagen está vacía o corrupta."})

        img_procesada = normalizar_iluminacion_rostro(img_bgr)
        rostros_detectados = face_recognition.face_encodings(img_procesada)
        
        if len(rostros_detectados) == 0:
            return JsonResponse({
                "success": False, 
                "message": "No se detectó ningún rostro. Asegúrate de mirar de frente y despejar tu cara."
            })

        rostro_codificado = rostros_detectados[0]
        vector_json_string = json.dumps(rostro_codificado.tolist())
        usuario_actual = request.user
        
        guardado_exitoso = False
        if hasattr(usuario_actual, 'perfil') and usuario_actual.perfil is not None:
            usuario_actual.perfil.rostro_biometrico = vector_json_string
            usuario_actual.perfil.save()
            guardado_exitoso = True
        else:
            try:
                usuario_actual.rostro_biometrico = vector_json_string
                usuario_actual.save()
                guardado_exitoso = True
            except Exception:
                pass

        if not guardado_exitoso:
            return JsonResponse({
                "success": False,
                "message": "Error al guardar: Tu modelo de usuario no permite almacenar datos de biometría."
            })

        return JsonResponse({"success": True, "message": "¡Tu rostro maestro ha sido registrado con éxito!"})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error al guardar: {str(e)}"})


# =========================================================================
# 2. VISTAS DE DASHBOARDS & LOGOUT
# =========================================================================

@login_required
def dashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect('dashboard_admin')
    return redirect('dashboard_user')


@login_required
def dashboard_admin(request):
    return render(request, "dashboard_admin.html")


@login_required
def dashboard_user(request):
    from prestamo.models import Prestamo
    # ACTUALIZADO: Filtra y muestra únicamente los últimos 5 préstamos realizados
    mis_prestamos = Prestamo.objects.filter(usuario=request.user).order_by('-id')[:5]
    return render(request, "dashboard_user.html", {"prestamos": mis_prestamos})


@login_required
def historial_completo_user(request):
    from prestamo.models import Prestamo
    # NUEVA VISTA: Obtiene todos los registros históricos del usuario sin límites
    todos_mis_prestamos = Prestamo.objects.filter(usuario=request.user).order_by('-id')
    return render(request, "inventario/historial_completo.html", {"prestamos": todos_mis_prestamos})


def logout_usuario(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('login')


# =========================================================================
# 3. VISTAS DEL SISTEMA DE INVENTARIO (EQUIPOS & CATEGORÍAS)
# =========================================================================

@login_required
def lista_equipos(request):
    """
    Lista todos los equipos aplicando filtros de búsqueda y estado.
    """
    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()

    equipos = Equipo.objects.all()

    if buscar:
        equipos = equipos.filter(
            Q(codigo__icontains=buscar) |
            Q(nombre__icontains=buscar) |
            Q(marca__icontains=buscar) |
            Q(modelo__icontains=buscar)
        )

    if estado:
        equipos = equipos.filter(estado=estado)

    total_equipos = Equipo.objects.count()
    disponibles = Equipo.objects.filter(estado="Disponible").count()
    prestados = Equipo.objects.filter(estado="Prestado").count()
    mantenimiento = Equipo.objects.filter(estado="Mantenimiento").count()

    context = {
        "equipos": equipos,
        "buscar": buscar,
        "estado": estado,
        "total_equipos": total_equipos,
        "disponibles": disponibles,
        "prestados": prestados,
        "mantenimiento": mantenimiento,
    }

    return render(request, "inventario/lista_equipos.html", context)


@login_required
def crear_equipo(request):
    if request.method == "POST":
        form = EquipoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipo creado exitosamente.")
            return redirect("lista_equipos")
    else:
        form = EquipoForm()
        
    return render(request, "inventario/crear_equipo.html", {"form": form})


@login_required
def editar_equipo(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    if request.method == "POST":
        form = EquipoForm(request.POST, instance=equipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipo actualizado exitosamente.")
            return redirect("lista_equipos")
    else:
        form = EquipoForm(instance=equipo)
        
    return render(request, "inventario/editar_equipo.html", {"equipo": equipo, "form": form})


@login_required
def eliminar_equipo(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    if request.method == "POST":
        equipo.delete()
        messages.success(request, "Equipo eliminado exitosamente.")
        return redirect("lista_equipos")
    return render(request, "inventario/eliminar_equipo.html", {"equipo": equipo})


@login_required
def lista_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, "inventario/lista_categorias.html", {"categorias": categorias})


@login_required
def crear_categoria(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        Categoria.objects.create(nombre=nombre, descripcion=descripcion)
        messages.success(request, "Categoría creada con éxito.")
        return redirect("lista_categorias")
    return render(request, "inventario/crear_categoria.html")


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        categoria.nombre = request.POST.get("nombre")
        categoria.descripcion = request.POST.get("descripcion")
        categoria.save()
        messages.success(request, "Categoría actualizada con éxito.")
        return redirect("lista_categorias")
    return render(request, "inventario/editar_categoria.html", {"categoria": categoria})


@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoría eliminada con éxito.")
        return redirect("lista_categorias")
    return render(request, "inventario/eliminar_categoria.html", {"categoria": categoria})


@login_required
def api_estadisticas_dashboard(request):
    data = {
        "total": Equipo.objects.count(),
        "disponibles": Equipo.objects.filter(estado="Disponible").count(),
        "prestados": Equipo.objects.filter(estado="Prestado").count(),
        "mantenimiento": Equipo.objects.filter(estado="Mantenimiento").count(), 
    }
    return JsonResponse(data)


@login_required
def reporte_equipos_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_equipos.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=20
    )
    story.append(Paragraph("Reporte General de Equipos de Laboratorio", title_style))
    story.append(Spacer(1, 10))

    data = [["ID", "Nombre", "N° Serie/Código", "Categoría", "Estado"]]
    equipos = Equipo.objects.all()
    for eq in equipos:
        n_serie = getattr(eq, 'serie', None) or getattr(eq, 'numero_serie', None) or getattr(eq, 'codigo', 'N/A')
        
        data.append([
            str(eq.id),
            eq.nombre,
            n_serie,
            eq.categoria.nombre if eq.categoria else "S/C",
            eq.estado
        ])

    table = Table(data, colWidths=[40, 150, 120, 120, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
    ]))
    
    story.append(table)
    doc.build(story)
    return response