from django.db import migrations


CAREERS = [
    'Ingeniería Agronómica',
    'Ingeniería Civil',
    'Ingeniería de Diseño de Producto',
    'Ingeniería de Procesos',
    'Ingeniería de Producción',
    'Ingeniería de Sistemas',
    'Ingeniería Física',
    'Ingeniería Matemática',
    'Ingeniería Mecánica',
    'Geociencias',
    'Biología',
    'Administración de Negocios',
    'Contaduría Pública',
    'Economía',
    'Finanzas',
    'Mercadeo',
    'Negocios Internacionales',
    'Derecho',
    'Ciencias Políticas',
    'Comunicación Social',
    'Psicología',
    'Música',
    'Diseño Urbano y Gestión del Hábitat',
    'Artes (Plásticas)',
]


def populate_careers(apps, schema_editor):
    Career = apps.get_model('accounts', 'Career')
    for career_name in CAREERS:
        Career.objects.get_or_create(name=career_name)


def unpopulate_careers(apps, schema_editor):
    Career = apps.get_model('accounts', 'Career')
    Career.objects.filter(name__in=CAREERS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_career_remove_studentprofile_career_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_careers, unpopulate_careers),
    ]
