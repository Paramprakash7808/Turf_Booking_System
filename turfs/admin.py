from django.contrib import admin
from django.utils.html import format_html
from .models import Sport, Amenity, Turf, TimeSlot, Booking, Review, HeroSlide, Organization, Branch, OrganizationRole, UserProfile

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'location', 'city', 'phone', 'is_active')
    list_filter = ('organization', 'city', 'is_active')
    search_fields = ('name', 'location', 'organization__name')

@admin.register(OrganizationRole)
class OrganizationRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'can_manage_turfs', 'can_manage_slots', 'can_manage_bookings', 'can_manage_staff')
    list_filter = ('organization',)
    search_fields = ('name', 'organization__name')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'organization', 'branch', 'custom_role', 'phone')
    list_filter = ('role', 'organization', 'branch')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone')

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('preview_thumb', 'title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)
    fields = ('title', 'image', 'image_url', 'order', 'is_active')

    def preview_thumb(self, obj):
        url = obj.get_image_url
        if url:
            return format_html('<img src="{}" style="width: 80px; height: 46px; object-fit: cover; border-radius: 8px; border: 1px solid #e2e8f0;" />', url)
        return format_html('<span style="color: #94a3b8; font-size: 11px;">No image</span>')
    preview_thumb.short_description = "Preview"

@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'primary_sport', 'price_per_hour', 'rating', 'is_featured')
    list_filter = ('is_featured', 'primary_sport', 'city')
    search_fields = ('name', 'location', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('sports', 'amenities')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('label', 'start_time', 'end_time')
    ordering = ('start_time',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'turf', 'user', 'date', 'time_slot', 'total_price', 'payment_method', 'payment_status', 'status', 'created_at')
    list_filter = ('payment_method', 'payment_status', 'status', 'date', 'turf')
    search_fields = ('turf__name', 'user__username', 'player_name', 'player_phone', 'razorpay_payment_id')
    date_hierarchy = 'date'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('turf', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('turf__name', 'user__username', 'comment')

