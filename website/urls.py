from django.urls import path
from website.apis.v1.urls import urlpatterns as api_v1_urls
from base.views import *

app_name = 'webiste'

urlpatterns = []

urlpatterns = urlpatterns + api_v1_urls