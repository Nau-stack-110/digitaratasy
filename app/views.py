from django.shortcuts import render
from rest_framework import viewsets, generics
from .models import *
from .serializer import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

class CommuneViewSet(viewsets.ModelViewSet):
    queryset = Commune.objects.all()
    serializer_class = CommuneSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class DemandeActeViewSet(viewsets.ModelViewSet):
    queryset = DemandeActe.objects.all()
    serializer_class = DemandeActeSerializer
    #permission_classes = [IsAuthenticated]

class AdminCommuneCreateView(generics.CreateAPIView):
    serializer_class = AdminCommuneCreateSerializer
    #permission_classes = [IsAuthenticated]

class ClientBulkCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    # permission_classes = [IsAuthenticated]  # Décommentez si nécessaire

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class StatisticsView(APIView):
    def get(self, request, format=None):
        User = get_user_model()
        
        # Statistiques existantes
        data = {
            "users": User.objects.count(),
            "regions": Region.objects.count(),
            "communes": Commune.objects.count(),
            "clients": Client.objects.count(),
            "administrateurs": User.objects.filter(is_admin_commune=True).count(),
            "demandes_acte": DemandeActe.objects.count(),
            
            "types_acte": {
                choice[1]: DemandeActe.objects.filter(type_acte=choice[0]).count()
                for choice in TypeActe.choices
            },
            "clients_par_commune": [
                {
                    "commune": commune.nom,
                    "count": Client.objects.filter(lieu_naissance=commune).count()
                } 
                for commune in Commune.objects.all()
            ]
        }
        
        serializer = StatisticsSerializer(data)
        return Response(serializer.data)
