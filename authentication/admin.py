from django.contrib import admin
from authentication.models import *
from django.utils.translation import gettext_lazy as _

class LoginDetail_Admin(admin.ModelAdmin): 
    search_fields = ('user__username',)
    readonly_fields = ['timestamp',]
    list_display = ('user', 'user_ip_address', 'user_os', 'timestamp')
    
class Profile_Admin(admin.ModelAdmin): 
    search_fields = ('user__username',)
    readonly_fields = ['wallet_balance', 'created',]
    
    list_display = ('user_email', 'wallet_balance', 'phone_number', 'country')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

class AlphaspaceAuthToken_Admin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not AlphaspaceAuthToken.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
        
    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.title = _("Alphaspace Authentication Tokens")
        return changelist

# Register your models here.
admin.site.register(Profile, Profile_Admin)
admin.site.register(LoginDetail, LoginDetail_Admin)
#admin.site.register(AlphaspaceAuthToken, AlphaspaceAuthToken_Admin)

