# Generated by Django 5.2 on 2025-04-12 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_client_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demandeacte',
            name='type_acte',
            field=models.CharField(choices=[('naissance', 'Acte de naissance'), ('copie', "Copie d'acte"), ('cin', "Carte d'identité (CIN)"), ('mariage', 'Acte de mariage'), ('legalise', 'Légalisation de document'), ('divorce', 'Acte de divorce')], max_length=20),
        ),
    ]
