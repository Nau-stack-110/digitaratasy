from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
from django.contrib.auth.password_validation import validate_password

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
class UserSerializer(serializers.ModelSerializer):
    is_admin_commune = serializers.BooleanField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'is_superuser', 'is_staff', 
                 'is_admin_commune', 'reset_pin', 'pin_attempts', 'pin_expires_at']

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class CommuneSerializer(serializers.ModelSerializer):
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())
    admin_commune = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_admin_commune=True),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Commune
        fields = ['id', 'nom', 'region', 'admin_commune']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['region'] = RegionSerializer(instance.region).data
        if instance.admin_commune:
            representation['admin_commune'] = UserSerializer(instance.admin_commune).data
        return representation

class ClientBulkSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        clients = [Client(**item) for item in validated_data]
        return Client.objects.bulk_create(clients)

    class Meta:
        model = Client
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    qrcode = serializers.CharField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Client
        fields = '__all__'
        list_serializer_class = ClientBulkSerializer
        extra_kwargs = {
            'lieu_naissance': {'required': False}
        }

class DemandeActeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeActe
        fields = '__all__'

class AdminCommuneCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'is_admin_commune']
        extra_kwargs = {
            'is_admin_commune': {'default': True, 'read_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            is_admin_commune=True
        )
        return user

class CommuneStatSerializer(serializers.Serializer):
    commune = serializers.CharField()
    count = serializers.IntegerField()

class StatisticsSerializer(serializers.Serializer):
    users = serializers.IntegerField()
    regions = serializers.IntegerField()
    communes = serializers.IntegerField()
    clients = serializers.IntegerField()
    administrateurs = serializers.IntegerField()
    demandes_acte = serializers.IntegerField()
    types_acte = serializers.DictField(child=serializers.IntegerField())
    clients_par_commune = CommuneStatSerializer(many=True)
    
    
class MytokenObtainPairView(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        token['username'] = user.username
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser 
        token['is_staff'] = user.is_staff         
        token['is_client'] = user.is_client
        token['is_admin_commune'] = user.is_admin_commune
        
        return token
    
    
    User = get_user_model()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            user.generate_reset_pin()  # Générer et enregistrer le PIN
            
            # # Envoyer le PIN par email
            # send_mail(
            #     subject="Réinitialisation du mot de passe",
            #     message=f"Votre code de réinitialisation est : {user.reset_pin}\n\nIl est valide pendant 10 minutes.",
            #     from_email="andriatahianaarnaud@gmail.com",
            #     recipient_list=[user.email],
            #     fail_silently=False
            # )

        except ObjectDoesNotExist:
            raise serializers.ValidationError("Aucun compte trouvé avec cet email.")

        return value
        
        
        

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_pin = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
            
            # Vérifier si le PIN est expiré
            if user.pin_expires_at and user.pin_expires_at < now():
                raise serializers.ValidationError("Le PIN a expiré. Demandez un nouveau PIN.")

            # Vérifier les tentatives
            if user.pin_attempts >= 3:
                raise serializers.ValidationError("Trop de tentatives incorrectes. Demandez un nouveau PIN.")

            # Vérifier si le PIN est correct
            if user.reset_pin != data["reset_pin"]:
                user.pin_attempts += 1 
                user.save()
                raise serializers.ValidationError("PIN incorrect. Essayez à nouveau.")

            # Réinitialiser le mot de passe et supprimer le PIN
            user.set_password(data["new_password"])
            user.reset_pin = None
            user.pin_attempts = 0
            user.pin_expires_at = None
            user.save()

        except ObjectDoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")

        return data
        
        
        
        
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user  # Récupérer l'utilisateur connecté
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        
        user.set_password(data["new_password"])
        user.save()
        return data