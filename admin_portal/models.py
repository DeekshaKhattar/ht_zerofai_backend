from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from base.models import TimeStampedModel, validate_mobile

from django.contrib.auth import get_user_model
User = get_user_model()

USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('super_admin','Super Admin'),
)

SOLUTION_TYPE_CHOICES = (
    ('exe', 'Exe'),
    ('command', 'Command'),
    ('both', 'Both'),
)

SOLUTION_RUN_TYPE_CHOCIES = (
    ('autofix', 'Auto Fix'),
    ('kb', 'Knowledge Base'),
    ('ticket', 'Ticket'),
    ('password_change', 'Password Change'),
)

SENTIMENT_STATUS_CHOICES = (
    ('happy', 'Happy'),
    ('sad', 'Sad'),
)

FEEDBACK_CHOCIES = (
    ('one', 1),
    ('two', 2),
    ('three', 3),
    ('four', 4),
    ('five', 5),
)

ANNOUNCEMENT_FORM_CHOICES = (
    ('boolean_form', 'Acknowledgement Form'),
    ('text_form', 'Feedback Form'),
)

ANNOUNCEMENT_STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('expired', 'Expired'),
)

COMPLAINCE_CONF_TYPE_CHOICES = (
    ('cmd', 'Cmd'),
    ('powershell', 'Powershell'),
    ('python', 'Python'),
)

COMPLAINCE_TYPE_CHOICES = (
    ('exe', 'Exe'),
    ('command', 'Command'),
    ('both','Both')
)

class Customer(TimeStampedModel):
    user = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE, related_name='customer_user', null=True, blank=True, help_text='Select customer admin')
    company_name = models.CharField(verbose_name='Company Name', null=False, blank=False, help_text='Enter Company Name')
    company_address = models.TextField(verbose_name='Company Address', help_text='Enter Complete Company Address')
    company_phone = models.CharField(max_length=10, validators=[validate_mobile], unique=True, help_text='Enter Mobile Number')
    domain = models.CharField(verbose_name='Domain', null=True, blank=True, max_length=255)
    client_secret = models.CharField(verbose_name='Client Secret', null=True, blank=True, max_length=255)
    python_setup_file = models.FileField(verbose_name='Python Setup EXE', upload_to='conf/', null=True, blank=True)
    service_file = models.FileField(verbose_name='Service File', upload_to='conf/', null=True, blank=True)
    system_health_file = models.FileField(verbose_name='System Health File', upload_to='conf/', null=True, blank=True)
    complaince_check_file = models.FileField(verbose_name='Complaince Health File', upload_to='conf/', null=True, blank=True)
    ram = models.FloatField(verbose_name='RAM Usage Threshold', null=True, blank=True)
    cpu = models.FloatField(verbose_name='CPU Usage Threshold', null=True, blank=True)
    hardisk = models.FloatField(verbose_name='Hardisk Usage Threshold', null=True, blank=True)
    page_memory = models.FloatField(verbose_name='Page Memory Threshold', null=True, blank=True)
    critical_services = models.FloatField(verbose_name='Critical Services Threshold', null=True, blank=True)
    latency = models.FloatField(verbose_name='Latency Threshold', null=True, blank=True)
    uptime = models.FloatField(verbose_name='Up Time Threshold', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.company_name:
            self.company_name = self.company_name.title()
        super(Customer, self).save(*args, **kwargs)

    def __str__(self):
        return self.company_name
    
    class Meta:
        verbose_name_plural= "Customers"
        ordering = ['-updated_at']


class Host(TimeStampedModel):
    customer = models.ForeignKey('Customer', verbose_name='Customer', on_delete=models.CASCADE, related_name='customer_host', null=True, blank=True, help_text='Select customer admin')
    hostname = models.CharField(verbose_name='Host Name', null=True, blank=True, max_length=100,unique=True)
    mac_address = models.CharField(verbose_name='Mac Address', null=True, blank=True, max_length=100)
    version = models.CharField(verbose_name='App Version', null=True, blank=True, max_length=100)

    def __str__(self):
        return f"{self.customer} - {self.hostname}"

    class Meta:
        verbose_name_plural= "Host Machines"
        ordering = ['-updated_at']


class PurchasedLicense(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='customer_purchased_license')
    license_count = models.PositiveIntegerField(verbose_name='Total Purchased License', default=0)
    start_date = models.DateField(verbose_name='License Start Date')
    end_date = models.DateField(verbose_name='License End Date')

    def __str__(self):
        return f"{self.customer.company_name}"

    class Meta:
        verbose_name_plural= "Purchased Licenses"
        ordering = ['-created_at']


class License(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='customer_license')
    start_date = models.DateField(verbose_name='License Start Date')
    end_date = models.DateField(verbose_name='License End Date')
    total_license = models.PositiveIntegerField(verbose_name='Total License Count', default=0)
    used_license = models.PositiveIntegerField(verbose_name='Total Used License Count', default=0)
    avialable_license = models.PositiveIntegerField(verbose_name='Total Avaibale License Count', default=0)
    app_version = models.CharField(verbose_name='Current App Version', null=True, blank=True, max_length=100)
    status = models.BooleanField(verbose_name='Status', default=False)

    def __str__(self):
        return f"{self.customer.company_name}"
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            original_instance = License.objects.get(pk=self.pk)
            if self.used_license != original_instance.used_license:
                self.avialable_license = self.total_license - self.used_license
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural= "Licenses"
        ordering = ['-created_at']


class Solution(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='customer_solution')
    name = models.CharField(verbose_name='Solution Name', max_length=100)
    description = models.TextField(verbose_name='Description', null=True, blank=True)
    type = models.CharField(verbose_name='Solution Type', max_length=100, choices=SOLUTION_TYPE_CHOICES)
    command = models.TextField(verbose_name='Solution Command', null=True, blank=True)
    exe_file = models.FileField(verbose_name='Solution EXE', null=True, blank=True, upload_to='solutions/exe/')
    command_type = models.CharField(null=True,blank=True,choices=COMPLAINCE_CONF_TYPE_CHOICES)

    def __str__(self):
        return f"{self.customer.company_name} - {self.name}"

    class Meta:
        verbose_name_plural= "Solutions"
        ordering = ['-created_at']


class Ticket(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='ticket_customer')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='ticket_host')
    ticket_id = models.CharField(verbose_name='Ticket ID', null=True, blank=True, max_length=100)
    subject = models.TextField(verbose_name='Subject', null=True, blank=True)
    description = models.TextField(verbose_name='Description', null=True, blank=True)

    def __str__(self):
        return f"{self.customer.company_name} - {self.host.hostname}"

    class Meta:
        verbose_name_plural= "Tickets"
        ordering = ['-created_at']


class SolutionRun(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='solution_customer')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='solution_host')
    solution = models.ForeignKey(Solution, verbose_name='Solution', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='solution_solution')
    type = models.CharField(verbose_name='Resolution Type', max_length=100, choices=SOLUTION_RUN_TYPE_CHOCIES)

    def __str__(self):
        return f"{self.customer.company_name} - {self.host.hostname}"

    class Meta:
        verbose_name_plural= "Solution Run"
        ordering = ['-created_at']


class ApplicationSettings(TimeStampedModel):
    version = models.CharField(verbose_name='Application Version')
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='application_customer')

    def __str__(self):
        return self.customer

    class Meta:
        verbose_name_plural = 'Application Settings'
        ordering = ['-id']


class HostAnnouncementAnswer(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='host_announcement_customer')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='host_announcement_host')
    announcement = models.ForeignKey('AnnouncementBoradcasting', verbose_name='Announcement', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='host_announcement_answer')
    boolean_answer = models.BooleanField(verbose_name='Boolean Answer', null=True, blank=True)
    text_answer = models.TextField(verbose_name='Text Answer', null=True, blank=True)
    status = models.BooleanField(verbose_name='Read By User', null=True, blank=True)

    def __str__(self):
        return f"{self.announcement} - {self.host}"

    class Meta:
        verbose_name_plural= "Announcement Form Host Answer"
        ordering = ['-created_at']


class AnnouncementBoradcasting(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='announcement_customer')
    feed = models.TextField(verbose_name='Announcement Feed', null=True, blank=True)
    is_form_active = models.BooleanField(verbose_name='Is Form Active?', default=False)
    form_type = models.CharField(verbose_name='Form Type', null=True, blank=True, choices=ANNOUNCEMENT_FORM_CHOICES)
    question = models.CharField(verbose_name='Question', null=True, blank=True)
    status = models.CharField(verbose_name='Is Active', default='draft', choices=ANNOUNCEMENT_STATUS_CHOICES)
    expiry_date = models.DateTimeField(verbose_name='Expiry Date Time', null=True, blank=True)

    def __str__(self):
        return f"{self.customer} - {self.id}"
        
    class Meta:
        verbose_name_plural= "Announcement Boradcasting"
        ordering = ['-updated_at']


class Sentiment(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='sentiment_customer')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='sentiment_host')
    ram = models.FloatField(verbose_name='RAM Usage', null=True, blank=True)
    cpu = models.FloatField(verbose_name='CPU Usage', null=True, blank=True)
    hardisk = models.FloatField(verbose_name='Hardisk Usage', null=True, blank=True)
    page_memory = models.FloatField(verbose_name='Page Memory', null=True, blank=True)
    critical_services = models.FloatField(verbose_name='Critical Services', null=True, blank=True)
    latency = models.FloatField(verbose_name='Latency', null=True, blank=True)
    uptime = models.FloatField(verbose_name='Up Time', null=True, blank=True)
    status = models.CharField(verbose_name='Status', max_length=10, null=True, blank=True, choices=SENTIMENT_STATUS_CHOICES)
    critical_services_details=models.JSONField(verbose_name='Critical Services Details',null=True,blank=True)


    def __str__(self):
        return self.customer.company_name
    
    class Meta:
        verbose_name_plural = 'Machine Sentiments'
        ordering = ['-updated_at']
        indexes = [
        models.Index(fields=['status', 'created_at', 'host']),
        models.Index(fields=['host', 'created_at', 'status']),
        models.Index(fields=['created_at', 'status']),
        ]


class Feedback(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='feedback_customer')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='feedback_host')
    solution = models.ForeignKey(Solution, verbose_name='Solution', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='feedback_solution')
    feedback = models.CharField(verbose_name='Star Rating', null=True, blank=True, choices=FEEDBACK_CHOCIES)
    solution_type = models.CharField(verbose_name='Solution Type', null=True, blank=True, choices=SOLUTION_RUN_TYPE_CHOCIES)

    def __str__(self):
        customer_name = self.customer.company_name if self.customer else "No Customer"
        host_name = self.host.hostname if self.host else "No Host"
        solution_name = self.solution.name if self.solution else "No Solution"
        return f"{customer_name} - {host_name} - {solution_name}"

    class Meta:
        verbose_name_plural = 'Feedbacks'
        ordering = ['-created_at']


class ComplainceConfiguration(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='complaince_customer')
    parameter_name = models.CharField(verbose_name='Parameter Name', max_length=255, null=True, blank=True)
    type = models.CharField(verbose_name='Command Type', max_length=100, choices=COMPLAINCE_CONF_TYPE_CHOICES, null=True, blank=True)
    command = models.TextField(verbose_name='Command', null=True, blank=True)
    status = models.BooleanField(verbose_name='Parameter Status', default=True)

    def __str__(self):
        return self.parameter_name
    
    class Meta:
        verbose_name_plural = 'Compalaince Hardening Parameters'
        ordering = ['-updated_at']


class ComplainceEntry(TimeStampedModel):
    customer = models.ForeignKey(
        Customer, verbose_name='Customer', on_delete=models.DO_NOTHING,
        null=True, blank=True, related_name='complaince_entry'
    )
    host = models.ForeignKey(
        Host, verbose_name='Hostname', on_delete=models.DO_NOTHING,
        null=True, blank=True, related_name='complaince_entry_host'
    )
    data = models.JSONField(verbose_name='Paramter Data', null=True, blank=True)
    status = models.BooleanField(verbose_name='Compliance Status', default=False)

    def __str__(self):
        return f"{self.host} - {self.updated_at}"
    class Meta:
        verbose_name_plural = 'Compalaince Hardening Entry'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['updated_at']),
            models.Index(fields=['status']),
            models.Index(fields=['host']),
            models.Index(fields=['customer']),
        ]

class SelfHealConfiguration(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='selfheal_customer')
    parameter_name = models.CharField(verbose_name='Parameter Name', max_length=255, null=True, blank=True)
    type = models.CharField(verbose_name='Command Type', max_length=100, choices=COMPLAINCE_CONF_TYPE_CHOICES, null=True, blank=True)
    command = models.TextField(verbose_name='Command', null=True, blank=True)
    threshold=models.FloatField(verbose_name='Threshold Value', null=True, blank=True)
    status = models.BooleanField(verbose_name='Parameter Status', default=True)

    def __str__(self):
        return self.parameter_name
    
    class Meta:
        verbose_name_plural = 'Self Heal Parameters'
        ordering = ['-updated_at']


class SelfHealEntry(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='selfheal_entry')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='selfheal_entry_host')
    data = models.JSONField(verbose_name='Paramter Data', null=True, blank=True)
    status = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.host} - {self.created_at}"
    
    class Meta:
        verbose_name_plural = 'Self Heal Entry'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['host', 'created_at']),         # speeds up latest per host queries
            models.Index(fields=['created_at', 'host']),         # speeds up date range + host filters
            models.Index(fields=['status']),                     # if you filter by status often
            models.Index(fields=['host', 'status']),             # for host+status filtering
            models.Index(fields=['created_at', 'status']),      # For daily summary
            models.Index(fields=['host', 'status', 'created_at']),  # For top issues resolved
        ]

class ApplicationConfiguration(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='customer_configuration')
    ad_server = models.CharField(verbose_name='AD Server', max_length=100, null=True, blank=True)
    ad_username = models.CharField(verbose_name='AD Username', max_length=100, null=True, blank=True)
    ad_password = models.CharField(verbose_name='AD Password', max_length=100, null=True, blank=True)
    itsm_api_url = models.CharField(verbose_name='ITSM API URL', max_length=255, null=True, blank=True)
    itsm_api_key = models.CharField(verbose_name='ITSM API Key', max_length=255, null=True, blank=True)
    itsm_api_token = models.CharField(verbose_name='ITSM API Token', max_length=255, null=True, blank=True)
    rasa_url = models.CharField(verbose_name='Rasa URL', max_length=255, null=True, blank=True)
    api_url = models.CharField(verbose_name='API URL', max_length=255, null=True, blank=True)
    meta_data = models.JSONField(verbose_name='Meta Data', null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.customer}"
    
    class Meta:
        verbose_name_plural = 'Application Configuration'
        ordering = ['-updated_at']


class AgentVerification(TimeStampedModel):
    hostname = models.CharField(verbose_name='Hostname', null=True, blank=True)
    data = models.JSONField(verbose_name='Json Data', null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.hostname}"
    
    class Meta:
        verbose_name_plural = 'Agent Verification'
        ordering = ['-created_at']

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    timestamp = models.IntegerField()  # Timestamp when OTP was generated
    expiry_time = models.IntegerField(default=300)  # Expiry time in seconds

class complainceHardeningAutoFix(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='customer_compliance')
    name = models.CharField(verbose_name='Compliance Name', max_length=100)
    type = models.CharField(verbose_name='Compliance Type', max_length=100, choices=COMPLAINCE_TYPE_CHOICES)
    command = models.TextField(verbose_name='Compliance Command', null=True, blank=True)
    exe_file = models.FileField(verbose_name='Compliance EXE', null=True, blank=True, upload_to='solutions/exe/')
    complaince = models.ForeignKey(ComplainceConfiguration,verbose_name='Compliance',on_delete=models.CASCADE,null=True,blank=True,related_name='compliance')

    class Meta:
        verbose_name_plural = 'Compalaince AutoFix'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name+" "+self.type 

class ComplianceAutoFixEntry(TimeStampedModel):
    customer = models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='complaince_autofix_entry')
    host = models.ForeignKey(Host, verbose_name='Hostname', on_delete=models.CASCADE, null=True, blank=True, related_name='complaince_autofix_entry_host')
    data = models.JSONField(verbose_name='Paramter Data', null=True, blank=True)

    def __str__(self):
        return f"{self.host} - {self.created_at}"
    
    class Meta:
        verbose_name_plural = 'Compalaince AutoFix Entry'
        ordering = ['-updated_at']

class Release(TimeStampedModel):
    customer=models.ForeignKey(Customer, verbose_name='Customer', on_delete=models.CASCADE, null=True, blank=True)
    version = models.CharField(max_length=50, unique=True)
    file = models.FileField(upload_to='releases/')
    file_name = models.CharField(max_length=255)
    is_latest = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if self.is_latest:
            # Ensure only one release is marked as latest
            Release.objects.filter(is_latest=True).update(is_latest=False)
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.version} ({'Latest' if self.is_latest else 'Not Latest'})"