import os
import django

# Configuramos el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Define aquí las credenciales que usarás para entrar en producción
username = 'admin'
email = 'admin@example.com'
password = 'TuContrasenaSegura123'  # <-- Cambia esto por la contraseña que quieras usar

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("¡Superusuario creado con éxito en producción!")
else:
    print("El superusuario ya existe.")