from django.db import models
from base.models import *
from admin_portal.models import *

BLOG_STATUS_CHOICES = (
    ('draft', 'DRAFT'),
    ('published', 'PUBLISHED'),
)

SERVICE_TYPE_CHOICES = (
    ('Proactive', 'Proactive'),
    ('Predictive', 'Predictive'),
    ('Reactive', 'Reactive'),
)

'''
Dynamic data for the website will be contained in here in the below models.
'''

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Solutions(TimeStampedModel):
    solution_name = models.CharField(verbose_name='Solution Name', max_length=100)
    image = models.ImageField(verbose_name='Solution Image', upload_to='website/solution/', null=True, blank=True)
    description = models.TextField(verbose_name='Solution Description')
    status = models.BooleanField(verbose_name='Is Active?', default=True)

    def __str__(self):
        return f"{self.solution_name} - {self.id}"

    class Meta:
        verbose_name_plural= "Website Solution"
        ordering = ['-updated_at']

class Services(TimeStampedModel):
    service_name = models.CharField(verbose_name='Service Name', max_length=100)
    image = models.ImageField(verbose_name='Service Image', upload_to='website/service/', null=True, blank=True)
    description = models.TextField(verbose_name='Service Description')
    status = models.BooleanField(verbose_name='Is Active?', default=True)
    type = models.CharField(verbose_name='Type', choices=SERVICE_TYPE_CHOICES, default='Proactive', max_length=20)

    def __str__(self):
        return f"{self.service_name} - {self.id}"

    class Meta:
        verbose_name_plural = "Services"
        ordering = ['-updated_at']


class CaseStudy(TimeStampedModel):
    author = models.ForeignKey(User, verbose_name="Author", on_delete=models.CASCADE,
        null=True, blank=True, related_name='user_case_studies')
    title = models.CharField(verbose_name="Title", max_length=100)
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(verbose_name='Solution Image', upload_to='website/casestudies/', null=True, blank=True)
    status = models.BooleanField(verbose_name='Is Active?', default=True)
    class Meta:
        verbose_name_plural = "Case Studies"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.author}"
    

class Testimonial(TimeStampedModel):
    author = models.ForeignKey(User, verbose_name="Author", on_delete=models.CASCADE,
        null=True, blank=True, related_name='user_testimonial')
    company = models.ForeignKey(Customer, verbose_name="Company", on_delete=models.CASCADE,
        null=True, blank=True, related_name='user_company')
    rating = models.IntegerField(verbose_name="Rating", default=5, choices=[(i, i) for i in range(1, 6)])
    content = models.TextField(verbose_name="Content")
    status = models.BooleanField(verbose_name='Is Active?', default=True)

    class Meta:
        verbose_name_plural = "Testimonials"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.author}"


class BlogPosts(TimeStampedModel):
    author = models.ForeignKey(User, verbose_name='Author', on_delete=models.CASCADE, related_name='blog_author_name')
    title = models.CharField(verbose_name='Title', max_length=100)
    content = models.TextField(verbose_name='Content (HTML String)', blank=True, null=True)
    description = models.TextField(verbose_name='Description (Raw String)', blank=True, null=True)
    image = models.ImageField(verbose_name='Image', upload_to='blogs/image', null=True, blank=True)
    status = models.CharField(verbose_name='Status', max_length=15, choices=BLOG_STATUS_CHOICES, default='draft')

    class Meta:
        verbose_name_plural = "BlogPost"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.author} - {self.title}"
    

class ContactUs(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name="Name")
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Message")
    phone_number = models.CharField(max_length=10, validators=[validate_mobile], help_text='Enter Mobile Number', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Contact Us"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Message from {self.name} with Email: {self.email}"
    

class Career(TimeStampedModel):
    position = models.CharField(max_length=100, verbose_name="Position Name")
    location = models.CharField(max_length=100, verbose_name="Location")
    description = models.TextField(verbose_name="Job Description")
    requirements = models.TextField(verbose_name="Requirements")
    status = models.BooleanField(verbose_name='Is Active?', default=True)
    vacancy_count = models.PositiveIntegerField(verbose_name='Total Vacancy', default=1)
    application_starting_date = models.DateTimeField(verbose_name='Application submition starting From')
    application_closing_date = models.DateTimeField(verbose_name='Application accepted till')
    application_received = models.PositiveIntegerField(verbose_name='Total applications recevied', default=0)

    class Meta:
        verbose_name_plural = "Careers"
        ordering = ['-updated_at']

    def __str__(self):
        return self.position
    

class CarrerSubmission(TimeStampedModel):
    carrer = models.ForeignKey(Career, verbose_name="Career", on_delete=models.CASCADE,
        null=True, blank=True, related_name='carrer_application_submission')
    name = models.CharField(verbose_name='Candidate Name', null=True, blank=True, max_length=100)
    email = models.EmailField(verbose_name='Candidate Email', null=True, blank=True)
    phone_number = models.CharField(verbose_name='Candidate Phone Number', max_length=10,
        validators=[validate_mobile], help_text='Enter Mobile Number', null=True, blank=True)
    resume = models.FileField(verbose_name='Candidate Resume', null=True, blank=True, upload_to='carrers/resume')
    
    class Meta:
        verbose_name_plural = "Carrer Application Submission"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Subbision for {self.carrer.position} from {self.email}"
