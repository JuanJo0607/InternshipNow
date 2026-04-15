from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('internshipApp', '0008_merge_20260414_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='internshipoffer',
            name='closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='InternshipOfferView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('offer', models.ForeignKey(on_delete=models.CASCADE, related_name='views', to='internshipApp.internshipoffer')),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='offer_views', to='internshipApp.studentprofile')),
            ],
        ),
    ]
