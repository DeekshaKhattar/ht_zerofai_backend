from rest_framework.views import APIView
from rest_framework.views import status
from rest_framework.response import Response
from website.apis.v1.serializers import *
from rest_framework.permissions import AllowAny
from django.db.models import Q, Value, Sum, F
from base.mixins import PaginationHandlerMixin, CustomPagination
import logging
from io import BytesIO
import base64
from random import randint
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from django.conf import settings
from premailer import transform
import email.header
logger = logging.getLogger(__name__)
import re

"""
Here all the website APIs will be available.
"""

"""
This will be used with the following methods:
1. GET: To return all the active solutions
"""
class SolutionsOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = SolutionGetSerializer
    permission_classes = [AllowAny]
    queryset = Solutions.objects.filter(status=True)

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    solution_name__icontains=search
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for website solutions due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)
    
class ServiceOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ServiceGetSerializer
    permission_classes = [AllowAny]
    queryset = Services.objects.filter(status=True)

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    service_name__icontains=search
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for website services due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class CaseStudiesOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = CaseStudyGetSerializer
    permission_classes = [AllowAny]
    queryset = CaseStudy.objects.filter(status=True)

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for website case studies due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class TestimonialOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = TestimonialGetSerializer
    permission_classes = [AllowAny]
    queryset = Testimonial.objects.filter(status=True)

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(content__icontains=search)
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for website testimonials due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)
    

class BlogPostsOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = BlogPostsGetSerializer
    permission_classes = [AllowAny]
    queryset = BlogPosts.objects.filter(status='published')

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for website blogs due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)
    

class CareerOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = CareerGetSerializer
    post_serializer_class = CareerPostSerializer
    permission_classes = [AllowAny]
    queryset = Career.objects.filter(status=True)
    post_queryset = CarrerSubmission.objects.all()

    def get_formatted_doc(self, b64_data):
        doc = None
        try:
            # Remove the header from the base64 string
            doc_data = b64_data.split(',')[1]
            # Convert the base64 string to bytes
            doc_bytes = base64.b64decode(doc_data)
            doc = BytesIO(doc_bytes)
        except Exception as e:
            logger.warning(f"Can not decode the document due to {e}")
        return doc

    def create_application_submission_entry(self, **kwrags):
        obj = None
        try:
            obj = CarrerSubmission.objects.create(**kwrags)
        except Exception as e:
            logger.warning(f"Can not make entry to carrer application model due to: {e}")
        return obj

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(position__icontains=search) |
                    Q(location__icontains=search) |
                    Q(description__icontains=search) |
                    Q(requirements__icontains=search)
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for website carrers due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)

    def post(self, request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        try:
            if not request.data.get('name'):
                response['message'] = 'Name is mandatory.'
                return Response(response, status=status_code)
            
            if not request.data.get('email'):
                response['message'] = 'Email is mandatory.'
                return Response(response, status=status_code)
            
            if request.data.get('phone_number'):
                if len(str(request.data.get('phone_number'))) != 10:
                    response['message'] = 'Phone number should be 10 in length.'
                    return Response(response, status=status_code)
                if not str(request.data.get('phone_number')).isdigit():
                    response['message'] = 'Phone number should be numeric.'
                    return Response(response, status=status_code)
            else:
                response['message'] = 'Phone number is mandatory.'
                return Response(response, status=status_code)
            
            if not request.data.get('resume'):
                response['message'] = 'Resume is mandatory.'
                return Response(response, status=status_code)

            if not request.data.get('carrer_id'):
                response['message'] = 'Carrer selection is mandatory.'
                return Response(response, status=status_code)

            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                try:
                    try:
                        carrer_obj = Career.objects.get(id=serializer.validated_data.get('carrer_id'))
                        obj_data = {
                            "carrer" : carrer_obj,
                            "name" : serializer.validated_data.get('name'),
                            "email" : serializer.validated_data.get('email'),
                            "phone_number" : serializer.validated_data.get('phone_number'),
                        }
                        if serializer.validated_data.get('resume'):
                            doc_extension = serializer.validated_data.get('resume').split('/')[1].split(';')[0]
                            if doc_extension in ['jpg', 'jpeg', 'png',
                                    'gif', 'bmp', 'svg', 'xls', 'xlsx',
                                    'vnd.openxmlformats-officedocument.wordprocessingml.document']:
                                response['message'] = 'Please provide a valid pdf or word format.'
                                return Response(response, status=status_code)
                        contact_us_obj = self.create_application_submission_entry(**obj_data)
                        if contact_us_obj:
                            b64_doc = serializer.validated_data.get('resume')
                            image = self.get_formatted_doc(b64_doc)
                            if image:
                                doc_extension = b64_doc.split('/')[1].split(';')[0]
                                contact_us_obj.resume.delete(False)
                                contact_us_obj.resume.save(f"{contact_us_obj.name.replace(' ','')}_{contact_us_obj.id}_{randint(0, 100)}.{doc_extension}", image)
                            carrer_obj.application_received += 1
                            carrer_obj.save()
                            response['status'] = True
                            response['message'] = 'Your application has been submitted successfully, TA team will get back to you soon.'
                            status_code = status.HTTP_201_CREATED
                        else:
                            logger.warning(f"Can not create carrer application obj")
                            response['message'] = "Something went wrong, please try again later."
                    except Career.DoesNotExist:
                        response['message'] = 'Carrer object with the provided id does not exists.'
                except Exception as e:
                    logger.warning(f"Can not create an application submission due to: {e}")
                    response['message'] = 'Something went wrong, please try again later.'
                    if contact_us_obj:
                        contact_us_obj.delete()
            else:
                logger.warning(f"Carrer application serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create Carrer application data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
            if contact_us_obj:
                contact_us_obj.delete()
        return Response(response, status=status_code)

class ContactUsOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    post_serializer_class = ContactUsPostSerializer
    permission_classes = [AllowAny]
    queryset = ContactUs.objects.all()

    def create_contact_us_entry(self, **kwrags):
        obj = None
        print(kwrags)
        try:
            obj = ContactUs.objects.create(**kwrags)
        except Exception as e:
            logger.warning(f"Can not create entry to contact us model due to: {e}")
        return obj
    
    def send_contact_us_email(self, data):
        """Sends an email with contact us details and multiple embedded images."""
        subject = str(email.header.make_header(email.header.decode_header("New Contact Us Inquiry")))
        print(f"Email Subject: {subject}")
        recipient_email = "deeksha.khattar@teamcomputers.com"
        sender_email = settings.EMAIL_ADDRESS_FOR_PASSWORD

        # Create root message (multipart/alternative)
        msg_root = MIMEMultipart('alternative')
        msg_root['Subject'] = subject
        msg_root['From'] = sender_email
        msg_root['To'] = sender_email
        def clean_plain_text(html):
            # Remove <style> blocks and their content.
            cleaned_html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            return strip_tags(cleaned_html)

        # Then use it instead of plain strip_tags:
        # Create text version
        html_content = render_to_string("contact_us_email/new-email.html", data)
        text_content = clean_plain_text(html_content)
        part_text = MIMEText(text_content, 'plain')

        # Create HTML version with inlined CSS
        html_content = transform(html_content)  # Inline CSS styles
        part_html = MIMEText(html_content, 'html')

        # Create related container for HTML + images
        msg_related = MIMEMultipart('related')
        msg_related.attach(part_html)

        # Attach images with correct Content-ID
        image_filenames = ["Beefree.png", "facebook2x.png", "footer.png", "instagram2x.png",
                        "linkedin2x.png", "twitter2x.png", 
                        "vecteezy_contact-us-button-web-banner-templates-vector-illustration_17055622.jpg"]

        for image_name in image_filenames:
            image_path = os.path.join(settings.BASE_DIR, "website", "templates", 
                                    "contact_us_email", "images", image_name)
            if os.path.exists(image_path):
                with open(image_path, "rb") as img:
                    mime_img = MIMEImage(img.read())
                    # Match CID in HTML: <img src="cid:Beefree.png">
                    mime_img.add_header('Content-ID', f'<{image_name}>')
                    msg_related.attach(mime_img)

        # Build the final MIME structure
        msg_root.attach(part_text)
        msg_root.attach(msg_related)

        try:
            # Send email
            server = smtplib.SMTP(settings.SMTP_SERVER_FOR_PASSWORD, settings.SMTP_PORT_FOR_PASSWORD)
            server.starttls()
            server.login(settings.EMAIL_ADDRESS_FOR_PASSWORD, settings.EMAIL_PASSWORD_FOR_PASSWORD)
            server.sendmail(sender_email, sender_email, msg_root.as_string())
            server.quit()
            print(f"Email sent successfully to {sender_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")


    def post(self, request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        try:
            if not request.data.get('name'):
                response['message'] = 'Name is mandatory.'
                return Response(response, status=status_code)
            
            if not request.data.get('email'):
                response['message'] = 'Email is mandatory.'
                return Response(response, status=status_code)
            
            if not request.data.get('message'):
                response['message'] = 'Message is mandatory.'
                return Response(response, status=status_code)
            
            if request.data.get('phone_number'):
                if len(str(request.data.get('phone_number'))) != 10:
                    response['message'] = 'Phone number not valid.'
                    return Response(response, status=status_code)
                if not str(request.data.get('phone_number')).isdigit():
                    response['message'] = 'Phone number should be numeric.'
                    return Response(response, status=status_code)
            
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                obj_data = {
                    "name" : serializer.validated_data.get('name'),
                    "email" : serializer.validated_data.get('email'),
                    "message" : serializer.validated_data.get('message'),
                    "phone_number" : serializer.validated_data.get('phone_number'),
                }
                contact_us_obj = self.create_contact_us_entry(**obj_data)
                print('contact_us_obj', contact_us_obj)
                if contact_us_obj:
                    self.send_contact_us_email(obj_data)
                    # email also needs to be send to admin email id that will be done later
                    response['status'] = True
                    response['message'] = 'Your query raised succesfully, our team will get back to you soon.'
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create contact us obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Contact Us serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create contact us data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)
    	