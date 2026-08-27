from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login
from django.contrib import messages
from django.shortcuts import redirect, render

from .otp import (
    start_otp_session, verify_otp, send_otp,
    get_pending_otp, clear_otp_session, mask_phone, mask_email,
)

# Roles zinazohitaji OTP 2FA - Parent/Student hazihitaji (kama tulivyokubaliana)
OTP_REQUIRED_ROLES = ['HEADMASTER', 'SECOND_MASTER', 'ACADEMIC', 'TEACHER', 'DISCIPLINE', 'ACCOUNTANT']


class TenantLoginView(LoginView):
    """
    LoginView ya kawaida ya Django, ila:
    1. Inaongeza 'school' kwenye context (kutoka request.school - TenantMiddleware)
       ili login page ionyeshe logo/jina la shule husika kwa subdomain yake.
    2. Inazuia mtu wa shule A kuingia kwenye subdomain ya shule B, hata kama
       jina la mtumiaji/password ni sahihi (ulinzi wa ziada wa multi-tenant).
    3. Kwa roles zenye OTP (walimu, wakuu n.k.) - baada ya password kuthibitika,
       inatuma OTP (SMS + email) badala ya kumuingiza moja kwa moja.
    """
    template_name = 'shule_core/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = getattr(self.request, 'school', None)
        return context

    def form_valid(self, form):
        user = form.get_user()
        request_school = getattr(self.request, 'school', None)

        # Super Admin (bila school) anaruhusiwa kila mahali
        if user.school_id and request_school and user.school_id != request_school.id:
            form.add_error(None, f"Akaunti hii ni ya shule nyingine, siyo {request_school.name}.")
            return self.form_invalid(form)

        if user.role in OTP_REQUIRED_ROLES:
            if not user.phone and not user.email:
                form.add_error(None, "Akaunti hii haina namba ya simu wala barua pepe - wasiliana na Mkuu wa Shule.")
                return self.form_invalid(form)

            code = start_otp_session(self.request, user)
            send_otp(user, code, school=request_school)

            return render(self.request, 'shule_core/otp_verify.html', {
                'school': request_school,
                'masked_phone': mask_phone(user.phone) if user.phone else None,
                'masked_email': mask_email(user.email) if user.email else None,
            })

        return super().form_valid(form)


# ============================================================
# Kila role inapelekwa dashboard yake. Zile zenye None bado
# hazijajengwa - zitabadilishwa kadri tunavyoendelea na roadmap
# (Discipline, Accountant, Teacher, Parent, Student).
# ============================================================
ROLE_DASHBOARD_URLS = {
    'HEADMASTER': 'academic:academic_dashboard',      # TODO: headmaster_dashboard yake mwenyewe baadaye
    'SECOND_MASTER': 'academic:academic_dashboard',
    'ACADEMIC': 'academic:academic_dashboard',
    'TEACHER': 'teacher_portal:teacher_dashboard',
    'DISCIPLINE': 'discipline:discipline_dashboard',
    'ACCOUNTANT': 'accountant:accountant_dashboard',
    'PARENT': 'family_portal:parent_dashboard',
    'STUDENT': 'family_portal:student_dashboard',
}


@login_required
def post_login_redirect_view(request):
    """
    Weka LOGIN_REDIRECT_URL = 'accounts:post_login_redirect' kwenye
    settings.py. Kila mtumiaji akiingia (login), atapelekwa hapa kwanza,
    na hapa ndipo tunapo-decide dashboard sahihi kutegemea role yake.
    """
    if request.user.must_change_password:
        return redirect('accounts:force_password_change')

    url_name = ROLE_DASHBOARD_URLS.get(request.user.role)
    if url_name:
        return redirect(url_name)
    return render(request, 'accounts/dashboard_coming_soon.html', {
        'role': request.user.get_role_display(),
    })


@login_required
def force_password_change_view(request):
    """
    Ukurasa wa LAZIMA - mtumiaji mwenye must_change_password=True (akaunti
    mpya za PIN/reg_number) hawezi kwenda popote pengine mpaka abadilishe
    password yake. Hakuna nav/sidebar hapa kwa makusudi (template rahisi).
    """
    if not request.user.must_change_password:
        return redirect('accounts:post_login_redirect')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save()
            update_session_auth_hash(request, user)  # asitolewe nje baada ya kubadilisha password
            messages.success(request, "Password imebadilishwa kikamilifu.")
            return redirect('accounts:post_login_redirect')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/force_password_change.html', {'form': form})


@login_required
def password_change_view(request):
    """Ukurasa wa hiari - mtu yeyote anaweza kubadilisha password yake wakati wowote."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password imebadilishwa kikamilifu.")
            return redirect('accounts:post_login_redirect')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})


def otp_verify_view(request):
    """
    Ukurasa wa kuweka namba 6 za OTP zilizotumwa baada ya password
    kuthibitika. Ikiwa sahihi na haijaisha muda, mtumiaji anaingizwa
    (login) kikamilifu.
    """
    from shule_core.models import CustomUser

    school = getattr(request, 'school', None)

    if request.method == 'POST':
        code = request.POST.get('otp', '').strip()
        user_id, error = verify_otp(request, code)

        if error:
            messages.error(request, error)
            pending = get_pending_otp(request)
            if not pending:
                return redirect('accounts:login')
            return render(request, 'shule_core/otp_verify.html', {'school': school})

        try:
            user = CustomUser.objects.get(pk=user_id, is_active=True)
        except CustomUser.DoesNotExist:
            messages.error(request, "Akaunti haipatikani. Ingia tena.")
            return redirect('accounts:login')

        login(request, user)
        return redirect('accounts:post_login_redirect')

    # GET (mfano mtu ame-refresh ukurasa) - kama hakuna OTP inayosubiriwa, mrudishe login
    if not get_pending_otp(request):
        return redirect('accounts:login')
    return render(request, 'shule_core/otp_verify.html', {'school': school})


def otp_resend_view(request):
    """Tuma OTP mpya (inafuta ile ya zamani) - kwa mtumiaji anayesubiri OTP kwa sasa."""
    from shule_core.models import CustomUser

    data = get_pending_otp(request)
    if not data:
        return redirect('accounts:login')

    try:
        user = CustomUser.objects.get(pk=data['user_id'], is_active=True)
    except CustomUser.DoesNotExist:
        clear_otp_session(request)
        return redirect('accounts:login')

    school = getattr(request, 'school', None)
    code = start_otp_session(request, user)
    send_otp(user, code, school=school)

    messages.success(request, "OTP mpya imetumwa.")
    return render(request, 'shule_core/otp_verify.html', {
        'school': school,
        'masked_phone': mask_phone(user.phone) if user.phone else None,
        'masked_email': mask_email(user.email) if user.email else None,
    })
