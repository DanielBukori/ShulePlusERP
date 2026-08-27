"""
accounts/otp.py

OTP (One-Time PIN) ya 2FA - inabadilisha magic_link.py.

Muundo: OTP inahifadhiwa kwenye SESSION (siyo database) - haihitaji model
mpya. Session inaanza kabla ya user kuingia rasmi (login()), kwa hiyo
tunaweza kuhifadhi 'ni user gani anasubiri OTP' hapo kabla ya login kamili.

Namba 6 za tarakimu, zinaisha muda dakika 5, na zina kikomo cha majaribio
5 kabla ya kulazimika kuomba OTP mpya.
"""
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from shule_core.sms_service import send_sms_to_user

OTP_SESSION_KEY = 'pending_otp'
OTP_TTL_SECONDS = 300  # dakika 5
MAX_ATTEMPTS = 5


def generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"  # tarakimu 6, mfano 384726


def start_otp_session(request, user):
    """Tengeneza OTP mpya, ihifadhi kwenye session, irudishe (ili itumwe)."""
    code = generate_otp()
    request.session[OTP_SESSION_KEY] = {
        'user_id': user.id,
        'code': code,
        'expires': (timezone.now() + timedelta(seconds=OTP_TTL_SECONDS)).isoformat(),
        'attempts': 0,
    }
    return code


def get_pending_otp(request):
    return request.session.get(OTP_SESSION_KEY)


def clear_otp_session(request):
    request.session.pop(OTP_SESSION_KEY, None)


def verify_otp(request, submitted_code):
    """
    Inarudisha (user_id, None) kama OTP ni sahihi, au (None, error_message)
    kama siyo sahihi/imeisha muda/majaribio yamezidi.
    """
    data = get_pending_otp(request)
    if not data:
        return None, "Hakuna OTP inayosubiriwa. Ingia tena."

    expires = timezone.datetime.fromisoformat(data['expires'])
    if timezone.is_naive(expires):
        expires = timezone.make_aware(expires)

    if timezone.now() > expires:
        clear_otp_session(request)
        return None, "OTP imeisha muda (dakika 5). Ingia tena upate OTP mpya."

    data['attempts'] = data.get('attempts', 0) + 1
    request.session[OTP_SESSION_KEY] = data

    if data['attempts'] > MAX_ATTEMPTS:
        clear_otp_session(request)
        return None, "Umejaribu mara nyingi mno. Ingia tena upate OTP mpya."

    if submitted_code.strip() != data['code']:
        return None, "OTP siyo sahihi. Jaribu tena."

    user_id = data['user_id']
    clear_otp_session(request)
    return user_id, None


def send_otp(user, code, school=None):
    """
    SMS ndiyo njia kuu (kupitia Beem - itaandika console tu mpaka
    BEEM_API_KEY/SECRET viwekwe kwenye settings). Email ni nakala ya ziada
    ikiwa mtumiaji ana email - haizuii chochote kama haipo.
    """
    message = f"ShulePlusERP: Namba yako ya kuingia (OTP) ni {code}. Inaisha muda dakika 5. Usimpe mtu yeyote."
    sms_result = send_sms_to_user(school, user, message)

    if user.email:
        try:
            send_mail(
                "ShulePlusERP - Namba yako ya OTP",
                f"Habari {user.get_full_name() or user.username},\n\n"
                f"Namba yako ya kuingia (OTP) ni: {code}\n"
                f"Inaisha muda baada ya dakika 5.\n\n"
                f"Kama hukuomba hii, puuza ujumbe huu.\n\nShulePlusERP",
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shuleplus.co.tz'),
                [user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # email ni nakala tu - isivunje mtiririko wa SMS

    return sms_result


def mask_phone(phone):
    if not phone or len(phone) < 4:
        return phone
    return f"****{phone[-4:]}"


def mask_email(email):
    if not email or '@' not in email:
        return email
    name, domain = email.split('@', 1)
    if len(name) <= 2:
        return f"**@{domain}"
    return f"{name[0]}***{name[-1]}@{domain}"
