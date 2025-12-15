from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.validators import UniqueValidator
from website.models import *
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SolutionGetSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        image = settings.BASE_URL + (obj.image.url) if obj.image else 'https://images.pexels.com/photos/355948/pexels-photo-355948.jpeg?cs=srgb&dl=pexels-pixabay-355948.jpg&fm=jpg'
        return image
    
    class Meta:
        model = Solutions
        fields = '__all__'

class ServiceGetSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        image = settings.BASE_URL + (obj.image.url) if obj.image else 'https://images.pexels.com/photos/355948/pexels-photo-355948.jpeg?cs=srgb&dl=pexels-pixabay-355948.jpg&fm=jpg'
        return image
    
    class Meta:
        model = Services
        fields = '__all__'


class CaseStudyGetSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    author = serializers.CharField(source='author.get_full_name')


    def get_image(self, obj):
        image = settings.BASE_URL + (obj.image.url) if obj.image else None
        return image
    
    class Meta:
        model = CaseStudy
        fields = '__all__'


class TestimonialGetSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.get_full_name')
    company = serializers.CharField(source='company.company_name')
    class Meta:
        model = Testimonial
        fields = '__all__'


class BlogPostsGetSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    author = serializers.CharField(source='author.get_full_name')

    def get_image(self, obj):
        image = settings.BASE_URL + (obj.image.url) if obj.image else None
        return image
    
    class Meta:
        model = BlogPosts
        fields = '__all__'


class ContactUsGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = '__all__'


class ContactUsPostSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    message = serializers.CharField(required=True)
    phone_number = serializers.IntegerField(required=False, allow_null=True)


class CareerGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = '__all__'


class CareerApplicationGetSerializer(serializers.ModelSerializer):
    carrer = serializers.CharField(source='carrer.position')
    resume = serializers.SerializerMethodField()

    def get_resume(self, obj):
        resume = settings.BASE_URL + (obj.resume.url) if obj.resume else None
        return resume
    
    class Meta:
        model = CarrerSubmission
        fields = '__all__'


class CareerPostSerializer(serializers.Serializer):
    carrer_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True)
    resume = serializers.CharField(required=True)
