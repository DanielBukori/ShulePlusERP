"""
SMS SERVICE - Beem Africa integration.
Weka faili hii: shule_core/sms_service.py

MPANGILIO (settings.py):
    BEEM_API_KEY = os.environ.get('BEEM_API_KEY')
    BEEM_SECRET_KEY = os.environ.get('BEEM_SECRET_KEY')

Kisha weka environment variables halisi (usiziandike moja kwa moja kwenye
code, hasa ukitumia Git - zitumie .env au server environment):
    export BEEM_API_KEY="xxxx"
    export BEEM_SECRET_KEY="xxxx"

Bila hizo mbili, send_sms() haitavunja mfumo - itarudisha
{'sent': False, 'reason': 'no_credentials'} bila kuandika ujumbe wenye PIN kwenye log.
Hii inaruhusu maendeleo ya local bila akaunti ya Beem, na itaanza kutuma
SMS halisi mara utakapoweka hizo credentials - hakuna code itakayobadilika.
"""
import base64
import os
import requests
from django.conf import settings

BEEM_API_URL = "https://apisms.beem.africa/v1/send"


def _normalize_tz_phone(phone_digits):
    """Beem inahitaji namba katika mfumo wa kimataifa: 255XXXXXXXXX (bila +)."""
    phone_digits = ''.join(ch for ch in str(phone_digits) if ch.isdigit())
    if phone_digits.startswith('0'):
        return '255' + phone_digits[1:]
    if phone_digits.startswith('255'):
        return phone_digits
    return phone_digits


def send_sms(school, recipients, message):
    """
    school: School instance (inatumia school.sender_id kama 'source_addr')
    recipients: list ya namba za simu (mfano ['0712345678', '255755000111'])
    message: maandishi ya ujumbe

    Inarudisha dict: {'sent': True/False, 'raw': <response kutoka Beem> au 'reason': <error>}
    """
    api_key = getattr(settings, 'BEEM_API_KEY', None) or os.environ.get('BEEM_API_KEY')
    secret_key = getattr(settings, 'BEEM_SECRET_KEY', None) or os.environ.get('BEEM_SECRET_KEY')

    if not recipients:
        return {'sent': False, 'reason': 'no_recipients'}

    if not api_key or not secret_key:
        return {'sent': False, 'reason': 'no_credentials'}

    source_addr = getattr(school, 'sender_id', None) or 'INFO'
    auth_token = base64.b64encode(f"{api_key}:{secret_key}".encode()).decode()

    payload = {
        "source_addr": source_addr,
        "schedule_time": "",
        "encoding": 0,
        "message": message,
        "recipients": [
            {"recipient_id": i + 1, "dest_addr": _normalize_tz_phone(phone)}
            for i, phone in enumerate(recipients)
        ],
    }

    try:
        response = requests.post(
            BEEM_API_URL,
            json=payload,
            headers={
                "Authorization": f"Basic {auth_token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {'sent': False, 'reason': 'invalid_response'}
        return {'sent': bool(data.get('successful')), 'raw': data}
    except requests.RequestException:
        return {'sent': False, 'reason': 'request_error'}
    except ValueError:
        return {'sent': False, 'reason': 'invalid_response'}


def send_sms_to_user(school, user, message):
    """Kifupi: tuma kwa CustomUser mmoja (kwa kutumia user.phone)."""
    if not user or not getattr(user, 'phone', None):
        return {'sent': False, 'reason': 'no_phone'}
    return send_sms(school, [user.phone], message)
