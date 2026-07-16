# backend/prestamo/urls.py
from django.urls import path
from . import views

# Definimos el espacio de nombres para esta app
app_name = 'prestamo'

urlpatterns = [
    path("", views.lista_prestamos, name="lista_prestamos"),
    path("nuevo/", views.crear_prestamo, name="crear_prestamo"),
    path("mis-prestamos/", views.mis_prestamos, name="mis_prestamos"),
    path("devolucion/", views.crear_devolucion, name="crear_devolucion"),
    path("reporte/pdf/", views.reporte_prestamos_pdf, name="reporte_prestamos_pdf"),
    path('devolver/<int:prestamo_id>/', views.procesar_devolucion, name='procesar_devolucion'), 
    path('api/mis-prestamos/', views.api_mis_prestamos, name='api_mis_prestamos'),
]