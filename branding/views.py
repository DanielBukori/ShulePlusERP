from functools import wraps
import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count

from shule_core.models import School, Student, Staff
from .models import (
    SchoolProfile, BrandingPost, PostImage, LeadershipMember,
    AcademicProgram, Facility, Testimonial, AdmissionInquiry,
)
from .forms import (
    SchoolProfileForm, BrandingPostForm, LeadershipMemberForm,
    AcademicProgramForm, FacilityForm, TestimonialForm, AdmissionInquiryForm,
)

MANAGER_ROLES = ['HEADMASTER', 'SECOND_MASTER']


def branding_manager_required(view_func):
    """Mkuu wa Shule AU Naibu/IT wa Shule (Second Master) ndio wanaoruhusiwa kuhariri tovuti."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'school', None):
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        if request.user.role not in MANAGER_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def _resolve_school(request, subdomain=None):
    if subdomain:
        return get_object_or_404(School, subdomain=subdomain, is_approved=True)
    return getattr(request, 'school', None)


def _get_or_create_profile(school):
    profile, _ = SchoolProfile.objects.get_or_create(school=school)
    return profile


# ============================================================
# UKURASA WA UMMA (public) - kila mmoja ana wrapper mbili:
# moja inayotumia request.school (TenantMiddleware/subdomain live),
# na "_local" inayopokea subdomain moja kwa moja kwenye URL (kwa
# matumizi ya nje ya subdomain routing, mfano preview/links za marketing).
# ============================================================

def _school_home(request, school):
    if not school:
        return render(request, 'branding/school_not_found.html', status=404)

    profile = _get_or_create_profile(school)
    posts = BrandingPost.objects.filter(school=school, is_published=True)[:6]
    leadership = LeadershipMember.objects.filter(school=school, is_published=True)[:4]
    programs = AcademicProgram.objects.filter(school=school, is_published=True)
    facilities = Facility.objects.filter(school=school, is_published=True)[:6]
    testimonials = Testimonial.objects.filter(school=school, is_published=True)[:6]

    stats = {
        'students': Student.objects.filter(school=school, school_class__isnull=False).count(),
        'teachers': Staff.objects.filter(school=school, is_teaching_staff=True).count(),
        'programs': programs.count(),
    }

    context = {
        'school': school, 'profile': profile, 'posts': posts,
        'leadership': leadership, 'programs': programs, 'facilities': facilities,
        'testimonials': testimonials, 'stats': stats,
    }
    return render(request, 'branding/school_home.html', context)


def school_home_view(request):
    return _school_home(request, _resolve_school(request))


def school_home_local_view(request, subdomain):
    return _school_home(request, _resolve_school(request, subdomain))


def _post_list(request, school, category=None):
    if not school:
        return render(request, 'branding/school_not_found.html', status=404)
    posts = BrandingPost.objects.filter(school=school, is_published=True)
    if category:
        posts = posts.filter(category=category)
    context = {'school': school, 'posts': posts, 'categories': BrandingPost.CATEGORY_CHOICES, 'selected_category': category}
    return render(request, 'branding/post_list.html', context)


def post_list_view(request, category=None):
    return _post_list(request, _resolve_school(request), category)


def post_list_local_view(request, subdomain, category=None):
    return _post_list(request, _resolve_school(request, subdomain), category)


def _post_detail(request, school, post_id):
    if not school:
        return render(request, 'branding/school_not_found.html', status=404)
    post = get_object_or_404(BrandingPost, id=post_id, school=school, is_published=True)
    context = {'school': school, 'post': post, 'extra_images': post.extra_images.all()}
    return render(request, 'branding/post_detail.html', context)


def post_detail_view(request, post_id):
    return _post_detail(request, _resolve_school(request), post_id)


def post_detail_local_view(request, subdomain, post_id):
    return _post_detail(request, _resolve_school(request, subdomain), post_id)


def _leadership_list(request, school):
    if not school:
        return render(request, 'branding/school_not_found.html', status=404)
    members = LeadershipMember.objects.filter(school=school, is_published=True)
    return render(request, 'branding/leadership_list.html', {'school': school, 'members': members})


def leadership_list_view(request):
    return _leadership_list(request, _resolve_school(request))


def leadership_list_local_view(request, subdomain):
    return _leadership_list(request, _resolve_school(request, subdomain))


def _admissions(request, school):
    if not school:
        return render(request, 'branding/school_not_found.html', status=404)

    profile = _get_or_create_profile(school)
    programs = AcademicProgram.objects.filter(school=school, is_published=True)
    admission_posts = BrandingPost.objects.filter(school=school, category='ADMISSIONS', is_published=True)

    if request.method == 'POST':
        form = AdmissionInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.school = school
            inquiry.save()
            messages.success(request, "Asante! Ombi lako limepokelewa - Uongozi wa shule utawasiliana nawe hivi karibuni.")
            return redirect(request.path)
    else:
        form = AdmissionInquiryForm()

    context = {'school': school, 'profile': profile, 'programs': programs, 'admission_posts': admission_posts, 'form': form}
    return render(request, 'branding/admissions.html', context)


def admissions_view(request):
    return _admissions(request, _resolve_school(request))


def admissions_local_view(request, subdomain):
    return _admissions(request, _resolve_school(request, subdomain))


def school_not_found_view(request):
    return render(request, 'branding/school_not_found.html', status=404)


def school_asset_view(request, subdomain, kind, object_id):
    school = _resolve_school(request, subdomain)
    if not school or (request.school and request.school.pk != school.pk):
        raise Http404

    assets = {
        'school-logo': (
            School.objects.filter(pk=object_id, subdomain=school.subdomain),
            'logo',
            None,
        ),
        'profile-cover': (SchoolProfile.objects.filter(school=school, pk=object_id), 'cover_image', None),
        'post-image': (BrandingPost.objects.filter(school=school, pk=object_id), 'image', 'is_published'),
        'gallery-image': (
            PostImage.objects.filter(post__school=school, pk=object_id).select_related('post'),
            'image',
            'post',
        ),
        'leadership-photo': (
            LeadershipMember.objects.filter(school=school, pk=object_id),
            'photo',
            'is_published',
        ),
        'facility-image': (
            Facility.objects.filter(school=school, pk=object_id),
            'image',
            'is_published',
        ),
        'testimonial-photo': (
            Testimonial.objects.filter(school=school, pk=object_id),
            'photo',
            'is_published',
        ),
    }
    asset_config = assets.get(kind)
    if not asset_config:
        raise Http404

    queryset, field_name, published_attr = asset_config
    instance = get_object_or_404(queryset)
    asset = getattr(instance, field_name)
    if not asset:
        raise Http404
    if not asset.storage.exists(asset.name):
        return HttpResponseNotFound()

    is_manager = (
        request.user.is_authenticated
        and request.user.school_id == school.pk
        and request.user.role in MANAGER_ROLES
    )
    is_public = (
        published_attr is None
        or (
            getattr(instance, published_attr).is_published
            if published_attr == 'post'
            else getattr(instance, published_attr)
        )
    )
    if not is_public and not is_manager:
        raise Http404

    try:
        file_handle = asset.open('rb')
    except FileNotFoundError:
        return HttpResponseNotFound()

    response = FileResponse(
        file_handle,
        content_type=mimetypes.guess_type(asset.name)[0] or 'application/octet-stream',
    )
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    response['Cache-Control'] = 'public, max-age=3600' if is_public else 'private, no-store'
    return response


# ============================================================
# CMS - Headmaster/Second Master pekee
# ============================================================

@branding_manager_required
def branding_dashboard_view(request):
    school = request.school
    profile = _get_or_create_profile(school)

    context = {
        'school': school,
        'profile': profile,
        'profile_complete': profile.is_complete(),
        'post_counts': BrandingPost.objects.filter(school=school).values('category').annotate(n=Count('id')),
        'total_posts': BrandingPost.objects.filter(school=school).count(),
        'total_leadership': LeadershipMember.objects.filter(school=school).count(),
        'total_programs': AcademicProgram.objects.filter(school=school).count(),
        'total_facilities': Facility.objects.filter(school=school).count(),
        'total_testimonials': Testimonial.objects.filter(school=school).count(),
        'new_inquiries': AdmissionInquiry.objects.filter(school=school, is_contacted=False).count(),
    }
    return render(request, 'branding/branding_dashboard.html', context)


@branding_manager_required
def edit_profile_view(request):
    school = request.school
    profile = _get_or_create_profile(school)

    if request.method == 'POST':
        form = SchoolProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Wasifu wa shule umesasishwa.")
            return redirect('branding:edit_profile')
    else:
        form = SchoolProfileForm(instance=profile)

    return render(request, 'branding/edit_profile.html', {'school': school, 'form': form, 'profile': profile})


@branding_manager_required
def manage_posts_view(request):
    school = request.school

    if request.method == 'POST':
        form = BrandingPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.school = school
            post.created_by = request.user
            post.save()
            for f in request.FILES.getlist('extra_images'):
                PostImage.objects.create(post=post, image=f)
            messages.success(request, "Chapisho limehifadhiwa.")
            return redirect('branding:manage_posts')
    else:
        form = BrandingPostForm()

    posts = BrandingPost.objects.filter(school=school)
    return render(request, 'branding/manage_posts.html', {'school': school, 'form': form, 'posts': posts})


@branding_manager_required
def edit_post_view(request, post_id):
    school = request.school
    post = get_object_or_404(BrandingPost, id=post_id, school=school)

    if request.method == 'POST':
        form = BrandingPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            for f in request.FILES.getlist('extra_images'):
                PostImage.objects.create(post=post, image=f)
            messages.success(request, "Chapisho limesasishwa.")
            return redirect('branding:manage_posts')
    else:
        form = BrandingPostForm(instance=post)

    return render(request, 'branding/edit_post.html', {
        'school': school, 'form': form, 'post': post, 'extra_images': post.extra_images.all(),
    })


@branding_manager_required
def delete_post_view(request, post_id):
    school = request.school
    post = get_object_or_404(BrandingPost, id=post_id, school=school)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Chapisho limefutwa.")
    return redirect('branding:manage_posts')


@branding_manager_required
def toggle_publish_post_view(request, post_id):
    school = request.school
    post = get_object_or_404(BrandingPost, id=post_id, school=school)
    if request.method == 'POST':
        post.is_published = not post.is_published
        post.save(update_fields=['is_published'])
        if post.is_published:
            messages.success(request, f'"{post.title}" imechapishwa - sasa inaonekana kwenye tovuti.')
        else:
            messages.success(request, f'"{post.title}" imerudishwa rasimu - haionekani tena kwa umma.')
    return redirect('branding:manage_posts')


@branding_manager_required
def delete_post_image_view(request, image_id):
    school = request.school
    img = get_object_or_404(PostImage, id=image_id, post__school=school)
    post_id = img.post_id
    if request.method == 'POST':
        img.delete()
    return redirect('branding:edit_post', post_id=post_id)


# --- Leadership CMS ---
@branding_manager_required
def manage_leadership_view(request):
    school = request.school
    if request.method == 'POST':
        form = LeadershipMemberForm(request.POST, request.FILES)
        if form.is_valid():
            m = form.save(commit=False)
            m.school = school
            m.created_by = request.user
            m.save()
            messages.success(request, "Mwanauongozi ameongezwa.")
            return redirect('branding:manage_leadership')
    else:
        form = LeadershipMemberForm()
    members = LeadershipMember.objects.filter(school=school)
    return render(request, 'branding/manage_leadership.html', {'school': school, 'form': form, 'members': members})


@branding_manager_required
def edit_leadership_view(request, member_id):
    school = request.school
    member = get_object_or_404(LeadershipMember, id=member_id, school=school)
    if request.method == 'POST':
        form = LeadershipMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "Taarifa zimesasishwa.")
            return redirect('branding:manage_leadership')
    else:
        form = LeadershipMemberForm(instance=member)
    return render(request, 'branding/edit_leadership.html', {'school': school, 'form': form, 'member': member})


@branding_manager_required
def delete_leadership_view(request, member_id):
    school = request.school
    member = get_object_or_404(LeadershipMember, id=member_id, school=school)
    if request.method == 'POST':
        member.delete()
        messages.success(request, "Mwanauongozi ameondolewa.")
    return redirect('branding:manage_leadership')


# --- Programs CMS ---
@branding_manager_required
def manage_programs_view(request):
    school = request.school
    if request.method == 'POST':
        form = AcademicProgramForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.school = school
            p.created_by = request.user
            p.save()
            messages.success(request, "Programu imeongezwa.")
            return redirect('branding:manage_programs')
    else:
        form = AcademicProgramForm()
    programs = AcademicProgram.objects.filter(school=school)
    return render(request, 'branding/manage_programs.html', {'school': school, 'form': form, 'programs': programs})


@branding_manager_required
def edit_program_view(request, program_id):
    school = request.school
    program = get_object_or_404(AcademicProgram, id=program_id, school=school)
    if request.method == 'POST':
        form = AcademicProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Programu imesasishwa.")
            return redirect('branding:manage_programs')
    else:
        form = AcademicProgramForm(instance=program)
    return render(request, 'branding/edit_program.html', {'school': school, 'form': form, 'program': program})


@branding_manager_required
def delete_program_view(request, program_id):
    school = request.school
    program = get_object_or_404(AcademicProgram, id=program_id, school=school)
    if request.method == 'POST':
        program.delete()
        messages.success(request, "Programu imeondolewa.")
    return redirect('branding:manage_programs')


# --- Facilities CMS ---
@branding_manager_required
def manage_facilities_view(request):
    school = request.school
    if request.method == 'POST':
        form = FacilityForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.save(commit=False)
            f.school = school
            f.created_by = request.user
            f.save()
            messages.success(request, "Kifaa/Sehemu imeongezwa.")
            return redirect('branding:manage_facilities')
    else:
        form = FacilityForm()
    facilities = Facility.objects.filter(school=school)
    return render(request, 'branding/manage_facilities.html', {'school': school, 'form': form, 'facilities': facilities})


@branding_manager_required
def edit_facility_view(request, facility_id):
    school = request.school
    facility = get_object_or_404(Facility, id=facility_id, school=school)
    if request.method == 'POST':
        form = FacilityForm(request.POST, request.FILES, instance=facility)
        if form.is_valid():
            form.save()
            messages.success(request, "Imesasishwa.")
            return redirect('branding:manage_facilities')
    else:
        form = FacilityForm(instance=facility)
    return render(request, 'branding/edit_facility.html', {'school': school, 'form': form, 'facility': facility})


@branding_manager_required
def delete_facility_view(request, facility_id):
    school = request.school
    facility = get_object_or_404(Facility, id=facility_id, school=school)
    if request.method == 'POST':
        facility.delete()
        messages.success(request, "Imeondolewa.")
    return redirect('branding:manage_facilities')


# --- Testimonials CMS ---
@branding_manager_required
def manage_testimonials_view(request):
    school = request.school
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save(commit=False)
            t.school = school
            t.created_by = request.user
            t.save()
            messages.success(request, "Maoni yameongezwa.")
            return redirect('branding:manage_testimonials')
    else:
        form = TestimonialForm()
    testimonials = Testimonial.objects.filter(school=school)
    return render(request, 'branding/manage_testimonials.html', {'school': school, 'form': form, 'testimonials': testimonials})


@branding_manager_required
def edit_testimonial_view(request, testimonial_id):
    school = request.school
    t = get_object_or_404(Testimonial, id=testimonial_id, school=school)
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, "Yamesasishwa.")
            return redirect('branding:manage_testimonials')
    else:
        form = TestimonialForm(instance=t)
    return render(request, 'branding/edit_testimonial.html', {'school': school, 'form': form, 'testimonial': t})


@branding_manager_required
def delete_testimonial_view(request, testimonial_id):
    school = request.school
    t = get_object_or_404(Testimonial, id=testimonial_id, school=school)
    if request.method == 'POST':
        t.delete()
        messages.success(request, "Yameondolewa.")
    return redirect('branding:manage_testimonials')


# --- Admission Inquiries (maombi kutoka ukurasa wa umma) ---
@branding_manager_required
def manage_inquiries_view(request):
    school = request.school
    inquiries = AdmissionInquiry.objects.filter(school=school)
    return render(request, 'branding/manage_inquiries.html', {'school': school, 'inquiries': inquiries})


@branding_manager_required
def mark_inquiry_contacted_view(request, inquiry_id):
    school = request.school
    inquiry = get_object_or_404(AdmissionInquiry, id=inquiry_id, school=school)
    if request.method == 'POST':
        inquiry.is_contacted = True
        inquiry.save(update_fields=['is_contacted'])
    return redirect('branding:manage_inquiries')
