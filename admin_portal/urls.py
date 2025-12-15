from django.urls import path
from admin_portal.apis.v1.urls import urlpatterns as api_v1_urls

app_name = 'portal'

urlpatterns = []

urlpatterns = urlpatterns + api_v1_urls