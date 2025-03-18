from django.contrib import admin
from .models import *
from django.db.models import Sum
from admin_interface.models import Theme
from django.utils.translation import gettext_lazy as _

admin.site.unregister(Theme)

class AccountAdmin(admin.ModelAdmin):
    list_display = ('total_funding_profit', 'total_card_creation_profit', 'total_card_debit_withdrawals', 'total_card_maintenance_profit', 'total_wallet_balance')
    list_display_links = None

    def has_add_permission(self, request):
        return not Account.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
        
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Account Overview")
        return changelist

class WalletTransactionsAdmin(admin.ModelAdmin): 
    search_fields = ('user__username',)
    readonly_fields = ['timestamp', 'fee', 'funded_amount', 'purpose']
    list_display = ('user_email', 'purpose', 'amount', 'funded_amount', 'fee', 'fee_percentage', 'credit', 'timestamp',)
    list_filter = ('credit', 'purpose', 'timestamp',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Wallet Transactions")
        return changelist
    
class CryptoTransactionsAdmin(admin.ModelAdmin): 
    search_fields = ('user__username',)
    readonly_fields = ['processed', 'updated_at', 'created_at',]
    list_display = ('user_email', 'transaction_id', 'amount', 'processed', 'updated_at', 'created_at',)
    list_filter = ('processed', 'updated_at', 'created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Crypto Transactions")
        return changelist
        
class CriticalBroadcast_Admin(admin.ModelAdmin):
    search_fields = ('message',)
    readonly_fields = ('id', 'updated_at', 'created_at',)
    list_display = ('message', 'active', 'updated_at', 'created_at',)
    list_display_links = ('message',)
        
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Critical Broadcasts")
        return changelist

admin.site.register(WalletTransaction, WalletTransactionsAdmin)
admin.site.register(CryptoTransaction, CryptoTransactionsAdmin)
admin.site.register(CriticalBroadcast, CriticalBroadcast_Admin)
admin.site.register(Account, AccountAdmin)

admin.site.site_header = 'Bfree Admin'
admin.site.site_title = 'Bfree Admin'
admin.site.index_title = 'Welcome to Bfree Admin.'