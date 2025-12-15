from rest_framework import serializers
from django.contrib.auth import authenticate
from base.models import *
from django.conf import settings
import logging
from admin_portal.models import *

logger = logging.getLogger(__name__)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=200, required=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                user = None
                status = False
            else:
                user = user
                status = True
        data['user'] =  user
        data['status'] = status
        return data
    

class UserGetSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    license_data = serializers.SerializerMethodField()

    def get_profile_image(self, obj):
        profile_image = settings.BASE_URL + (obj.profile_image.url) if obj.profile_image else None
        return profile_image
    
    def get_license_data(self, obj):
        if obj.user_type == 'customer':
            customer = Customer.objects.get(user=obj)
            license = License.objects.get(customer=customer)
            data = {
                "total_license" : license.total_license,
                "used_license": license.used_license,
                "spare_license" : license.avialable_license
            }
            return data
        else:
            return None
    
    class Meta:
        model = User
        # fields = '__all__'
        exclude = ('password',)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    otp = serializers.CharField(required=False, allow_null=True, allow_blank=True)
