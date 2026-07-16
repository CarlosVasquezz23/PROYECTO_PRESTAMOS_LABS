from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Estadísticas
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/user/', views.dashboard_user, name='dashboard_user'),
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
    
    # Registro de rostros (HTML y API en la misma función)
    path('registrar-rostro/', views.registrar_rostro, name='registrar_rostro'),
    
    # API del login que procesa los datos que envía la cámara
    path('api/login-facial/', views.login_facial, name='login_facial'),
]