from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('super_admin', 'Super Admin'),
)

def validate_mobile(value):
    # Check if the mobile number consists of exactly 10 digits and is numeric
    if not (value.isdigit() and len(value) == 10):
        raise ValidationError(_('Invalid mobile number'))

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.active = True
        user.staff = True
        user.admin = True
        user.status = True
        user.user_type = 'super_admin'
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, TimeStampedModel):
    user_type = models.CharField(verbose_name='User Type', choices=USER_TYPE_CHOICES, null=True, blank=True)
    customer_obj = models.ForeignKey('admin_portal.Customer', verbose_name='Customer', on_delete=models.CASCADE, related_name='customer_user', null=True, blank=True)
    email = models.EmailField(verbose_name='Email Address', max_length=255, unique=True)
    first_name = models.CharField(verbose_name='First Name', max_length=50, null=True, blank=True)
    last_name = models.CharField(verbose_name='Last Name', max_length=50, null=True, blank=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{0,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(verbose_name='Mobile Number', validators=[phone_regex], max_length=17, blank=True, null=True)
    profile_image = models.ImageField(verbose_name='Profile Image', upload_to='users/profile_image' ,null=True, blank=True)
    status = models.BooleanField(verbose_name='Status', default=True)
    password_1 = models.CharField(verbose_name='Password 1', max_length=255, null=True, blank=True)
    password_2 = models.CharField(verbose_name='Password 2', max_length=255, null=True, blank=True)
    customer_id = models.CharField(verbose_name='Customer ID', max_length=50, null=True, blank=True)
    active = models.BooleanField(verbose_name='Is Active', default=True)
    staff = models.BooleanField(verbose_name='Is Staff User', default=False)
    admin = models.BooleanField(verbose_name='Is Admin User', default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        return self.first_name +' '+ self.last_name if self.last_name else ''

    def get_short_name(self):
        return self.first_name

    def __str__(self):             
        return self.email

    class Meta:
        verbose_name_plural= "Users"
        ordering = ['-updated_at']

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

    @property
    def is_active(self):
        "Is the user active?"
        return self.active

