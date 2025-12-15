from django.urls import path
from base.apis.v1.views import *
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('api/v1/login/', LoginOperation.as_view(), name='user_login'),
    path('api/v1/user/', UsersOperation.as_view(), name='user_get'),
    path('api/v1/change/password/', ChangePasswordOperation.as_view(), name='user_change_password'),
    path('api/v1/reset/password/', ForgetPasswordOperation.as_view(), name='user_forget_password'),
    path('api/v1/logout/', LogoutOperation.as_view(), name='user_logout'),
    # Token refresh
    path('api/v1/token/',jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]