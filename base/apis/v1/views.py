from base.apis.v1.serializers import *
from rest_framework.views import APIView
from rest_framework.views import status
from rest_framework.response import Response
from base.models import *
from django.contrib.auth import login
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken
from django.conf import settings
from django.db.models import Q, Value, Sum, F
from base.mixins import PaginationHandlerMixin, CustomPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import check_password, make_password
import logging, re, string, secrets, random, time
from django.core.cache import cache
from django.template.loader import render_to_string
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives, send_mail as django_send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.utils import timezone
import pytz
import os

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.views import APIView
# from .models import User, OTP
from .serializers import ForgetPasswordSerializer

# For encryption example using Fernet – ensure you have "cryptography" installed
from cryptography.fernet import Fernet

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64

# SMTP Configuration
SMTP_SERVER = settings.SMTP_SERVER_FOR_PASSWORD
SMTP_PORT = settings.SMTP_PORT_FOR_PASSWORD
EMAIL_ADDRESS = settings.EMAIL_ADDRESS_FOR_PASSWORD
EMAIL_PASSWORD = settings.EMAIL_PASSWORD_FOR_PASSWORD
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class LoginOperation(APIView):
    """
    Login user API:
    Method: POST
    Sample input:
        {
            "email":"admin@admin.com",
            "password":"admin"
        }
    Sample output:
        {
            "status": true,
            "message": "User logged in successfully",
            "data": {
                "email": "admin@admin.com",
                "full_name": "Admin User",
                "access_token" : "some random token",
                "refresh_token" : "some random token"
            }
        }
    """
    def post(self, request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        if not request.data.get('email'):
            response['message'] = 'Email required.'
            return Response(response,status=status_code)
        
        if not User.objects.filter(email=request.data['email']).exists():
            response['message'] = "Email not associated with an account."
            return Response(response,status=status_code)
        
        if not request.data.get('password').strip():
            response['message'] = "Incorrect password."
            return Response(response,status=status_code)

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login_status = serializer.validated_data['status']
            if login_status:
                # login(request,user)
                refresh_token = RefreshToken.for_user(user)
                access_token = refresh_token.access_token
                if request.data.get('remember_me'):
                    refresh_token.set_exp(lifetime=timedelta(days=60))
                response['status'] = True
                response['message'] = 'User logged in.'
                profile_image = settings.BASE_URL + (user.profile_image.url) if user.profile_image else None
                response['data'] = {
                    'id' : user.id,
                    'user_type' : user.user_type,
                    'email': user.email,
                    'full_name' : user.get_full_name(),
                    'profile_image': profile_image,
                    "access_token" : str(access_token),
                    "refresh_token" : str(refresh_token),
                    "status" : user.status,
                }
                status_code = status.HTTP_200_OK
                logger.warning(f"{user.email} has successfully logged In")
            else:
                response['message'] = "Incorrect password."
                logger.warning(f"{request.data['email']} is trying to log in with invalid/wrong credentials")
        else:
            response['message'] = 'Something went wrong please contact support.'
            status_code = status.HTTP_400_BAD_REQUEST
        return Response(response,status=status_code)


class UsersOperation(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = UserGetSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

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
            logger.warning(f"Can not able to fetch data for user due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)
    

class ChangePasswordOperation(APIView):
    post_serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def check_user_password_history(self, user, password):
        response = {
            "status" : False,
            "message" : None
        }
        action = False
        # first level check
        if check_password(password, user.password):
            pass
        elif user.password_1 and check_password(password, user.password_1):
            pass
        elif user.password_2 and check_password(password, user.password_2):
            pass
        else:
            if not user.password_1 and not user.password_2: # set new password and copy old password to password1
                user.password_1 = user.password
                action = True
            elif user.password_1 and not user.password_2:   # set new password and copy old pass to 1 and 1 to 2:
                user.password_2 = user.password_1
                user.password_1 = user.password
                action = True
            else:   # set new password and copy password to 1, 1 to 2
                user.password_2 = user.password_1
                user.password_1 = user.password
                action = True
        if action:
            response['status'] = True
            user.set_password(password)
            user.save()
        else:
            response['message'] = "New password can't match the last 3 passwords."
        return response

    def post(self, request):
        response = {
            "status":False,
            "message":None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        user = request.user

        if not request.data:
            response['message'] = 'No request data found.'
            return Response(response, status=status_code)
       
        if not request.data['old_password'].strip():
            response['message'] = 'Old password can not be blank.'
            return Response(response, status=status_code)

        if not request.data['new_password'].strip():
            response['message'] = 'New password can not be blank.'
            return Response(response, status=status_code)
        
        if not request.user.check_password(request.data['old_password']):
            response['message'] = 'Old password is incorrect.'
            return Response(response, status=status_code) 

        serializer = self.post_serializer_class(data=request.data)
        spl_char_regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
        digit_regex = re.compile('\d+')
        # new password validation
        # 8 char long, 1 special char, 1 number, 1 uppercase
        if serializer.is_valid():
            new_password = serializer.validated_data.get('new_password')
            old_password = serializer.validated_data.get('old_password')
            if new_password == old_password:
                response['message'] = 'Old and new password can not be same.'
                return Response(response, status=status_code)
            if len(new_password) < 8:
                response['message'] = 'Password should be 8 character long.'
                return Response(response, status=status_code)
            if (spl_char_regex.search(new_password) == None):
                response['message'] = 'New password should contains atleast one special character.'
                return Response(response, status=status_code)
            if (digit_regex.search(new_password) == None):
                response['message'] = 'New password should contain atleast one digit.'
                return Response(response, status=status_code)
            if new_password.islower():
                response['message'] = 'New password should contain atleast one uppercase letter.'
                return Response(response, status=status_code)
            set_password = self.check_user_password_history(user, serializer.validated_data.get('new_password'))
            if set_password['status']:
                user.save()
                response['status'] = True
                response['message'] = 'Password changed successfully.'
                status_code = status.HTTP_200_OK
                logger.warning(f"Password changed for {user.email}")
            else:
                response['message'] = set_password['message']
                logger.warning(f"Old password wrong for {user.email}")
        else:
            response['message'] = 'Something went wrong please contact support.'
            logger.warning(f"Can not change the password for due to {serializer.errors}")
        return Response(response, status=status_code)


class LogoutOperation(APIView):
    post_serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = {
            "status":False,
            "message":None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        try:
            if not request.data:
                response['message'] = 'Refresh token is required.'
                return Response(response, status=status_code)
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                refresh_token_value = serializer.validated_data.get("refresh_token")
                refresh_token = RefreshToken(refresh_token_value)
                
                # Extract the access token value from the refresh token payload
                # access_token_value = refresh_token.access_token
                # Blacklist the access token
                # BlacklistedToken.objects.get_or_create(token=access_token_value)

                # Blacklist the refresh token
                refresh_token.blacklist()
                response['message'] = 'User logged out successfully.'
                status_code = status.HTTP_205_RESET_CONTENT
            else:
                response['message'] = 'Something went wrong please contact support.'
                logger.warning(f"Can not change the password for due to {serializer.errors}")
        except Exception as e:
            logger.warning(f"Can not logout the user due to: {e}")
            response['message'] = 'Something went wrong please contact support.'
        return Response(response, status=status_code)


class CustomerOperation(APIView):

    def generate_secret_key(self, length):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(secrets.choice(characters) for _ in range(length))
        return random_string
    
    def create_user(self, **kwargs):
        try:
            user = User.objects.create(**kwargs)
        except Exception as e:
            print(f"Can not create user due to: {e}")
            user = None
        return user

    def create_customer(self, **kwargs):
        try:
            customer = Customer.objects.create(**kwargs)
        except Exception as e:
            print(f"Can not create customer due to: {e}")
            customer = None
        return customer
    
    def create_purchased_license(self, **kwargs):
        try:
            purchased_license = PurchasedLicense.objects.create(**kwargs)
        except Exception as e:
            print(f"Can not create purchased license due to: {e}")
            purchased_license = None
        return purchased_license
    
    def create_customer_license(self, **kwargs):
        try:
            customer_license = License.objects.create(**kwargs)
        except Exception as e:
            print(f"Can not create license due to: {e}")
            customer_license = None
        return customer_license
    
def encrypt(data: bytes) -> str:
    """
    Encrypt the given bytes using Fernet.
    Ensure that settings.ENCRYPTION_KEY is a valid URL-safe base64-encoded 32-byte key.
    """
    fernet = Fernet(settings.ENCRYPTION_KEY)
    return fernet.encrypt(data).decode()

class ForgetPasswordOperation(APIView):
    post_serializer_class = ForgetPasswordSerializer

    def send_email(self, recipient_email, subject, otp):
        try:
            # Root message for related content (HTML + images)
            msg_root = MIMEMultipart('related')
            msg_root['From'] = EMAIL_ADDRESS
            msg_root['To'] = recipient_email
            msg_root['Subject'] = subject

            # Alternative part for plain and HTML
            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)

            # Plain text part
            text = f"Your OTP is {otp}"
            msg_alternative.attach(MIMEText(text, "plain"))

            # Load and encode the image as Base64
            image_path = os.path.join(settings.BASE_DIR, "media", "website", "otp-bg-image", "otp-bg-2.jpg")
            base64_encoded_image = ""
            
            if os.path.exists(image_path):
                try:
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                        # Ensure proper MIME type and encoding
                        base64_encoded_image = base64.b64encode(image_data).decode('utf-8')
                except Exception as e:
                    logger.error(f"Failed to encode image at {image_path}: {e}")
            else:
                logger.error(f"Image not found at {image_path}")
                # Fallback to a placeholder or skip image
                base64_encoded_image = None

            # HTML content with Base64-encoded image
            html = f"""\
            <html>
            <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                .container {{
                    max-width: 650px;
                    margin: 10px auto;
                    background: #fff;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                    background-color: white;
                }}
                .header {{
                    height: auto;
                    overflow: hidden;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                }}
                .header img {{
                    width: 100%;
                    max-height: 155px;
                    object-fit: cover;
                    display: block;
                }}
                .content {{
                    padding: 20px 30px;
                    text-align: center;
                }}
                h2 {{
                    color: #2e2e2e;
                    font-size: 26px;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #5a5a5a;
                    font-size: 15px;
                    line-height: 1.6;
                    margin: 10px 0;
                }}
                .otp-box {{
                    display: inline-block;
                    padding: 10px 32px;
                    background-color: #e0f7fa;
                    color: #002279;
                    border-radius: 32px;
                    font-size: 22px;
                    font-weight: bold;
                    margin: 20px 0;
                    box-shadow: 0 4px 10px rgba(0, 121, 107, 0.2);
                }}
                .footer {{
                    background: #f1f1f1;
                    padding: 18px;
                    font-size: 13px;
                    text-align: center;
                    color: #999;
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                }}
                .social-icons {{
                    margin-top: 10px;
                }}
                .social-icons img {{
                    width: 22px;
                    margin: 0 6px;
                    vertical-align: middle;
                }}
            </style>
            </head>
            <body>
            <div class="container">
                <div class="content">
                    <h2>ZerofAI Password Reset OTP</h2>
                    <p>Hello, Please use the following OTP to reset your password:</p>
                    <div class="otp-box">{otp}</div>
                    <p>If you did not request this, please ignore this email.</p>
                    <p style="margin-top: 20px;">Best regards,<br><strong>ZerofAI Support Team</strong></p>
                </div>
                <div class="footer">
                    <p>Stay connected with us</p>
                    <div class="social-icons">
                        <a href="https://www.linkedin.com/showcase/zerofai/about/"><img src="https://cdn-icons-png.flaticon.com/512/145/145807.png" alt="LinkedIn" /></a>
                    </div>
                </div>
            </div>
            </body>
            </html>
            """

            msg_alternative.attach(MIMEText(html, "html"))

            # Send the email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, recipient_email, msg_root.as_string())

            return True

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False

    def post(self, request, *args, **kwargs):
        serializer = self.post_serializer_class(data=request.data)
        if serializer.is_valid():
            recipient_email = serializer.validated_data['email']
            otp = "123456"  # Generate a real OTP in production
            subject = "Your ZerofAI Password Reset OTP"
            if self.send_email(recipient_email, subject, otp):
                return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_otp(self, otp_length=6):
        return ''.join(str(random.randint(0, 9)) for _ in range(otp_length))
    
    def save_otp(self, user, otp):
        OTP.objects.create(user=user, otp=otp, timestamp=int(time.time()), expiry_time=300)
    
    def verify_otp(self, email, otp):
        response = {"status": False, "message": "Invalid OTP"}
        try:
            user = User.objects.get(email=email)
            otp_record = OTP.objects.filter(user=user).order_by('-timestamp').first()
            
            if otp_record:
                otp_timestamp = datetime.fromtimestamp(otp_record.timestamp, pytz.UTC)  # Convert to aware datetime
                expiry_time = timedelta(seconds=otp_record.expiry_time)
                
                if timezone.now() < otp_timestamp + expiry_time:
                    if str(otp) == str(otp_record.otp):
                        response = {"status": True, "message": "OTP verified successfully."}
        except ObjectDoesNotExist:
            response['message'] = 'User not found'
        return response
    
    def check_user_password_history(self, user, new_password):
        if check_password(new_password, user.password) or \
           (user.password_1 and check_password(new_password, user.password_1)) or \
           (user.password_2 and check_password(new_password, user.password_2)):
            return {"status": False, "message": "New password can't match the last 3 passwords."}
        
        user.password_2 = user.password_1
        user.password_1 = user.password
        user.set_password(new_password)
        user.save()
        return {"status": True}
    
    def post(self, request):
        response = {"status": False, "message": None, "data": {}}
        status_code = status.HTTP_400_BAD_REQUEST
        try:
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data.get('email')
                user = User.objects.filter(email=email).first()
                if not user:
                    response['message'] = 'No user associated with this email address.'
                else:
                    # If no OTP is provided, then generate and send one
                    if not serializer.validated_data.get('otp'):
                        otp = self.generate_otp()
                        self.save_otp(user, otp)
                        email_sent = self.send_email(
                            email, 
                            "OTP for ZerofAI Account Password Reset", 
                            otp
                        )
                        if email_sent:
                            response.update({"message": "OTP sent successfully.", "status": True})
                            status_code = status.HTTP_200_OK
                        else:
                            response['message'] = 'Error sending OTP email.'
                    else:
                        # OTP is provided; verify it first
                        otp_verification = self.verify_otp(email, serializer.validated_data.get('otp'))
                        if otp_verification['status']:
                            # If a new password is provided along with OTP, reset password
                            if serializer.validated_data.get('new_password'):
                                pwd_response = self.check_user_password_history(user, serializer.validated_data.get('new_password'))
                                if pwd_response['status']:
                                    response.update({
                                        "status": True,
                                        "message": "Password reset successfully."
                                    })
                                    status_code = status.HTTP_200_OK
                                else:
                                    response.update(pwd_response)
                            else:
                                # Only OTP verification is requested
                                response.update({
                                    "status": True,
                                    "message": "OTP verified successfully."
                                })
                                status_code = status.HTTP_200_OK
                        else:
                            response = otp_verification
            else:
                response['message'] = 'Invalid request data.'
        except Exception as e:
            logger.error(f"Error processing forget password request: {e}")
            response['message'] = 'Something went wrong. Please try again later.'
        return Response(response, status=status_code)
