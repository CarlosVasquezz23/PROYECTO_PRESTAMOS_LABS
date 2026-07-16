from django import forms
from .models import Equipo, Categoria 

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej: PC de Escritorio'}),
            'categoria': forms.Select(attrs={'class': 'form-select bg-light'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej: LAB-001'}),
            'marca': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej: Dell'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej: Optiplex 3080'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej: Laboratorio 1'}),
            'estado': forms.Select(attrs={'class': 'form-select bg-light'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 3, 'placeholder': 'Detalles adicionales del equipo...'}),
        }
        

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej: Laptops, Microscopios...'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 3, 'placeholder': 'Breve descripción de la categoría...'}),
        }