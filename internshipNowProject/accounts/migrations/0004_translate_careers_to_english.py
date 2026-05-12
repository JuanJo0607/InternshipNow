from django.db import migrations

CAREER_TRANSLATIONS = {
    'Ingeniería Agronómica': 'Agricultural Engineering',
    'Ingeniería Civil': 'Civil Engineering',
    'Ingeniería de Diseño de Producto': 'Product Design Engineering',
    'Ingeniería de Procesos': 'Process Engineering',
    'Ingeniería de Producción': 'Production Engineering',
    'Ingeniería de Sistemas': 'Systems Engineering',
    'Ingeniería Física': 'Physics Engineering',
    'Ingeniería Matemática': 'Mathematical Engineering',
    'Ingeniería Mecánica': 'Mechanical Engineering',
    'Geociencias': 'Geosciences',
    'Biología': 'Biology',
    'Administración de Negocios': 'Business Administration',
    'Contaduría Pública': 'Public Accounting',
    'Economía': 'Economics',
    'Finanzas': 'Finance',
    'Mercadeo': 'Marketing',
    'Negocios Internacionales': 'International Business',
    'Derecho': 'Law',
    'Ciencias Políticas': 'Political Science',
    'Comunicación Social': 'Social Communication',
    'Psicología': 'Psychology',
    'Música': 'Music',
    'Diseño Urbano y Gestión del Hábitat': 'Urban Design and Habitat Management',
    'Artes (Plásticas)': 'Visual Arts',
}


def translate_careers(apps, schema_editor):
    Career = apps.get_model('accounts', 'Career')
    for spanish, english in CAREER_TRANSLATIONS.items():
        Career.objects.filter(name=spanish).update(name=english)


def reverse_translate_careers(apps, schema_editor):
    Career = apps.get_model('accounts', 'Career')
    for spanish, english in CAREER_TRANSLATIONS.items():
        Career.objects.filter(name=english).update(name=spanish)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_populate_careers'),
    ]

    operations = [
        migrations.RunPython(translate_careers, reverse_translate_careers),
    ]
