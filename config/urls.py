# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include
from inventario import views as inventario_views
from prestamo import views as prestamo_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Rutas del Dashboard con Prioridad Absoluta
    # Al ponerlas aquí arriba, Django las procesa antes de entrar a inventario.urls
    path('dashboard/user/', prestamo_views.dashboard, name='dashboard_usuario_legacy'),
    path('dashboard/', prestamo_views.dashboard, name='dashboard'),
    
    # 🛠️ SOLUCIÓN AL REVERSE: Atajo exacto para el botón del historial completo de la UNEMI
    path('dashboard/user/panel/', prestamo_views.dashboard, name='dashboard_user'),
    
    # 🛠️ 1.5 ATAJOS GLOBALES DE RESCATE (Para solucionar el NoReverseMatch de la UNEMI)
    # Estas líneas interceptan las llamadas planas que hace tu plantilla sin usar namespaces
    path('dashboard/prestamos/lista/', prestamo_views.lista_prestamos, name='lista_prestamos'),
    path('dashboard/prestamos/reporte-pdf/', prestamo_views.reporte_prestamos_pdf, name='reporte_prestamos_pdf'),
    
    # 2. Rutas de Autenticación
    path('login/', inventario_views.vista_login_pagina, name='login'),
    path('', inventario_views.vista_login_pagina, name='login_raiz'),
    
    # 3. Inclusión de las Apps del Sistema
    path('prestamos/', include('prestamo.urls')),
    path('usuarios/', include('usuario.urls')),
    
    # Dejamos esta al último para que capture el resto del inventario sin pisar el dashboard
    path('', include('inventario.urls')), 
]