# Generated by Django 5.2 on 2025-04-13 02:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_remove_client_conjoint_remove_client_enfants'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='conjoint',
            field=models.CharField(blank=True, max_length=233, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='enfants',
            field=models.CharField(blank=True, max_length=233, null=True),
        ),
    ]
