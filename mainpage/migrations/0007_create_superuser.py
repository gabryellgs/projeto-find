from django.db import migrations
from django.contrib.auth.hashers import make_password

def set_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    # Tenta achar o usuário 'gabryell'. Se não existir, cria.
    user, created = User.objects.get_or_create(
        username='gabryell',
        defaults={'email': 'gabryell@find.com'}
    )
    user.is_superuser = True
    user.is_staff = True
    user.password = make_password('admin123')
    user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0006_move_models_to_apps'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(set_superuser),
    ]
