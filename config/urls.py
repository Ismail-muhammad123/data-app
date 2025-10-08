from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', RedirectView.as_view(url='admin/', permanent=True)),
    path('admin/', admin.site.urls),
    path('api/account/', include("users.urls")),
    path('api/wallet/', include("wallet.urls")),
    path('api/payment/', include("payments.urls")),
    path('api/orders/', include("orders.urls")),
    
    # SWAGGER
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),   
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)