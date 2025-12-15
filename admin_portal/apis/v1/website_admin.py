from rest_framework.views import APIView
from rest_framework.views import status
from rest_framework.response import Response
from website.apis.v1.serializers import *
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Value, Sum, F
from base.mixins import PaginationHandlerMixin, CustomPagination
import logging
from admin_portal.models import Solution as CustomerSolution
from website.models import Solutions as website_solution
from admin_portal.apis.v1.serializers import PortalSolutionGetSerializer

logger = logging.getLogger(__name__)

class SolutionsOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_website_serializer_class = SolutionGetSerializer
    get_portal_serializer_class = PortalSolutionGetSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomerSolution.objects.all()

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        status_code = status.HTTP_200_OK
        response = {}
        serializer = None
        try:
            if request.user.user_type == 'customer':
                customer = request.user.customer_obj
                self.queryset = CustomerSolution.objects.filter(customer=customer)
                serializer = self.get_portal_serializer_class
            else:
                self.queryset = website_solution.objects.filter(status=True)
                serializer = self.get_website_serializer_class
            if search:
                queryset = self.queryset.filter(
                    solution_name__icontains=search
                )
            elif id:
                queryset = self.queryset.filter(id=id)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            serializer = serializer(page, many=True)
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


class CaseStudiesOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    get_serializer_class = CaseStudyGetSerializer
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    get_submission_serializer_class = CareerApplicationGetSerializer
    permission_classes = [IsAuthenticated]
    queryset = Career.objects.filter(status=True)

    def get(self, request):
        search = request.GET.get("search")
        id = request.GET.get("id")
        application_carrer = request.GET.get("carrer")
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
            elif application_carrer:
                try:
                    carrer_obj = Career.objects.get(id=application_carrer)
                    queryset = CarrerSubmission.objects.filter(carrer=carrer_obj)
                except Career.DoesNotExist:
                    logger.warning(f"Can not able to fetch data for website carrers submission due to {e}")
                    response = {
                        "status" : True,
                        "message" : 'No data available',
                        "count" : 0,
                        "next" : None,
                        "previous" : None,
                        "result" : []
                    }
                    return Response(response, status=status_code)
            else:
                queryset = self.queryset.all()
            page = self.paginate_queryset(queryset)
            if application_carrer:
                serializer = self.get_submission_serializer_class(page, many=True)
            else:
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


class ContactUsOperations(APIView, PaginationHandlerMixin):
    pagination_class = CustomPagination
    post_serializer_class = ContactUsPostSerializer
    permission_classes = [IsAuthenticated]
    queryset = ContactUs.objects.all()

    def create_contact_us_entry(self, **kwrags):
        obj = None
        try:
            obj = ContactUs.objects.create(**kwrags)
        except Exception as e:
            logger.warning(f"Can not create entry to contact us model due to: {e}")
        return obj
    
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
                if contact_us_obj:
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
