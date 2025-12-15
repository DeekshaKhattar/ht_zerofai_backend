"""
URL configuration for zerofai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


from django.conf import settings
from django.conf.urls.static import static
from website.views import *

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="ZerofAI",
        default_version='v1',
        description="ZerofAI is a versatile AI-driven solution that can be deployed as either a SaaS-based application or a standalone on-premise application, depending on customer needs.",
        terms_of_service="https://www.your-website.com/terms/",
        contact=openapi.Contact(email="abhishek.g@teamcomputers.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    # base urls
    path('auth/', include('base.urls', namespace='base')),
    # website urls
    path('website/', include('website.urls', namespace='webiste')),
    # admin portal
    path('portal/', include('admin_portal.urls', namespace='portal')),
    # swagger documentation
    re_path(r'^zerofai-swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('zerofai-swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('zerofai-redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
    urlpatterns += staticfiles_urlpatterns()