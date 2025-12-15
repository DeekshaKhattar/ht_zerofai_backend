from rest_framework.views import APIView
from rest_framework.views import status
from rest_framework.response import Response
from admin_portal.apis.v1.serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, Value, Sum, F, Subquery, Count
from django.db.models import OuterRef, Subquery, Max, Q
from base.mixins import PaginationHandlerMixin, CustomPagination
from django.db.models.functions import Concat
from base.models import User
from website.models import *
from website.apis.v1.serializers import *
import logging
import string, secrets, csv
from datetime import datetime, timedelta
from admin_portal.apis.v1.permissions import *
from django.db.models import Max
from django.http import HttpResponse
from collections import defaultdict
from django.db.models import OuterRef, Subquery, Max, Q
import json
from django.db.models.expressions import RawSQL
from collections import OrderedDict
import calendar
# from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE, MODIFY_DELETE
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.db.models import Case, When, F, Count
from django.db.models import Avg,Exists
from django.utils.timezone import now
from ast import literal_eval
import re
from rest_framework.permissions import AllowAny
from django.db.models.functions import TruncMonth
# from django.db.models import FloatField
import pandas as pd
from collections import Counter, defaultdict
from admin_portal.models import ComplianceAutoFixEntry
from django.utils.timezone import now, make_naive
logger = logging.getLogger(__name__)
from django.utils.timezone import make_aware, get_current_timezone
from dateutil.relativedelta import relativedelta
from io import StringIO
from django.http import StreamingHttpResponse
from dateutil.parser import parse

from django.core.cache import cache
# from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time 
from django.utils.timezone import make_aware, get_current_timezone, is_naive
from io import StringIO
from django.http import StreamingHttpResponse
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import connection
from datetime import datetime, time as dt_time
from calendar import monthrange
import time 
logger = logging.getLogger(__name__)

class CustomerOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = CustomerGetSerializer
    post_serializer_class = CustomerPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = Customer.objects.all().annotate(full_name=Concat('user__first_name', Value(' '), 'user__last_name'))

    def generate_secret_key(self, length):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(secrets.choice(characters) for _ in range(length))
        return random_string
    
    def create_user(self, **kwargs):
        try:
            user = User.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create user due to: {e}")
            user = None
        return user

    def create_customer(self, **kwargs):
        try:
            customer = Customer.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create customer due to: {e}")
            customer = None
        return customer
    
    def create_purchased_license(self, **kwargs):
        try:
            purchased_license = PurchasedLicense.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create purchased license due to: {e}")
            purchased_license = None
        return purchased_license
    
    def create_customer_license(self, **kwargs):
        try:
            customer_license = License.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create license due to: {e}")
            customer_license = None
        return customer_license

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        if not request.user.user_type == 'super_admin':
            response['message'] = 'You are not authorized to access.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(company_name__icontains=search) |
                    Q(company_phone__icontains=search) |
                    Q(domain__icontains=search) |
                    Q(full_name__icontains=search)
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
            logger.warning(f"Can not able to fetch data for customers due to {e}")
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
        user = None
        customer = None
        purchased_license = None
        license = None
        try:
            # Check if all required fields are present in request.data
            field_names = ['first_name', 'last_name', 'email', 'phone_number', 'company_name', 'company_phone', 'company_domain', 'company_address', 'license_start_date', 'license_end_date', 'license_count']
            for field_name in field_names:
                if field_name not in request.data:
                    response["message"] = f'{field_name.replace("_", " ").capitalize()} is mandatory'
                    return Response(response, status=status_code)
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                # User creation which will be used for the login system.
                if User.objects.filter(email=serializer.validated_data.get('email')).exists():
                    response['message'] = 'User already exists with the same email address.'
                    return Response(response, status=status_code)
                
                if User.objects.filter(phone_number=serializer.validated_data.get('phone_number')).exists():
                    response['message'] = 'User already exists with the same phone number.'
                    return Response(response, status=status_code)
                
                user_data = {
                    "first_name" : serializer.validated_data.get('first_name'),
                    "last_name" : serializer.validated_data.get('last_name'),
                    "email" : serializer.validated_data.get('email'),
                    "phone_number" : serializer.validated_data.get('phone_number'),
                    "user_type" : "customer"
                }
                user = self.create_user(**user_data)
                if user:
                    user.set_password(f"{serializer.validated_data.get('first_name')}@123")
                    user.save()
                    # Company creation to which the user will be belonged.
                    if Customer.objects.filter(company_name=serializer.validated_data.get('company_name')).exists():
                        response['message'] = 'Customer already exists with the same company name.'
                        if user:
                            user.delete()
                        return Response(response, status=status_code)
                    
                    if Customer.objects.filter(company_phone=serializer.validated_data.get('company_phone')).exists():
                        response['message'] = 'Customer already exists with the same company phone number.'
                        if user:
                            user.delete()
                        return Response(response, status=status_code)
                    
                    if Customer.objects.filter(domain=serializer.validated_data.get('company_domain')).exists():
                        response['message'] = 'Customer already exists with the same company domain.'
                        if user:
                            user.delete()
                        return Response(response, status=status_code)
                    
                    customer_data = {
                        "user" : user,
                        "company_name" : serializer.validated_data.get('company_name'),
                        "company_address" : serializer.validated_data.get('company_address'),
                        "company_phone" : serializer.validated_data.get('company_phone'),
                        "domain" : serializer.validated_data.get('company_domain'),
                        "client_secret" : self.generate_secret_key(50)
                    }
                    customer = self.create_customer(**customer_data)
                    if customer:
                        # assign customer to the created user
                        user.customer_obj = customer
                        user.save()
                        # License creation for the company.
                        license_data = {
                            "customer" : customer,
                            "start_date" : serializer.validated_data.get('license_start_date'),
                            "end_date" : serializer.validated_data.get('license_end_date'),
                            "total_license" : serializer.validated_data.get('license_count'),
                            "avialable_license" : serializer.validated_data.get('license_count')
                        }
                        license = self.create_customer_license(**license_data)
                        if license:
                            purchased_license_data = {
                                "customer" : customer,
                                "start_date" : serializer.validated_data.get('license_start_date'),
                                "end_date" : serializer.validated_data.get('license_end_date'),
                                "license_count" : serializer.validated_data.get('license_count')
                            }
                            purchased_license = self.create_purchased_license(**purchased_license_data)
                            if purchased_license:
                                user.customer_id = f'ZEROFAI-{customer.company_name[:4]}'
                                user.save()
                                response['status'] = True
                                response['message'] = 'Customer created successfully.'
                                status_code = status.HTTP_201_CREATED
                            else:
                                if license:
                                    license.delete()
                                if customer:
                                    customer.delete()
                                if user:
                                    user.delete()
                                response['message'] = 'Something went wrong, please try again later.'
                        else:
                            if customer:
                                customer.delete()
                            if user:
                                user.delete()
                            response['message'] = 'Something went wrong, please try again later.'
                    else:
                        if user:
                            user.delete()
                        response['message'] = 'Something went wrong, please try again later.'
                else:
                    response['message'] = 'Something went wrong, please try again later.'
            else:
                logger.warning(f"Can not create customer due to: {serializer.errors}")
                response['message'] = 'Something went wrong, please try again later.'
        except Exception as e:
            if purchased_license:
                purchased_license.delete()
            
            if license:
                license.delete()

            if customer:
                customer.delete()

            if user:
                user.delete()
            logger.warning(f"Customer can not be created due to an exception: {e}")
            response['message'] = 'Something went wrong, please try again later.'
        return Response(response, status=status_code)
        

class HostOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = HostGetSerializer
    post_serializer_class = HostPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = Host.objects.all()

    def create_host(self, **kwargs):
        host = None
        try:
            host = Host.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create Host due to: {e}")
        return host

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        host_id = request.GET.get("host_id")
        response = {}
        try:
            # Ensure queryset is initialized
            if not hasattr(self, 'queryset') or self.queryset is None:
                self.queryset = Host.objects.all()  # Replace `Host` with the appropriate model

            if request.user.user_type == 'customer':
                self.queryset = self.queryset.filter(customer=request.user.customer_obj)
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search) |
                    Q(hostname__icontains=search) |
                    Q(mac_address__icontains=search)
                )
            elif host_id:
                queryset = self.queryset.filter(id=host_id)
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
            logger.warning(f"Can not able to fetch data for host due to {e}")
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
            "message" : "Something went wrong, please contact support."
        }
        status_code = status.HTTP_400_BAD_REQUEST
        customer = None
        serializer = self.post_serializer_class(data=request.data)
        if serializer.is_valid():
            customer = request.user.customer_obj
            try:
                try:
                    host = Host.objects.get(customer=customer, hostname=serializer.validated_data.get('hostname'))
                    if host.version != serializer.validated_data.get('version'):
                        host.version = serializer.validated_data.get('version')
                        logger.warning(f"Host: {host.hostname} version has been changed from {host.version} to {serializer.validated_data.get('version')}")
                    host.save()
                    status_code = status.HTTP_200_OK
                    response['status'] = True
                    response['message'] = 'Host entry updated.'
                    logger.warning(f"Host entry has been updated.")
                except Host.DoesNotExist:
                    host_data = {
                        "customer" : customer,
                        "hostname" : serializer.validated_data.get('hostname'),
                        "mac_address" : serializer.validated_data.get('mac_address'),
                        "version" : serializer.validated_data.get('version')
                    }
                    host_obj = self.create_host(**host_data)
                    if host_obj:
                        customer_license = License.objects.get(customer=customer)
                        # customer_license = customer_license.first()
                        customer_license = customer_license
                        customer_license.used_license += 1
                        customer_license.avialable_license -= 1
                        customer_license.save()
                        status_code = status.HTTP_201_CREATED
                        response['status'] = True
                        response['message'] = 'Host entry created.'
                        logger.warning(f"New Host entry has been created with Host ID: {host_obj.id}")
                    else:
                        logger.warning(f"Can not create Host entry.")
            except Exception as e:
                logger.warning(f"Error: {e}")
                response['message'] = 'Domain does not exists.'
        else:
            logger.warning(f"Error occured in:\nclass: MachineHosts\nmethod: POST\nError: {serializer.errors}")
        return Response(response, status=status_code)


class LicenseOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = LicenseGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = License.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search)
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
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class PurchasedLicenseOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = PurchasedLicenseGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = PurchasedLicense.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search)
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
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class SolutionOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = PortalSolutionGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = Solution.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if request.user.user_type == 'customer':
                self.queryset = self.queryset.filter(customer=request.user.customer_obj)
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search) |
                    Q(name__icontains=search) |
                    Q(type__domain__icontains=search)
                )
            elif id:
                queryset = self.queryset.filter(id=id)
                logger.warning(f"Solution GET API trigger with ID: {id} and queryset: {queryset}")
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class TicketOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = TicketGetSerializer
    post_serializer_class = TicketPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = Ticket.objects.all()

    def create_ticket(self, **kwargs):
        try:
            ticket = Ticket.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create ticket due to: {e}")
            ticket = None
        return ticket

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        host_id = request.GET.get("host_id")

        response = {}
        try:
            # Ensure queryset is initialized
            if not hasattr(self, 'queryset') or self.queryset is None:
                self.queryset = Ticket.objects.all()

            # Filter by customer if user is a customer
            if request.user.user_type == 'customer':
                self.queryset = self.queryset.filter(customer=request.user.customer_obj)
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search) |
                    Q(host__hostname__icontains=search) |
                    Q(host__mac_address__icontains=search) |
                    Q(ticket_id__icontains=search) |
                    Q(subject__icontains=search)
                )
            elif host_id:
                queryset = self.queryset.filter(host__id=host_id)
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()

            # Paginate and serialize the queryset
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer_class(page, many=True)
                data = self.get_paginated_response(serializer.data)
                response = data.data
            else:
                serializer = self.get_serializer_class(queryset, many=True)
                response = serializer.data

            # Add count and total_count to the response
            response['count'] = len(response['results']) if 'results' in response else len(response)
            response['total_count'] = queryset.count()

        except Host.DoesNotExist:
            logger.warning(f"Host with ID {host_id} does not exist.")
            response = {
                "status": False,
                "message": "Host not found.",
                "count": 0,
                "next": None,
                "previous": None,
                "result": []
            }
        except Exception as e:
            logger.warning(f"Cannot fetch data for tickets due to: {e}")
            response = {
                "status": False,
                "message": "No data available.",
                "count": 0,
                "next": None,
                "previous": None,
                "result": []
            }
        return Response(response, status=status_code)
    def post(self, request):
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            "status" : False,
            "message" : "Something went wrong, please contact support."
        }
        serializer = self.post_serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                try:
                    # customer = request.user.customer
                    customer = request.user.customer_obj
                    host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                    ticket_obj = {
                        "customer" : customer,
                        "host" : host,
                        "ticket_id" : serializer.validated_data.get('ticket_id'),
                        "subject" : serializer.validated_data.get('subject'),
                        "description" : serializer.validated_data.get('description'),
                    }
                    ticket = self.create_ticket(**ticket_obj)
                    if ticket:
                        status_code = status.HTTP_201_CREATED
                        response['status'] = True
                        response['message'] = 'Ticket logged successfully.'
                except Customer.DoesNotExist:
                    logger.warning(f"Customer does not exists with the provided API Key")
                    response['message'] = f"Customer does not exists with the provided API Key"
                except Host.DoesNotExist:
                    logger.warning(f"Host does not exists with the provided hostname: {serializer.validated_data.get('hostname')}")
                    response['message'] = f"Host does not exists with the provided hostname: {serializer.validated_data.get('hostname')}"
                except Exception as e:
                    logger.warning(f"Can not create the ticket object due to: {e}")
                    response['message'] = f"Can not create the ticket object due to: {e}"
            except Exception as e:
                logger.warning(f"Error: {e}")
                response['message'] = 'Something went wrong, please contact support.'
        else:
            logger.warning(f"Error occured in:\nclass: TicketOperations\nmethod: POST\nError: {serializer.errors}")
        return Response(response, status=status_code)


class SolutionRunOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = SolutionRunGetSerializer
    post_serializer_class = SolutionRunPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = SolutionRun.objects.all()

    def create_solution_run(self, **kwargs):
        try:
            solution_run = SolutionRun.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create solution_run due to: {e}")
            solution_run = None
        return solution_run

    def get(self, request):
        search = request.GET.get("search")
        id_ = request.GET.get("id")
        host_id = request.GET.get("host_id")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        status_code = status.HTTP_200_OK

        try:
            # 1) Build base Q filter: customer + optional date range
            base_filter = Q()
            if request.user.user_type == 'customer':
                base_filter &= Q(customer=request.user.customer_obj)

            if start_date:
                sd = timezone.make_aware(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"))
                base_filter &= Q(created_at__gte=sd)
            if end_date:
                ed = timezone.make_aware(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"))
                base_filter &= Q(created_at__lte=ed)

            # 2) Start with base queryset
            qs = SolutionRun.objects.filter(base_filter)

            # 3) Narrow to a specific host if requested
            if host_id:
                qs = qs.filter(host_id=host_id)

            # 4) Apply id or search if provided
            if id_:
                qs = qs.filter(id=id_)
            elif search:
                try:
                    # Try parsing search as a date (e.g., "4 July", "2025-07-04")
                    parsed_date = parse(search, fuzzy=True)
                    if parsed_date:
                        # Filter for the entire day
                        start_of_day = timezone.make_aware(datetime(parsed_date.year, parsed_date.month, parsed_date.day))
                        end_of_day = start_of_day + timedelta(days=1)
                        qs = qs.filter(created_at__range=[start_of_day, end_of_day])
                except ValueError:
                    # Fallback to other field searches if not a valid date
                    qs = qs.filter(
                        Q(customer__company_name__icontains=search) |
                        Q(customer__domain__icontains=search) |
                        Q(host__hostname__icontains=search) |
                        Q(host__mac_address__icontains=search) |
                        Q(solution__name__icontains=search) |
                        Q(type__icontains=search)
                    )

            # 5) Paginate and serialize
            page = self.paginate_queryset(qs)
            serializer = self.get_serializer_class(page, many=True, context={"request": request})
            data = self.get_paginated_response(serializer.data).data

            # 6) Attach counting metadata
            data['count'] = len(data['results'])
            data['total_count'] = qs.count()

            return Response(data, status=status_code)

        except Exception as e:
            logger.warning(f"Cannot fetch solution runs due to: {e}")
            empty = {
                "status": True,
                "message": "No data available",
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            }
            return Response(empty, status=status_code)

    def post(self, request):
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            "status" : False,
            "message" : "Something went wrong, please contact support."
        }
        logger.info(f"request data {request.data}")
        serializer = self.post_serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                try:
                    customer = request.user.customer_obj
                    host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                    if serializer.validated_data.get('solution'):
                        solution = Solution.objects.get(id=serializer.validated_data.get('solution'))
                    else:
                        solution = None
                    solution_run_obj = {
                        "customer" : customer,
                        "host" : host,
                        "solution" : solution,
                        "type" : serializer.validated_data.get('type')
                    }
                    solution_run_id=serializer.validated_data.get("solution_run_id")
                    print("\n\nsolution run id",solution_run_id)
                    if not solution_run_id:
                        solution_run = self.create_solution_run(**solution_run_obj)
                        status_code = status.HTTP_201_CREATED
                    else:
                        solution_run = SolutionRun.objects.get(id=solution_run_id)
                        solution_run.type = solution_run_obj.get("type")
                        solution_run.save()
                        status_code = status.HTTP_200_OK
                    if solution_run:
                        status_code = status.HTTP_201_CREATED
                        response['status'] = True
                        response['message'] = 'Solution Run logged successfully.'
                        response['solution_run_id'] = solution_run.id
                except Customer.DoesNotExist:
                    logger.warning(f"Customer does not exists with the provided API Key")
                    response['message'] = f"Customer does not exists with the provided API Key"
                except Host.DoesNotExist:
                    logger.warning(f"Host does not exists with the provided hostname: {serializer.validated_data.get('hostname')}")
                    response['message'] = f"Host does not exists with the provided hostname: {serializer.validated_data.get('hostname')}"
                except Solution.DoesNotExist:
                    logger.warning(f"Solution does not exists with the provided id: {serializer.validated_data.get('solution')}")
                    response['message'] = f"Solution does not exists with the provided id: {serializer.validated_data.get('solution')}"
                except Exception as e:
                    logger.warning(f"Can not create the solurion run object due to: {e}")
                    response['message'] = f"Can not create the solurion run object due to: {e}"
            except Exception as e:
                logger.warning(f"Error: {e}")
                response['message'] = 'Something went wrong, please contact support.'
        else:
            logger.warning(f"Error occured in:\nclass: SolurionRunOperations\nmethod: POST\nError: {serializer.errors}")
            response['message'] = 'Something went wrong, please contact support.'
        return Response(response, status=status_code)


class FeedbackOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = FeedbackGetSeializer
    post_serializer_class = FeedbackPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = Feedback.objects.all()

    def create_feedback(self, **kwargs):
        try:
            feedback = Feedback.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create feedback due to: {e}")
            feedback = None
        return feedback

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        host_id = request.GET.get("host_id")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        status_code = status.HTTP_200_OK
        response = {}

        try:
            queryset = self.queryset

            # Filter for customer users
            if request.user.user_type == 'customer':
                queryset = queryset.filter(customer=request.user.customer_obj)

            # Apply date range filter if both are provided
            if start_date and end_date:
                try:
                    start_dt = timezone.make_aware(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"))
                    end_dt = timezone.make_aware(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"))
                    queryset = queryset.filter(created_at__range=[start_dt, end_dt])
                except Exception as e:
                    logger.warning(f"Invalid date format: {e}")

            # Filter by host_id if provided
            if host_id:
                queryset = queryset.filter(host_id=host_id)

            # Filter by search
            if search:
                queryset = queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search) |
                    Q(host__hostname__icontains=search) |
                    Q(host__mac_address__icontains=search) |
                    Q(feedback__icontains=search) |
                    Q(solution_type__icontains=search)
                )

            # Filter by specific feedback ID
            if id:
                queryset = queryset.filter(id=id)

            # Pagination + Serialization
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True, context={"request": request})
            data = self.get_paginated_response(serializer.data).data
            data['count'] = len(data['results'])
            data['total_count'] = queryset.count()
            response = data

        except Exception as e:
            logger.warning(f"Unable to fetch data due to: {e}")
            response = {
                "status": True,
                "message": "No data available",
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            }

        return Response(response, status=status_code)

    def post(self, request):
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            "status" : False,
            "message" : "Something went wrong, please contact support."
        }
        serializer = self.post_serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                try:
                    customer = request.user.customer_obj
                    host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                    try:
                        solution = Solution.objects.get(id=serializer.validated_data.get('solution'))
                        type = serializer.validated_data.get('type')
                    except Exception as e:
                        solution = None
                        type = 'ticket'
                    feedback_obj = {
                        "customer" : customer,
                        "host" : host,
                        "solution" : solution,
                        "feedback" : serializer.validated_data.get('feedback'),
                        "solution_type" : type
                    }
                    feedback = self.create_feedback(**feedback_obj)
                    if feedback:
                        status_code = status.HTTP_201_CREATED
                        response['status'] = True
                        response['message'] = 'Feedback logged successfully.'
                except Customer.DoesNotExist:
                    logger.warning(f"Customer does not exists with the provided API Key")
                    response['message'] = f"Customer does not exists with the provided API Key"
                except Host.DoesNotExist:
                    logger.warning(f"Host does not exists with the provided hostname: {serializer.validated_data.get('hostname')}")
                    response['message'] = f"Host does not exists with the provided hostname: {serializer.validated_data.get('hostname')}"
                except Solution.DoesNotExist:
                    logger.warning(f"Solution does not exists with the provided id: {serializer.validated_data.get('solution')}")
                    response['message'] = f"Solution does not exists with the provided id: {serializer.validated_data.get('solution')}"
                except Exception as e:
                    logger.warning(f"Can not create the feedback object due to: {e}")
                    response['message'] = f"Can not create the feedback object due to: {e}"
            except Exception as e:
                logger.warning(f"Error: {e}")
                response['message'] = 'Something went wrong, please contact support.'
        else:
            logger.warning(f"Error occured in:\nclass: FeedbackOperations\nmethod: POST\nError: {serializer.errors}")
        return Response(response, status=status_code)


class SentimentOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = SentimentGetSeializer
    post_serializer_class = SentimentPostSerializer
    get_main_serializer_class = SentimentMainSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = Sentiment.objects.all()

    def create_new_sentiment_entry(self, **kwargs):
        obj = None
        try:
            obj = Sentiment.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create sentiment object due to: {e}")
        return obj

    def get(self, request):
        start_time = time.time()
        search = request.GET.get("search")
        id = request.GET.get("id")
        host_id = request.GET.get("host_id")
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        status_code = status.HTTP_200_OK
        search_query = request.GET.get('search')
        ordering = request.GET.get('ordering', '-updated_at')
        response = {}

        # Parse start_date and end_date
        start_date = None
        end_date = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                print(f"Filtering Sentiment entries from {start_date} to {end_date}")
            except ValueError:
                logger.warning(f"Invalid datetime format for start_date or end_date")
                return Response({
                    "status": False,
                    "message": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS.",
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "result": []
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Initialize Sentiment queryset
            sentiment_queryset = Sentiment.objects.all()
            if request.user.user_type == 'customer':
                sentiment_queryset = sentiment_queryset.filter(customer=request.user.customer_obj)

            # Apply datetime range filtering to Sentiment queryset
            if start_date and end_date:
                sentiment_queryset = sentiment_queryset.filter(created_at__range=[start_date, end_date])

            if host_id:
                print('HOST ID EXIST')
                host = Host.objects.get(id=host_id)
                queryset = sentiment_queryset.filter(host=host)
                page = self.paginate_queryset(queryset)
                serializer = self.get_serializer_class(page, many=True, context={"request": request, "start_date": start_date, "end_date": end_date})
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['threshold'] = {
                    "ram": host.customer.ram,
                    "cpu": host.customer.cpu,
                    "hardisk": host.customer.hardisk,
                    "page_memory": host.customer.page_memory,
                    "critical_services": host.customer.critical_services,
                    "latency": host.customer.latency,
                    "uptime": host.customer.uptime,
                }
                response['count'] = len(response['results'])
                response['total_count'] = queryset.count()
            else:
                # Build Host queryset from filtered Sentiment entries
                sentiment_host_ids = sentiment_queryset.values_list('host', flat=True).distinct()
                self.queryset = Host.objects.filter(id__in=sentiment_host_ids)
                if request.user.user_type == 'customer':
                    self.queryset = self.queryset.filter(customer=request.user.customer_obj)

                # Annotate each Host with latest Sentiment status and update time
                latest_sentiment = Sentiment.objects.filter(
                    host=OuterRef('pk')
                )
                if start_date and end_date:
                    latest_sentiment = latest_sentiment.filter(created_at__range=[start_date, end_date])
                self.queryset = self.queryset.annotate(
                    latest_status=Subquery(latest_sentiment.order_by('-updated_at', '-created_at').values('status')[:1]),
                    latest_update=Subquery(latest_sentiment.order_by('-updated_at', '-created_at').values('updated_at')[:1])
                )

                if search_query:
                    try:
                        search_date = datetime.strptime(search_query, '%Y-%m-%d').date()
                        self.queryset = self.queryset.annotate(
                            latest_entry_date=Subquery(
                                Sentiment.objects.filter(
                                    host=OuterRef('pk')
                                ).order_by('-updated_at', '-created_at').values('created_at__date')[:1]
                            )
                        ).filter(latest_entry_date=search_date)
                        queryset = self.queryset.order_by(ordering)
                    except ValueError:
                        is_numeric = False
                        try:
                            float(search_query)
                            is_numeric = True
                        except ValueError:
                            pass

                        host_q = Q()
                        status_q = Q()

                        host_q |= Q(hostname__icontains=search_query)
                        host_q |= Q(mac_address__icontains=search_query)
                        host_q |= Q(version__icontains=search_query)

                        status_q |= Q(latest_status__icontains=search_query)

                        if is_numeric:
                            self.queryset = self.queryset.annotate(
                                latest_ram=Subquery(latest_sentiment.values('ram')[:1]),
                                latest_cpu=Subquery(latest_sentiment.values('cpu')[:1]),
                                latest_hardisk=Subquery(latest_sentiment.values('hardisk')[:1]),
                                latest_page_memory=Subquery(latest_sentiment.values('page_memory')[:1]),
                                latest_critical_services=Subquery(latest_sentiment.values('critical_services')[:1]),
                                latest_latency=Subquery(latest_sentiment.values('latency')[:1]),
                                latest_uptime=Subquery(latest_sentiment.values('uptime')[:1]),
                            )
                            numeric_query = float(search_query)
                            status_q |= Q(latest_ram=numeric_query)
                            status_q |= Q(latest_cpu=numeric_query)
                            status_q |= Q(latest_hardisk=numeric_query)
                            status_q |= Q(latest_page_memory=numeric_query)
                            status_q |= Q(latest_critical_services=numeric_query)
                            status_q |= Q(latest_latency=numeric_query)
                            status_q |= Q(latest_uptime=numeric_query)

                        combined_q = host_q | status_q
                        queryset = self.queryset.filter(combined_q).distinct().order_by(ordering)
                elif id:
                    queryset = self.queryset.filter(id=id)
                else:
                    queryset = self.queryset.all().order_by(ordering)

                page = self.paginate_queryset(queryset)
                serializer = self.get_main_serializer_class(page, many=True, context={"request": request})
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['count'] = len(response['results'])
                response['total_count'] = queryset.count()

        except Exception as e:
            logger.warning(f"Can not fetch data due to {e}")
            response = {
                "status": True,
                "message": 'No data available',
                "count": 0,
                "next": None,
                "previous": None,
                "result": []
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
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                customer = Customer.objects.get(user=request.user)
                # host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                try:
                    host = Host.objects.get(mac_address=serializer.validated_data.get('mac_address'), customer=customer)
                except Host.DoesNotExist:
                    host = Host.objects.get(customer=customer, hostname=serializer.validated_data.get('hostname'))

                ram = float(serializer.validated_data.get('ram'))
                cpu = float(serializer.validated_data.get('cpu'))
                hardisk = float(serializer.validated_data.get('hardisk'))
                page_memory = float(serializer.validated_data.get('page_memory'))
                critical_services = float(serializer.validated_data.get('critical_services'))
                latency = float(serializer.validated_data.get('latency'))
                uptime = float(serializer.validated_data.get('uptime'))
                critical_services_details = serializer.validated_data.get("critical_services_details")
                obj_data = {}
                
                obj_data = {
                    'customer': customer,
                    'host': host,
                    'ram': ram,
                    'cpu': cpu,
                    'hardisk': hardisk,
                    'page_memory': page_memory,
                    'critical_services': critical_services,
                    'latency': latency,
                    'uptime': uptime,
                    'critical_services_details': critical_services_details
                }

                if ram > customer.ram or cpu > customer.cpu or hardisk > customer.hardisk or \
                    page_memory > customer.hardisk or critical_services != customer.critical_services or \
                    latency > customer.latency or uptime > customer.uptime:
                    obj_data['status'] = 'sad'
                else:
                    obj_data['status'] = 'happy'

                new_sentiment_obj = self.create_new_sentiment_entry(**obj_data)
                if new_sentiment_obj:
                    logger.warning(f"Sentiment entry logged for user: {serializer.validated_data.get('hostname')}.")
                    response['status'] = True
                    response['message'] = f"Sentiment entry logged for user: {serializer.validated_data.get('hostname')}."
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create sentiment obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Sentiment serializer validation fails due to: {serializer.errors}")
                logger.warning(f"Request data: {request.data}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create sentiment data entry due to: {e}")
            logger.warning(f"Request data: {request.data}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)


class AnnouncementBoradcastingOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = AnnouncementBoradcastingGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = AnnouncementBoradcasting.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        type = request.GET.get("type")
        response = {}
        try:
            if request.user.user_type == 'customer':
                customer = request.user.customer_obj
                if type:
                    logger.warning(f"If Statement")
                    current_datetime = timezone.now()
                    self.queryset = self.queryset.filter(customer=customer, status='active', expiry_date__gt=current_datetime)
                else:
                    self.queryset = self.queryset.filter(customer=customer)
                
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search) |
                    Q(form_type__icontains=search) |
                    Q(feed__icontains=search) |
                    Q(question__icontains=search) |
                    Q(status__icontains=search) |
                    Q(form_type__icontains=search)
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            logger.warning(f"Data for Notifications:\nCustomer: {customer}\nQueryset: {queryset}")
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class AnnouncementAnswerOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = HostAnnouncementAnswerGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = HostAnnouncementAnswer.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if request.user.user_type == 'customer':
                customer = request.user.customer_obj
                self.queryset = self.queryset.filter(customer=customer)
            if search:
                queryset = self.queryset.filter(
                    Q(customer__company_name__icontains=search) |
                    Q(customer__domain__icontains=search) |
                    Q(host__hostname__icontains=search) |
                    Q(host__mac_address__icontains=search) |
                    Q(announcement__feed__icontains=search) |
                    Q(text_answer__icontains=search) |
                    Q(status__icontains=search)
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
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)
    

class ContactUsAdminOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ContactUsGetSerializer
    post_serializer_class = ContactUsPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = ContactUs.objects.all()
    
    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if search:
                queryset = self.queryset.filter(
                    Q(name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(phone_number__icontains=search)
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
            logger.warning(f"Can not able to fetch data for admin contact us due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


class ComplainceOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ComplainceEntryGetSerializer
    get_main_serializer_class = ComplainceMainSerializer
    post_serializer_class = ComplainceEntryPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = ComplainceEntry.objects.all()

    def create_new_complaince_entry(self, **kwargs):
        obj = None
        try:
            obj = ComplainceEntry.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create complaince entry object due to: {e}")
        return obj

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        host_id = request.GET.get("host_id")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        status_code = status.HTTP_200_OK
        search_query = request.GET.get('search', None)
        ordering = request.GET.get('ordering', '-updated_at')
        response = {}
        try:
            compliance_queryset = ComplainceEntry.objects.all()
            if request.user.user_type == 'customer':
                compliance_queryset = compliance_queryset.filter(customer=request.user.customer_obj)

            # Apply datetime range filtering using updated_at
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
                    print(f"Filtering Compliance entries from {start_date} to {end_date} based on updated_at")
                    compliance_queryset = compliance_queryset.filter(updated_at__range=[start_date, end_date])
                except ValueError:
                    logger.warning(f"Invalid datetime format for start_date or end_date")
                    return Response({
                        "status": False,
                        "message": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS.",
                        "count": 0,
                        "next": None,
                        "previous": None,
                        "result": []
                    }, status=status.HTTP_400_BAD_REQUEST)

            if host_id:
                host = Host.objects.get(id=host_id)
                queryset = compliance_queryset.filter(host=host)
                page = self.paginate_queryset(queryset)
                serializer = self.get_serializer_class(page, many=True, context={'request': request, 'start_date': start_date, 'end_date': end_date})
                print(f"Compliance entries for host {host_id}: {serializer.data}")
                data = self.get_paginated_response(serializer.data)
                response = data.data
                print(f"Compliance entries for host {host_id}: {response['results']}")
                response['count'] = len(response['results'])
                response['total_count'] = queryset.count()
            else:
                compliance_host_ids = compliance_queryset.values_list('host', flat=True).distinct()
                self.queryset = Host.objects.filter(id__in=compliance_host_ids)
                if request.user.user_type == 'customer':
                    self.queryset = self.queryset.filter(customer=request.user.customer_obj)

                # Annotate the latest entry's updated_at and status within the filtered date range
                latest_entry = compliance_queryset.filter(
                    host=OuterRef('pk')
                ).order_by('-updated_at')[:1]
                self.queryset = self.queryset.annotate(
                    latest_update=Subquery(latest_entry.values('updated_at')[:1]),
                    latest_status=Subquery(latest_entry.values('status')[:1])
                )
                # print(f"Annotated host queryset with latest compliance entry: {self.queryset.values('latest_update', 'latest_status')}")

                if search_query:
                    search_lower = search_query.lower()
                    if search_lower in ['true', 'false']:
                        desired_status = (search_lower == 'true')
                        self.queryset = self.queryset.filter(latest_status=desired_status)
                        self.queryset = self.queryset.distinct('id').order_by('id', '-updated_at')
                    else:
                        try:
                            search_date = datetime.strptime(search_query, '%Y-%m-%d').date()
                            self.queryset = self.queryset.filter(latest_update__date=search_date)
                        except ValueError:
                            self.queryset = self.queryset.filter(
                                Q(customer__company_name__icontains=search_query) |
                                Q(customer__domain__icontains=search_query) |
                                Q(hostname__icontains=search_query) |
                                Q(mac_address__icontains=search_query)
                            )
                elif id:
                    self.queryset = self.queryset.filter(id=id)
                else:
                    self.queryset = self.queryset.all().order_by(ordering)

                page = self.paginate_queryset(self.queryset)
                serializer = self.get_main_serializer_class(page, many=True, context={'request': request, 'start_date': start_date, 'end_date': end_date})
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['count'] = len(response['results'])
                response['total_count'] = self.queryset.count()

        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status": True,
                "message": 'No data available',
                "count": 0,
                "next": None,
                "previous": None,
                "result": []
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
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                if not serializer.validated_data.get('hostname'):
                    response['message'] = 'Hostname is required.'
                    return Response(response, status=status_code)
                
                if not serializer.validated_data.get('complaince_data'):
                    response['message'] = 'Complaince data is required.'
                    return Response(response, status=status_code)
                
                customer = request.user.customer_obj
                host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                obj_data = {}
                
                obj_data = {
                    'customer': customer,
                    'host': host,
                    'data' : serializer.validated_data.get('complaince_data')
                }
                # Calculate status: True if all values in complaince_data are True, else False
                complaince_data_values = serializer.validated_data.get('complaince_data').values()
                obj_data['status'] = all(
                    value is True for value in complaince_data_values
                )
                new_complaince_entry_obj = self.create_new_complaince_entry(**obj_data)
                if new_complaince_entry_obj:
                    logger.warning(f"New Complaince entry logged for user: {serializer.validated_data.get('hostname')}.")
                    response['status'] = True
                    response['message'] = f"New complaince entry logged for user: {serializer.validated_data.get('hostname')}."
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create complaince entry obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Complaince Entry serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create complaince entry data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)


class ComplainceReportOperations(APIView):
    permission_classes = [BotAPIPermissionClass]
    
    def get(self, request):
        complaince_id = request.GET.get('complaince_id')
        response = {}
        if not id:
            response['message'] = 'Complaince object can not be blank.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        try:
            complaince_obj = ComplainceEntry.objects.get(id=complaince_id)
            # Your header names
            headers = ['Complaince Parameter', 'Status', 'Run Date']
            # complaince obj data itteration
            failed_data = [[key.title(), value, complaince_obj.created_at.strftime('%d-%m-%Y')] for key, value in complaince_obj.data.items()]
            # Create a CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f"attachment; filename={complaince_obj.host.hostname}_complaince_{complaince_obj.created_at.strftime('%d-%m-%Y')}.csv"
            # Create a CSV writer and write the headers
            csv_writer = csv.writer(response)
            csv_writer.writerow(headers)
            # Write demo data rows
            for row in failed_data:
                csv_writer.writerow(row)
            return response
        except ComplainceEntry.DoesNotExist:
            logger.warning(f"Can not download the csv due to complaince entry object using: {complaince_id} does not exists.")
            response['message'] = 'Complaince object does not exists.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.warning(f"Can not download the csv due to {e}")
            response['message'] = 'Something went wrong. please contact support.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class ComplainceConfigurationOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ComplainceConfigurationGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = ComplainceConfiguration.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            queryset = self.queryset  # start from class attribute, unfiltered
            # Filter for customer users only
            if request.user.user_type == 'customer':
                queryset = queryset.filter(customer=request.user.customer_obj)

            # Always filter status=True
            queryset = queryset.filter(status=True)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)


def evaluate_selfheal_status(entry):
    """
    Evaluate the self-heal status for a given SelfHealEntry record.
    For each key/value in entry.data:
      - Parse safely (avoid exceptions).
      - If the value is a list/tuple and the second item is True or "true", return True.
    Return False otherwise.
    """

    def safe_parse(val):
        if isinstance(val, (dict, list)):
            return val

        if isinstance(val, str):
            val = val.strip()

            if not (val.startswith("[") and val.endswith("]")):
                logger.debug(f"Ignored non-list-looking value: {val}")
                return None

            try:
                parsed = ast.literal_eval(val)
                return parsed if isinstance(parsed, (dict, list)) else None
            except (SyntaxError, ValueError) as e:
                logger.warning(f"safe_parse failed for value: {val!r} with error: {e}")
                return None

        return None


    if entry and entry.data:
        for key, value in entry.data.items():
            parsed = safe_parse(value)
            if isinstance(parsed, (list, tuple)) and len(parsed) > 1:
                flag = parsed[1]
                if isinstance(flag, bool) and flag:
                    return True
                if isinstance(flag, str) and flag.lower() == "true":
                    return True
    return False

class ComplainceAutoFixPOSTOperations(APIView,PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ComplainceAutoFixGetSerializer
    post_serializer_class= ComplainceAutofixEntryPOSTSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = complainceHardeningAutoFix.objects.all()
    def create_new_compliance_autofix_entry(self,**kwargs):
        obj = None
        try:
            obj = ComplianceAutoFixEntry.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create compliance autofix entry object due to: {e}")
        return obj
    def post(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            input_data = request.data
            print("\n\nrequest data",input_data)
            # if request.user.user_type == 'customer':
            #     self.queryset = self.queryset.filter(customer=Customer.objects.get(pk=request.user.customer_obj.id))
            # if search:
            #     queryset = self.queryset.filter(
            #         Q(customer__company_name__icontains=search) |
            #         Q(customer__domain__icontains=search) |
            #         Q(name__icontains=search) |
            #         Q(type__domain__icontains=search)
            #     )
            # elif id:
            #     queryset = self.queryset.filter(id=id)
            #     logger.warning(f"Solution GET API trigger with ID: {id} and queryset: {queryset}")
            # else:
            host_type=request.headers.get("Host-Type")
            if host_type:
                host_type = host_type.strip().lower()
                if host_type in ["vdi_user"]:
                    return Response(response,status=status_code)

            ids_to_fetch = [item['id'] for item in input_data]
            queryset = complainceHardeningAutoFix.objects.filter(complaince__pk__in=ids_to_fetch)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            print("response data",response)
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)

class ComplainceAutoFixOperations(APIView,PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ComplainceAutoFixGetSerializer
    post_serializer_class= ComplainceAutofixEntryPOSTSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = complainceHardeningAutoFix.objects.all()
    def create_new_compliance_autofix_entry(self,**kwargs):
        obj = None
        try:
            obj = ComplianceAutoFixEntry.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create compliance autofix entry object due to: {e}")
        return obj
    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            print("\n\nrequest data",request.data)
            # if request.user.user_type == 'customer':
            #     self.queryset = self.queryset.filter(customer=Customer.objects.get(user=request.user))
            # if search:
            #     queryset = self.queryset.filter(
            #         Q(customer__company_name__icontains=search) |
            #         Q(customer__domain__icontains=search) |
            #         Q(name__icontains=search) |
            #         Q(type__domain__icontains=search)
            #     )
            # elif id:
            #     queryset = self.queryset.filter(id=id)
            #     logger.warning(f"Solution GET API trigger with ID: {id} and queryset: {queryset}")
            # else:
            ids_to_fetch = [item['id'] for item in request.data]
            queryset = complainceHardeningAutoFix.objects.filter(complaince__pk__in=ids_to_fetch)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            print("response data",response)
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)

    def post(self,request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        print("compliance autofix request data",request.data)
        try:         
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                if not serializer.validated_data.get('hostname'):
                    response['message'] = 'Hostname is required.'
                    return Response(response, status=status_code)
                
                if not serializer.validated_data.get('data'):
                    response['message'] = 'Compliance Autofix data is required.'
                    return Response(response, status=status_code)
                
                customer = Customer.objects.get(user=request.user)
                host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                obj_data = {}
                
                obj_data = {
                    'customer': customer,
                    'host': host,
                    'data' : serializer.validated_data.get('data')
                }
                
                new_complaince_entry_obj = self.create_new_compliance_autofix_entry(**obj_data)
                if new_complaince_entry_obj:
                    logger.warning(f"New Compliance auto fix entry logged for user: {serializer.validated_data.get('hostname')}.")
                    response['status'] = True
                    response['message'] = f"New Compliance autofix entry logged for user: {serializer.validated_data.get('hostname')}."
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create Compliance autofix entry obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Self Heal Entry serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create compliance autofix entry data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)

        


class ComplainceAutoFixOperations(APIView,PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ComplainceAutoFixGetSerializer
    post_serializer_class= ComplainceAutofixEntryPOSTSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = complainceHardeningAutoFix.objects.all()
    def create_new_compliance_autofix_entry(self,**kwargs):
        obj = None
        try:
            obj = ComplianceAutoFixEntry.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create compliance autofix entry object due to: {e}")
        return obj
    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            print("\n\nrequest data",request.data)
            # if request.user.user_type == 'customer':
            #     self.queryset = self.queryset.filter(customer=Customer.objects.get(pk=request.user.customer_obj.id))
            # if search:
            #     queryset = self.queryset.filter(
            #         Q(customer__company_name__icontains=search) |
            #         Q(customer__domain__icontains=search) |
            #         Q(name__icontains=search) |
            #         Q(type__domain__icontains=search)
            #     )
            # elif id:
            #     queryset = self.queryset.filter(id=id)
            #     logger.warning(f"Solution GET API trigger with ID: {id} and queryset: {queryset}")
            # else:
            ids_to_fetch = [item['id'] for item in request.data]
            queryset = complainceHardeningAutoFix.objects.filter(complaince__pk__in=ids_to_fetch)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            print("response data",response)
            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)

    def post(self,request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        print("compliance autofix request data",request.data)
        try:         
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                if not serializer.validated_data.get('hostname'):
                    response['message'] = 'Hostname is required.'
                    return Response(response, status=status_code)
                
                if not serializer.validated_data.get('data'):
                    response['message'] = 'Compliance Autofix data is required.'
                    return Response(response, status=status_code)
                
                customer = Customer.objects.get(user=request.user)
                host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                obj_data = {}
                
                obj_data = {
                    'customer': customer,
                    'host': host,
                    'data' : serializer.validated_data.get('data')
                }
                
                new_complaince_entry_obj = self.create_new_compliance_autofix_entry(**obj_data)
                if new_complaince_entry_obj:
                    logger.warning(f"New Compliance auto fix entry logged for user: {serializer.validated_data.get('hostname')}.")
                    response['status'] = True
                    response['message'] = f"New Compliance autofix entry logged for user: {serializer.validated_data.get('hostname')}."
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create Compliance autofix entry obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Self Heal Entry serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create compliance autofix entry data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)

class ComplainceAutoFixConfigurationOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = ComplianceAutoFixEntryGetSerializer
    permission_classes = [BotAPIPermissionClass]

    def get_hosts_with_status(self,customer_id):
        with connection.cursor() as cursor:
            cursor.execute("""
               SELECT 
                    h.id, 
                    h.hostname,
                    CASE 
                        WHEN c.id IS NOT NULL THEN TRUE 
                        ELSE FALSE 
                    END AS status,
                    c.created_at,
                    c.updated_at
                FROM admin_portal_host h
                LEFT JOIN (
                    SELECT DISTINCT ON (host_id) id, host_id, created_at, updated_at
                    FROM admin_portal_complianceautofixentry
                    ORDER BY host_id, created_at DESC
                ) c ON c.host_id = h.id
                WHERE h.customer_id = %s;
            """, [customer_id])
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        host_id = request.GET.get("host_id")
        status_param = request.GET.get("status")  # Retrieve the 'status' query parameter
        status_code = status.HTTP_200_OK
        response = {}
        try:
            if request.user.user_type == 'customer':
                customer = Customer.objects.get(pk=request.user.customer_obj.id)

            # If no filters are applied, return all hosts with compliance status
            if not any([search, id, host_id, status_param]):
                # Define subqueries for the created_at and updated_at from ComplainceAutoFixEntry
                queryset = self.get_hosts_with_status(customer.pk)
                # ✅ Use dictionary serializer for queryset with .values()
                serializer = HostStatusSerializer(queryset, many=True)
                response = {"results": serializer.data, "count": len(serializer.data)}

            elif host_id:
                # Fetch compliance autofix data for a specific host
                host = Host.objects.get(id=host_id)
                queryset = ComplianceAutoFixEntry.objects.filter(customer=customer,host=host)
                page = self.paginate_queryset(queryset)
                serializer = self.get_serializer_class(page, many=True)
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['count'] = len(response['results'])
                response['total_count'] = queryset.count()
            else:
                # Default case: List all hosts with computed status
                if customer:
                    queryset = Host.objects.filter(customer=customer)
                else:
                    # For non-customer users, get hosts that have self-heal entries.
                    compliance_host_ids = ComplianceAutoFixEntry.objects.values_list('host', flat=True).distinct()
                    if compliance_host_ids:
                        self.queryset = Host.objects.filter(id__in=compliance_host_ids)
                    else:
                        logger.warning("No compliance host IDs found")
                        self.queryset = Host.objects.none()

                # Apply search filters
                if search:
                    queryset = ComplianceAutoFixEntry.objects.filter(
                                Q(customer__company_name__icontains=search) |
                                Q(customer__domain__icontains=search) |
                                Q(host__hostname__icontains=search) |
                                Q(host__mac_address__icontains=search),
                                customer=customer  # This should be inside the `filter()`
                   )
                elif id:
                    queryset = ComplianceAutoFixEntry.objects.filter(id=id)

                page = self.paginate_queryset(queryset)
                serializer = self.get_serializer_class(page, many=True)
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['count'] = len(response['results'])
                response['total_count'] = queryset.count()

        except Customer.DoesNotExist:
            logger.warning("Customer not found for the given user.")
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Unable to fetch data for host due to: {e}")
            response = {
                "status": False,
                "message": "No data available",
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            }

        return Response(response, status=status_code)
    
def time_decorator(func):
    """Decorator to measure and log execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        print(f"Function '{func.__name__}' took {execution_time:.4f} seconds")
        return result
    return wrapper

class DashboardCards(APIView):
    pagination_class = CustomPagination
    permission_classes = [BotAPIPermissionClass]


    @time_decorator
    def parse_date(self, date_str):
        """Parse date string to offset-naive datetime object."""
        try:
            parsed_date = parse(date_str)
            # Ensure offset-naive datetime
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.replace(tzinfo=None)
            return parsed_date
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format: {e}")
            return None
        
    @time_decorator
    def get_solution_metrics(self, customer=None, start_date=None, end_date=None):
        """Calculate solution run, auto-fix, and KB-based resolution counts."""
        try:
            filters = {'customer': customer} if customer else {}
            # print(f"Solution metrics filters: {start_date}, {end_date}")
            if start_date:
                filters['created_at__gte'] = start_date
            if end_date:
                filters['created_at__lte'] = end_date + timedelta(days=1)
            # print(f"Filters applied: {filters}")
            solution_run = SolutionRun.objects.filter(**filters).count()
            auto_fix = SolutionRun.objects.filter(**filters, type='autofix').count()
            # print(f"Auto-fix count: {auto_fix}")
            # print(f"Solution run: {SolutionRun.objects.all()}")
            using_kb = SolutionRun.objects.filter(**filters, type='kb').count()
            # print(f"Using KB count: {using_kb}")
            return solution_run, auto_fix, using_kb
        except Exception as e:
            logger.warning(f"Error fetching solution metrics: {e}")
            return 0, 0, 0


    @time_decorator
    def get_incident_reduction(self, solution_run, auto_fix, using_kb):
        """Calculate overall incident reduction percentage."""
        try:
            return ((auto_fix + using_kb) / solution_run) * 100 if solution_run > 0 else 0
        except Exception as e:
            logger.warning(f"Error calculating incident reduction: {e}")
            return 0

    @time_decorator
    def get_monthly_incident_reduction(self, customer=None, start_date=None, end_date=None):
        """Calculate incident reduction for current and previous months or date range."""
        try:
            if start_date and end_date:
                # Current range calculation
                solution_run, auto_fix, using_kb = self.get_solution_metrics(customer, start_date, end_date)
                current_incident_reduced = round(self.get_incident_reduction(solution_run, auto_fix, using_kb), 2)

                # Previous month range based on start_date
                start_of_previous_month = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
                end_of_previous_month = start_date.replace(day=1) - timedelta(days=1)

                prev_solution_run, prev_auto_fix, prev_using_kb = self.get_solution_metrics(
                    customer, start_of_previous_month, end_of_previous_month
                )
                previous_incident_reduced = round(
                    self.get_incident_reduction(prev_solution_run, prev_auto_fix, prev_using_kb), 2
                )

                comparison_text = (
                    "Incident reduction rate has improved during the selected period."
                    if current_incident_reduced > previous_incident_reduced
                    else "Incident reduction rate has declined during the selected period."
                    if current_incident_reduced < previous_incident_reduced
                    else "Incident reduction rate remains the same compared to the previous month."
                )

                return {
                    "current_month": current_incident_reduced,
                    "previous_month": previous_incident_reduced,
                    "comparison_text": comparison_text
                }

            # Default: Current vs Previous month logic
            today = now()
            start_of_current_month = make_aware(datetime(today.year, today.month, 1))
            start_of_previous_month = (start_of_current_month - timedelta(seconds=1)).replace(day=1)
            end_of_previous_month = start_of_current_month - timedelta(days=1)

            current_solution_run, current_auto_fix, current_using_kb = self.get_solution_metrics(
                customer, start_of_current_month, today
            )
            current_incident_reduced = round(
                self.get_incident_reduction(current_solution_run, current_auto_fix, current_using_kb), 2
            )

            previous_solution_run, previous_auto_fix, previous_using_kb = self.get_solution_metrics(
                customer, start_of_previous_month, end_of_previous_month
            )
            previous_incident_reduced = round(
                self.get_incident_reduction(previous_solution_run, previous_auto_fix, previous_using_kb), 2
            )

            comparison_text = (
                "Incident reduction rate has improved this month."
                if current_incident_reduced > previous_incident_reduced
                else "Incident reduction rate has declined this month."
                if current_incident_reduced < previous_incident_reduced
                else "Incident reduction rate remains the same as last month."
            )

            return {
                "current_month": current_incident_reduced,
                "previous_month": previous_incident_reduced,
                "comparison_text": comparison_text
            }
        except Exception as e:
            logger.warning(f"Error calculating monthly incident reduction percentages: {e}")
            return {
                "current_month": 0,
                "previous_month": 0,
                "comparison_text": "Unable to calculate incident reduction comparison."
            }

    @time_decorator
    def get_system_health(self, customer=None, start_date=None, end_date=None):
        print("Fetching system health data...", customer, start_date, end_date)
        try:
            base_qs = Sentiment.objects.all()
            if customer:
                base_qs = base_qs.filter(customer=customer)
            if start_date:
                base_qs = base_qs.filter(created_at__gte=start_date)
            if end_date:
                end_date = end_date + timedelta(days=1)
                base_qs = base_qs.filter(created_at__lt=end_date)

            print(f"Filtered base queryset count: {base_qs.count()}")

            # Get latest sentiment per host within the filtered queryset
            latest_sentiment = Sentiment.objects.filter(
                host=OuterRef('host'),
                created_at__gte=start_date,
                created_at__lte=end_date
            ).order_by('-updated_at').values('id')[:1]
            final_qs = base_qs.filter(id__in=Subquery(latest_sentiment))

            print(f"Latest sentiments count: {final_qs.count()}")

            unhealthy_asset_count = final_qs.filter(status='sad').count()
            healthy_asset_count = final_qs.filter(status='happy').count()
            total_assets = unhealthy_asset_count + healthy_asset_count

            overall_health = round((healthy_asset_count / total_assets) * 100, 2) if total_assets else 0.0

            return {
                "overall_analysis": overall_health,
                "healthy_assets": healthy_asset_count,
                "unhealthy_assets": unhealthy_asset_count
            }

        except Exception as e:
            logger.warning(f"Error in Predictive Health Report: {e}")
            return {
                "overall_analysis": 0.0,
                "healthy_assets": 0,
                "unhealthy_assets": 0
            }

    @time_decorator
    def get_compliance_data(self, customer=None, start_date=None, end_date=None):
        """Calculate compliance metrics."""
        try:
            filters = {}
            if customer:
                filters['customer'] = customer
            if start_date:
                filters['updated_at__gte'] = start_date

            if end_date:
                filters['updated_at__lte'] = end_date + timedelta(days=1)
            # logger.info(f"Compliance data filters: {filters}")
            # Get latest updated_at per host within filters
            latest_per_host = ComplainceEntry.objects.filter(**filters).values('host').annotate(
                latest_updated=Max('updated_at')
            )
            # Get entries matching the latest updated_at per host
            latest_entries = ComplainceEntry.objects.filter(
                **filters,
                updated_at__in=latest_per_host.values('latest_updated')
            ).select_related('host')
            compliant = latest_entries.filter(status=True).count()
            non_compliant = latest_entries.filter(status=False).count()
            return {"compliant": compliant, "non_compliant": non_compliant}
        except Exception as e:
            logger.warning(f"Cannot fetch compliance data: {e}")
            return 0, 0

    @time_decorator


    def get_self_heal_data(self, customer=None, start_date=None, end_date=None):
        """Calculate overall self-heal metrics."""
        try:
            # Ensure start_date and end_date are timezone-aware and include full end_date
            if start_date and isinstance(start_date, str):
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date, timezone=timezone.get_current_timezone())
            if end_date and isinstance(end_date, str):
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                end_date = timezone.make_aware(end_date, timezone=timezone.get_current_timezone())
            elif end_date and isinstance(end_date, timezone.datetime):
                end_date = end_date.replace(hour=23, minute=59, second=59)
                if not timezone.is_aware(end_date):
                    end_date = timezone.make_aware(end_date, timezone=timezone.get_current_timezone())
            else:
                print(f"No end_date conversion applied: {end_date}")

            # Build host filters
            host_filters = Q()
            if customer:
                host_filters &= Q(customer=customer)

            # Get host IDs that have SelfHealEntry in date range
            selfheal_entry_filter = Q()
            if start_date and end_date:
                selfheal_entry_filter &= Q(created_at__gte=start_date, created_at__lte=end_date)
            elif start_date:
                selfheal_entry_filter &= Q(created_at__gte=start_date)
            elif end_date:
                selfheal_entry_filter &= Q(created_at__lte=end_date)

            selfheal_host_ids = SelfHealEntry.objects.filter(
                selfheal_entry_filter
            ).values_list('host', flat=True).distinct()

            # logger.debug(f"Found {len(selfheal_host_ids)} hosts with SelfHealEntry: {list(selfheal_host_ids)}")

            hosts = Host.objects.filter(id__in=selfheal_host_ids).filter(host_filters)

            # Get latest entry per host within the date range
            latest_entry_qs = SelfHealEntry.objects.filter(
                host=OuterRef('pk'),
                **({'created_at__gte': start_date, 'created_at__lte': end_date} if start_date and end_date else {})
            ).order_by('-created_at').values('status')[:1]

            hosts = hosts.annotate(
                latest_status=Subquery(latest_entry_qs)
            )

            # Count healed and not healed hosts
            healed_count = 0
            not_healed_count = 0
            for h in hosts:
                logger.debug(f"Host {h.id}: latest_status={h.latest_status}")
                if h.latest_status is True:
                    healed_count += 1
                elif h.latest_status is False:
                    not_healed_count += 1
                else:
                    logger.warning(f"Host {h.id} has unexpected latest_status: {h.latest_status}")

            total_selfheal = healed_count + not_healed_count
            self_healed_percent = round((healed_count / total_selfheal * 100), 2) if total_selfheal > 0 else 0.0

            # logger.debug(f"Healed count: {healed_count}, Not healed count: {not_healed_count}, Self-healed percent: {self_healed_percent}")

            return healed_count, not_healed_count, self_healed_percent

        except Exception as e:
            logger.warning(f"Error fetching self-heal data: {e}")
            return 0, 0, 0.0

    @time_decorator
    def get_monthly_self_heal(self, customer=None, start_date=None, end_date=None):
        """Calculate self-heal metrics for current and previous months or date range."""
        try:
            if start_date and end_date:
                # Current period (custom date range)
                healed_count, not_healed_count, self_healed_percent = self.get_self_heal_data(customer, start_date, end_date)

                # Calculate previous period based on month before start_date
                start_of_previous_month = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
                end_of_previous_month = start_date.replace(day=1) - timedelta(days=1)

                _, _, previous_percent = self.get_self_heal_data(customer, start_of_previous_month, end_of_previous_month)

                comparison_text = (
                    "Self-heal percentage has improved compared to previous month."
                    if self_healed_percent > previous_percent
                    else "Self-heal percentage has declined compared to previous month."
                    if self_healed_percent < previous_percent
                    else "Self-heal percentage remains the same as previous month."
                )

                return {
                    "current_month_percentage": self_healed_percent,
                    "previous_month_percentage": previous_percent,
                    "comparison_text": comparison_text
                }

            # Default case: compare current and previous full months
            today = make_naive(now())  # Ensure offset-naive
            start_of_current_month = make_aware(datetime(today.year, today.month, 1))
            start_of_previous_month = (start_of_current_month - timedelta(seconds=1)).replace(day=1)
            end_of_previous_month = start_of_current_month - timedelta(seconds=1)

            current_month_healed, current_month_not_healed, current_month_self_healed_percent = self.get_self_heal_data(
                customer, start_of_current_month, today
            )
            previous_month_healed, previous_month_not_healed, previous_month_self_healed_percent = self.get_self_heal_data(
                customer, start_of_previous_month, end_of_previous_month
            )

            comparison_text = (
                "Self-heal percentage has improved this month."
                if current_month_self_healed_percent > previous_month_self_healed_percent
                else "Self-heal percentage has declined this month."
                if current_month_self_healed_percent < previous_month_self_healed_percent
                else "Self-heal percentage remains the same as last month."
            )

            return {
                "current_month_percentage": current_month_self_healed_percent,
                "previous_month_percentage": previous_month_self_healed_percent,
                "comparison_text": comparison_text
            }
        except Exception as e:
            logger.warning(f"Error calculating monthly self-heal percentages: {e}")
            return {
                "current_month_percentage": 0.0,
                "previous_month_percentage": 0.0,
                "comparison_text": "Unable to calculate self-heal comparison."
            }
    @time_decorator
    def get_resolution_percentages(self, auto_fix, using_kb, customer=None, start_date=None, end_date=None):
        """Calculate resolution percentages and insights."""
        auto_fix = auto_fix or 0
        using_kb = using_kb or 0
        total = auto_fix + using_kb
        try:
            filters = {'customer': customer} if customer else {}
            if start_date:
                filters['created_at__gte'] = start_date
            if end_date:
                filters['created_at__lte'] = end_date + timedelta(days=1)
            logger.debug(f"Resolution percentages filters: {filters}")
            all_selfheals = SelfHealEntry.objects.filter(**filters)
            total_healed_count = SelfHealEntry.objects.filter(**filters, status=True).count()
            overall_self_healed_count = total_healed_count
            total_resolutions = auto_fix + using_kb + overall_self_healed_count
            resolution_percentages = {
                "auto_fix_percentage": round((auto_fix / total_resolutions * 100)) if total_resolutions > 0 else 0.0,
                "kb_percentage": round((using_kb / total_resolutions * 100)) if total_resolutions > 0 else 0.0,
                "self_heal_percentage": round((overall_self_healed_count / total_resolutions * 100)) if total_resolutions > 0 else 0.0,
                "total_count": total_resolutions,
                "auto_fix_count": auto_fix,
                "kb_count": using_kb,
                "self_heal_count": overall_self_healed_count,
            }
            resolution_insight = "No resolution data yet."
            if total_resolutions > 0:
                auto_fix_per = resolution_percentages["auto_fix_percentage"]
                kb_per = resolution_percentages["kb_percentage"]
                self_heal_per = resolution_percentages["self_heal_percentage"]
                highest = max(auto_fix_per, kb_per, self_heal_per)
                if highest == auto_fix_per:
                    resolution_insight = f"Auto-fix has run {auto_fix} times with highest percentage."
                elif highest == kb_per:
                    resolution_insight = f"Knowledge base has run {using_kb} times with highest percentage."
                else:
                    resolution_insight = f"Self-heal has run {overall_self_healed_count} times with highest percentage."
                resolution_percentages["resolution_insight"] = resolution_insight
            return resolution_percentages, overall_self_healed_count
        except Exception as e:
            logger.warning(f"Error calculating resolution percentages: {e}")
            return {
                "auto_fix_percentage": 0.0,
                "kb_percentage": 0.0,
                "self_heal_percentage": 0.0,
                "total_count": 0,
                "auto_fix_count": auto_fix,
                "kb_count": using_kb,
                "self_heal_count": 0,
                "resolution_insight": "No resolution data yet."
            }, 0
        
    @time_decorator
    def get_happiness_index(self, customer=None, start_date=None, end_date=None):
        """Calculate overall happiness index."""
        try:
            filters = {'customer': customer} if customer else {}
            if start_date:
                filters['created_at__gte'] = start_date
            if end_date:
                filters['created_at__lte'] = end_date + timedelta(days=1)
            print(f"Calculating happiness index with filters: {filters}")
            logger.debug(f"Happiness index filters: {filters}")
            feedbacks = Feedback.objects.filter(**filters)
            total_feedback_sum = sum(x.get_feedback_display() for x in feedbacks)
            highest_feedback_sum = feedbacks.count() * 5
            total_feedbacks = int((total_feedback_sum / highest_feedback_sum) * 100) if highest_feedback_sum > 0 else 0
            return total_feedbacks
        except Exception as e:
            logger.warning(f"Error calculating happiness index: {e}")
            return 0

    @time_decorator
    def get_monthly_happiness_index(self, customer=None, start_date=None, end_date=None):
        """Calculate happiness index for current and previous months or date range."""
        try:
            if start_date and end_date:
                # Calculate current period feedback
                current_feedback = self.get_happiness_index(customer, start_date, end_date)

                # Calculate previous month's range based on start_date
                start_of_previous_month = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
                end_of_previous_month = start_date.replace(day=1) - timedelta(days=1)

                previous_feedback = self.get_happiness_index(customer, start_of_previous_month, end_of_previous_month)

                # Compare
                comparison_text = (
                    "Feedback has improved during the selected period."
                    if current_feedback > previous_feedback
                    else "Feedback has declined during the selected period."
                    if current_feedback < previous_feedback
                    else "Feedback remains the same compared to the previous month."
                )
                if not customer:
                    comparison_text = (
                        "User Happiness Index has improved."
                        if current_feedback > previous_feedback
                        else "User Happiness Index has declined."
                        if current_feedback < previous_feedback
                        else "User Happiness Index remains the same."
                    )

                return {
                    "total_feedbacks": current_feedback,
                    "current_month_feedback_percentage": current_feedback,
                    "previous_month_feedback_percentage": previous_feedback,
                    "feedback_comparison_text": comparison_text
                }

            # Default: no dates passed, use current month vs previous month
            today = make_naive(now())
            start_of_current_month = make_aware(datetime(today.year, today.month, 1))
            start_of_previous_month = (start_of_current_month - timedelta(seconds=1)).replace(day=1)
            end_of_previous_month = start_of_current_month - timedelta(days=1)

            current_feedback = self.get_happiness_index(customer, start_of_current_month, today)
            previous_feedback = self.get_happiness_index(customer, start_of_previous_month, end_of_previous_month)

            comparison_text = (
                "Feedback has improved this month."
                if current_feedback > previous_feedback
                else "Feedback has declined this month."
                if current_feedback < previous_feedback
                else "Feedback remains the same as last month."
            )
            if not customer:
                comparison_text = (
                    "User Happiness Index has improved."
                    if current_feedback > previous_feedback
                    else "User Happiness Index has declined this month."
                    if current_feedback < previous_feedback
                    else "User Happiness Index remains the same as last month."
                )

            return {
                "total_feedbacks": self.get_happiness_index(customer),
                "current_month_feedback_percentage": current_feedback,
                "previous_month_feedback_percentage": previous_feedback,
                "feedback_comparison_text": comparison_text
            }
        except Exception as e:
            logger.warning(f"Error calculating monthly feedback percentages: {e}")
            return {
                "total_feedbacks": 0,
                "current_month_feedback_percentage": 0,
                "previous_month_feedback_percentage": 0,
                "feedback_comparison_text": "Unable to calculate feedback comparison."
            }

    @time_decorator
    def get_host_creation_by_month(self, customer=None, start_date=None, end_date=None):
        try:
            filters = {'customer': customer} if customer else {}

            if start_date:
                if isinstance(start_date, datetime):
                    if is_naive(start_date):
                        start_date = make_aware(start_date)
                else:
                    start_date = make_aware(datetime.combine(start_date, time.min))
                filters['created_at__gte'] = start_date

                if end_date:
                    if isinstance(end_date, datetime):
                        if is_naive(end_date):
                            end_date = make_aware(end_date)
                    else:
                        end_date = make_aware(datetime.combine(end_date, time.max))

                    # Adjust end_date to end of the month if needed:
                    last_day = monthrange(end_date.year, end_date.month)[1]
                    if end_date.day != last_day or end_date.time() != time.max:
                        end_date = end_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

                    filters['created_at__lte'] = end_date

            tz = timezone.get_current_timezone()  # Asia/Kolkata for you

            host_monthly_data = (
                Host.objects
                .filter(**filters)
                .annotate(month=TruncMonth('created_at', tzinfo=tz))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month')
            )

            return [
                {
                    "month": entry['month'].strftime("%B"),
                    "year": entry['month'].strftime("%Y"),
                    "count": entry['count']
                }
                for entry in host_monthly_data if entry['month']
            ]
        except Exception as e:
            logger.warning(f"Error fetching host creation data: {e}")
            return []

    @time_decorator
    def get(self, request):
        status_code = status.HTTP_200_OK
        response = {}
        card_data = {}
        try:
            # Parse query params
            type_param = request.query_params.get('type')

            # Parse date parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            start_date = self.parse_date(start_date_str) if start_date_str else None
            end_date = self.parse_date(end_date_str) if end_date_str else None
            today = make_naive(now())

            host_start_date = start_date
            host_end_date = end_date

            if not start_date and not end_date:
                host_start_date = datetime(datetime.today().year, 1, 1)
                host_end_date = datetime.today().replace(day=1)
   
            if not start_date and not end_date:
                end_date = today  # current date and time
                start_date = datetime(today.year, today.month, 1, 0, 0, 0)  # first day of month at 00:00:00

            if start_date or end_date:
                if not (start_date and end_date):
                    return Response({
                        "status": False,
                        "message": "Both start_date and end_date must be provided.",
                        "count": 0,
                        "next": None,
                        "previous": None,
                        "result": []
                    }, status=status.HTTP_400_BAD_REQUEST)
                if start_date > end_date:
                    return Response({
                        "status": False,
                        "message": "start_date must be before end_date.",
                        "count": 0,
                        "next": None,
                        "previous": None,
                        "result": []
                    }, status=status.HTTP_400_BAD_REQUEST)
                if start_date > today or end_date > today:
                    return Response({
                        "status": False,
                        "message": "Date range cannot be in the future.",
                        "count": 0,
                        "next": None,
                        "previous": None,
                        "result": []
                    }, status=status.HTTP_400_BAD_REQUEST)

            customer = request.user.customer_obj if request.user.user_type == 'customer' else None

            # Handle specific types first
            if type_param == "solution_run":
                # Only calculate sr_percentage
                _, auto_fix, using_kb = self.get_solution_metrics(customer, start_date, end_date)
                resolution_percentages, _ = self.get_resolution_percentages(auto_fix, using_kb, customer, start_date, end_date)
                return Response({"sr_percentage": resolution_percentages}, status=status_code)

            elif type_param == "self_heal":
                # Only calculate self_healed_devices
                healed_count, not_healed_count, self_healed_percent = self.get_self_heal_data(customer, start_date, end_date)
                self_heal_data = self.get_monthly_self_heal(customer, start_date, end_date)
                self_heal_data.update({
                    "percentage": self_healed_percent,
                    "healed": healed_count,
                    "not_healed": not_healed_count,
                    "overall_self_healed_count": 0
                })
                _, overall_self_healed_count = self.get_resolution_percentages(None, None, customer, start_date, end_date)
                self_heal_data["overall_self_healed_count"] = overall_self_healed_count
                return Response({"self_healed_devices": self_heal_data}, status=status_code)

            # If no type is specified, return everything EXCEPT sr_percentage and self_healed_devices
            # Calculate everything else
            solution_run, auto_fix, using_kb = self.get_solution_metrics(customer, start_date, end_date)

            total_tickets = Ticket.objects.filter(
                **({'customer': customer} if customer else {}),
                **({'created_at__gte': start_date} if start_date else {}),
                **({'created_at__lte': end_date} if end_date else {})
            ).count()

            host_creation_by_month = self.get_host_creation_by_month(customer, host_start_date, host_end_date)


            system_health = self.get_system_health(customer, start_date, end_date)
            compliance_data = self.get_compliance_data(customer, start_date, end_date)
            user_happiness_index = self.get_monthly_happiness_index(customer, start_date, end_date)
            incident_reduced = self.get_incident_reduction(solution_run, auto_fix, using_kb)
            incident_reduction_obj = self.get_monthly_incident_reduction(customer, start_date, end_date)
            total_solution_count = Solution.objects.filter(customer=customer).count() if customer else Solution.objects.all().count()

            card_data = {
                "incident_reduction_obj": {
                    "current_month": incident_reduction_obj["current_month"],
                    "previous_month": incident_reduction_obj["previous_month"],
                    "comparison_text": incident_reduction_obj["comparison_text"],
                    "incident_reduced": incident_reduced
                },
                "incident_reduction": incident_reduced,
                "user_happiness_index": user_happiness_index["total_feedbacks"],
                "user_happiness_index_obj": user_happiness_index,
                "system_health_report": system_health,
                "solution_run": solution_run,
                "resolution_using_auto_fix": auto_fix,
                "resolution_using_kb": using_kb,
                "tickets": total_tickets,
                "compliance_data": compliance_data,
                "total_solutions": total_solution_count,
                "host_creation_by_month": host_creation_by_month
            }

            if customer:
                license_obj = License.objects.get(customer=customer)
                card_data['license'] = {
                    "total": license_obj.total_license,
                    "used_license": license_obj.used_license,
                    "free_license": int(license_obj.total_license - license_obj.used_license)
                }
            else:
                card_data['customers'] = Customer.objects.all().count()

            response = card_data
        except Exception as e:
            logger.error(f"Failed to fetch dashboard data due to: {e}", exc_info=True)
            response = {
                "status": True,
                "message": "No data available",
                "count": 0,
                "next": None,
                "previous": None,
                "result": []
            }

        return Response(response, status=status_code)

"""
Dashboard Graphs will be containg below types:
1. Solution Run (solution_run) [bar chart]
2. Solution Analysis (solution_analysis) [pie chart]
3. User happiness index (happiness_index) [bar chart]
4. Top 5 Solutions Used (top_solutions) [bar chart]
5. Health Report (predective_health) [pie chart]
"""
class DashboardGraphs(APIView):
    permission_classes = [BotAPIPermissionClass]
    # bar chart
    def get_solution_run_graph_data(self, user_type, user,month=None, customer=None, start_date=None, end_date=None):
        try:
            today = timezone.now()
            # Determine the month to use
            if month:
                try:
                    if isinstance(month, str):
                        year, month_num = map(int, month.split('-'))
                    else:
                        year = today.year
                        month_num = int(month)
                    start_of_month = timezone.datetime(year, month_num, 1)
                    next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                    end_of_month = next_month - timedelta(days=1)
                except (ValueError, TypeError):
                    raise Exception("Invalid month format. Use 'YYYY-MM' or month number (1-12)")
            else:
                start_of_month = make_aware(datetime(today.year, today.month, 1))
                next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                end_of_month = next_month - timedelta(days=1)

            # Set current period based on start_date and end_date, or use full month
            if start_date and end_date:
                try:
                    current_period_start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                    current_period_end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                    # Ensure dates are timezone-aware
                    current_period_start = timezone.make_aware(current_period_start)
                    current_period_end = timezone.make_aware(current_period_end)
                except ValueError:
                    raise Exception("Invalid date format. Use 'YYYY-MM-DD'")
            else:
                current_period_start = start_of_month
                current_period_end = end_of_month

            # Calculate previous period (same days in previous month or full previous month)
            previous_period_start = current_period_start - relativedelta(months=1)
            previous_period_end = current_period_end - relativedelta(months=1)

            # Filter runs for current and previous periods
            current_period_runs = SolutionRun.objects.filter(
                created_at__gte=current_period_start,
                created_at__lte=current_period_end
            )
            previous_period_runs = SolutionRun.objects.filter(
                created_at__gte=previous_period_start,
                created_at__lte=previous_period_end
            )

            if user_type == 'customer':
                customer = customer
                # customer = Customer.objects.get(user=user)
                current_period_runs = current_period_runs.filter(customer=customer)
                previous_period_runs = previous_period_runs.filter(customer=customer)

            # Count total runs
            current_period_count = current_period_runs.count()
            previous_period_count = previous_period_runs.count()

            # Generate categories and counts for the current period
            dates = [current_period_start + timedelta(days=i) for i in range((current_period_end - current_period_start).days + 1)]
            categories = [date.strftime('%d') for date in dates]
            counts = [0] * len(categories)

            daily_counts = (
                current_period_runs
                .extra({'day': "date(created_at)"})
                .values('day')
                .annotate(runs_count=Count('id'))
                .order_by('day')
            )
            for item in daily_counts:
                day = item['day'].day
                index = day - current_period_start.day
                if 0 <= index < len(counts):
                    counts[index] = item['runs_count']

            # Generate insight text
            if start_date and end_date:
                period_str = f"from {start_date} to {end_date}"
                comparison_str = "compared to the same period in the previous month"
            else:
                period_str = start_of_month.strftime('%B %Y')
                comparison_str = "as compared to previous month"

            if current_period_count > previous_period_count:
                insight_text = f"Solution runs have increased in {period_str} {comparison_str}"
            elif current_period_count < previous_period_count:
                insight_text = f"Solution runs have decreased in {period_str} {comparison_str}"
            else:
                insight_text = f"Solution runs remain consistent in {period_str} {comparison_str}"

        except Exception as e:
            logger.warning(f"Can not fetch the data for solution run graph due to: {e}")
            current_period_count = 0
            previous_period_count = 0
            counts = [0] * 30  # Default to 30 days as a fallback
            categories = [str(day) for day in range(1, 31)]
            insight_text = "Unable to generate insights due to an error."

        data = {
            'type': 'solution_run',
            'count': counts,
            'categories': categories,
            'current_month_total': current_period_count,
            'previous_month_total': previous_period_count,
            'insight': insight_text,
            'month': start_of_month.strftime('%Y-%m') if month else today.strftime('%Y-%m')
        }
        return data

    # pie chart
    def get_solution_analysis_graph_data(self, user_type, user,customer=None, start_date=None, end_date=None):
        try:
            # Base queryset for SolutionRun objects
            solution_run_qs = SolutionRun.objects.all()

            # Apply date filtering if both start_date and end_date are provided
            if start_date and end_date:
                try:
                    # Parse the dates into datetime objects
                    start_dt = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                    # Make them timezone-aware to match the database
                    start_dt = timezone.make_aware(start_dt)
                    end_dt = timezone.make_aware(end_dt)
                    # Filter SolutionRun objects within the date range
                    solution_run_qs = solution_run_qs.filter(created_at__range=(start_dt, end_dt))
                except ValueError:
                    logger.warning("Invalid date format provided for start_date or end_date. Proceeding without date filter.")

            # Filter based on user type
            if user_type == 'customer':
                customer = customer
                solution_run = solution_run_qs.filter(customer=customer).values('type').annotate(count=Count('id'))
            else:
                solution_run = solution_run_qs.values('type').annotate(count=Count('id'))

            # Prepare the response data
            data = {
                "type": "solution_analysis",
                "count": [],
                "categories": ["Autofix", "Kb", "Ticket"],
            }

            # Populate the counts for each category
            for category in ['autofix', 'kb', 'ticket']:
                category_count = next((type_count["count"] for type_count in solution_run if type_count["type"] == category), 0)
                data["count"].append(category_count)

        except Exception as e:
            logger.warning(f"Can not fetch the data for solution analysis graph due to: {e}")
            data = {
                "type": "solution_analysis",
                "count": [0, 0, 0],
                "categories": ["Autofix", "Kb", "Ticket"],
            }
        return data

    # bar chart
    def get_happiness_index_graph_data(self, user_type, user,customer=None, month=None, start_date=None, end_date=None):
        try:
            today = timezone.now()

            # Determine the current period based on provided parameters
            if start_date and end_date:
                try:
                    current_period_start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                    current_period_end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                    current_period_start = timezone.make_aware(current_period_start)
                    current_period_end = timezone.make_aware(current_period_end)
                    if current_period_start > current_period_end:
                        raise ValueError("start_date must be before or equal to end_date.")
                except ValueError as e:
                    logger.error(f"Invalid date format or range: {e}")
                    raise Exception("Invalid start_date or end_date. Use 'YYYY-MM-DD' and ensure start_date <= end_date.")
            else:
                if month:
                    try:
                        if isinstance(month, str):
                            year, month_num = map(int, month.split('-'))
                        else:
                            year = today.year
                            month_num = int(month)
                        start_of_month = timezone.datetime(year, month_num, 1, tzinfo=timezone.get_current_timezone())
                        next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                        end_of_month = next_month - timedelta(days=1)
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid month format: {e}")
                        raise Exception("Invalid month format. Use 'YYYY-MM' or month number (1-12)")
                else:
                    start_of_month = make_aware(datetime(today.year, today.month, 1))
                    next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                    end_of_month = next_month - timedelta(days=1)
                current_period_start = start_of_month
                current_period_end = end_of_month

            # Calculate the previous period
            previous_period_start = current_period_start - relativedelta(months=1)
            previous_period_end = current_period_end - relativedelta(months=1)

            # Filter feedback based on user type and date ranges
            if user_type == 'customer':
                customer = customer
                current_period_feedback = Feedback.objects.filter(
                    customer=customer,
                    created_at__gte=current_period_start,
                    created_at__lt=current_period_end + timedelta(days=1)
                )
                previous_period_feedback = Feedback.objects.filter(
                    customer=customer,
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end + timedelta(days=1)
                )
            else:
                current_period_feedback = Feedback.objects.filter(
                    created_at__gte=current_period_start,
                    created_at__lt=current_period_end + timedelta(days=1)
                )
                previous_period_feedback = Feedback.objects.filter(
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end + timedelta(days=1)
                )

            # Aggregate feedback counts for each star rating
            counts_query = current_period_feedback.values('feedback').annotate(count=Count('id'))
            key_mapping = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
            counts = defaultdict(int)
            for item in counts_query:
                feedback_rating_str = item['feedback']
                feedback_rating_int = key_mapping.get(feedback_rating_str)
                if feedback_rating_int:
                    counts[feedback_rating_int] = item['count']

            # Define categories and calculate totals
            categories = ["1 ⭐", "2 ⭐", "3 ⭐", "4 ⭐", "5 ⭐"]
            total_feedback = sum(counts.values())
            current_period_total_feedback = current_period_feedback.count()
            previous_period_total_feedback = previous_period_feedback.count()

            # Generate insight text based on the period
            if total_feedback > 0:
                avg_rating = sum(rating * count for rating, count in counts.items()) / total_feedback
                if start_date and end_date:
                    period_str = f"from {current_period_start.strftime('%Y-%m-%d')} to {current_period_end.strftime('%Y-%m-%d')}"
                else:
                    period_str = f"for {current_period_start.strftime('%B %Y')}"
                if avg_rating >= 4.5:
                    insight_text = f"Excellent! Average User Happiness Index is {avg_rating:.1f} stars {period_str}."
                elif avg_rating >= 3.5:
                    insight_text = f"Average User Happiness Index is {avg_rating:.1f} stars {period_str}."
                else:
                    insight_text = f"Average User Happiness Index is {avg_rating:.1f} stars {period_str}."
            else:
                if start_date and end_date:
                    insight_text = f"No feedback data available from {current_period_start.strftime('%Y-%m-%d')} to {current_period_end.strftime('%Y-%m-%d')}."
                else:
                    insight_text = f"No feedback data available for {current_period_start.strftime('%B %Y')}."

        except Exception as e:
            logger.warning(f"Cannot fetch the data for happiness graph due to: {e}")
            counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            categories = ["1 ⭐", "2 ⭐", "3 ⭐", "4 ⭐", "5 ⭐"]
            total_feedback = 0
            current_period_total_feedback = 0
            previous_period_total_feedback = 0
            insight_text = "Unable to generate insights due to an error."
            current_period_start = make_aware(datetime(today.year, today.month, 1))
            current_period_end = (current_period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Create the data dictionary
        data = {
            'type': 'happiness_index',
            'count': [counts.get(i, 0) for i in range(1, 6)],
            'categories': categories,
            'total_feedback': total_feedback,
            'current_month_total_feedback': current_period_total_feedback,
            'previous_month_total_feedback': previous_period_total_feedback,
            'insight': insight_text,
            'start_date': current_period_start.strftime('%Y-%m-%d'),
            'end_date': current_period_end.strftime('%Y-%m-%d')
        }

        return data

    # bar chart
    def get_top_solutions_graph_data(self, user_type, user,customer=None, month=None, start_date=None, end_date=None):
        try:
            today = timezone.now()
            period_type = 'all'  # Default to all-time data if no filters are provided

            # Determine the current period based on provided parameters
            if start_date and end_date:
                try:
                    current_period_start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                    current_period_end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                    current_period_start = timezone.make_aware(current_period_start)
                    current_period_end = timezone.make_aware(current_period_end)
                    if current_period_start > current_period_end:
                        raise ValueError("start_date must be before or equal to end_date.")
                    period_type = 'custom'
                    current_period_description = f"from {start_date} to {end_date}"
                except ValueError as e:
                    logger.warning(f"Invalid date format or range: {e}")
                    period_type = 'month'
            if period_type != 'custom':
                if month:
                    try:
                        if isinstance(month, str):
                            year, month_num = map(int, month.split('-'))
                        else:
                            year = today.year
                            month_num = int(month)
                        start_of_month = timezone.datetime(year, month_num, 1, tzinfo=timezone.get_current_timezone())
                        next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                        end_of_month = next_month - timedelta(days=1)
                        period_type = 'month'
                        current_period_description = start_of_month.strftime('%B %Y')
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid month format: {e}")
                        raise Exception("Invalid month format. Use 'YYYY-MM' or month number (1-12)")
                else:
                    start_of_month = make_aware(datetime(today.year, today.month, 1))
                    next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                    end_of_month = next_month - timedelta(days=1)
                    period_type = 'month'
                    current_period_description = start_of_month.strftime('%B %Y')

            # Calculate previous period
            if period_type == 'custom':
                previous_period_start = current_period_start - relativedelta(months=1)
                previous_period_end = current_period_end - relativedelta(months=1)
            elif period_type == 'month':
                start_of_previous_month = (start_of_month - timedelta(days=1)).replace(day=1)
                end_of_previous_month = start_of_month - timedelta(days=1)

            # Get base queryset
            if user_type == 'customer':
                base_qs = SolutionRun.objects.filter(customer=customer)
            else:
                base_qs = SolutionRun.objects.all()

            # Filter for current period
            if period_type == 'custom':
                current_qs = base_qs.filter(
                    created_at__gte=current_period_start,
                    created_at__lt=current_period_end + timedelta(days=1)
                )
            else:
                current_qs = base_qs.filter(
                    created_at__gte=start_of_month,
                    created_at__lt=end_of_month + timedelta(days=1)
                )

            # Get latest SolutionRun per host
            # latest_solution_run = SolutionRun.objects.filter(
            #     host=OuterRef('host'),
            #     created_at__gte=current_period_start if period_type == 'custom' else start_of_month,
            #     created_at__lt=(current_period_end + timedelta(days=1)) if period_type == 'custom' else (end_of_month + timedelta(days=1))
            # ).order_by('-created_at').values('id')[:1]
            # current_qs = current_qs.filter(id__in=Subquery(latest_solution_run))

            # Aggregate query for current period
            solution_runs_query = current_qs.values('solution').annotate(count=Count('id'))
            current_month_count = current_qs.count()

            # Previous period count
            if period_type == 'custom':
                previous_qs = base_qs.filter(
                    created_at__gte=previous_period_start,
                    created_at__lt=previous_period_end + timedelta(days=1)
                )
                # previous_qs = previous_qs.filter(id__in=Subquery(
                #     SolutionRun.objects.filter(
                #         host=OuterRef('host'),
                #         created_at__gte=previous_period_start,
                #         created_at__lt=previous_period_end + timedelta(days=1)
                #     ).order_by('-created_at').values('id')[:1]
                # ))
                previous_month_count = previous_qs.count()
            elif period_type == 'month':
                previous_qs = base_qs.filter(
                    created_at__gte=start_of_previous_month,
                    created_at__lt=start_of_month
                )
                # previous_qs = previous_qs.filter(id__in=Subquery(
                #     SolutionRun.objects.filter(
                #         host=OuterRef('host'),
                #         created_at__gte=start_of_previous_month,
                #         created_at__lt=start_of_month
                #     ).order_by('-created_at').values('id')[:1]
                # ))
                previous_month_count = previous_qs.count()
            else:
                previous_month_count = 0

            # Get top 5 solutions
            top_solutions_query = solution_runs_query.order_by('-count')[:5]
            top_solutions_ids = [solution['solution'] for solution in top_solutions_query]
            top_solutions_counts = [solution['count'] for solution in top_solutions_query]

            # Retrieve solution names
            top_solutions_info = {
                solution.id: solution.name for solution in Solution.objects.filter(id__in=top_solutions_ids)
            }
            categories = [top_solutions_info.get(solution_id, f'Solution {solution_id}') for solution_id in top_solutions_ids]

            # Calculate total run count
            total_run_count = sum(top_solutions_counts)

            # Generate insight text
            if top_solutions_counts:
                most_used_solution = categories[0]
                most_used_count = top_solutions_counts[0]
                insight_text = f"The most used solution {current_period_description} is '{most_used_solution}' with {most_used_count} runs."
            else:
                insight_text = f"No solutions have been run {current_period_description}."

        except Exception as e:
            logger.warning(f"Cannot fetch the data for top solutions graph due to: {e}")
            categories = ["Solution 1", "Solution 2", "Solution 3", "Solution 4", "Solution 5"]
            top_solutions_counts = [0, 0, 0, 0, 0]
            total_run_count = 0
            current_month_count = 0
            previous_month_count = 0
            insight_text = "Unable to generate insights due to an error."
            period_type = 'month'

        # Create response
        data = {
            'type': 'top_solutions',
            'count': top_solutions_counts,
            'categories': categories,
            'total_run_count': total_run_count,
            'current_month_count': current_month_count,
            'previous_month_count': previous_month_count,
            'insight': insight_text
        }
        if period_type == 'custom':
            data['start_date'] = start_date
            data['end_date'] = end_date
        elif period_type == 'month' and month:
            data['month'] = start_of_month.strftime('%Y-%m')

        return data
    # pie chart
    def get_predictive_health_report(self, user_type, user, customer=None, month=None, start_date=None, end_date=None):
        try:
            today = timezone.now()

            # Set period
            if start_date and end_date:
                current_period_start = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                current_period_end = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(microseconds=1)
                )
                previous_period_start = current_period_start - relativedelta(months=1)
                previous_period_end = current_period_end - relativedelta(months=1)
            else:
                year, month_num = today.year, today.month
                if month:
                    if isinstance(month, str):
                        year, month_num = map(int, month.split('-'))
                    else:
                        month_num = int(month)
                current_period_start = timezone.make_aware(datetime(year, month_num, 1))
                next_month = (current_period_start + timedelta(days=32)).replace(day=1)
                current_period_end = next_month - timedelta(days=1)
                previous_period_start = (current_period_start - timedelta(days=1)).replace(day=1)
                previous_period_end = current_period_start - timedelta(days=1)

            def get_sentiment_summary(start, end):
                # print(f"Fetching sentiment summary from {start} to {end} for user_type: {user_type}, customer: {customer}")
                base_filter = Q(updated_at__gte=start, updated_at__lte=end)
                if user_type == 'customer' and customer:
                    base_filter &= Q(customer=customer)

                latest_sentiment_subquery = Sentiment.objects.filter(
                    host=OuterRef('host')
                ).filter(base_filter).order_by('-updated_at', '-id').values('id')[:1]

                final_qs = Sentiment.objects.filter(id__in=Subquery(latest_sentiment_subquery))
                sentiment_counts = final_qs.values('status').annotate(count=Count('id'))
                print(f"Sentiment counts for period {start} to {end}: {sentiment_counts}")
                data = {'happy': 0, 'sad': 0}
                for item in sentiment_counts:
                    if item['status'] in data:
                        data[item['status']] = item['count']
                return data

            current_data = get_sentiment_summary(current_period_start, current_period_end)
            previous_data = get_sentiment_summary(previous_period_start, previous_period_end)

            # Compute insights
            total_current = current_data['happy'] + current_data['sad']
            total_previous = previous_data['happy'] + previous_data['sad']

            curr_percent = (current_data['happy'] / total_current * 100) if total_current else 0
            prev_percent = (previous_data['happy'] / total_previous * 100) if total_previous else 0

            if curr_percent > prev_percent:
                insight = f"System health has improved with {curr_percent:.1f}% healthy assets compared to {prev_percent:.1f}% last period."
            elif curr_percent < prev_percent:
                insight = f"System health has declined with {curr_percent:.1f}% healthy assets compared to {prev_percent:.1f}% last period."
            else:
                insight = f"System health remains consistent at {curr_percent:.1f}%."

            return {
                'type': 'predective_health',
                'current_month_healthy_count': current_data['happy'],
                'current_month_unhealthy_count': current_data['sad'],
                'previous_month_healthy_count': previous_data['happy'],
                'previous_month_unhealthy_count': previous_data['sad'],
                'categories': ['Healthy', 'Unhealthy'],
                'count': [current_data['happy'], current_data['sad']],
                'insight': insight,
                'start_date': current_period_start.strftime('%Y-%m-%d'),
                'end_date': current_period_end.strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.warning(f"Cannot fetch predictive health data: {e}")
            return {
                'type': 'predective_health',
                'current_month_healthy_count': 0,
                'current_month_unhealthy_count': 0,
                'previous_month_healthy_count': 0,
                'previous_month_unhealthy_count': 0,
                'categories': ['Healthy', 'Unhealthy'],
                'count': [0, 0],
                'insight': 'No data available due to error.',
                'start_date': '',
                'end_date': ''
            }

    # pie chart
    def get_complaince_analysis_graph_data(self, user_type, user, customer=None,start_date=None, end_date=None):
        complaint_count = 0
        non_complaint_count = 0
        try:
            # Initialize base queryset for ComplainceEntry
            base_qs = ComplainceEntry.objects.all()

            # Apply date filtering if both start_date and end_date are provided
            if start_date and end_date:
                try:
                    start_dt = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                    start_dt = timezone.make_aware(start_dt)
                    end_dt = timezone.make_aware(end_dt)
                    if start_dt > end_dt:
                        raise ValueError("start_date must be before or equal to end_date")
                    base_qs = base_qs.filter(updated_at__gte=start_dt, updated_at__lt=end_dt + timezone.timedelta(days=1))
                except ValueError as e:
                    logger.warning(f"Invalid date format or range: {e}")
                    # Proceed without date filter if dates are invalid

            # Filter by user type
            if user_type == 'customer':
                customer = customer
                latest_complaince_subquery = base_qs.filter(
                    host=OuterRef('host'), customer=customer
                ).order_by('-updated_at').values('updated_at')[:1]
            else:
                latest_complaince_subquery = base_qs.filter(
                    host=OuterRef('host')
                ).order_by('-updated_at').values('updated_at')[:1]

            # Main query to get the latest compliance entries
            latest_complaints = base_qs.filter(updated_at=Subquery(latest_complaince_subquery))

            # Count compliant and non-compliant entries
            for entry in latest_complaints:
                if all(entry.data.values()):
                    complaint_count += 1
                else:
                    non_complaint_count += 1

            # Generate insight text
            total_entries = complaint_count + non_complaint_count
            if total_entries > 0:
                compliance_percentage = (complaint_count / total_entries) * 100
                period_str = f"from {start_date} to {end_date}" if start_date and end_date else "overall"
                insight_text = f"Compliance rate is {compliance_percentage:.1f}% {period_str}."
            else:
                period_str = f"from {start_date} to {end_date}" if start_date and end_date else "overall"
                insight_text = f"No compliance data available {period_str}."

            # Prepare response data
            data = {
                "type": "complaince_analysis",
                "count": [complaint_count, non_complaint_count],
                "categories": ["Compliant", "Non-Compliant"],
                "insight": insight_text
            }
            if start_date and end_date:
                data["start_date"] = start_date
                data["end_date"] = end_date

        except Exception as e:
            logger.warning(f"Cannot fetch the data for compliance analysis graph due to: {e}")
            data = {
                "type": "complaince_analysis",
                "count": [0, 0],
                "categories": ["Compliant", "Non-Compliant"],
                "insight": "Unable to generate insights due to an error."
            }
            if start_date and end_date:
                data["start_date"] = start_date
                data["end_date"] = end_date

        return data

    # emotions monthly data
    def get_emotions_monthly_data(self, user_type, user, customer=None,month=None, start_date=None, end_date=None):
        try:
            today = timezone.now()

            # Determine the current period based on provided parameters
            if start_date and end_date:
                try:
                    current_period_start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                    current_period_end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                    current_period_start = timezone.make_aware(current_period_start)
                    current_period_end = timezone.make_aware(current_period_end)
                    if current_period_start > current_period_end:
                        raise ValueError("start_date must be before or equal to end_date")
                    period_type = 'custom'
                    current_period_description = f"from {start_date} to {end_date}"
                except ValueError as e:
                    logger.warning(f"Invalid date format or range: {e}, falling back to month")
                    start_date = None
                    end_date = None
            if not start_date or not end_date:
                if month:
                    try:
                        if isinstance(month, str):
                            year, month_num = map(int, month.split('-'))
                        else:
                            year = today.year
                            month_num = int(month)
                        start_of_month = timezone.datetime(year, month_num, 1, tzinfo=timezone.get_current_timezone())
                        next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                        end_of_month = next_month - timedelta(days=1)
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid month format: {e}")
                        raise Exception("Invalid month format. Use 'YYYY-MM' or month number (1-12)")
                else:
                    start_of_month = make_aware(datetime(today.year, today.month, 1))
                    next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                    end_of_month = next_month - timedelta(days=1)
                current_period_start = start_of_month
                current_period_end = end_of_month
                period_type = 'month'
                current_period_description = start_of_month.strftime('%B %Y')

            # Calculate previous period
            previous_period_start = current_period_start - relativedelta(months=1)
            previous_period_end = current_period_end - relativedelta(months=1)

            # Apply user type filter
            base_qs = Sentiment.objects.all()
            if user_type == 'customer':
                customer = customer
                base_qs = base_qs.filter(customer=customer)

            # Get the latest entry for each host and day within the current period
            latest_entries = (
                base_qs
                .filter(updated_at__gte=current_period_start, updated_at__lt=current_period_end + timedelta(days=1))
                .values('host', 'updated_at__date')
                .annotate(latest_update=Max('updated_at'))
            )

            # Filter sentiments to get only the latest entries
            sentiments = (
                base_qs
                .filter(updated_at__in=[entry['latest_update'] for entry in latest_entries])
                .extra({'day': "date(updated_at)"})
                .values('day', 'status')
                .annotate(status_count=Count('id'))
                .order_by('day')
            )

            # Initialize counts for sad and happy statuses
            days_in_period = (current_period_end - current_period_start).days + 1
            count_for_sad = [0] * days_in_period
            count_for_happy = [0] * days_in_period
            categories = [(current_period_start + timedelta(days=i)).strftime('%d') for i in range(days_in_period)]

            # Populate the counts lists
            for item in sentiments:
                day_index = (item['day'] - current_period_start.date()).days
                if 0 <= day_index < days_in_period:
                    if item['status'] == 'sad':
                        count_for_sad[day_index] = item['status_count']
                    elif item['status'] == 'happy':
                        count_for_happy[day_index] = item['status_count']

            # Calculate current and previous period counts
            current_period_counts = base_qs.filter(
                updated_at__gte=current_period_start,
                updated_at__lt=current_period_end + timedelta(days=1)
            ).values('status').annotate(count=Count('id'))

            previous_period_counts = base_qs.filter(
                updated_at__gte=previous_period_start,
                updated_at__lt=previous_period_end + timedelta(days=1)
            ).values('status').annotate(count=Count('id'))

            # Initialize data dictionaries
            current_period_data = {'happy': 0, 'sad': 0}
            previous_period_data = {'happy': 0, 'sad': 0}

            # Populate current period data
            for item in current_period_counts:
                if item['status'] in current_period_data:
                    current_period_data[item['status']] = item['count']

            # Populate previous period data
            for item in previous_period_counts:
                if item['status'] in previous_period_data:
                    previous_period_data[item['status']] = item['count']

            # Generate insight text
            total_current = current_period_data['happy'] + current_period_data['sad']
            if total_current > 0:
                happy_percentage = (current_period_data['happy'] / total_current) * 100
                insight_text = f"Positive sentiment is at {happy_percentage:.1f}% {current_period_description}."
            else:
                insight_text = f"No sentiment data available {current_period_description}."

        except Exception as e:
            logger.warning(f"Cannot fetch the data for sentiment graph due to: {e}")
            days_in_period = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1)).day
            count_for_sad = [0] * days_in_period
            count_for_happy = [0] * days_in_period
            categories = [str(day) for day in range(1, days_in_period + 1)]
            current_period_data = {'happy': 0, 'sad': 0}
            previous_period_data = {'happy': 0, 'sad': 0}
            current_period_start = make_aware(datetime(today.year, today.month, 1))
            current_period_end = (current_period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            insight_text = "Unable to generate insights due to an error."

        # Create response data
        data = {
            'type': 'emotions_monthly',
            'count': {
                'count_for_sad': count_for_sad,
                'count_for_happy': count_for_happy
            },
            'categories': categories,
            'current_period': {
                'happy': current_period_data['happy'],
                'sad': current_period_data['sad']
            },
            'previous_period': {
                'happy': previous_period_data['happy'],
                'sad': previous_period_data['sad']
            },
            'insight': insight_text,
            'start_date': current_period_start.strftime('%Y-%m-%d'),
            'end_date': current_period_end.strftime('%Y-%m-%d')
        }

        return data

    # complaince monthly data
    def get_compliance_monthly_data(self, user_type, user, customer=None, month=None, start_date=None, end_date=None):
        try:
            today = timezone.now()

            # --- Determine current period ---
            if start_date and end_date:
                try:
                    current_period_start = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                    current_period_end = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d')).replace(
                        hour=23, minute=59, second=59
                    )
                    if current_period_start > current_period_end:
                        raise ValueError("start_date must be before or equal to end_date")
                    period_type = 'custom'
                    current_period_description = f"from {start_date} to {end_date}"
                except ValueError:
                    start_date = end_date = None  # fallback to month
            if not start_date or not end_date:
                if month:
                    if isinstance(month, str):
                        year, month_num = map(int, month.split('-'))
                    else:
                        year = today.year
                        month_num = int(month)
                    current_period_start = timezone.datetime(year, month_num, 1, tzinfo=timezone.get_current_timezone())
                    next_month = (current_period_start + timedelta(days=32)).replace(day=1)
                    current_period_end = (next_month - timedelta(seconds=1)).replace(hour=23, minute=59, second=59)
                else:
                    current_period_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    next_month = (current_period_start + timedelta(days=32)).replace(day=1)
                    current_period_end = (next_month - timedelta(seconds=1)).replace(hour=23, minute=59, second=59)
                period_type = 'month'
                current_period_description = current_period_start.strftime('%B %Y')

            # --- Previous period ---
            previous_period_start = current_period_start - relativedelta(months=1)
            previous_period_end = (current_period_end - relativedelta(months=1)).replace(hour=23, minute=59, second=59)

            # --- Base queryset ---
            base_qs = ComplainceEntry.objects.all()
            if user_type == 'customer' and customer:
                base_qs = base_qs.filter(customer=customer)

            # --- Fetch all entries within current period ---
            entries_in_period = base_qs.filter(updated_at__range=(current_period_start, current_period_end))

            # Annotate entries with date only (no time)
            entries_in_period = entries_in_period.annotate(
                updated_date=F('updated_at__date')
            )

            # Get latest updated_at per host per day
            latest_per_host_day = entries_in_period.values('host_id', 'updated_date').annotate(
                latest_updated=Max('updated_at')
            )

            # Prepare a dict {(host_id, date): latest_updated}
            latest_map = {(item['host_id'], item['updated_date']): item['latest_updated'] for item in latest_per_host_day}

            # Filter entries to only those with updated_at == latest_updated for that host/day
            # Pull those entries in bulk (reduce queries)
            # We'll filter manually in Python instead of using complex ORM queries
            filtered_entries = [
                entry for entry in entries_in_period
                if latest_map.get((entry.host_id, entry.updated_at.date())) == entry.updated_at
            ]

            # Prepare daily counts
            days_in_period = (current_period_end.date() - current_period_start.date()).days + 1
            count_for_compliant = [0] * days_in_period
            count_for_non_compliant = [0] * days_in_period
            categories = [(current_period_start + timedelta(days=i)).strftime('%d') for i in range(days_in_period)]

            # Tally compliant/non-compliant counts per day
            for entry in filtered_entries:
                day_index = (entry.updated_at.date() - current_period_start.date()).days
                if entry.status:
                    count_for_compliant[day_index] += 1
                else:
                    count_for_non_compliant[day_index] += 1

            total_compliant = sum(count_for_compliant)
            total_non_compliant = sum(count_for_non_compliant)

            # --- Previous period compliance counts ---
            prev_entries = base_qs.filter(updated_at__range=(previous_period_start, previous_period_end))

            prev_latest_per_host_day = prev_entries.values('host_id', 'updated_at__date').annotate(
                latest_updated=Max('updated_at')
            )
            prev_latest_map = {(item['host_id'], item['updated_at__date']): item['latest_updated'] for item in prev_latest_per_host_day}

            prev_filtered_entries = [
                entry for entry in prev_entries
                if prev_latest_map.get((entry.host_id, entry.updated_at.date())) == entry.updated_at
            ]

            previous_period_compliant = sum(1 for e in prev_filtered_entries if e.status)
            previous_period_non_compliant = sum(1 for e in prev_filtered_entries if not e.status)

            # --- Insights ---
            total_hosts = total_compliant + total_non_compliant
            if total_hosts > 0:
                compliance_rate = (total_compliant / total_hosts) * 100
                if compliance_rate > 80:
                    insight_text = f"{current_period_description}, {total_compliant} out of {total_hosts} hosts were compliant ({compliance_rate:.1f}%)."
                elif compliance_rate > 50:
                    insight_text = f"{current_period_description}, {total_compliant} out of {total_hosts} hosts were compliant ({compliance_rate:.1f}%)."
                else:
                    insight_text = f"{current_period_description}, only {total_compliant} out of {total_hosts} hosts were compliant ({compliance_rate:.1f}%)."
            else:
                insight_text = f"No compliance data available {current_period_description}."

        except Exception as e:
            logger.warning(f"Cannot fetch data for compliance graph due to: {e}")
            days_in_period = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1)).day
            count_for_compliant = [0] * days_in_period
            count_for_non_compliant = [0] * days_in_period
            categories = [str(day) for day in range(1, days_in_period + 1)]
            insight_text = "Unable to generate insights due to an error."
            total_compliant = total_non_compliant = 0
            previous_period_compliant = previous_period_non_compliant = 0
            current_period_start = timezone.make_aware(datetime(today.year, today.month, 1))
            current_period_end = (current_period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        data = {
            'type': 'compliance_monthly',
            'count': {
                'count_for_compliant': count_for_compliant,
                'count_for_non_compliant': count_for_non_compliant,
            },
            'categories': categories,
            'insight': insight_text,
            'total_compliant': total_compliant,
            'total_non_compliant': total_non_compliant,
            'previous_period_compliant': previous_period_compliant,
            'previous_period_non_compliant': previous_period_non_compliant,
            'start_date': current_period_start.strftime('%Y-%m-%d'),
            'end_date': current_period_end.strftime('%Y-%m-%d'),
        }
        return data

    def get(self, request):
        status_code = status.HTTP_200_OK
        response = {}
        graph_data = {}
        customer = None
        graph_type = request.GET.get('type')
        month = request.GET.get('month')  # format YYYY-MM or month number
        start_date = request.GET.get('start_date')  # string or None
        end_date = request.GET.get('end_date')  # string or None    

        user = request.user
        customer = Customer.objects.get(pk=request.user.customer_obj.id)
        today = make_naive(now()) 
        
            # ─── DEFAULT TO LAST 3 MONTHS IF NO DATES PROVIDED ───
        if not start_date and not end_date:
            end_date = today.strftime('%Y-%m-%d')
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        try:
            if not graph_type:
                response['message'] = 'Graph type is not specified.'
                return Response(response, status=status_code)
            
            if graph_type not in ['solution_run', 'solution_analysis', 'happiness_index', 'top_solutions', 'predective_health',
                                  'emotions_monthly', 'compliance_monthly', 'complaince_analysis']:
                response['message'] = 'Graph type is not valid.'
                return Response(response, status=status_code)
            
            if request.user.user_type == 'customer':
                user_type = 'customer'
            else:
                user_type = 'super_admin'

            if graph_type == 'solution_run':
                graph_data = self.get_solution_run_graph_data(user_type, user, month,customer, start_date, end_date)
            elif graph_type == 'solution_analysis':
                graph_data = self.get_solution_analysis_graph_data(user_type, user,customer, start_date, end_date)
            elif graph_type == 'happiness_index':
                graph_data = self.get_happiness_index_graph_data(user_type, user,customer, month, start_date, end_date)
            elif graph_type == 'top_solutions':
                graph_data = self.get_top_solutions_graph_data(user_type, user,customer, month, start_date, end_date)
            elif graph_type == 'predective_health':
                graph_data = self.get_predictive_health_report(user_type, user, customer,month, start_date, end_date)
            elif graph_type == 'emotions_monthly':
                graph_data = self.get_emotions_monthly_data(user_type, user,customer, month, start_date, end_date)
            elif graph_type == 'compliance_monthly':
                graph_data = self.get_compliance_monthly_data(user_type, user,customer, month, start_date, end_date)
            elif graph_type == 'complaince_analysis':
                graph_data = self.get_complaince_analysis_graph_data(user_type, user,customer, start_date, end_date)
            else:
                response['message'] = 'Graph type is not valid.'
            response = graph_data
        except Exception as e:
            logger.warning(f"Can not able to fetch data for graph due to {e}")
            response = {}
        return Response(response, status=status_code)

"""
Dashboard Reports will be containing types:
1. Solution Run (solution_run)
2. User Happiness Index (happiness_index)
3. Predective Health Report (predective_health)
4. All Solutions (all_solutions)
5. All Hosts (all_hosts)
"""
class ReportsOperation(APIView):

    # solution run report
    def get_solution_run_report(self, user, start_date, end_date):
        solution_run_obj = SolutionRun.objects.all().order_by('customer')
        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            solution_run_obj = solution_run_obj.filter(customer=customer)
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")
            # Setting start_date to 12:00 AM
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Setting end_date to 11:59 PM
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            solution_run_obj = solution_run_obj.filter(created_at__range=(start_date, end_date))

        # Your header names
        headers = ['Customer', 'Host', 'Solution', 'Type', 'Run Date']
        # complaince obj data itteration
        solution_run_obj = [[data.customer.company_name, data.host.hostname, data.solution.name.title() if data.solution else "N/A", data.get_type_display(), timezone.localtime(data.created_at).strftime('%d-%m-%Y %H:%M:%S')] for data in solution_run_obj]
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename=test.csv"
        # Create a CSV writer and write the headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(headers)
        # Write demo data rows
        for row in solution_run_obj:
            csv_writer.writerow(row)
        return response

    # feedback report
    def get_feedback_report(self, user, start_date, end_date):
        feedback_obj = Feedback.objects.all().order_by('customer')
        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            feedback_obj = feedback_obj.filter(customer=customer)
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")
            # Setting start_date to 12:00 AM
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Setting end_date to 11:59 PM
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            feedback_obj = feedback_obj.filter(created_at__range=(start_date, end_date))

        # Your header names
        headers = ['Customer', 'Host', 'Solution', 'Feedback' ,'Type', 'Date']
        # complaince obj data itteration
        feedback_obj = [
            [
                data.customer.company_name,
                data.host.hostname,
                data.solution.name.title() if data.solution else "N/A",
                data.get_feedback_display(),
                data.get_solution_type_display(),
                timezone.localtime(data.created_at).strftime('%d-%m-%Y %H:%M:%S')
            ]
            for data in feedback_obj
        ]
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename=test.csv"
        # Create a CSV writer and write the headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(headers)
        # Write demo data rows
        for row in feedback_obj:
            csv_writer.writerow(row)
        return response

    # hosts report
    def get_hosts_report(self, user, start_date, end_date):
        def trim_version(version_str):
            return ".".join(version_str.split(".")[:3]) if version_str else ""
    
        host_obj = Host.objects.all().order_by('customer')
        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            host_obj = host_obj.filter(customer=customer)
        
        if start_date and end_date:
             # Parse the date strings in "dd-mm-yyyy" format
            start_date = datetime.strptime(start_date, "%d-%m-%Y").replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.strptime(end_date, "%d-%m-%Y").replace(hour=23, minute=59, second=59, microsecond=999999)

            # Make datetime objects timezone-aware (important if USE_TZ = True in Django settings)
            tz = get_current_timezone()
            start_date = make_aware(start_date, timezone=tz)
            end_date = make_aware(end_date, timezone=tz)

            # Apply the date range filter on the queryset
            host_obj = host_obj.filter(created_at__range=(start_date, end_date))

        # Your header names
        headers = ['Customer', 'Hostname', 'Created At', 'Last Login','Mac Address', 'Version']
        # complaince obj data itteration
        host_obj = [[data.customer.company_name, data.hostname, timezone.localtime(data.created_at).strftime('%d-%m-%Y %H:%M:%S'),timezone.localtime(data.updated_at).strftime('%d-%m-%Y %H:%M:%S'), data.mac_address, trim_version(data.version)] for data in host_obj]
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename=test.csv"
        # Create a CSV writer and write the headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(headers)
        # Write demo data rows
        for row in host_obj:
            csv_writer.writerow(row)
        return response
    
    def calculate_active_agents(self, start_date, end_date):
        """
        Calculate active hosts based on activities within the specified date range.
        Returns a set of unique hostnames.
        """
        # Query unique hosts/hostnames from all relevant tables
        solution_run_hosts = SolutionRun.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('host__hostname').distinct()

        agent_verification_hosts = AgentVerification.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('hostname').distinct()

        sentiment_hosts = Sentiment.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('host__hostname').distinct()
        
        complaince_entry_hosts = ComplainceEntry.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('host__hostname').distinct()
        
        complaince_autofix_entry_hosts = ComplianceAutoFixEntry.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('host__hostname').distinct()

        selfheal_hosts = SelfHealEntry.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('host__hostname').distinct()

        all_hosts = Host.objects.filter(
            updated_at__range=(start_date, end_date)
        ).values('hostname').distinct()

        # Combine all unique hosts/hostnames
        sol_lis = [i['host__hostname'] for i in solution_run_hosts]
        agent_lis = [j['hostname'] for j in agent_verification_hosts]
        sent_lis = [k['host__hostname'] for k in sentiment_hosts]
        compl_autofix = [l['host__hostname'] for l in complaince_entry_hosts]
        selfheal_lis = [m['host__hostname'] for m in selfheal_hosts]
        compl_autofix_lis = [n['host__hostname'] for n in complaince_autofix_entry_hosts]
        all_hosts_lis = [o['hostname'] for o in all_hosts]

        # Return set of all unique hostnames
        all_hostnames = set(sol_lis) | set(agent_lis) | set(sent_lis) | set(compl_autofix) | set(selfheal_lis) | set(compl_autofix_lis) | set(all_hosts_lis)
        unique_hostnames = list(set(all_hostnames))
        
        return unique_hostnames
    
    def get_active_agents_report(self, user, start_date, end_date):
        response = {}
        try:
            # Parse and validate date parameters
            if not start_date or not end_date:
                response['message'] = 'Start date and end date must be provided.'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                start_date = datetime.strptime(start_date, '%d-%m-%Y')
                end_date = datetime.strptime(end_date, '%d-%m-%Y').replace(hour=23, minute=59, second=59)
            except ValueError:
                response['message'] = 'Invalid date format. Use YYYY-MM-DD.'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            # Get unique hostnames
            unique_hostnames = self.calculate_active_agents(start_date, end_date)
            
            # Create CSV response
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Hostname'])
            
            # Write hostname data
            for hostname in unique_hostnames:
                writer.writerow([hostname or 'N/A'])
            
            # Prepare response
            output.seek(0)
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="active_agents_report.csv"'}
            )
            response.write(output.getvalue())
            output.close()
            
            return response
            
        except Exception as e:
            logger.warning(f"Cannot generate active agents report due to {e}")
            response['message'] = 'Something went wrong. Please contact support.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
    def get_solutions_report(self, user, start_date, end_date):
        solution_obj = Solution.objects.all().order_by('customer')
        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            solution_obj = solution_obj.filter(customer=customer)
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")
            # Setting start_date to 12:00 AM
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Setting end_date to 11:59 PM
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            solution_obj = solution_obj.filter(created_at__range=(start_date, end_date))

        # Your header names
        headers = ['Customer', 'Name', 'Created On']
        # complaince obj data itteration
        solution_obj = [[data.customer.company_name, data.name, timezone.localtime(timezone.localtime(data.created_at)).strftime('%d-%m-%Y %H:%M:%S')] for data in solution_obj]
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename=test.csv"
        # Create a CSV writer and write the headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(headers)
        # Write demo data rows
        for row in solution_obj:
            csv_writer.writerow(row)
        return response

    # customer report
    def get_customers_report(self, user, start_date, end_date):
        customer_obj = Customer.objects.all()
        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            customer_obj = customer_obj.filter(customer=customer)
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")
            # Setting start_date to 12:00 AM
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Setting end_date to 11:59 PM
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            customer_obj = customer_obj.filter(created_at__range=(start_date, end_date))

        # Your header names
        headers = ['Name', 'Phone', 'Domain', 'Host Count', 'License Start Date', 'License End Date', 'Total Licenses', 'Used Licenses', 'Avaibale Licenses', 'Created On']
        # complaince obj data itteration
        customer_obj = [
            [
                data.company_name,
                data.domain,
                Host.objects.filter(customer=data).count(),
                License.objects.get(customer=data).start_date.strftime('%d-%m-%Y'),
                License.objects.get(customer=data).end_date.strftime('%d-%m-%Y'),
                License.objects.get(customer=data).end_date,
                License.objects.get(customer=data).total_license,
                License.objects.get(customer=data).used_license,
                int(License.objects.get(customer=data).total_license - License.objects.get(customer=data).used_license),
                timezone.localtime(timezone.localtime(data.created_at)).strftime('%d-%m-%Y %H:%M:%S')
            ]
        for data in customer_obj]
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename=test.csv"
        # Create a CSV writer and write the headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(headers)
        # Write demo data rows
        for row in customer_obj:
            csv_writer.writerow(row)
        return response

    # compalince all host report
    def get_complaince_all_host_report(self, user, start_date, end_date):
        # Parse date range if provided
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, "%d-%m-%Y")
                end_date = datetime.strptime(end_date, "%d-%m-%Y")
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                return HttpResponseBadRequest("Invalid date format. Use DD-MM-YYYY.")
        else:
            start_date = None
            end_date = None

        # Fetch all compliance entries
        compliance_entries = ComplainceEntry.objects.all()

        # Apply date range filter if specified
        if start_date and end_date:
            compliance_entries = compliance_entries.filter(created_at__range=(start_date, end_date))

        # Filter by customer for customer users
        if user.user_type == 'customer':
            customer = user.customer_obj
            compliance_entries = compliance_entries.filter(customer=customer)
        else:
            customer = None  # for super admin

        # Get excluded parameters from ComplainceConfiguration where status=False
        config_filter = {} if user.user_type != 'customer' else {'customer': customer}
        excluded_keys = list(
            ComplainceConfiguration.objects.filter(status=False, **config_filter)
            .values_list('parameter_name', flat=True)
        )

        # Order by host and descending creation time to get latest entries
        compliance_entries = compliance_entries.order_by('host', '-created_at')

        # Collect the latest entry for each host
        latest_entries = []
        seen_hosts = set()
        for entry in compliance_entries:
            if entry.host_id not in seen_hosts:
                latest_entries.append(entry)
                seen_hosts.add(entry.host_id)

        # Collect unique parameter keys from the data JSON field (excluding excluded keys)
        parameter_set = set()
        for entry in latest_entries:
            if entry.data:
                for key in entry.data.keys():
                    if key not in excluded_keys:
                        parameter_set.add(key)
        parameter_list = sorted(list(parameter_set))

        # Define function to extract clean app names from keys
        def extract_app_name(key):
            start = key.find("'") + 1
            end = key.find("'", start)
            if start > 0 and end > start:
                return key[start:end]
            elif key.startswith("Status of "):
                return key[10:]
            else:
                return key

        # Define CSV headers with extracted app names
        headers = ['Customer', 'Host', 'Date'] + [extract_app_name(param) for param in parameter_list]

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="compliance_report.csv"'
        csv_writer = csv.writer(response)

        # Write headers
        csv_writer.writerow(headers)

        # Write data rows
        for entry in latest_entries:
            row = [
                entry.customer.company_name,
                entry.host.hostname,
                timezone.localtime(entry.created_at).strftime('%d-%m-%Y %H:%M:%S'),
            ] + [str(entry.data.get(param, 'N/A')) for param in parameter_list]
            csv_writer.writerow(row)
        return response

    # emotions all host report
    def get_emotions_all_host_report(self, user, start_date, end_date):
        sentiments_obj = Sentiment.objects.all().order_by('customer')
        headers = ['Customer', 'Host', 'RAM', 'CPU', 'Hardisk', 'Page Memory', 'Critical Services', 'Latency', 'Up Time', 'Run Time', 'Status']
        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            sentiments_obj = sentiments_obj.filter(customer=customer)
            # Your header names
            headers = [
                        'Customer', 'Host', 
                        f'RAM ({customer.ram})', 
                        f'CPU ({customer.cpu})', 
                        f'Hardisk ({customer.hardisk})',
                        f'Page Memory ({customer.page_memory})',
                        f'Critical Services ({customer.critical_services})',
                        f'Latency ({customer.latency})',
                        f'Up Time ({customer.uptime})',
                        'Run Time', 'Status'
                    ]
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")
            # Setting start_date to 12:00 AM
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Setting end_date to 11:59 PM
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            sentiments_obj = sentiments_obj.filter(created_at__range=(start_date, end_date))
        # complaince obj data itteration
        if user.user_type == 'customer':
            sentiments_obj = [
                [
                    data.customer.company_name, 
                    data.host.hostname,
                    data.ram,
                    data.cpu,
                    data.hardisk,
                    data.page_memory,
                    data.critical_services,
                    data.latency,
                    data.uptime,
                    data.get_status_display(),
                    timezone.localtime(timezone.localtime(data.created_at)).strftime('%d-%m-%Y %H:%M:%S')
                ] for data in sentiments_obj]
        else:
            sentiments_obj = [
                [
                    data.customer.company_name, 
                    data.host.hostname,
                    f'{round(data.ram, 2)} / {data.customer.ram}',
                    f'{round(data.cpu, 2)} / {data.customer.cpu}',
                    f'{round(data.hardisk, 2)} / {data.customer.hardisk}',
                    f'{round(data.page_memory, 2)} / {data.customer.page_memory}',
                    f'{round(data.critical_services, 2)} / {data.customer.critical_services}',
                    f'{round(data.latency, 2)} / {data.customer.latency}',
                    f'{round(data.uptime, 2)} / {data.customer.uptime}',
                    data.get_status_display(),
                    timezone.localtime(timezone.localtime(data.created_at)).strftime('%d-%m-%Y %H:%M:%S')
                ] for data in sentiments_obj]
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename=test.csv"
        # Create a CSV writer and write the headers
        csv_writer = csv.writer(response)
        csv_writer.writerow(headers)
        # Write demo data rows
        for row in sentiments_obj:
            csv_writer.writerow(row)
        return response
    
    def get_self_heal_report(self, user, start_date, end_date):
        """
        Generate and download a CSV report of SelfHealEntry records for the given date range.
        """
        try:
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, "%d-%m-%Y")
                    end_date = datetime.strptime(end_date, "%d-%m-%Y")
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                except ValueError:
                    return HttpResponseBadRequest("Invalid date format. Use DD-MM-YYYY.")
            else:
                start_date = None
                end_date = None

            # Fetch all parameter names from SelfHealConfiguration
            all_parameters = list(
                SelfHealConfiguration.objects.values_list("parameter_name", flat=True).distinct()
            )

            # Clean parameter names: remove "Status of" and exclude "Update Host Entry"
            cleaned_parameters = []
            for param in all_parameters:
                cleaned_param = param.replace("Status of ", "").replace("status of ", "").replace("'", "")
                if cleaned_param not in ["Update Host Entry", "'Update Host Entry'", "clear update logs", "'clear update logs'"]:
                    cleaned_parameters.append(cleaned_param)

            # Define CSV header
            headers = ["Customer", "Hostname", "Date"] + cleaned_parameters

            # Fetch SelfHealEntry records
            entries = SelfHealEntry.objects.select_related("customer", "host").filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            )

            # Create CSV content
            def generate_csv():
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(headers)  # Write header

                if not entries.exists():
                    writer.writerow(["No data available for the specified date range."] + [''] * (len(headers) - 1))
                else:
                    for entry in entries:
                        # Safely extract customer and host data
                        customer_name = getattr(entry.customer, 'company_name', str(entry.customer)) if entry.customer else 'N/A'
                        hostname = getattr(entry.host, 'hostname', str(entry.host)) if entry.host else 'N/A'

                        row = [
                            customer_name,
                            hostname,
                            entry.created_at.strftime("%Y-%m-%d %H:%M:%S") if entry.created_at else 'N/A'
                        ]

                        # Create a map of parameter status
                        status_map = {name: '' for name in cleaned_parameters}

                        # Parse JSON data for parameter statuses
                        try:
                            data = entry.data or {}
                            for param_name, value in data.items():
                                # Clean parameter name
                                cleaned_param_name = param_name.replace("Status of ", "").replace("status of ", "").replace("'", "")
                                if cleaned_param_name in ["Update Host Entry", "'Update Host Entry'"]:
                                    continue

                                try:
                                    # Try to parse as JSON or Python literal
                                    if isinstance(value, str):
                                        try:
                                            parsed_value = json.loads(value)
                                        except json.JSONDecodeError:
                                            parsed_value = ast.literal_eval(value)
                                    else:
                                        parsed_value = value

                                    # Ensure parsed_value is a list or tuple with message and status
                                    if isinstance(parsed_value, (list, tuple)) and len(parsed_value) == 2:
                                        message, status = parsed_value
                                        status_map[cleaned_param_name] = message if not status else message
                                    else:
                                        status_map[cleaned_param_name] = f"Error: Invalid data format for {cleaned_param_name}"
                                except (json.JSONDecodeError, ValueError, SyntaxError):
                                    status_map[cleaned_param_name] = f"Error: Invalid data format for {cleaned_param_name}"
                        except Exception as e:
                            logger.warning(f"Error parsing data for entry {entry.id}: {e}")

                        # Append statuses in order
                        row += [status_map.get(name, '') for name in cleaned_parameters]
                        writer.writerow(row)

                        output.seek(0)
                        yield output.read()
                        output.seek(0)
                        output.truncate(0)

            # Set up streaming response
            response = StreamingHttpResponse(
                generate_csv(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="self_heal_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
            return response

        except Exception as e:
            logger.error(f"Error generating self heal report: {e}")
            return Response({'message': 'Something went wrong. Please contact support.'}, status=status.HTTP_400_BAD_REQUEST)

    def get_compliance_autofix_report(self, user, start_date, end_date):
        """
        Generate and download a CSV report of ComplainceAutoFixEntry records for the given date range.
        """
        try:
            # Parse date strings, trying multiple formats
            date_formats = ['%d-%m-%Y', '%Y-%m-%d']
            parsed_start_date = None
            parsed_end_date = None

            for date_format in date_formats:
                try:
                    parsed_start_date = datetime.strptime(start_date, date_format).replace(tzinfo=timezone.get_current_timezone())
                    parsed_end_date = datetime.strptime(end_date, date_format).replace(tzinfo=timezone.get_current_timezone()) + timedelta(days=1)
                    break
                except ValueError:
                    continue

            if parsed_start_date is None or parsed_end_date is None:
                logger.error("Invalid date format provided.")
                return Response({'message': 'Invalid date format. Use DD-MM-YYYY or YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate date range
            if parsed_start_date > parsed_end_date:
                logger.error("start_date cannot be later than end_date.")
                return Response({'message': 'start_date cannot be later than end_date.'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch all compliance names from complainceHardeningAutoFix
            all_compliances = list(
                complainceHardeningAutoFix.objects.values_list("name", flat=True).distinct()
            )

            # Define CSV header
            headers = ["Customer", "Hostname", "Date"] + all_compliances

            # Fetch ComplainceAutoFixEntry records
            entries = ComplianceAutoFixEntry.objects.select_related("customer", "host").filter(
                created_at__gte=parsed_start_date,
                created_at__lt=parsed_end_date
            )

            # Create CSV content
            def generate_csv():
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(headers)  # Write header

                if not entries.exists():
                    writer.writerow(["No data available for the specified date range."] + [''] * (len(headers) - 1))
                else:
                    for entry in entries:
                        # Safely extract customer and host data
                        customer_name = getattr(entry.customer, 'company_name', str(entry.customer)) if entry.customer else 'N/A'
                        hostname = getattr(entry.host, 'hostname', str(entry.host)) if entry.host else 'N/A'

                        row = [
                            customer_name,
                            hostname,
                            entry.created_at.strftime("%Y-%m-%d %H:%M:%S") if entry.created_at else 'N/A'
                        ]

                        # Create a map of compliance status
                        status_map = {name: '' for name in all_compliances}

                        # Parse data for compliance statuses
                        try:
                            data = entry.data or []
                            for item in data:
                                name = item.get("compliance")
                                status = item.get("status")
                                remark = item.get("remark", "")
                                if name in status_map:
                                    status_map[name] = "Success" if status else f"Failed {remark}"
                        except Exception as e:
                            logger.warning(f"Error parsing data for entry {entry.id}: {e}")

                        # Append statuses in order
                        row += [status_map[name] for name in all_compliances]
                        writer.writerow(row)

                        output.seek(0)
                        yield output.read()
                        output.seek(0)
                        output.truncate(0)

            # Set up streaming response
            response = StreamingHttpResponse(
                generate_csv(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="compliance_autofix_report_{parsed_start_date.strftime("%Y%m%d")}_{parsed_end_date.strftime("%Y%m%d")}.csv"'
            return response

        except Exception as e:
            logger.error(f"Error generating compliance autofix report: {e}")
            return Response({'message': 'Something went wrong. Please contact support.'}, status=status.HTTP_400_BAD_REQUEST)
        
    def get_ticket_report(self, user, start_date, end_date):
        ticket_obj = Ticket.objects.all().order_by('customer')

        if user.user_type == 'customer':
            customer = Customer.objects.get(pk=user.customer_obj.id)
            ticket_obj = ticket_obj.filter(customer=customer)

        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")
            # Set time bounds
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            ticket_obj = ticket_obj.filter(created_at__range=(start_date, end_date))

        # CSV headers
        headers = ['Customer', 'Host', 'Ticket ID', 'Subject', 'Description', 'Date']

        # Convert ticket queryset to list of row data
        rows = [
            [
                ticket.customer.company_name if ticket.customer else "N/A",
                ticket.host.hostname if ticket.host else "N/A",
                ticket.ticket_id or "N/A",
                ticket.subject or "N/A",
                ticket.description or "N/A",
                timezone.localtime(ticket.created_at).strftime('%d-%m-%Y %H:%M:%S')
            ]
            for ticket in ticket_obj
        ]

        # Create response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=ticket_report.csv'
        writer = csv.writer(response)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

        return response

    def get(self, request):
        type = request.GET.get('type')
        print(f"Generating report for type: {type}")
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        response = {}
        if not type:
            response['message'] = 'Report type should be specified.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        try:
            if type not in ['solution_run', 'feedback', 'hosts', 'solutions', 'customers', 'ticket',
                                  'complaince_all_host', 'emotions_all_host', 'active_agents', 'auto_compliance', 'self_heal']:
                response['message'] = 'Report type is not valid.'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if request.user.user_type == 'customer' and type == 'customers':
                response['message'] = 'You are not authorized for the action.'
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            
            if type == 'solution_run':
                response = self.get_solution_run_report(request.user, start_date, end_date)
            elif type == 'feedback':
                response = self.get_feedback_report(request.user, start_date, end_date)
            elif type == 'hosts':
                response = self.get_hosts_report(request.user, start_date, end_date)
            elif type == 'active_agents':
                print("Generating active agents report...")
                response = self.get_active_agents_report(request.user, start_date, end_date)
            elif type == 'auto_compliance':
                response = self.get_compliance_autofix_report(request.user, start_date, end_date)
            elif type == 'self_heal':
                response = self.get_self_heal_report(request.user, start_date, end_date)
            elif type == 'solutions':
                response = self.get_solutions_report(request.user, start_date, end_date)
            elif type == 'customers':
                response = self.get_customers_report(request.user, start_date, end_date)
            elif type == 'complaince_all_host':
                response = self.get_complaince_all_host_report(request.user, start_date, end_date)
            elif type == 'emotions_all_host':
                response = self.get_emotions_all_host_report(request.user, start_date, end_date)
            elif type == 'ticket':
                response = self.get_ticket_report(request.user, start_date, end_date)
            else:
                response['message'] = 'Report type is not valid.'
            return response
        except Exception as e:
            logger.warning(f"Can not download the csv due to {e}")
            response['message'] = 'Something went wrong. please contact support.'
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class ApplicationConfOperations(APIView):
    permission_classes = [BotAPIPermissionClass]

    def get(self, request):
        status_code = status.HTTP_200_OK
        response = {}
        try:
            customer = request.user.customer_obj
            app_conf = ApplicationConfiguration.objects.filter(customer=customer)
            app_conf = app_conf.first()
            response = {
                "ad_server" : app_conf.ad_server,
                "ad_username" : app_conf.ad_username,
                "ad_password" : app_conf.ad_password,
                "itsm_api_url" : app_conf.itsm_api_url,
                "itsm_api_key" : app_conf.itsm_api_key,
                "itsm_api_token" : app_conf.itsm_api_token,
                "rasa_url" : app_conf.rasa_url,
                "api_url" : app_conf.api_url,
                "meta_data": app_conf.meta_data,
            }
        except Exception as e:
            logger.warning(f"Can not able to fetch data for application configuration due to {e}")
            response = {}
        return Response(response, status=status_code)
    

class AgentVerifificationOperation(APIView):
    post_serializer_class = AgentCheckPostSerializer
    permission_classes = [AllowAny]

    def create_new_agent_verification_entry(self, **kwargs):
        obj = None
        try:
            obj = AgentVerification.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Can not create agent verification entry object due to: {e}")
        return obj
    
    def clean_agent_data(self, agent_data):
        """
        Cleans up the nested 'tasks' field in the 'agent_data' dictionary.
        Parses and structures the task details into a more readable format.
        """
        tasks = agent_data.get('tasks', {})
        cleaned_tasks = {}

        # Loop through each task and reformat its details
        for task_name, task_details in tasks.items():
            # Split details by lines and create a dictionary of key-value pairs
            task_lines = task_details.splitlines()
            task_info = {}

            for line in task_lines:
                # Split only at the first occurrence of ':' to avoid issues in values
                if ':' in line:
                    key, value = line.split(':', 1)
                    task_info[key.strip()] = value.strip()

            # Structure and clean up specific fields as needed
            cleaned_tasks[task_name] = {
                'Folder': task_info.get('Folder', 'N/A'),
                'HostName': task_info.get('HostName', 'N/A'),
                'TaskName': task_info.get('TaskName', 'N/A'),
                'Next Run Time': task_info.get('Next Run Time', 'N/A'),
                'Status': task_info.get('Status', 'N/A'),
                'Last Run Time': task_info.get('Last Run Time', 'N/A'),
                'Last Result': task_info.get('Last Result', 'N/A'),
                'Task To Run': task_info.get('Task To Run', 'N/A'),
                'Start Time': task_info.get('Start Time', 'N/A'),
                'End Date': task_info.get('End Date', 'N/A'),
                'Schedule Type': task_info.get('Schedule Type', 'N/A'),
                'Days': task_info.get('Days', 'N/A'),
            }

        # Replace the original 'tasks' field with the cleaned structure
        agent_data['tasks'] = cleaned_tasks
        return agent_data

    def post(self, request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        try:
            cleaned_data = self.clean_agent_data(request.data)
            serializer = self.post_serializer_class(data=cleaned_data)
            if serializer.is_valid():
                if not serializer.validated_data.get('hostname'):
                    response['message'] = 'Hostname is required.'
                    return Response(response, status=status_code)
                
                if not serializer.validated_data.get('agent_data'):
                    response['message'] = 'Agent data is required.'
                    return Response(response, status=status_code)
                
                obj_data = {}
                
                obj_data = {
                    'hostname': serializer.validated_data.get('hostname'),
                    'data' : serializer.validated_data.get('agent_data'),
                }
                new_complaince_entry_obj = self.create_new_agent_verification_entry(**obj_data)
                if new_complaince_entry_obj:
                    logger.warning(f"New agent verification entry logged for user: {serializer.validated_data.get('hostname')}.")
                    response['status'] = True
                    response['message'] = f"New agent verification entry logged for user: {serializer.validated_data.get('hostname')}."
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create agent verification entry obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Agent verification entry serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create agent verification entry data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)

#Self Heal Section
class SelfHealConfigurationOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = SelfHealConfigurationGetSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = SelfHealConfiguration.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        try:
            customer_obj = Customer.objects.get(user=request.user)
            if request.user.user_type == 'customer':
                # self.queryset = self.queryset.filter(customer=request.user.customer_obj)
                self.queryset = self.queryset.filter(customer=customer_obj.id)
            queryset = self.queryset
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer_class(page, many=True)
            data = self.get_paginated_response(serializer.data)
            response = data.data
            for row in response["results"]:
                script_content = row["command"]
                threshold_value=row["threshold"]
                if threshold_value:
                    # Replace the placeholder in the script content
                    script_content = script_content.replace("{{THRESHOLD}}", str(threshold_value))
                    row["command"]=script_content

            response['count'] = len(response['results'])
            response['total_count'] = queryset.count()
        except Exception as e:
            logger.warning(f"Can not able to fetch data for host due to {e}")
            response = {
                "status" : True,
                "message" : 'No data available',
                "count" : 0,
                "next" : None,
                "previous" : None,
                "result" : []
            }
        return Response(response, status=status_code)

class SelfHealOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    # Use these serializer classes accordingly:
    get_serializer_class = SelfHealEntryGetSerializer
    get_main_serializer_class = SelfHealListSerializer
    post_serializer_class = SelfHealEntryPostSerializer
    permission_classes = [BotAPIPermissionClass]
    queryset = SelfHealEntry.objects.all()

    def get_status(self, host):
        latest_entry = SelfHealEntry.objects.filter(host=host).order_by('-created_at').first()
        if latest_entry:
            return latest_entry.status
        return False  # Or False or some default depending on your use case

    def create_new_selfheal_entry(self, **kwargs):
        try:
            obj = SelfHealEntry.objects.create(**kwargs)
        except Exception as e:
            logger.warning(f"Cannot create self-heal entry object due to: {e}")
            obj = None
        return obj

    def get(self, request):
        start_total = time.time()
        print("Starting get method")

        # Parse query parameters
        start_parse_params = time.time()
        search = request.GET.get("search")
        id = request.GET.get("id")
        host_id = request.GET.get("host_id")
        status_param = request.GET.get("status")
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        status_code = status.HTTP_200_OK
        response = {}
        print(f"Parse query parameters took {time.time() - start_parse_params:.3f} seconds")

        # Parse start_date and end_date
        start_parse_dates = time.time()
        start_date = None
        end_date = None
        if start_date_str and end_date_str:
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S'))
                end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S'))
            except ValueError:
                print("Invalid datetime format")
                return Response({
                    "status": False,
                    "message": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS.",
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "result": []
                }, status=status.HTTP_400_BAD_REQUEST)
        print(f"Parse dates took {time.time() - start_parse_dates:.3f} seconds")

        try:
            # Base queryset with customer filter
            start_base_queryset = time.time()
            selfheal_queryset = SelfHealEntry.objects.all()
            if request.user.user_type == 'customer':
                selfheal_queryset = selfheal_queryset.filter(customer=request.user.customer_obj)
            if start_date and end_date:
                selfheal_queryset = selfheal_queryset.filter(created_at__range=[start_date, end_date])
            # print(f"Base queryset construction took {time.time() - start_base_queryset:.3f} seconds")

            if host_id:
                start_host_fetch = time.time()
                host = Host.objects.get(id=host_id)
                # print(f"Fetching host took {time.time() - start_host_fetch:.3f} seconds")

                start_host_queryset = time.time()
                queryset = selfheal_queryset.filter(host=host)
                # print(f"Host queryset filter took {time.time() - start_host_queryset:.3f} seconds")

                start_pagination = time.time()
                page = self.paginate_queryset(queryset)
                # print(f"Pagination took {time.time() - start_pagination:.3f} seconds")

                start_serialization = time.time()
                serializer = self.get_serializer_class(page, many=True)
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['count'] = len(response['results'])
                response['total_count'] = queryset.count()
                # print(f"Serialization and response prep took {time.time() - start_serialization:.3f} seconds")
            else:
                start_host_ids = time.time()
                selfheal_host_ids = selfheal_queryset.values_list('host', flat=True).distinct()
                # print(f"Fetching distinct host IDs took {time.time() - start_host_ids:.3f} seconds")

                start_host_queryset = time.time()
                if request.user.user_type == 'customer':
                    self.queryset = Host.objects.filter(
                        id__in=selfheal_host_ids,
                        customer=request.user.customer_obj
                    ).select_related('customer').only('id', 'hostname', 'customer__company_name')
                else:
                    self.queryset = Host.objects.filter(id__in=selfheal_host_ids).select_related('customer').only('id', 'hostname', 'customer__company_name')
                print(f"Host queryset construction took {time.time() - start_host_queryset:.3f} seconds")

                start_annotation = time.time()
                latest_entry = SelfHealEntry.objects.filter(
                    host=OuterRef('pk')
                )
                if start_date and end_date:
                    latest_entry = latest_entry.filter(created_at__range=[start_date, end_date])
                self.queryset = self.queryset.annotate(
                    latest_update=Subquery(latest_entry.order_by('-created_at').values('updated_at')[:1]),
                    latest_status=Subquery(latest_entry.order_by('-created_at').values('status')[:1])
                )
                print(f"Annotation took {time.time() - start_annotation:.3f} seconds")

                queryset = self.queryset

                start_filters = time.time()
                if search:
                    queryset = queryset.filter(
                        Q(customer__company_name__icontains=search) |
                        Q(customer__domain__icontains=search) |
                        Q(hostname__icontains=search) |
                        Q(mac_address__icontains=search)
                    )
                elif id:
                    queryset = queryset.filter(id=id)
                if status_param is not None:
                    if status_param.lower() == 'true':
                        queryset = queryset.filter(latest_status=True)
                    elif status_param.lower() == 'false':
                        queryset = queryset.filter(latest_status=False)

                page = self.paginate_queryset(queryset)
                serializer = self.get_main_serializer_class(page, many=True)  # No context needed
                data = self.get_paginated_response(serializer.data)
                response = data.data
                response['count'] = len(response['results'])
                response['total_count'] = len(queryset)
        except Exception as e:
            logger.warning(f"Unable to fetch data for host due to: {e}")
            response = {
                "status": True,
                "message": "No data available",
                "count": 0,
                "next": None,
                "previous": None,
                "result": []
            }
        return Response(response, status=status_code)

    def post(self, request):
        response = {
            "status" : False,
            "message" : None,
            "data" : {}
        }
        status_code = status.HTTP_400_BAD_REQUEST
        hosts = Host.objects.all()
        print(f"Request user: {request.user}")

        print("selfheal request data",request.data)
        try:         
            serializer = self.post_serializer_class(data=request.data)
            if serializer.is_valid():
                if not serializer.validated_data.get('hostname'):
                    response['message'] = 'Hostname is required.'
                    return Response(response, status=status_code)
                
                if not serializer.validated_data.get('selfheal_data'):
                    response['message'] = 'SelfHeal data is required.'
                    return Response(response, status=status_code)
                
                customer = Customer.objects.get(user=request.user)
                host = Host.objects.get(hostname=serializer.validated_data.get('hostname'), customer=customer)
                obj_data = {}
                
                obj_data = {
                    'customer': customer,
                    'host': host,
                    'data' : serializer.validated_data.get('selfheal_data')
                }

                # Check if any value in selfheal_data is True
                selfheal_data_values = serializer.validated_data.get('selfheal_data').values()
                status_flag = any(
                    value if isinstance(value, bool) else (
                        eval(value)[1] if isinstance(value, str) and value.startswith('[') else False
                    )
                    for value in selfheal_data_values
                )

                obj_data['status'] = status_flag  # Set the computed status
                
                new_complaince_entry_obj = self.create_new_selfheal_entry(**obj_data)
                if new_complaince_entry_obj:
                    logger.warning(f"New Self Heal entry logged for user: {serializer.validated_data.get('hostname')}.")
                    response['status'] = True
                    response['message'] = f"New Self Heal entry logged for user: {serializer.validated_data.get('hostname')}."
                    status_code = status.HTTP_201_CREATED
                else:
                    logger.warning(f"Can not create self heal entry obj")
                    response['message'] = "Something went wrong, please try again later."
            else:
                logger.warning(f"Self Heal Entry serializer validation fails due to: {serializer.errors}")
                response['message'] = "Something went wrong, please try again later."
        except Exception as e:
            logger.warning(f"Can not create Self Heal entry data entry due to: {e}")
            response['message'] = "Something went wrong, please try again later."
        return Response(response, status=status_code)

logger = logging.getLogger(__name__)

# Configurable thresholds for priority logic (customize per environment)
PRIORITY_THRESHOLDS = {
    "compliance_metrics": {"high": 80, "medium": 95},
    "host_with_most_raised_tickets": {"high_factor": 3, "medium_factor": 1.5},
    "consistently_sad_hosts": {"high": {"percentage": 85, "sad_entries": 10}, "medium": {"percentage": 60, "sad_entries": 5}},
    "latency_down_hosts": {"high": {"violation_percentage": 60, "days_count": 30}, "medium": {"violation_percentage": 30, "days_count": 10}},
    "hosts_with_high_ram_usage": {"high": {"violation_percentage": 60, "days_count": 30}, "medium": {"violation_percentage": 30, "days_count": 10}},
    "performance_metrics": {"overutilized": {"high": 95, "medium": 80}, "underutilized": {"medium": 25}},
    "self_heal_summary_today": {"high": {"rate": 50, "min_runs": 10, "min_success": 5}, "medium": 80},
    "top_5_issues_resolved": {"high": {"count": 10, "proportion": 0.1}, "medium": 3},
    "solution_run": {"high": {"ticket_dominance": True}, "medium": {"ticket_count": 0}}
}

# Parameter-specific action suggestions
PARAMETER_ACTIONS = {
    "cpu": "Optimize workloads or upgrade CPU capacity.",
    "ram": "Check for memory leaks or add more RAM.",
    "latency": "Review network configurations or increase bandwidth.",
    "hardisk": "Free up disk space or expand storage.",
    "page_memory": "Optimize paging settings or increase RAM.",
    "critical_services": "Ensure critical services are running and properly configured.",
    "uptime": "Investigate frequent reboots or power issues."
}

class DashboardSystemInsights(APIView):
    permission_classes = [BotAPIPermissionClass]

    def safe_parse(self, val):
        """Safely parse a string representation of a list or return list/dict as-is. Return None if parsing fails."""
        if isinstance(val, (dict, list)):
            return val
        if isinstance(val, str):
            val = val.strip()
            if not (val.startswith("[") and val.endswith("]")):
                return None
            try:
                parsed = ast.literal_eval(val)
                return parsed if isinstance(parsed, (dict, list)) else None
            except (SyntaxError, ValueError):
                # logger.warning(f"safe_parse failed for value: {val}")
                return None
        return None

    def _initialize_data(self, request, start_date, end_date):
        """Initialize common data structures for metric computations with date range."""
        customer_filter = {}
        if request.user.user_type == 'customer':
            customer = Customer.objects.get(pk=request.user.customer_obj.id)
            customer_filter = {'customer': customer}
            total_hosts = Host.objects.filter(customer=customer).count()
            host_qs = Host.objects.filter(customer=customer).select_related('customer')
        else:
            total_hosts = Host.objects.all().count()
            host_qs = Host.objects.all().select_related('customer')

        host_ids = list(host_qs.values_list('id', flat=True))
        hosts = Host.objects.all()
        host_map = {host.id: str(host) for host in hosts}

        sentiment_qs = Sentiment.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            host_id__in=host_ids
        ).values('host_id', 'status', 'created_at', 'latency', 'ram', 'cpu', 'hardisk', 'page_memory', 'critical_services', 'uptime')
        sentiment_df = pd.DataFrame.from_records(sentiment_qs)
        if not sentiment_df.empty:
            sentiment_df['date'] = pd.to_datetime(sentiment_df['created_at']).dt.date

        thresholds = {h.id: {
            "cpu": h.customer.cpu, "ram": h.customer.ram, "hardisk": h.customer.hardisk,
            "page_memory": h.customer.page_memory, "critical_services": h.customer.critical_services,
            "latency": h.customer.latency, "uptime": h.customer.uptime
        } for h in host_qs}

        return {
            'customer_filter': customer_filter,
            'total_hosts': total_hosts,
            'host_qs': host_qs,
            'host_ids': host_ids,
            'host_map': host_map,
            'start_date': start_date,
            'end_date': end_date,
            'sentiment_df': sentiment_df,
            'thresholds': thresholds
        }

    def _compute_compliance_metrics(self, data, include_insights, include_data):
        """Compute compliance metrics and insights."""
        compliance_qs = ComplainceEntry.objects.filter(
            updated_at__gte=data['start_date'],
        updated_at__lte=data['end_date'],
            **data['customer_filter']
        ).values('host_id', 'data', 'updated_at')
        compliance_df = pd.DataFrame.from_records(compliance_qs)
        compliant = 0
        if not compliance_df.empty:
            compliance_df = compliance_df.sort_values('updated_at').drop_duplicates('host_id', keep='last')
            compliance_df['is_compliant'] = compliance_df['data'].apply(
                lambda d: all(self.safe_parse(d).values()) if self.safe_parse(d) is not None else False
            )
            compliant = compliance_df['is_compliant'].sum()

        compliance_rate = (compliant / data['total_hosts'] * 100) if data['total_hosts'] > 0 else 0
        metric_data = {"compliance_rate": round(compliance_rate, 2)} if include_data else None
        insights = []

        if include_insights:
            priority = (
                "low" if compliance_rate > PRIORITY_THRESHOLDS["compliance_metrics"]["medium"] else
                "medium" if compliance_rate > PRIORITY_THRESHOLDS["compliance_metrics"]["high"] else "high"
            )
            
            if compliant == 0:
                text = f"None of the {data['total_hosts']} hosts (0.0%) are compliant with security standards. Immediate action is recommended to address all non-compliant hosts."
            elif data['total_hosts'] > compliant:
                text = f"{compliant} of {data['total_hosts']} hosts ({compliance_rate:.1f}%) are compliant with security standards. Address non-compliant hosts to reduce risks."
            else:
                text = f"{compliant} of {data['total_hosts']} hosts ({compliance_rate:.1f}%) are compliant with security standards. Great job!"

            insights.append({
                "title": "Compliance Overview",
                "text": text,
                "priority": priority,
                "details": {"compliant_hosts": compliant, "total_hosts": data['total_hosts'], "compliance_rate": round(compliance_rate, 2)}
            })

        return metric_data, insights

    def _compute_host_with_most_raised_tickets(self, data, include_insights, include_data):
        """Compute host with most raised tickets and insights for the specified date range."""
        ticket_qs = Ticket.objects.filter(
            created_at__gte=data['start_date'],
            created_at__lte=data['end_date'],
            **data['customer_filter']
        )
        ticket_df = pd.DataFrame.from_records(ticket_qs.values('host_id'))
        host_with_most_raised_tickets = {"host": None, "count": 0}
        avg_tickets_per_host = ticket_df['host_id'].value_counts().mean() if not ticket_df.empty else 0

        if not ticket_df.empty:
            top_ticket = ticket_df['host_id'].value_counts().idxmax()
            count = ticket_df['host_id'].value_counts().max()
            host_with_most_raised_tickets = {
                "host": data['host_map'].get(top_ticket, "Unknown"),
                "count": count
            }

        metric_data = host_with_most_raised_tickets if include_data else None
        insights = []

        if include_insights and host_with_most_raised_tickets["host"]:
            priority = (
                "high" if host_with_most_raised_tickets["count"] > PRIORITY_THRESHOLDS["host_with_most_raised_tickets"]["high_factor"] * avg_tickets_per_host else
                "medium" if host_with_most_raised_tickets["count"] > PRIORITY_THRESHOLDS["host_with_most_raised_tickets"]["medium_factor"] * avg_tickets_per_host else
                "low"
            )
            date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
            insights.append({
                "title": "Host with Most Tickets",
                "text": f"Host '{host_with_most_raised_tickets['host']}' raised {host_with_most_raised_tickets['count']} tickets {date_range_text}, "
                        f"above the average of {avg_tickets_per_host:.1f} tickets per host.",
                "priority": priority,
                "details": {"host": host_with_most_raised_tickets["host"], "count": host_with_most_raised_tickets["count"]}
            })

        return metric_data, insights

    def _compute_consistently_sad_hosts(self, data, include_insights, include_data):
        """Compute consistently sad hosts and insights for the specified date range."""
        consistently_sad_hosts = []
        if not data['sentiment_df'].empty:
            sad_stats = data['sentiment_df'].groupby('host_id').agg(
                total_entries=('status', 'count'),
                sad_entries=('status', lambda x: (x == 'sad').sum())
            )
            sad_stats['sad_percentage'] = 100 * sad_stats['sad_entries'] / sad_stats['total_entries']
            sad_stats = sad_stats.sort_values('sad_percentage', ascending=False)

            top_hosts_df = sad_stats[sad_stats['sad_percentage'] >= 90].head(5)
            if top_hosts_df.empty:
                top_hosts_df = sad_stats.head(5)

            parameters = ['cpu', 'ram', 'hardisk', 'page_memory', 'critical_services', 'latency', 'uptime']
            sad_sentiments = data['sentiment_df'][data['sentiment_df']['status'] == 'sad']
            host_to_failed_params = defaultdict(list)

            for _, row in sad_sentiments.iterrows():
                host_id = row['host_id']
                threshold = data['thresholds'].get(host_id)
                if not threshold:
                    continue
                for param in parameters:
                    val = row.get(param)
                    thresh = threshold.get(param)
                    if val is not None and thresh is not None and val > thresh:
                        host_to_failed_params[host_id].append(param)

            for host_id, row in top_hosts_df.iterrows():
                failed_params = host_to_failed_params.get(host_id, [])
                top_params = [param for param, _ in Counter(failed_params).most_common(3)]
                consistently_sad_hosts.append({
                    "host": data['host_map'].get(host_id, "Unknown"),
                    "percentage": round(row['sad_percentage'], 2),
                    "total_entries": int(row['total_entries']),
                    "sad_entries": int(row['sad_entries']),
                    "top_3_parameters": top_params
                })

        metric_data = consistently_sad_hosts if include_data else None
        insights = []

        if include_insights and consistently_sad_hosts:
            top = consistently_sad_hosts[0]
            priority = (
                "high" if (top['percentage'] >= PRIORITY_THRESHOLDS["consistently_sad_hosts"]["high"]["percentage"] and
                        top['sad_entries'] > PRIORITY_THRESHOLDS["consistently_sad_hosts"]["high"]["sad_entries"]) else
                "medium" if (top['percentage'] >= PRIORITY_THRESHOLDS["consistently_sad_hosts"]["medium"]["percentage"] or
                            top['sad_entries'] > PRIORITY_THRESHOLDS["consistently_sad_hosts"]["medium"]["sad_entries"]) else
                "low"
            )
            param_text = f" Key problem areas: {', '.join(top['top_3_parameters'])}." if top['top_3_parameters'] else " No specific parameters identified."
            date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
            insights.append({
                "title": "Consistently Sad Host",
                "text": f"Host '{top['host']}' reported most issues {date_range_text} ({top['percentage']}%).{param_text}",
                "priority": priority,
                "details": {"host": top['host'], "sad_percentage": top['percentage'], "top_parameters": top['top_3_parameters']}
            })

        return metric_data, insights

    def _compute_latency_down_hosts(self, data, include_insights, include_data):
        """Compute latency down hosts and insights for the specified date range."""
        latency_down_hosts = []
        if not data['sentiment_df'].empty:
            sentiment_df = data['sentiment_df'].copy()
            sentiment_df['latency_threshold'] = sentiment_df['host_id'].map({h.id: h.customer.latency for h in data['host_qs']})
            latency_df = sentiment_df[sentiment_df['latency'] > sentiment_df['latency_threshold']]
            for hid in latency_df['host_id'].unique():
                host_data = sentiment_df[sentiment_df['host_id'] == hid]
                over_thresh = host_data[host_data['latency'] > host_data['latency_threshold']]
                total_entries = len(host_data)
                violations = len(over_thresh)
                unique_violation_days = over_thresh['date'].nunique()
                avg_exceeded_value = over_thresh['latency'].mean()
                last_violation_date = over_thresh['date'].max()
                latency_down_hosts.append({
                    "host": data['host_map'].get(hid, "Unknown"),
                    "days_count": unique_violation_days,
                    "threshold": data['thresholds'].get(hid, {}).get('latency'),
                    "total_entries_checked": total_entries,
                    "violation_percentage": round((violations / total_entries) * 100, 1) if total_entries else 0,
                    "avg_value_when_exceeded": round(avg_exceeded_value, 1) if not pd.isna(avg_exceeded_value) else None,
                    "most_recent_violation": str(last_violation_date) if pd.notnull(last_violation_date) else None
                })
            latency_down_hosts.sort(key=lambda x: x["days_count"], reverse=True)

        metric_data = latency_down_hosts[:5] if include_data else None
        insights = []

        if include_insights:
            date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
            if latency_down_hosts:
                top = latency_down_hosts[0]
                priority = (
                    "high" if (top['violation_percentage'] >= PRIORITY_THRESHOLDS["latency_down_hosts"]["high"]["violation_percentage"] and
                            top['days_count'] > PRIORITY_THRESHOLDS["latency_down_hosts"]["high"]["days_count"]) else
                    "medium" if (top['violation_percentage'] >= PRIORITY_THRESHOLDS["latency_down_hosts"]["medium"]["violation_percentage"] or
                                top['days_count'] > PRIORITY_THRESHOLDS["latency_down_hosts"]["medium"]["days_count"]) else
                    "low"
                )
                insights.append({
                    "title": "High Latency Host",
                    "text": f"Host '{top['host']}' had high latency {date_range_text}. "
                            f"This may impact performance.",
                    "priority": priority,
                    "action": "Investigate network or resource bottlenecks on this host.",
                    "details": {"host": top['host'], "days_count": top['days_count'], "violation_percentage": top['violation_percentage']}
                })
            else:
                insights.append({
                    "title": "High Latency Host",
                    "text": f"No hosts detected with significant latency issues {date_range_text}.",
                    "priority": "low",
                    "action": "Continue monitoring latency metrics.",
                    "details": {"hosts_affected": 0}
                })

        return metric_data, insights

    def _compute_hosts_with_high_ram_usage(self, data, include_insights, include_data):
        """Compute hosts with high RAM usage and insights for the specified date range."""
        hosts_with_high_ram_usage = []
        if not data['sentiment_df'].empty:
            sentiment_df = data['sentiment_df'].copy()
            sentiment_df['ram_threshold'] = sentiment_df['host_id'].map({h.id: h.customer.ram for h in data['host_qs']})
            ram_df = sentiment_df[sentiment_df['ram'] > sentiment_df['ram_threshold']]
            for hid in ram_df['host_id'].unique():
                host_data = sentiment_df[sentiment_df['host_id'] == hid]
                over_thresh = host_data[host_data['ram'] > host_data['ram_threshold']]
                total_entries = len(host_data)
                violations = len(over_thresh)
                unique_violation_days = over_thresh['date'].nunique()
                avg_exceeded_value = over_thresh['ram'].mean()
                last_violation_date = over_thresh['date'].max()
                hosts_with_high_ram_usage.append({
                    "host": data['host_map'].get(hid, "Unknown"),
                    "days_count": unique_violation_days,
                    "threshold": data['thresholds'].get(hid, {}).get('ram'),
                    "total_entries_checked": total_entries,
                    "violation_percentage": round((violations / total_entries) * 100, 1) if total_entries else 0,
                    "avg_value_when_exceeded": round(avg_exceeded_value, 1) if not pd.isna(avg_exceeded_value) else None,
                    "most_recent_violation": str(last_violation_date) if pd.notnull(last_violation_date) else None
                })
            hosts_with_high_ram_usage.sort(key=lambda x: x["days_count"], reverse=True)

        metric_data = hosts_with_high_ram_usage[:5] if include_data else None
        insights = []

        if include_insights:
            date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
            if hosts_with_high_ram_usage:
                top = hosts_with_high_ram_usage[0]
                priority = (
                    "high" if (top['violation_percentage'] >= PRIORITY_THRESHOLDS["hosts_with_high_ram_usage"]["high"]["violation_percentage"] and
                            top['days_count'] > PRIORITY_THRESHOLDS["hosts_with_high_ram_usage"]["high"]["days_count"]) else
                    "medium" if (top['violation_percentage'] >= PRIORITY_THRESHOLDS["hosts_with_high_ram_usage"]["medium"]["violation_percentage"] or
                                top['days_count'] > PRIORITY_THRESHOLDS["hosts_with_high_ram_usage"]["medium"]["days_count"]) else
                    "low"
                )
                insights.append({
                    "title": "High RAM Usage",
                    "text": f"Host '{top['host']}' exceeded RAM threshold {date_range_text}. "
                            f"This may slow processes.",
                    "priority": priority,
                    "action": "Investigate memory-intensive processes or consider upgrading RAM.",
                    "details": {"host": top['host'], "days_count": top['days_count'], "violation_percentage": top['violation_percentage']}
                })
            else:
                insights.append({
                    "title": "High RAM Usage",
                    "text": f"No hosts detected with significant RAM usage issues {date_range_text}.",
                    "priority": "low",
                    "action": "Continue monitoring RAM usage metrics.",
                    "details": {"hosts_affected": 0}
                })

        return metric_data, insights

    def _compute_performance_metrics(self, data, include_insights, include_data):
        """Compute performance metrics and insights for the specified date range."""
        performance_metrics = {}
        latest_critical_subquery = Sentiment.objects.filter(
            host=OuterRef('pk'),
            created_at__gte=data['start_date'],
            created_at__lte=data['end_date']
        ).order_by('-updated_at').values('critical_services')[:1]
        hosts_with_latest_critical = data['host_qs'].annotate(
            latest_critical=Subquery(latest_critical_subquery)
        )
        critical_service_hosts_count = hosts_with_latest_critical.filter(latest_critical__lt=100).count()
        performance_metrics["critical_services_host_count"] = critical_service_hosts_count

        latest_page_memory_subquery = Sentiment.objects.filter(
            host=OuterRef('pk'),
            created_at__gte=data['start_date'],
            created_at__lte=data['end_date'],
            **data['customer_filter']
        ).order_by('-updated_at').values('page_memory')[:1]
        hosts_with_latest_page_memory = Host.objects.filter(
            id__in=Sentiment.objects.filter(
                created_at__gte=data['start_date'],
                created_at__lte=data['end_date'],
                **data['customer_filter']
            ).values_list('host', flat=True).distinct()
        ).annotate(latest_page_memory=Subquery(latest_page_memory_subquery))
        avg_page_memory = hosts_with_latest_page_memory.aggregate(avg_page_memory=Avg('latest_page_memory'))['avg_page_memory'] or 0.0
        performance_metrics["avg_page_memory_usage"] = round(avg_page_memory, 2)

        latest_cpu_subquery = Sentiment.objects.filter(
            host=OuterRef('pk'),
            created_at__gte=data['start_date'],
            created_at__lte=data['end_date'],
            **data['customer_filter']
        ).order_by('-updated_at').values('cpu')[:1]
        latest_ram_subquery = Sentiment.objects.filter(
            host=OuterRef('pk'),
            created_at__gte=data['start_date'],
            created_at__lte=data['end_date'],
            **data['customer_filter']
        ).order_by('-updated_at').values('ram')[:1]
        hosts_with_latest_util = Host.objects.filter(
            id__in=Sentiment.objects.filter(
                created_at__gte=data['start_date'],
                created_at__lte=data['end_date'],
                **data['customer_filter']
            ).values_list('host', flat=True).distinct()
        ).annotate(
            latest_cpu=Subquery(latest_cpu_subquery),
            latest_ram=Subquery(latest_ram_subquery),
            cpu_threshold=F('customer__cpu'),
            ram_threshold=F('customer__ram'),
            combined_threshold=F('customer__cpu') + F('customer__ram')
        )

        underutilized_hosts = hosts_with_latest_util.filter(
            latest_cpu__lt=ExpressionWrapper(F('cpu_threshold') * 0.20, output_field=FloatField()),
            latest_ram__lt=ExpressionWrapper(F('ram_threshold') * 0.20, output_field=FloatField())
        ).order_by('-combined_threshold')[:5]
        top_underutilized_systems = [
            {
                "host": host.hostname,
                "latest_cpu": host.latest_cpu,
                "cpu_threshold": host.cpu_threshold,
                "latest_ram": host.latest_ram,
                "ram_threshold": host.ram_threshold,
                "combined_threshold": host.combined_threshold
            } for host in underutilized_hosts
        ]
        performance_metrics["top_underutilized_systems"] = top_underutilized_systems

        overutilized_hosts = hosts_with_latest_util.filter(
            latest_cpu__gt=ExpressionWrapper(F('cpu_threshold') * 0.90, output_field=FloatField()),
            latest_ram__gt=ExpressionWrapper(F('ram_threshold') * 0.90, output_field=FloatField())
        ).order_by('-latest_cpu', '-latest_ram')[:5]
        top_overutilized_systems = [
            {
                "host": host.hostname,
                "latest_cpu": host.latest_cpu,
                "cpu_threshold": host.cpu_threshold,
                "latest_ram": host.latest_ram,
                "ram_threshold": host.ram_threshold,
            } for host in overutilized_hosts
        ]
        performance_metrics["top_overutilized_systems"] = top_overutilized_systems

        metric_data = performance_metrics if include_data else None
        insights = []

        if include_insights:
            date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
            if top_overutilized_systems:
                top = top_overutilized_systems[0]
                priority = (
                    "high" if (top['latest_cpu'] / top['cpu_threshold'] * 100 > PRIORITY_THRESHOLDS["performance_metrics"]["overutilized"]["high"] or
                            top['latest_ram'] / top['ram_threshold'] * 100 > PRIORITY_THRESHOLDS["performance_metrics"]["overutilized"]["high"]) else
                    "medium" if (top['latest_cpu'] / top['cpu_threshold'] * 100 > PRIORITY_THRESHOLDS["performance_metrics"]["overutilized"]["medium"] or
                                top['latest_ram'] / top['ram_threshold'] * 100 > PRIORITY_THRESHOLDS["performance_metrics"]["overutilized"]["medium"]) else
                    "low"
                )
                insights.append({
                    "title": "Overutilized Host",
                    "text": f"Host '{top['host']}' is heavily loaded {date_range_text}, using {top['latest_cpu']}% CPU and "
                            f"{top['latest_ram']}% RAM (thresholds: {top['cpu_threshold']}%, {top['ram_threshold']}%). "
                            f"This risks performance issues.",
                    "priority": priority,
                    "action": "Optimize workloads or redistribute tasks to underutilized hosts.",
                    "details": {"host": top['host'], "cpu_usage": top['latest_cpu'], "ram_usage": top['latest_ram']}
                })
            else:
                insights.append({
                    "title": "Overutilized Host",
                    "text": f"No hosts detected with significant CPU or RAM overutilization {date_range_text}.",
                    "priority": "low",
                    "action": "Continue monitoring CPU and RAM usage.",
                    "details": {"hosts_affected": 0}
                })

            if top_underutilized_systems:
                top = top_underutilized_systems[0]
                priority = (
                    "medium" if (top['latest_cpu'] / top['cpu_threshold'] * 100 < PRIORITY_THRESHOLDS["performance_metrics"]["underutilized"]["medium"] and
                                top['latest_ram'] / top['ram_threshold'] * 100 < PRIORITY_THRESHOLDS["performance_metrics"]["underutilized"]["medium"]) else
                    "low"
                )
                insights.append({
                    "title": "Underutilized Host",
                    "text": f"Host '{top['host']}' is underused {date_range_text}, running at {top['latest_cpu']}% CPU and "
                            f"{top['latest_ram']}% RAM (thresholds: {top['cpu_threshold']}%, {top['ram_threshold']}%). "
                            f"You may be overpaying for capacity.",
                    "priority": priority,
                    "action": "Consider consolidating workloads or downsizing resources.",
                    "details": {"host": top['host'], "cpu_usage": top['latest_cpu'], "ram_usage": top['latest_ram']}
                })
            else:
                insights.append({
                    "title": "Underutilized Host",
                    "text": f"No hosts detected with significant CPU or RAM underutilization {date_range_text}.",
                    "priority": "low",
                    "action": "Continue monitoring resource utilization.",
                    "details": {"hosts_affected": 0}
                })

        return metric_data, insights

    def _compute_self_heal_summary_today(self, data, include_insights, include_data):
        """Compute self-heal summary for the specified date range and insights."""
        start = time.time()
        current_date = now().date()
        start_date = make_aware(datetime.combine(current_date, dt_time(0, 0, 0)))
        end_date = make_aware(datetime.combine(current_date, dt_time(23, 59, 59)))
        # print(f"--------Start date: {start_date}, End date: {end_date}")
        all_qs = SelfHealEntry.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        counts = all_qs.aggregate(
            total_runs=Count('id'),
            successful_runs=Count('id', filter=Q(status=True))
        )

        total_self_heal_runs = counts['total_runs']
        successful_self_heals = counts['successful_runs']

        summary = {
            "start_date": str(start_date.date()),
            "end_date": str(end_date.date()),
            "total_runs": total_self_heal_runs,
            "successful_self_heals": successful_self_heals
        }
        metric_data = summary if include_data else None
        insights = []

        if include_insights and total_self_heal_runs > 0:
            rate = (successful_self_heals / total_self_heal_runs) * 100
            priority = (
                "high" if (rate < PRIORITY_THRESHOLDS["self_heal_summary_today"]["high"]["rate"] or
                        (total_self_heal_runs > PRIORITY_THRESHOLDS["self_heal_summary_today"]["high"]["min_runs"] and
                            successful_self_heals < PRIORITY_THRESHOLDS["self_heal_summary_today"]["high"]["min_success"])) else
                "medium" if rate < PRIORITY_THRESHOLDS["self_heal_summary_today"]["medium"] else
                "low"
            )
            date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
            insights.append({
                "title": "Self-Heal Success Rate",
                "text": f"{successful_self_heals} of {total_self_heal_runs} self-healing attempts succeeded ({rate:.1f}%) {date_range_text}.",
                "priority": priority,
                "action": "Review failed self-heal attempts to identify persistent issues." if rate < 90 else "Continue monitoring self-heal performance.",
                "details": {
                    "total_runs": total_self_heal_runs,
                    "successful_runs": successful_self_heals,
                    "success_rate": round(rate, 1)
                }
            })
        return metric_data, insights
    
    def _compute_top_5_issues_resolved(self, data, include_insights, include_data):
        """Compute top 5 issues resolved in the specified date range using optimized parsing."""
        # Get current date in the project's timezone
        current_date = now().date()
        start_date = make_aware(datetime.combine(current_date, dt_time(0, 0, 0)))
        end_date = make_aware(datetime.combine(current_date, dt_time(23, 0, 0)))
        self_heal_entries = SelfHealEntry.objects.filter(
            host_id__in=data['host_ids'],
            created_at__gte=start_date,
            created_at__lte=end_date,
            status=True
        ).values_list('data', flat=True)

        issue_counter = Counter()
        total_self_heals = 0

        for raw_data in self_heal_entries:
            if not raw_data:
                continue
            try:
                parsed_data = self.safe_parse(raw_data)
                if not isinstance(parsed_data, dict):
                    continue

                for key, val in parsed_data.items():
                    val_parsed = self.safe_parse(val)
                    if isinstance(val_parsed, list) and len(val_parsed) == 2 and val_parsed[1] is True:
                        param_name = key.strip("'")
                        issue_counter[param_name] += 1
                        total_self_heals += 1
            except Exception:
                continue

        top_5_issues_resolved = [
            {"parameter": name.replace("_", " "), "count": count}
            for name, count in issue_counter.most_common(5)
        ]
        metric_data = top_5_issues_resolved if include_data else None
        insights = []

        if include_insights:
            date_range_text = f"on {start_date.date()}"
            if top_5_issues_resolved:
                top = top_5_issues_resolved[0]
                priority = (
                    "high" if (
                        top['count'] > PRIORITY_THRESHOLDS["top_5_issues_resolved"]["high"]["count"] and
                        top['count'] > PRIORITY_THRESHOLDS["top_5_issues_resolved"]["high"]["proportion"] * total_self_heals
                    ) else
                    "medium" if top['count'] > PRIORITY_THRESHOLDS["top_5_issues_resolved"]["medium"] else
                    "low"
                )
                insights.append({
                    "title": "Top Resolved Issue",
                    "text": f"Top resolved issue was '{top['parameter']}', fixed {top['count']} times {date_range_text}. "
                            f"This may indicate a recurring problem.",
                    "priority": priority,
                    "action": f"Investigate root cause of recurring '{top['parameter']}' issues.",
                    "details": {"parameter": top['parameter'], "count": top['count']}
                })
            else:
                insights.append({
                    "title": "Top Resolved Issue",
                    "text": f"No self-heal issues resolved {date_range_text}.",
                    "priority": "low",
                    "action": "Continue monitoring self-heal activity.",
                    "details": {"issues_resolved": 0}
                })

        return metric_data, insights

    def _compute_solution_run(self, request, data, include_insights, include_data):
        """Compute solution run metrics and insights for the specified date range."""
        solution_counts = {'auto_fix': 0, 'using_kb': 0, 'ticket_count': 0}
        max_solution_type = 'none'
        max_count = 0
        metric_data = None
        insights = []

        try:
            if request.user.user_type == 'customer':
                customer = Customer.objects.get(pk=request.user.customer_obj.id)
                solution_counts['ticket_count'] = SolutionRun.objects.filter(
                    customer=customer, type='ticket', created_at__gte=data['start_date'], created_at__lte=data['end_date']
                ).count()
                solution_counts['auto_fix'] = SolutionRun.objects.filter(
                    customer=customer, type='autofix', created_at__gte=data['start_date'], created_at__lte=data['end_date']
                ).count()
                solution_counts['using_kb'] = SolutionRun.objects.filter(
                    customer=customer, type='kb', created_at__gte=data['start_date'], created_at__lte=data['end_date']
                ).count()
            else:
                solution_counts['ticket_count'] = SolutionRun.objects.filter(
                    type='ticket', created_at__gte=data['start_date'], created_at__lte=data['end_date']
                ).count()
                solution_counts['auto_fix'] = SolutionRun.objects.filter(
                    type='autofix', created_at__gte=data['start_date'], created_at__lte=data['end_date']
                ).count()
                solution_counts['using_kb'] = SolutionRun.objects.filter(
                    type='kb', created_at__gte=data['start_date'], created_at__lte=data['end_date']
                ).count()

            total_counts = sum(solution_counts.values())
            if total_counts > 0:
                max_solution_type = max(solution_counts, key=solution_counts.get)
                max_count = solution_counts[max_solution_type]

            if include_data:
                metric_data = {
                    'max_solution_type': max_solution_type,
                    'max_count': max_count,
                    'ticket_count': solution_counts['ticket_count'],
                    'auto_fix_count': solution_counts['auto_fix'],
                    'kb_count': solution_counts['using_kb']
                }

            if include_insights:
                solution_type_names = {
                    'ticket_count': 'manual tickets', 'auto_fix': 'auto-fixes',
                    'using_kb': 'knowledge base solutions', 'none': 'no solutions'
                }
                date_range_text = f"from {data['start_date'].date()} to {data['end_date'].date()}"
                if total_counts == 0:
                    priority = "low"
                    insight_text = f"No solution runs (tickets, auto-fixes, or KB usage) detected {date_range_text}."
                    action = "Verify if monitoring systems are correctly logging solution runs."
                else:
                    priority = (
                        "high" if (max_solution_type == 'ticket_count' and
                                solution_counts['ticket_count'] > solution_counts['auto_fix'] + solution_counts['using_kb']) else
                        "medium" if solution_counts['ticket_count'] > PRIORITY_THRESHOLDS["solution_run"]["medium"]["ticket_count"] else
                        "low"
                    )
                    insight_text = (f"Most common solution type {date_range_text} was {solution_type_names[max_solution_type]} "
                                    f"with {max_count} occurrences. "
                                    f"{'High ticket volume may indicate systemic issues.' if max_solution_type == 'ticket_count' else ''}")
                    action = ("Review ticket details for systemic issues." if max_solution_type == 'ticket_count'
                            else "Continue optimizing auto-fix and KB usage.")

                insights.append({
                    "title": "Dominant Solution Type",
                    "text": insight_text,
                    "priority": priority,
                    "action": action,
                    "details": {
                        "max_solution_type": solution_type_names[max_solution_type],
                        "max_count": max_count,
                        "ticket_count": solution_counts['ticket_count'],
                        "auto_fix_count": solution_counts['auto_fix'],
                        "kb_count": solution_counts['using_kb']
                    }
                })

        except Customer.DoesNotExist:
            logger.warning(f"No Customer found for user {request.user.id}")
            if include_data:
                metric_data = {
                    'error': "Customer data not available",
                    'max_solution_type': 'none',
                    'max_count': 0,
                    'ticket_count': 0,
                    'auto_fix_count': 0,
                    'kb_count': 0
                }
            if include_insights:
                insights.append({
                    "title": "Dominant Solution Type",
                    "text": "Unable to retrieve solution run data due to missing customer information.",
                    "priority": "high",
                    "action": "Verify user account configuration.",
                    "details": {"error": "Customer data not available"}
                })

        return metric_data, insights

    def get(self, request):
        """Handle GET request to fetch system insights and metrics."""
        response = {}
        insights = {}
        types_requested = request.query_params.getlist("type")
        all_data_requested = not types_requested
        include_insights = all_data_requested or "insights" in types_requested
        only_insights_requested = types_requested == ["insights"]

        # Parse start_date and end_date from query parameters
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        try:
            # Default to last 90 days if dates are not provided
            today = timezone.now()
            if not start_date_str and not end_date_str:
                end_date = today
                start_date = datetime(today.year, today.month, 1, 0, 0, 0) 
            else:
                try:
                    start_date = make_aware(datetime.strptime(start_date_str, "%Y-%m-%d"))
                    end_date = make_aware(datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
                    if start_date > end_date:
                        return Response({"error": "start_date cannot be later than end_date"}, status=400)
                except ValueError:
                    return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

            if start_date_str and end_date_str:
                try:
                    start_date = make_aware(datetime.strptime(start_date_str, "%Y-%m-%d"))
                    end_date = make_aware(datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
                    if start_date > end_date:
                        return Response({"error": "start_date cannot be later than end_date"}, status=400)
                except ValueError:
                    return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

            # Initialize shared data with date range
            data = self._initialize_data(request, start_date, end_date)

            # Define metrics to compute
            if only_insights_requested:
                metrics_to_compute = [
                    "compliance_metrics", "host_with_most_raised_tickets", "consistently_sad_hosts",
                    "latency_down_hosts", "hosts_with_high_ram_usage", "performance_metrics",
                    "self_heal_summary_today", "top_5_issues_resolved", "solution_run"
                ]
            else:
                metrics_to_compute = types_requested if not all_data_requested else [
                    "compliance_metrics", "host_with_most_raised_tickets", "consistently_sad_hosts",
                    "latency_down_hosts", "hosts_with_high_ram_usage", "performance_metrics",
                    "self_heal_summary_today", "top_5_issues_resolved", "solution_run"
                ]

            # Map metric names to their computation functions
            metric_functions = {
                "compliance_metrics": self._compute_compliance_metrics,
                "host_with_most_raised_tickets": self._compute_host_with_most_raised_tickets,
                "consistently_sad_hosts": self._compute_consistently_sad_hosts,
                "latency_down_hosts": self._compute_latency_down_hosts,
                "hosts_with_high_ram_usage": self._compute_hosts_with_high_ram_usage,
                "performance_metrics": self._compute_performance_metrics,
                "self_heal_summary_today": self._compute_self_heal_summary_today,
                "top_5_issues_resolved": self._compute_top_5_issues_resolved,
                # "solution_run": self._compute_solution_run
            }

            # Compute requested metrics
            for metric in metrics_to_compute:
                if metric not in metric_functions:
                    continue
                include_data = all_data_requested or metric in types_requested
                func = metric_functions[metric]
                args = [data, include_insights, include_data]
                if metric == "solution_run":
                    args.insert(0, request)
                metric_data, metric_insights = func(*args)
                if include_data and metric_data is not None:
                    response[metric] = metric_data
                if include_insights and metric_insights:
                    insights[metric] = metric_insights

            # Handle response formatting
            if only_insights_requested:
                response = {"insights": insights if insights else {"message": "No insights available"}}
            elif include_insights:
                response["insights"] = insights if insights else {"message": "No insights available"}

        except Exception as e:
            logger.warning(f"DashboardSystemInsights error: {e}")
            response = {"message": "Unable to fetch system insights", "insights": {}, "result": []}

        return Response(response, status=200)

class HostDataSearchAPIView(APIView):
    """
    API to search for a hostname in specific tables and return the table names where data exists.
    """
    def post(self, request, *args, **kwargs):
        hostname = request.data.get('hostname', None)
        print(f"hostname", hostname)
        if not hostname:
            return Response({"error": "Hostname is required."}, status=status.HTTP_400_BAD_REQUEST)

        data_array = []
        table_entries = {}

        # Check in Host table
        hosts = Host.objects.filter(hostname__icontains=hostname)
        for host in hosts:
            if "Host" not in table_entries:
                table_entries["Host"] = {
                    "table_name": "Host",
                    "host_name": host.hostname,
                    "host_id": host.id
                }

        # Check in SelfHealEntry table
        self_heal_entries = SelfHealEntry.objects.filter(host__hostname__icontains=hostname)
        for self_heal_entry in self_heal_entries:
            if "SelfHealEntry" not in table_entries:
                table_entries["SelfHealEntry"] = {
                    "table_name": "Self Heal",
                    "host_name": self_heal_entry.host.hostname,
                    "host_id": self_heal_entry.host.id
                }

        # Check in Ticket table
        tickets = Ticket.objects.filter(host__hostname__icontains=hostname)
        for ticket in tickets:
            if "Ticket" not in table_entries:
                table_entries["Ticket"] = {
                    "table_name": "Tickets",
                    "host_name": ticket.host.hostname,
                    "host_id": ticket.host.id
                }

        # Check in Solution table
        solutions = ComplainceEntry.objects.filter(customer__customer_host__hostname__icontains=hostname)
        for solution in solutions:
            if "Solution" not in table_entries:
                table_entries["Solution"] = {
                    "table_name": "Compliance",
                    "host_name": hostname,
                    "host_id": solution.host.id  # Solution does not directly reference Host
                }

        # Check in Sentiment table
        sentiments = Sentiment.objects.filter(host__hostname__icontains=hostname)
        for sentiment in sentiments:
            if "Sentiment" not in table_entries:
                table_entries["Sentiment"] = {
                    "table_name": "Sentiment",
                    "host_name": sentiment.host.hostname,
                    "host_id": sentiment.host.id
                }

        # Check in SolutionRun table
        solution_runs = SolutionRun.objects.filter(host__hostname__icontains=hostname)
        for solution_run in solution_runs:
            if "SolutionRun" not in table_entries:
                table_entries["SolutionRun"] = {
                    "table_name": "Solution Run",
                    "host_name": solution_run.host.hostname,
                    "host_id": solution_run.host.id
                }

        # Check in Feedback table
        feedbacks = Feedback.objects.filter(host__hostname__icontains=hostname)
        for feedback in feedbacks:
            if "Feedback" not in table_entries:
                table_entries["Feedback"] = {
                    "table_name": "Feedback",
                    "host_name": feedback.host.hostname,
                    "host_id": feedback.host.id
                }

        # Collect unique entries
        data_array = list(table_entries.values())

        return Response({"data_array": data_array}, status=status.HTTP_200_OK)
    
class GetLatestRelease(APIView):
    permission_classes = [BotAPIPermissionClass]
    def get(self, request):
        try:
            customer=Customer.objects.get(user=request.user)
            latest_release=Release.objects.filter(customer=customer,is_latest=True)
            print("\nlatest_release",latest_release.values_list(),"\n")
            if not latest_release:
                return Response({"error": "No release found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = ReleaseSerializer(latest_release,many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print("error",e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self,request):
        try:
            customer=Customer.objects.get(user=request.user)
            latest_release=Release.objects.filter(customer=customer,is_latest=True)
            print("\nlatest_release",latest_release.values_list(),"\n")
            if not latest_release:
                return Response({"error": "No release found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = ReleaseSerializer(latest_release,many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print("error",e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)