from datetime import timedelta
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
import qrcode
import base64
from io import BytesIO
from django.core.exceptions import ValidationError
# Create your models here.

class User(AbstractUser):
    username = models.CharField(max_length=70)
    email = models.EmailField(unique=True)
    is_admin_commune = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    reset_pin = models.CharField(max_length=6, null=True, blank=True)
    pin_attempts = models.IntegerField(default=0)
    pin_expires_at = models.DateTimeField(null=True, blank=True)
    client_linked = models.OneToOneField(
        'Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account'
    )

    def generate_reset_pin(self):
        """Génère un PIN à 6 chiffres, définit une expiration et réinitialise les tentatives."""
        self.reset_pin = str(random.randint(100000, 999999))  # Génère un PIN aléatoire
        self.pin_attempts = 0  # Réinitialiser le compteur de tentatives
        self.pin_expires_at = pow() + timedelta(minutes=10)  # Expiration dans 10 minutes
        self.save()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    

class Region(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class Commune(models.Model):
    nom = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="communes")
    admin_commune = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='communes_adminisrees'
    )

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"


class Client(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin')
    ]
    
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    lieu_naissance = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    adresse = models.CharField(max_length=255)
    cin = models.CharField(max_length=20, unique=True)
    image = models.ImageField(upload_to='client_images/', null=True, blank=True)
    conjoint = models.CharField( max_length=233, null=True, blank=True)
    enfants = models.CharField( max_length=233, null=True, blank=True)
    
    # conjoint = models.OneToOneField(
    #     'self', 
    #     null=True, 
    #     blank=True, 
    #     on_delete=models.SET_NULL, 
    #     related_name='epoux_de'
    # )
    # enfants = models.ManyToManyField(
    #     'self', 
    #     symmetrical=False, 
    #     related_name='parents', 
    #     blank=True
    # )
    qrcode = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def generate_qrcode(self):
        data = {
            "nom": self.nom,
            "prenom": self.prenom,
            "date_naissance": str(self.date_naissance),
            "lieu_naissance": self.lieu_naissance.nom if self.lieu_naissance else None,
            # "conjoint": f"{self.conjoint.nom} {self.conjoint.prenom}" if self.conjoint else None,
            # "enfants": [f"{enfant.nom} {enfant.prenom}" for enfant in self.enfants.all()]
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered)
        return base64.b64encode(buffered.getvalue()).decode()

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Premier enregistrement pour obtenir l'ID
        is_new = not self.pk
        if is_new:
            super().save(*args, **kwargs)

        # Génération du QR code après avoir l'ID
        if is_new or self.has_changed():
            self.qrcode = self.generate_qrcode()
            if is_new:
                # Mise à jour directe pour éviter la récursion
                Client.objects.filter(pk=self.pk).update(qrcode=self.qrcode)
            else:
                super().save(*args, **kwargs)

        # Enregistrement final pour les instances existantes
        if not is_new:
            super().save(*args, **kwargs)

        # Modification de la génération d'email pour inclure un identifiant unique
        email = f'client_{self.cin}@digitaratasy.mg'  # Nouveau format d'email

        # Création utilisateur avec vérification d'unicité
        User.objects.update_or_create(
            client_linked=self,
            defaults={
                'username': self.cin,
                'email': email,  # Utilisation du nouvel email
                'is_client': True,
                'first_name': self.prenom,
                'last_name': self.nom
            }
        )

    def has_changed(self):
        if self.pk:
            original = Client.objects.get(pk=self.pk)
            return any(
                getattr(self, field) != getattr(original, field)
                for field in ['nom', 'prenom', 'date_naissance', 'lieu_naissance']
            ) or self.enfants.exclude(pk__in=original.enfants.all()).exists()
        return True

    # def clean(self):
    #     super().clean()
    #     if self.conjoint and self.conjoint.sexe == self.sexe:
    #         raise ValidationError("Les conjoints doivent être de sexe différent")


class TypeActe(models.TextChoices):
    ACTE_NAISSANCE = 'naissance', "Acte de naissance"
    COPIE_ACTE = 'copie', "Copie d'acte"
    CIN = 'cin', "Carte d'identité (CIN)"
    ACTE_MARIAGE = 'mariage', "Acte de mariage"
    LEGALISATION = 'legalise', "Légalisation de document"
    ACTE_DE_DIVORCE = 'divorce', "Acte de divorce"
    ACTE_DE_DECES = 'decès', "Acte de decès"


class DemandeActe(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='demandes')
    type_acte = models.CharField(max_length=20, choices=TypeActe.choices)
    date_demande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, default='en attente')

    def __str__(self):
        return f"{self.client.nom} - {self.get_type_acte_display()}"


# @receiver(m2m_changed, sender=Client.enfants.through)
# def update_qrcode_on_enfant_change(sender, instance, action, **kwargs):
#     if action in ['post_add', 'post_remove', 'post_clear']:
#         instance.save()  # regenration du QR code


@receiver(post_save, sender=Client)
def create_client_user(sender, instance, created, **kwargs):
    if created:
        User.objects.create_user(
            username=instance.cin,
            email=f'{instance.cin}@client.digitaratasy',
            password=instance.cin,  # Mot de passe par défaut = CIN
            is_client=True,
            first_name=instance.prenom,
            last_name=instance.nom
        )

