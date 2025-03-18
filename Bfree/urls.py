from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('authentication.urls')),
    path('crypto/', include('crypto_wallet.urls')),
    path('card/', include('card.urls')),
    path('webhook/', include('webhooks.urls'))
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [path('i18n/', include('django.conf.urls.i18n'))]
