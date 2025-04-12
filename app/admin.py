from django.contrib import admin
from .models import *


class CommuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'admin_commune')
    list_filter = ('region',)

admin.site.register(Region)
admin.site.register(Commune, CommuneAdmin)
admin.site.register(Client)
admin.site.register(DemandeActe)
