from django.contrib import admin
from base.models import *
from django.contrib.auth.models import Group

admin.site.register(User)

admin.site.unregister(Group)

admin.site.site_header = 'ZerofAI | Admin'
admin.site.site_title = 'ZerofAI'