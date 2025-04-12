from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'demandes-acte', views.DemandeActeViewSet)
router.register(r'regions', views.RegionViewSet)
router.register(r'communes', views.CommuneViewSet)
router.register(r'clients', views.ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('clients/bulk/', views.ClientBulkCreateView.as_view(), name='client-bulk-create'),
    path('create-admin-commune/', views.AdminCommuneCreateView.as_view(), name='create-admin-commune'),
    path('stats/', views.StatisticsView.as_view(), name='statistics'),
]
