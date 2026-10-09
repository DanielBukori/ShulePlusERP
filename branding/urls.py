from django.urls import path
from . import views

app_name = 'branding'

urlpatterns = [
    # --- Umma (Public) ---
    path('', views.school_home_view, name='school_home'),
    path('assets/<str:subdomain>/<str:kind>/<int:object_id>/', views.school_asset_view, name='school_asset'),
    path('s/<str:subdomain>/', views.school_home_local_view, name='school_home_local'),

    path('news/', views.post_list_view, name='post_list'),
    path('news/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('news/<str:category>/', views.post_list_view, name='post_list'),
    path('s/<str:subdomain>/news/', views.post_list_local_view, name='post_list_local'),
    path('s/<str:subdomain>/news/<int:post_id>/', views.post_detail_local_view, name='post_detail_local'),
    path('s/<str:subdomain>/news/<str:category>/', views.post_list_local_view, name='post_list_local'),

    path('leadership/', views.leadership_list_view, name='leadership_list'),
    path('s/<str:subdomain>/leadership/', views.leadership_list_local_view, name='leadership_list_local'),

    path('admissions/', views.admissions_view, name='admissions'),
    path('s/<str:subdomain>/admissions/', views.admissions_local_view, name='admissions_local'),

    path('haipo/', views.school_not_found_view, name='school_not_found'),

    # --- CMS (Headmaster/Second Master) ---
    path('cms/dashboard/', views.branding_dashboard_view, name='branding_dashboard'),
    path('cms/profile/', views.edit_profile_view, name='edit_profile'),

    path('cms/posts/', views.manage_posts_view, name='manage_posts'),
    path('cms/posts/<int:post_id>/edit/', views.edit_post_view, name='edit_post'),
    path('cms/posts/<int:post_id>/delete/', views.delete_post_view, name='delete_post'),
    path('cms/posts/<int:post_id>/toggle-publish/', views.toggle_publish_post_view, name='toggle_publish_post'),
    path('cms/post-images/<int:image_id>/delete/', views.delete_post_image_view, name='delete_post_image'),

    path('cms/leadership/', views.manage_leadership_view, name='manage_leadership'),
    path('cms/leadership/<int:member_id>/edit/', views.edit_leadership_view, name='edit_leadership'),
    path('cms/leadership/<int:member_id>/delete/', views.delete_leadership_view, name='delete_leadership'),

    path('cms/programs/', views.manage_programs_view, name='manage_programs'),
    path('cms/programs/<int:program_id>/edit/', views.edit_program_view, name='edit_program'),
    path('cms/programs/<int:program_id>/delete/', views.delete_program_view, name='delete_program'),

    path('cms/facilities/', views.manage_facilities_view, name='manage_facilities'),
    path('cms/facilities/<int:facility_id>/edit/', views.edit_facility_view, name='edit_facility'),
    path('cms/facilities/<int:facility_id>/delete/', views.delete_facility_view, name='delete_facility'),

    path('cms/testimonials/', views.manage_testimonials_view, name='manage_testimonials'),
    path('cms/testimonials/<int:testimonial_id>/edit/', views.edit_testimonial_view, name='edit_testimonial'),
    path('cms/testimonials/<int:testimonial_id>/delete/', views.delete_testimonial_view, name='delete_testimonial'),

    path('cms/inquiries/', views.manage_inquiries_view, name='manage_inquiries'),
    path('cms/inquiries/<int:inquiry_id>/contacted/', views.mark_inquiry_contacted_view, name='mark_inquiry_contacted'),
]
