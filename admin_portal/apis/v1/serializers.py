from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.validators import UniqueValidator
from admin_portal.models import *
from django.conf import settings
import logging
from django.utils import timezone
import ast

logger = logging.getLogger(__name__)

class CustomerGetSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerPostSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.IntegerField(required=True)
    company_name = serializers.CharField(required=True)
    company_phone = serializers.IntegerField(required=True)
    company_domain = serializers.CharField(required=True)
    company_address = serializers.CharField(required=True)
    license_start_date = serializers.DateField(format='%d-%m-%Y', required=True)
    license_end_date = serializers.DateField(format='%d-%m-%Y', required=True)
    license_count = serializers.IntegerField(required=True)


class HostGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    
    class Meta:
        model = Host
        fields = '__all__'


class HostPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    mac_address = serializers.CharField(required=True)
    version = serializers.CharField(required=True)


class PurchasedLicenseGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    
    class Meta:
        model = PurchasedLicense
        fields = '__all__'


class LicenseGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    
    class Meta:
        model = License
        fields = '__all__'


class PortalSolutionGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    solution_name = serializers.CharField(source='name')
    
    class Meta:
        model = Solution
        fields = '__all__'


class TicketGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    host = serializers.CharField(source='host.hostname')
    
    class Meta:
        model = Ticket
        fields = '__all__'


class TicketPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    ticket_id = serializers.CharField(required=True)
    subject = serializers.CharField(required=True)
    description = serializers.CharField(required=True)


class SolutionRunGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    type = serializers.CharField(source='get_type_display')
    solution = serializers.SerializerMethodField()
    host = serializers.CharField(source='host.hostname')

    def get_solution(self, obj):
        if obj.solution:
            return obj.solution.name
        else:
            if obj.type == 'password_change':
                return 'Password Change'
            if obj.type == 'ticket':
                return 'New Ticket'
        return 'N/A'
    
    class Meta:
        model = SolutionRun
        fields = '__all__'



class SolutionRunPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    solution = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    solution_run_id= serializers.CharField(required=False,allow_null=True,allow_blank=True)
    type = serializers.CharField(required=True)
    # command_type=serializers.CharField()

class HostStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    hostname = serializers.CharField()
    status = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

class ApplicationSettingsGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    
    class Meta:
        model = ApplicationSettings
        fields = '__all__'


class HostAnnouncementAnswerGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    
    class Meta:
        model = HostAnnouncementAnswer
        fields = '__all__'


class AnnouncementBoradcastingGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    
    class Meta:
        model = AnnouncementBoradcasting
        fields = '__all__'


class SentimentGetSeializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    host = serializers.CharField(source='host.hostname')
    red_cells = serializers.SerializerMethodField()
    
    def get_red_cells(obj, self):
        red_cells = []
        if self.status == 'sad':
            fields = ['ram', 'cpu', 'hardisk', 'page_memory', 'critical_services', 'latency', 'uptime']
            for field in fields:
                if getattr(self, field) > getattr(self.customer, field):
                    red_cells.append(field)
        return red_cells

    class Meta:
        model = Sentiment
        fields = '__all__'
        read_only_fields = ('red_cells',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Format float fields to display only two decimal places
        for field in ['ram', 'cpu', 'hardisk', 'page_memory', 'critical_services', 'latency', 'uptime']:
            if representation.get(field) is not None:
                representation[field] = round(representation[field], 2)
        return representation
    

class SentimentMainSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    last_update = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        host_all_sentiment_entry = Sentiment.objects.filter(host=obj)
        if host_all_sentiment_entry:
            return host_all_sentiment_entry.first().status
        else:
            return None

    def get_last_update(self, obj):
        # Get the latest Sentiment entry's created_at for the host
        latest_entry = Sentiment.objects.filter(host=obj).order_by('-created_at').first()
        return latest_entry.created_at if latest_entry else None
    
    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'status',)


class ComplainceMainSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    last_update = serializers.SerializerMethodField()
    status = serializers.BooleanField(source='latest_status')

    def get_last_update(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = ComplainceEntry.objects.filter(host=obj)
        if start_date and end_date:
            queryset = queryset.filter(updated_at__range=[start_date, end_date])
        latest_entry = queryset.order_by('-updated_at').first()
        if latest_entry:
            return latest_entry.updated_at  # Use updated_at of the latest entry in range
        return None  # No entry exists within the date range
        
    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'status',)

class ComplianceAutoFixEntryGetSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    host_name = serializers.CharField(source='host.name', read_only=True)

    class Meta:
        model = ComplianceAutoFixEntry
        fields = ['id', 'customer_name', 'host_name', 'data', 'created_at', 'updated_at']

class SelfHealListSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    last_update = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_last_update(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = SelfHealEntry.objects.filter(host=obj)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        latest_entry = queryset.order_by('-created_at').first()
        return latest_entry.created_at if latest_entry else None

    def get_status(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = SelfHealEntry.objects.filter(host=obj)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        latest_entry = queryset.order_by('-created_at').first()
        return latest_entry.status if latest_entry else False

    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'status')


class SelfHealMainSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    last_update = serializers.SerializerMethodField()
    self_heal_data = serializers.SerializerMethodField() 
    # status = serializers.SerializerMethodField()

    def get_status(self, obj):
            latest_entry = SelfHealEntry.objects.filter(host=obj).order_by('-created_at').first()
            return latest_entry.status if latest_entry else None

    def get_last_update(self, obj):
        host_all_self_heal_entry = SelfHealEntry.objects.filter(host=obj)
        logger.debug(f"host_all_self_heal_entry: {host_all_self_heal_entry}")
        if host_all_self_heal_entry:
            return host_all_self_heal_entry.first().created_at
        return None
    
    def get_self_heal_data(self, obj):
        # Fetch the latest SelfHealEntry for the host
        latest_entry = SelfHealEntry.objects.filter(host=obj).order_by('-created_at').first()
        logger.debug(f"latest_entry: {latest_entry}")
        if latest_entry:
            return latest_entry.data  # Return the JSON data
        return None
    
    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'self_heal_data', 'status')

class SentimentPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    ram = serializers.CharField(required=True) 
    cpu = serializers.CharField(required=True) 
    hardisk = serializers.CharField(required=True) 
    page_memory = serializers.CharField(required=True) 
    critical_services = serializers.CharField(required=True) 
    latency = serializers.CharField(required=True) 
    uptime = serializers.CharField(required=True)
    critical_services_details = serializers.JSONField(required=False)


class ComplainceEntryGetSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    host = serializers.CharField(source='host.hostname')
    status = serializers.SerializerMethodField()
    complaint = serializers.SerializerMethodField()
    non_complaint = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    run_time = serializers.SerializerMethodField()

    def get_status(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = ComplainceEntry.objects.filter(host=obj.host)

        if start_date and end_date:
            queryset = queryset.filter(updated_at__range=[start_date, end_date])

        latest_entry = queryset.order_by('-updated_at').first()
        if latest_entry:
            return bool(latest_entry.status)  # ✅ use the status field only
        return None


    def get_complaint(self, obj):
        """Count compliant values from data."""
        data = obj.data or {}
        return sum(1 for v in data.values() if str(v).strip().lower() == "true")

    def get_non_complaint(self, obj):
        """Count non-compliant values from data."""
        data = obj.data or {}
        return sum(1 for v in data.values() if str(v).strip().lower() != "true")

    def get_date(self, obj):
        return obj.updated_at.strftime('%d-%m-%Y') if obj.updated_at else None

    def get_run_time(self, obj):
        if obj.updated_at:
            local_time = timezone.localtime(obj.updated_at)
            return local_time.strftime('%I:%M:%S %p')
        return None
    class Meta:
        model = ComplainceEntry
        fields = '__all__'
        read_only_fields = ('status', 'complaint', 'non_complaint', 'date', 'run_time',)

from rest_framework import serializers
from ...models import SelfHealEntry

class SelfHealEntryGetSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    host_name = serializers.CharField(source='host.name', read_only=True)

    class Meta:
        model = SelfHealEntry
        fields = ['id', 'customer_name', 'host_name', 'data', 'created_at', 'updated_at']

class SelfHealListSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    last_update = serializers.DateTimeField(source='latest_update', read_only=True)
    status = serializers.BooleanField(source='latest_status', read_only=True)

    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'status')


class ComplainceEntryPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    complaince_data = serializers.JSONField(required=True)


class ComplainceConfigurationGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplainceConfiguration
        fields = '__all__'

class SelfHealConfigurationGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfHealConfiguration
        fields = '__all__'

class SelfHealEntryPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    selfheal_data = serializers.JSONField(required=True)

class FeedbackGetSeializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    solution_type = serializers.CharField(source='get_solution_type_display', allow_null=True)
    solution = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    
    class Meta:
        model = Feedback
        fields = '__all__'

    def get_customer(self, obj):
        return obj.customer.company_name if obj.customer else "No Customer"

    def get_solution(self, obj):
        return obj.solution.name if obj.solution else "No Solution"

    def get_host(self, obj):
        return obj.host.hostname if obj.host else "No Host"


class FeedbackPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    solution = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    feedback = serializers.CharField(required=True)
    type = serializers.CharField(required=True)


class AgentCheckPostSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    agent_data = serializers.JSONField(required=True)

class ComplainceAutoFixGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = complainceHardeningAutoFix
        fields = '__all__'

class ComplainceAutofixEntryPOSTSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=True)
    data = serializers.JSONField(required=True)

class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'


class SentimentMainSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name', allow_null=True)
    last_update = serializers.DateTimeField(source='latest_update', allow_null=True)
    status = serializers.CharField(source='latest_status', allow_null=True)

    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'status')

class FeedbackMainSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer.company_name')
    last_update = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()
    solution_type = serializers.SerializerMethodField()

    def get_last_update(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = Feedback.objects.filter(host=obj)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        latest_entry = queryset.order_by('-updated_at', '-created_at').first()
        return latest_entry.updated_at if latest_entry else None

    def get_feedback(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = Feedback.objects.filter(host=obj)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        latest_entry = queryset.order_by('-updated_at', '-created_at').first()
        return latest_entry.feedback if latest_entry else None

    def get_solution_type(self, obj):
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')
        queryset = Feedback.objects.filter(host=obj)
        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        latest_entry = queryset.order_by('-updated_at', '-created_at').first()
        return latest_entry.solution_type if latest_entry else None

    class Meta:
        model = Host
        fields = ('id', 'hostname', 'last_update', 'customer', 'feedback', 'solution_type')