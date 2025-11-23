"""
URL configuration for shopproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import render

urlpatterns = [

    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('shop.urls')),
    path('cele-admin/', include('gestion.urls')),


]

# ---- ERROR HANDLERS ----


def error_403(request, exception=None):
    return render(request, 'error/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'error/404.html', status=404)


def error_500(request):
    return render(request, 'error/500.html', status=500)


def error_502(request, exception=None):
    return render(request, 'error/502.html', status=502)


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


admin.site.site_header = "CELEBOBO"
admin.site.site_title = "celestin"
admin.site.index_title = "L'administrateur General de CELEBOBO Business"

# ---- REGISTER HANDLERS ----
handler403 = 'shopproject.urls.error_403'
handler404 = 'shopproject.urls.error_404'
handler500 = 'shopproject.urls.error_500'
handler502 = 'shopproject.urls.error_502'
