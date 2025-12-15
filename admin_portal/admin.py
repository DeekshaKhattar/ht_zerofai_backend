from django.contrib import admin
from admin_portal.models import *
from django import forms

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'company_phone', 'domain', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__phone_number', 'company_name',  'company_phone', 'domain',)


class HostAdmin(admin.ModelAdmin):
    list_display = ('customer', 'hostname', 'mac_address', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name', 'hostname', 'mac_address',)


class PurchasedLicenseAdmin(admin.ModelAdmin):
    list_display = ('customer', 'license_count', 'start_date', 'end_date', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)


class LicenseAdmin(admin.ModelAdmin):
    list_display = ('customer', 'start_date', 'start_date', 'end_date', 'total_license', 'used_license', 'avialable_license', 'status', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)


class SolutionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'type', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)


class TicketAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'ticket_id', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name', 'host__hostname',)


class SolutionRunAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'solution', 'type', 'created_at', 'updated_at',)
    list_filter = ('type', 'customer', 'created_at')
    search_fields = ('customer__company_name', 'host__hostname', 'solution__name', 'created_at')


class HostAnnouncementAnswerAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'status', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name', 'host__hostname',)


class AnnouncementBoradcastingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'is_form_active', 'form_type', 'status', 'expiry_date', 'created_at', 'updated_at',)
    list_filter = ('form_type', 'status', 'is_form_active', 'customer',)
    search_fields = ('customer__company_name',)


class SentimentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'status', 'created_at', 'updated_at',)
    list_filter = ('status', 'customer', 'updated_at')
    search_fields = ('customer__company_name', 'host__hostname', 'status', 'updated_at')


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'solution', 'feedback', 'solution_type', 'created_at', 'updated_at',)
    list_filter = ('feedback', 'solution_type', 'customer',)
    search_fields = ('customer__company_name', 'host__hostname',)


class ComplainceConfigurationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'parameter_name', 'status', 'created_at', 'updated_at',)
    list_filter = ('status', 'customer',)
    search_fields = ('customer__company_name',)


class ComplainceEntryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)



class ApplicationConfigurationAdminForm(forms.ModelForm):
    ad_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        label='AD Password'
    )

    class Meta:
        model = ApplicationConfiguration
        fields = '__all__'

class ApplicationConfigurationAdmin(admin.ModelAdmin):
    form = ApplicationConfigurationAdminForm
    list_display = ('customer', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name', 'ad_server',)


class AgentVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'hostname', 'created_at', 'updated_at',)
    list_filter = ('hostname',)
    search_fields = ('hostname',)

class SelfHealEntryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)

class SelfHealConfigurationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'parameter_name', 'status', 'created_at', 'updated_at',)
    list_filter = ('status', 'customer',)
    search_fields = ('customer__company_name',)

class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'timestamp', 'expiry_time')
    search_fields = ('user__email', 'otp')

class complainceHardeningAutoFixAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'type', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)

class ComplianceAutoFixEntryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'host', 'created_at', 'updated_at',)
    list_filter = ('customer',)
    search_fields = ('customer__company_name',)

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ['version', 'file_name', 'is_latest', 'created_at','updated_at']
    list_filter = ['is_latest']
    search_fields = ['version', 'file_name']

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(PurchasedLicense, PurchasedLicenseAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(Solution, SolutionAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(SolutionRun, SolutionRunAdmin)
admin.site.register(ApplicationSettings)
admin.site.register(HostAnnouncementAnswer, HostAnnouncementAnswerAdmin)
admin.site.register(AnnouncementBoradcasting, AnnouncementBoradcastingAdmin)
admin.site.register(Sentiment, SentimentAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(ComplainceConfiguration, ComplainceConfigurationAdmin)
admin.site.register(ComplainceEntry, ComplainceEntryAdmin)
admin.site.register(SelfHealEntry,SelfHealEntryAdmin)
admin.site.register(SelfHealConfiguration,SelfHealConfigurationAdmin)
admin.site.register(ApplicationConfiguration, ApplicationConfigurationAdmin)
admin.site.register(AgentVerification, AgentVerificationAdmin)
admin.site.register(OTP, OTPAdmin)
admin.site.register(complainceHardeningAutoFix,complainceHardeningAutoFixAdmin)
admin.site.register(ComplianceAutoFixEntry,ComplianceAutoFixEntryAdmin)
admin.site.register(Release,ReleaseAdmin)
