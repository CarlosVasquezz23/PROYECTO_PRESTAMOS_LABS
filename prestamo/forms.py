from django import forms
from django.utils import timezone  
from .models import Prestamo, Devolucion  
from inventario.models import Equipo

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['equipo', 'fecha_devolucion']
        widgets = {
            # Aplicamos la clase 'form-select' de Bootstrap al selector de equipos
            'equipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            # Aplicamos 'form-control' y convertimos el input en un calendario nativo HTML5
            'fecha_devolucion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo equipos que no estén ocupados
        self.fields['equipo'].queryset = Equipo.objects.filter(estado='Disponible')

    def clean(self):
        cleaned_data = super().clean()
        fecha_devolucion = cleaned_data.get('fecha_devolucion')
        
        # Validación para evitar el error de fechas que se vio en la captura
        if fecha_devolucion:
            ahora = timezone.now()
            if fecha_devolucion < ahora:
                self.add_error('fecha_devolucion', 'La fecha de devolución no puede ser anterior a la fecha y hora actual del préstamo.')
        
        return cleaned_data


class DevolucionForm(forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ['prestamo', 'observaciones']
        widgets = {
            'prestamo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe aquí el estado en el que regresa el equipo...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo préstamos vigentes
        self.fields['prestamo'].queryset = Prestamo.objects.filter(estado="Activo")