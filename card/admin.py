from django.contrib import admin
from .models import *
from django.utils.translation import gettext_lazy as _
# Register your models here.

class CardProfitDeclaration_Admin(admin.ModelAdmin):
    list_display = ('failed_card_payment_fee', 'card_maintenance_fee')

    def has_add_permission(self, request):
        return not CardProfitDeclaration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

    #def has_change_permission(self, request, obj=None):
    #    return False
        
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Card Fees")
        return changelist
        
class Card_Admin(admin.ModelAdmin):
    search_fields = ('user__email', 'card_id', 'card_number')
    list_display = ('user', 'brand', 'card_masked_number')
    list_display_links = ('user',)

    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Cards")
        return changelist


admin.site.register(Card, Card_Admin)
admin.site.register(CardProfitDeclaration, CardProfitDeclaration_Admin)
