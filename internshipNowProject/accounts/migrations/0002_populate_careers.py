from django.db import migrations


CAREERS = [
    'Agricultural Engineering',
    'Civil Engineering',
    'Product Design Engineering',
    'Process Engineering',
    'Production Engineering',
    'Systems Engineering',
    'Physics Engineering',
    'Mathematical Engineering',
    'Mechanical Engineering',
    'Geosciences',
    'Biology',
    'Business Administration',
    'Public Accounting',
    'Economics',
    'Finance',
    'Marketing',
    'International Business',
    'Law',
    'Political Science',
    'Social Communication',
    'Psychology',
    'Music',
    'Urban Design and Habitat Management',
    'Visual Arts',
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
