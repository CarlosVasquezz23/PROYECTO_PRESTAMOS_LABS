# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include
from inventario import views as inventario_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Renderiza la vista de login importada desde inventario
    path('login/', inventario_views.vista_login_pagina, name='login'),
    
    # Redirige la raíz del sitio también al login visual
    path('', inventario_views.vista_login_pagina, name='login_raiz'),
    
    # Incluye el resto de las rutas de la app inventario
    path('', include('inventario.urls')), 
    
    # Incluye las rutas de la app prestamo de forma global
    path('prestamos/', include('prestamo.urls')),
    
    # Conecta las rutas de tu app usuario (aquí se genera 'usuarios/registro/')
    path('usuarios/', include('usuario.urls')),
]