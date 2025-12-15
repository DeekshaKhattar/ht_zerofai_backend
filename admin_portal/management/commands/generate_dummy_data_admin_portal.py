import os
import random
from django.core.management.base import BaseCommand
from faker import Faker
from base.models import User
from admin_portal.models import *

fake = Faker()

USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('super_admin','Super Admin'),
)

SOLUTION_TYPE_CHOICES = (
    ('exe', 'Exe'),
    ('command', 'Command')
)

SOLUTION_RUN_TYPE_CHOCIES = (
    ('autofix', 'Auto Fix'),
    ('kb', 'Knowledge Base'),
    ('ticket', 'Ticket'),
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


class Command(BaseCommand):
    help = 'Generate dummy data for models'

    def handle(self, *args, **kwargs):
        # Generate dummy data for Customers
        for _ in range(20):
            customer = Customer.objects.create(
                company_name=fake.company(),
                company_address=fake.address(),
                company_phone=''.join([str(random.randint(0, 9)) for _ in range(10)]),
                domain=fake.domain_name(),
            )
            customer.save()

        # Generate dummy data for Hosts
        for customer in Customer.objects.all():
            for _ in range(20):
                host = Host.objects.create(
                    customer=customer,
                    hostname=fake.hostname(),
                    mac_address=fake.mac_address(),
                    version=fake.random_element(elements=('1.0', '2.0', '3.0'))
                )
                host.save()

        # Generate dummy data for PurchasedLicenses
        for customer in Customer.objects.all():
            purchased_license = PurchasedLicense.objects.create(
                customer=customer,
                license_count=random.randint(1, 10),
                start_date=fake.date_between(start_date='-1y', end_date='today'),
                end_date=fake.date_between(start_date='today', end_date='+1y')
            )
            purchased_license.save()

        # Generate dummy data for Licenses
        for customer in Customer.objects.all():
            license = License.objects.create(
                customer=customer,
                start_date=fake.date_between(start_date='-1y', end_date='today'),
                end_date=fake.date_between(start_date='today', end_date='+1y'),
                total_license=random.randint(1, 10),
                used_license=random.randint(0, 5),
                avialable_license=random.randint(0, 10),
                app_version=fake.random_element(elements=('1.0', '2.0', '3.0')),
                status=random.choice([True, False])
            )
            license.save()

        # Generate dummy data for Solutions
        for customer in Customer.objects.all():
            for _ in range(20):
                solution = Solution.objects.create(
                    customer=customer,
                    name=fake.word(),
                    description=fake.sentence(),
                    type=random.choice([choice[0] for choice in SOLUTION_TYPE_CHOICES]),
                    command=fake.text(max_nb_chars=200),
                    exe_file=None  # Change this if you want to upload files
                )
                solution.save()

        # Generate dummy data for Tickets
        for customer in Customer.objects.all():
            for host in customer.customer_host.all():
                ticket = Ticket.objects.create(
                    customer=customer,
                    host=host,
                    ticket_id=fake.uuid4(),
                    subject=fake.sentence(),
                    description=fake.text(max_nb_chars=200)
                )
                ticket.save()

        # Generate dummy data for SolutionRuns
        for customer in Customer.objects.all():
            for host in customer.customer_host.all():
                for solution in customer.customer_solution.all():
                    solution_run = SolutionRun.objects.create(
                        customer=customer,
                        host=host,
                        solution=solution,
                        type=random.choice([choice[0] for choice in SOLUTION_RUN_TYPE_CHOCIES])
                    )
                    solution_run.save()

        # Generate dummy data for HostAnnouncementAnswers
        for customer in Customer.objects.all():
            for host in customer.customer_host.all():
                for announcement in AnnouncementBoradcasting.objects.all():
                    host_announcement_answer = HostAnnouncementAnswer.objects.create(
                        customer=customer,
                        host=host,
                        announcement=announcement,
                        boolean_answer=random.choice([True, False]),
                        text_answer=fake.text(max_nb_chars=200),
                        status=random.choice([True, False])
                    )
                    host_announcement_answer.save()

        # Generate dummy data for AnnouncementBroadcastings
        for customer in Customer.objects.all():
            announcement_boradcasting = AnnouncementBoradcasting.objects.create(
                customer=customer,
                feed=fake.text(max_nb_chars=200),
                is_form_active=random.choice([True, False]),
                form_type=random.choice([choice[0] for choice in ANNOUNCEMENT_FORM_CHOICES]),
                question=fake.sentence(),
                status=random.choice([choice[0] for choice in ANNOUNCEMENT_STATUS_CHOICES]),
                expiry_date=fake.date_time_this_year()
            )
            announcement_boradcasting.save()

        # Generate dummy data for Sentiments
        for customer in Customer.objects.all():
            for host in customer.customer_host.all():
                sentiment = Sentiment.objects.create(
                    customer=customer,
                    host=host,
                    ram=random.uniform(1, 16),
                    cpu=random.uniform(1, 100),
                    hardisk=random.uniform(1, 100),
                    page_memory=random.uniform(1, 100),
                    critical_services=random.uniform(1, 100),
                    latency=random.uniform(1, 100),
                    uptime=random.uniform(1, 100),
                    status=random.choice([choice[0] for choice in SENTIMENT_STATUS_CHOICES])
                )
                sentiment.save()

        # Generate dummy data for Feedbacks
        for customer in Customer.objects.all():
            for host in customer.customer_host.all():
                for solution in customer.customer_solution.all():
                    feedback = Feedback.objects.create(
                        customer=customer,
                        host=host,
                        solution=solution,
                        feedback=random.choice([choice[0] for choice in FEEDBACK_CHOCIES]),
                        solution_type=random.choice([choice[0] for choice in SOLUTION_RUN_TYPE_CHOCIES])
                    )
                    feedback.save()

        self.stdout.write(self.style.SUCCESS('Dummy data generated successfully.'))
