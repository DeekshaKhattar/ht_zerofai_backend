from django.urls import path
from admin_portal.apis.v1.views import *
from admin_portal.apis.v1.views import *
from admin_portal.apis.v1.website_admin import *

app_name = 'admin_portal'

urlpatterns = [
    path('api/v1/customer/', CustomerOperations.as_view(), name='portal_customer'),
    path('api/v1/host/', HostOperations.as_view(), name='portal_host'),
    path('api/v1/license/', LicenseOperations.as_view(), name='portal_license'),
    path('api/v1/purchased/license/', PurchasedLicenseOperations.as_view(), name='portal_purchased_license'),
    path('api/v1/solution/', SolutionOperations.as_view(), name='portal_solution'),
    path('api/v1/ticket/', TicketOperations.as_view(), name='portal_ticket'),
    path('api/v1/solution/run/', SolutionRunOperations.as_view(), name='portal_solution_run'),
    path('api/v1/feedback/', FeedbackOperations.as_view(), name='portal_feedback'),
    path('api/v1/sentiment/', SentimentOperations.as_view(), name='portal_sentiment'),
    path('api/v1/complaince/', ComplainceOperations.as_view(), name='portal_complaince'),
    path('api/v1/complaince/host/report/', ComplainceReportOperations.as_view(), name='portal_complaince_host_report'),
    path('api/v1/complaince/configuration/', ComplainceConfigurationOperations.as_view(), name='portal_complaince_configuration'),
    path('api/v1/complaince/fix/post/',ComplainceAutoFixPOSTOperations.as_view(), name='portal_complaince_auto_fix_post'),
    path('api/v1/announcement/', AnnouncementBoradcastingOperations.as_view(), name='portal_announcement'),
    path('api/v1/announcement/answer/', AnnouncementAnswerOperations.as_view(), name='portal_announcement_answer'),
    path('api/v1/contact/us/', ContactUsAdminOperations.as_view(), name='contact_us_admin_operation'),
    # Website admin urls
    path('api/v1/solutions/', SolutionsOperations.as_view(), name='get_portal_solution'),
    path('api/v1/casestudy/', CaseStudiesOperations.as_view(), name='get_portal_case_study'),
    path('api/v1/testimonial/', TestimonialOperations.as_view(), name='get_portal_testimonial'),
    path('api/v1/blogs/', BlogPostsOperations.as_view(), name='get_portal_blog'),
    path('api/v1/carrers/', CareerOperations.as_view(), name='get_portal_carrers'),
    path('api/v1/contact/us/', ContactUsOperations.as_view(), name='post_contact_us'),
    # Dashboard APIs
    path('api/v1/dashboard/cards/', DashboardCards.as_view(), name='dashboard_cards'),
    path('api/v1/dashboard/graph/', DashboardGraphs.as_view(), name='dashboard_graph'),
    path('api/v1/dashboard/ai-insights/', DashboardSystemInsights.as_view(), name='dashboard-system-insights'),
    # Reports
    path('api/v1/reports/data/', ReportsOperation.as_view(), name='reports_data'),
    # Application Configuration
    path('api/v1/application/configuration/', ApplicationConfOperations.as_view(), name='application_configuration'),
    # Agent Verification
    path('api/v1/agent/verification/', AgentVerifificationOperation.as_view(), name='agent_verification'),
    path('api/v1/selfheal/',SelfHealOperations.as_view(),name='portal_selfheal'),
    path('api/v1/host-data-search/', HostDataSearchAPIView.as_view(), name='host-data-search'),
    path('api/v1/selfheal/configuration/',SelfHealConfigurationOperations.as_view(),name='portal_selfheal_configuration'),
    path('api/v1/complaince/fix/',ComplainceAutoFixOperations.as_view(), name='portal_complaince_auto_fix'),
    path('api/v1/complaince/fix/configuration/',ComplainceAutoFixConfigurationOperations.as_view(), name='portal_complaince_auto_fix'),
    path('api/v1/latest-release/',GetLatestRelease.as_view(),name='Agent_Release')
]