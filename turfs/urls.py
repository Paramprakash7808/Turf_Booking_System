from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('explore/home/<str:city>/', views.home, name='home_city'),
    path('explore/turfs/<str:city>/', views.turf_list, name='turf_list_city'),
    path('set-city/<str:city>/', views.set_city, name='set_city'),
    path('turfs/', views.turf_list, name='turf_list'),
    path('sports/', views.sports_list, name='sports_list'),
    path('turfs/<slug:slug>/', views.turf_detail, name='turf_detail'),
    path('branches/<int:branch_id>/', views.branch_detail, name='branch_detail'),
    path('branches/<slug:slug>/', views.branch_detail, name='branch_detail_by_slug'),
    path('booking/<int:turf_id>/', views.booking_view, name='booking'),
    path('booking/<int:booking_id>/ticket/', views.booking_ticket, name='booking_ticket'),
    path('ticket/', views.ticket_hub, name='ticket'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.change_password_view, name='change_password'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Super Admin Portal Routes
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/orgs/create/', views.super_admin_create_org, name='super_admin_create_org'),
    path('super-admin/orgs/<int:org_id>/', views.super_admin_org_detail, name='super_admin_org_detail'),
    path('super-admin/orgs/<int:org_id>/update/', views.super_admin_update_org, name='super_admin_update_org'),
    path('super-admin/orgs/<int:org_id>/delete/', views.super_admin_delete_org, name='super_admin_delete_org'),
    path('super-admin/branches/create/', views.super_admin_create_branch, name='super_admin_create_branch'),
    path('super-admin/branches/<int:branch_id>/update/', views.super_admin_update_branch, name='super_admin_update_branch'),
    path('super-admin/branches/<int:branch_id>/delete/', views.super_admin_delete_branch, name='super_admin_delete_branch'),
    path('super-admin/roles/create/', views.super_admin_create_role, name='super_admin_create_role'),
    path('super-admin/team/create/', views.super_admin_create_team_member, name='super_admin_create_team_member'),
    
    # Organization Admin Portal Routes
    path('org-admin/', views.org_admin_dashboard, name='org_admin_dashboard'),
    path('org-admin/roles/create/', views.org_admin_create_role, name='org_admin_create_role'),
    path('org-admin/team/create/', views.org_admin_create_team_member, name='org_admin_create_team_member'),
    path('org-admin/branches/create/', views.org_admin_create_branch, name='org_admin_create_branch'),
    path('org-admin/branches/<int:branch_id>/update/', views.org_admin_update_branch, name='org_admin_update_branch'),
    path('org-admin/branches/<int:branch_id>/delete/', views.org_admin_delete_branch, name='org_admin_delete_branch'),
    path('org-admin/turfs/create/', views.org_admin_create_turf, name='org_admin_create_turf'),
    
    # Staff / Manager Portal Routes
    path('staff-portal/', views.staff_portal, name='staff_portal'),
    path('staff-portal/checkin/<int:booking_id>/', views.staff_checkin_booking, name='staff_checkin_booking'),

    # AJAX / Dynamic Multi-Branch Synchronization APIs
    path('api/turfs/<int:turf_id>/slots/', views.api_check_slots, name='api_check_slots'),
    path('api/organizations/<int:org_id>/sync/', views.api_organization_sync, name='api_organization_sync'),
    path('api/branches/<int:branch_id>/sync/', views.api_branch_sync, name='api_branch_sync'),
    path('api/staff/live-sync/', views.api_staff_live_sync, name='api_staff_live_sync'),
    path('api/org-admin/live-sync/', views.api_org_admin_live_sync, name='api_org_admin_live_sync'),
]
