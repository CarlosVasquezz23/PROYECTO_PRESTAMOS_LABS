# backend/usuario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Lista de usuarios (responderá en: /usuarios/)
    path(
        '',
        views.lista_usuarios,
        name='lista_usuarios'
    ),

    # Crear usuario (responderá en: /usuarios/crear/)
    path(
        'crear/',
        views.crear_usuario,
        name='crear_usuario'
    ),

    # Registro público (responderá en: /usuarios/registro/)
    path(
        'registro/',
        views.registro,
        name='registro'
    ),

    # Asignar rol (responderá en: /usuarios/asignar/<id>/)
    path(
        'asignar/<int:id>/',
        views.asignar_rol,
        name='asignar_rol'
    ),
]