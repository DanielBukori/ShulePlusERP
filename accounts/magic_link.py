"""
Weka faili hii: accounts/magic_link.py

Muundo: tunatumia django.core.signing (stateless - hauhitaji model/database
table mpya) kutengeneza token inayoisha muda baada ya dakika 10.

MUHIMU: settings.py inahitaji EMAIL_BACKEND halisi kwa hii kutuma email
kweli. Kwa majaribio ya LOCAL DEV (bila akaunti ya email bado), tumia:

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

Hii "inatuma" email kwa kuiandika kwenye terminal/console badala ya kweli
- unaweza kuona link ya magic pale pale bila kuwa na akaunti ya SMTP.

Ukiwa tayari na akaunti ya email (Gmail App Password au SendGrid/Mailgun),
badilisha kuwa SMTP halisi (angalia maelezo chini ya faili hii).
"""
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings

SALT = 'shuleplus-magic-link'
MAX_AGE_SECONDS = 600  # dakika 10


def generate_magic_token(user):
    return signing.dumps({'user_id': user.id}, salt=SALT)


def verify_magic_token(token):
    """Inarudisha user_id kama token ni sahihi na haijaisha muda, la sivyo None."""
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE_SECONDS)
        return data.get('user_id')
    except signing.BadSignature:
        return None


def send_magic_link_email(user, request):
    token = generate_magic_token(user)
    verify_path = f"/accounts/magic-verify/{token}/"
    link = request.build_absolute_uri(verify_path)

    subject = "ShulePlusERP - Link ya Kuingia"
    message = (
        f"Habari {user.get_full_name() or user.username},\n\n"
        f"Bofya link hii kuingia ShulePlusERP (inaisha muda baada ya dakika 10):\n\n"
        f"{link}\n\n"
        f"Kama hukuomba kuingia, puuza ujumbe huu.\n\n"
        f"ShulePlusERP"
    )
    send_mail(
        subject, message,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shuleplus.co.tz'),
        [user.email],
        fail_silently=False,
    )

# ============================================================
# MPANGILIO WA SMTP HALISI (settings.py) - ukiwa tayari:
#
#   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#   EMAIL_HOST = 'smtp.gmail.com'          # au provider yako
#   EMAIL_PORT = 587
#   EMAIL_USE_TLS = True
#   EMAIL_HOST_USER = 'yourschool@gmail.com'
#   EMAIL_HOST_PASSWORD = 'app-password-yako'   # SIYO password ya kawaida
#   DEFAULT_FROM_EMAIL = 'ShulePlusERP <yourschool@gmail.com>'
#
# Gmail inahitaji "App Password" (siyo password ya kawaida) - tengeneza
# kwenye Google Account -> Security -> 2-Step Verification -> App
# Passwords. Njia mbadala rahisi zaidi: Brevo (zamani Sendinblue) au
# Mailgun - wanatoa free tier ya SMTP bila usumbufu wa Gmail.
# ============================================================
