# backend/inventario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 🌟 ELIMINAMOS LA INTERFERENCIA:
    # Quitamos cualquier ruta que use 'dashboard/user/' a secas para que config/urls.py haga su trabajo.
    path('dashboard/user/historial/', views.historial_completo_user, name='historial_completo_user'),
    path('api/estadisticas/', views.api_estadisticas_dashboard, name='api_estadisticas'),
    path('logout/', views.logout_usuario, name='logout'),

    # CRUD de Equipos
    path("equipos/", views.lista_equipos, name="lista_equipos"),
    path("equipos/nuevo/", views.crear_equipo, name="crear_equipo"),
    path("equipos/<int:pk>/editar/", views.editar_equipo, name="editar_equipo"),
    path("equipos/<int:pk>/eliminar/", views.eliminar_equipo, name="eliminar_equipo"),
    
    # CRUD de Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),

    # Reportes
    path("reporte/equipos/pdf/", views.reporte_equipos_pdf, name="reporte_equipos_pdf"),
    
    # Registro de rostros y API facial
    path('registrar-rostro/', views.registrar_rostro, name='registrar_rostro'),
    path('api/login-facial/', views.login_facial, name='login_facial'),
]