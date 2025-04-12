from rest_framework import serializers
from .models import *

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
        depth = 1  # Pour l'affichage des relations complètes

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Conversion des IDs en objets complets avec le depth=1
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
    conjoint = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), 
        allow_null=True, 
        required=False
    )
    enfants = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Client
        fields = '__all__'
        list_serializer_class = ClientBulkSerializer

    def create(self, validated_data):
        enfants_data = validated_data.pop('enfants', [])
        conjoint_data = validated_data.pop('conjoint', None)
        
        client = Client.objects.create(**validated_data)
        
        if conjoint_data:
            client.conjoint = conjoint_data
            client.save()
        
        client.enfants.set(enfants_data)
        return client

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