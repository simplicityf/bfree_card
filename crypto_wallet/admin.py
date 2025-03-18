from django.contrib import admin
from crypto_wallet.models import *
from django.utils.translation import gettext_lazy as _


# Register your models here.
class CryptoAddressAdmin(admin.ModelAdmin): 
    search_fields = ('coin','network_chain')
    list_display = ('address', 'coin', 'network_chain')
    
class CryptoFundingRequestAdmin(admin.ModelAdmin): 
    search_fields = ('user__email','transaction_id')
    list_display = ('user_email', 'amount', 'confirmed', 'fee_percentage', 'last_update_timestamp', 'creation_timestamp',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Crypto Funding Requests")
        return changelist

admin.site.register(CryptoAddress, CryptoAddressAdmin)
admin.site.register(CryptoFundingRequest, CryptoFundingRequestAdmin)