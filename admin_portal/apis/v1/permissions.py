from rest_framework import permissions
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from admin_portal.models import *
from django.utils import timezone
import base64, logging
from itertools import cycle

logger = logging.getLogger(__name__)


class BotAPIPermissionClass(permissions.BasePermission):
    """
    Custom permission class for authentication.
    """
    def decrypt_key(self, data, key):
        key_cycle = cycle(key)
        decrypted = ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(data, key_cycle))
        return decrypted
    
    def has_permission(self, request, view):
        # authentication logic goes here
        current_date = timezone.now().date()
        api_key = request.headers.get('Authorization')
        if api_key:
            if not 'Bearer' in  api_key:
                encrypted_data = base64.b64decode(api_key).decode('utf-8')
                logger.warning(f"Encrypted key is: {encrypted_data}")
                dec_key = self.decrypt_key(encrypted_data, settings.API_KEY)
                logger.warning(f"Decrypted key is: {dec_key}")
                customer = Customer.objects.get(client_secret=dec_key)
                if customer:
                    customer_license = License.objects.get(customer=customer)
                    if current_date > customer_license.end_date:
                        # License has expired
                        logger.warning("License has expired.")
                        raise PermissionDenied("License has expired.")
                    else:
                        request.user = customer.user
                        return True
                else:
                    logger.warning("Customer not found.")
                    raise PermissionDenied("You are not authorized.")
            else:
                return True
        elif request.user.is_authenticated:
            return True
        else:
            logger.warning("Customer not found line 49.")
            raise PermissionDenied("You are not authorized.")