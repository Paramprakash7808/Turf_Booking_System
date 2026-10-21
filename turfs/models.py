from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

class Sport(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='trophy')
    image_url = models.CharField(max_length=500, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='check-circle')

    class Meta:
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.name

class Organization(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    logo_url = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Branch(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, blank=True)
    city = models.CharField(max_length=50, default="Ahmedabad")
    location = models.CharField(max_length=150)  # e.g. "Bodakdev, Ahmedabad"
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.organization.name}-{self.name}")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Branches"
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class OrganizationRole(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='custom_roles')
    name = models.CharField(max_length=50) # e.g. "Manager", "Staff", "Desk Supervisor"
    description = models.TextField(blank=True)
    can_manage_turfs = models.BooleanField(default=False)
    can_manage_slots = models.BooleanField(default=False)
    can_manage_bookings = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=False)
    can_manage_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class Turf(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='turfs')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='turfs')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    sports = models.ManyToManyField(Sport, related_name='turfs')
    primary_sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, related_name='primary_turfs')
    location = models.CharField(max_length=100)  # e.g. "Navrangpura, Ahmedabad"
    city = models.CharField(max_length=50, default="Ahmedabad")
    address = models.TextField(blank=True)
    description = models.TextField()
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    rating_count = models.PositiveIntegerField(default=24)
    image_url = models.CharField(max_length=500, blank=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='turfs')
    rules = models.TextField(
        blank=True, 
        default="• Booking cancellation must be done 24 hours in advance for a full refund\n• Wear appropriate sports footwear\n• No food or drinks allowed on the playing area\n• Arrive 15 minutes before your slot time"
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def rules_list(self):
        return [r.strip('• ').strip() for r in self.rules.split('\n') if r.strip()]

    def __str__(self):
        return f"{self.name} ({self.location})"

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=50)  # e.g. "06:00 AM - 07:00 AM"

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return self.label

class Booking(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='bookings')
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    PAYMENT_METHOD_CHOICES = [
        ('RAZORPAY', 'Razorpay (Online UPI / Cards / NetBanking)'),
        ('CASH', 'Cash on Counter (Pay at Venue)'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid Online'),
        ('PENDING_AT_COUNTER', 'Pay at Counter'),
        ('REFUNDED', 'Refunded'),
    ]

    player_name = models.CharField(max_length=100)
    player_phone = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='RAZORPAY')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='PAID')
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time_slot__start_time']
        unique_together = ('turf', 'date', 'time_slot')

    @property
    def pass_code(self):
        return f"TB-{self.date.strftime('%Y%m%d')}-{self.id:04d}"

    @property
    def formatted_slots_display(self):
        return self.time_slot.label if self.time_slot else "Standard Slot"

    def __str__(self):
        return f"Booking #{self.id} - {self.turf.name} on {self.date} ({self.time_slot.label})"

class Review(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.turf.name} ({self.rating} stars)"

class HeroSlide(models.Model):
    title = models.CharField(max_length=150, blank=True, help_text="Optional title or label for this slide")
    image = models.ImageField(upload_to='hero_slides/', blank=True, null=True, help_text="Upload background image from device")
    image_url = models.CharField(max_length=500, blank=True, help_text="Or enter a direct image URL (e.g. Unsplash / CDN)")
    order = models.PositiveIntegerField(default=0, help_text="Display order in slider (0 comes first)")
    is_active = models.BooleanField(default=True, help_text="Check to display on the homepage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Hero Slide"
        verbose_name_plural = "Hero Slides"

    @property
    def get_image_url(self):
        if self.image:
            return self.image.url
        return self.image_url

    def __str__(self):
        return self.title or f"Hero Slide #{self.id}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ORG_ADMIN', 'Organization Admin'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
        ('PLAYER', 'Player / Customer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PLAYER')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    custom_role = models.ForeignKey(OrganizationRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    city = models.CharField(max_length=100, default='Ahmedabad', blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(max_length=500, blank=True)
    favorite_sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, blank=True, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def get_avatar_url(self):
        if self.avatar:
            try:
                return self.avatar.url
            except Exception:
                return None
        return None

    @property
    def role_display_name(self):
        if self.custom_role:
            return self.custom_role.name
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'SUPER_ADMIN' if instance.is_superuser else 'PLAYER'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
    else:
        if hasattr(instance, 'profile'):
            if instance.is_superuser and instance.profile.role != 'SUPER_ADMIN':
                instance.profile.role = 'SUPER_ADMIN'
                instance.profile.save()
        else:
            role = 'SUPER_ADMIN' if instance.is_superuser else 'PLAYER'
            UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
