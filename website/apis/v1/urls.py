from django.urls import path
from website.apis.v1.views import *
# from rest_framework_simplejwt import views as jwt_views

app_name = 'website'

urlpatterns = [
    path('api/v1/solutions/', SolutionsOperations.as_view(), name='get_website_solution'),
    path('api/v1/services/', ServiceOperations.as_view(), name='get_website_services'),
    path('api/v1/casestudy/', CaseStudiesOperations.as_view(), name='get_website_case_study'),
    path('api/v1/testimonial/', TestimonialOperations.as_view(), name='get_website_testimonial'),
    path('api/v1/blogs/', BlogPostsOperations.as_view(), name='get_website_blog'),
    path('api/v1/carrers/', CareerOperations.as_view(), name='get_website_carrers'),
    path('api/v1/contact/us/', ContactUsOperations.as_view(), name='post_contact_us'),
]