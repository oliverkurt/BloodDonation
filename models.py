from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_admin = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    weight = models.FloatField()
    height = models.FloatField()
    region = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    municipality = models.CharField(max_length=50)
    blood_type = models.CharField(max_length=3)
    availability = models.BooleanField(default=False)
    last_donation_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    from django.db import models
    from django.contrib.auth.models import Profile

    class BloodDonationRequest(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        request_type = models.CharField(max_length=10, choices=[('donating', 'Donating'), ('receiving', 'Receiving')])
        blood_type = models.CharField(max_length=3, blank=True)
        region = models.CharField(max_length=50, blank=True)
        province = models.CharField(max_length=50, blank=True)
        municipality = models.CharField(max_length=50, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

    from django.contrib import admin
    from .models import BloodDonationRequest, Profile

    class BloodDonationRequestAdmin(admin.ModelAdmin):
        list_display = ('user', 'blood_type', 'request_type', 'region', 'province', 'municipality')
        search_fields = ('username', 'blood_type', 'request_type')

    class ProfileAdmin(admin.ModelAdmin):
        list_display = ('user', 'blood_type', 'availability')

