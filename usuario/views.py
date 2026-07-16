from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import login # Importación nueva para auto-loguear
from .forms import UsuarioForm
from django.contrib import messages

@login_required
def lista_usuarios(request):
    # Solo el administrador puede ver la lista de usuarios
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para acceder.")
        return redirect("dashboard_user")

    usuarios = User.objects.all()

    return render(
        request,
        "usuario/lista_usuarios.html",
        {
            "usuarios": usuarios
        }
    )

@login_required
def crear_usuario(request):
    # Solo el administrador puede crear usuarios
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para acceder.")
        return redirect("dashboard_user")

    if request.method == "POST":
        form = UsuarioForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("lista_usuarios")
    else:
        form = UsuarioForm()

    return render(
        request,
        "usuario/crear_usuario.html",
        {
            "form": form
        }
    )

def registro(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)

        if form.is_valid():
            # 1. Guardamos al usuario
            usuario = form.save(commit=False)
            usuario.is_active = True
            usuario.save()

            # 2. Le asignamos automáticamente el grupo "Usuario"
            grupo_usuario, created = Group.objects.get_or_create(name='Usuario')
            usuario.groups.add(grupo_usuario)

            # 3. Iniciamos su sesión de forma automática
            login(request, usuario)

            messages.success(request, f"¡Bienvenido {usuario.username}! Tu cuenta está lista para pedir equipos.")
            
            # 4. Lo mandamos directo adentro (cambia "dashboard" por el nombre de tu url principal si es diferente)
            return redirect("dashboard") 

    else:
        form = UsuarioForm()

    return render(
        request,
        "usuario/registro.html",
        {
            "form": form
        }
    )

@login_required
def asignar_rol(request, id):
    # Solo el administrador puede asignar roles
    if not request.user.groups.filter(name="Administrador").exists():
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect("dashboard_user")

    usuario = get_object_or_404(User, id=id)

    if request.method == "POST":
        rol = request.POST.get("rol")
        usuario.groups.clear()
        grupo = Group.objects.get(name=rol)
        usuario.groups.add(grupo)

        messages.success(request, "Rol asignado correctamente.")
        return redirect("lista_usuarios")

    return render(
        request,
        "usuario/asignar_rol.html",
        {
            "usuario": usuario
        }
    )