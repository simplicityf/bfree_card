from django.contrib import admin
from django.urls import path, include
# Serve static files in development
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Group API endpoints under /api/ for clarity
    path("core/", include("core.urls")),
    path("auth/", include("authentication.urls")),
    path("crypto/", include("crypto_wallet.urls")),
    path("card/", include("card.urls")),
    path("webhook/", include("webhooks.urls")),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# i18n endpoints if needed
# Used for changing language settings
urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')) 
]
