from django.contrib import admin
from .models import *
# Register your models here.

class Payload_Admin(admin.ModelAdmin): 
    search_fields = ('payload',)
    list_display = ('source', 'event', 'creation_timestamp')

admin.site.register(Payload, Payload_Admin)


