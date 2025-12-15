# YourApp/management/commands/generate_dummy_data.py

from django.core.management.base import BaseCommand
from faker import Faker
from base.models import User
from website.models import *
import random
from datetime import datetime, timedelta

fake = Faker()

company = Customer.objects.first()

class Command(BaseCommand):
    help = 'Generate dummy data for models'

    def handle(self, *args, **kwargs):
        # Generate dummy data for Solutions
        for _ in range(20):
            solution = Solutions.objects.create(
                solution_name=fake.company(),
                description=fake.text(),
                status=random.choice([True, False])
            )
            solution.save()

        # Generate dummy data for CaseStudy
        for _ in range(20):
            case_study = CaseStudy.objects.create(
                author=random.choice(User.objects.all()),
                title=fake.sentence(),
                description=fake.text(),
                status=random.choice([True, False])
            )
            case_study.save()

        # Generate dummy data for Testimonial
        for _ in range(20):
            testimonial = Testimonial.objects.create(
                author=random.choice(User.objects.all()),
                company=company,
                rating=random.randint(1, 5),
                content=fake.text(),
                status=random.choice([True, False])
            )
            testimonial.save()

        # Generate dummy data for BlogPosts
        for _ in range(20):
            blog_post = BlogPosts.objects.create(
                author=random.choice(User.objects.all()),
                title=fake.sentence(),
                content=fake.text(),
                description=fake.text(),
                status=random.choice(['draft', 'published'])
            )
            blog_post.save()

        # Generate dummy data for ContactUs
        for _ in range(20):
            contact_us = ContactUs.objects.create(
                name=fake.name(),
                email=fake.email(),
                message=fake.text(),
                phone_number=''.join([str(random.randint(0, 9)) for _ in range(10)])
            )
            contact_us.save()

        # Generate dummy data for Career
        for _ in range(20):
            career = Career.objects.create(
                position=fake.job(),
                location=fake.city(),
                description=fake.text(),
                requirements=fake.text(),
                status=random.choice([True, False]),
                vacancy_count=random.randint(1, 10),
                application_starting_date=datetime.now(),
                application_closing_date=datetime.now() + timedelta(days=30),
                application_received=random.randint(0, 100)
            )
            career.save()

        self.stdout.write(self.style.SUCCESS('Dummy data generated successfully.'))
