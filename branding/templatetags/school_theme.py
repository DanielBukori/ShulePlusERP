from django import template

register = template.Library()

NAVY = '#0B2545'
GOLD = '#D4AF37'
BLACKS = ('#000', '#000000')


def _rgb(value):
    text = (value or '').strip()
    if text[0:1] != '#':
        return None
    text = text[1:]
    if len(text) == 3:
        text = ''.join(c * 2 for c in text)
    if len(text) != 6:
        return None
    try:
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _usable(value):
    """
    Rangi inayotumika tu kama ni halisi. Nyeusi kamili (#000000) ni mabaki ya
    kisanduku cha rangi kinachohifadhi thamani chenyewe kabla mtumiaji
    hakibadilisha - haipaswi kufunika rangi ya shule iliyowekwa kwenye
    Mipangilio ya Shule.
    """
    text = (value or '').strip().lower()
    return bool(_rgb(text)) and text not in BLACKS


def _luminance(rgb):
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def _profile(school):
    return getattr(school, 'public_profile', None)


@register.filter
def theme_brand(school):
    """Rangi kuu ya tovuti ya umma: SchoolProfile > School > navy ya jukwaa."""
    if not school:
        return NAVY
    for candidate in (getattr(_profile(school), 'primary_color', None), school.primary_color):
        if _usable(candidate):
            return candidate.strip()
    return NAVY


@register.filter
def theme_accent(school):
    """
    Rangi ya pili. Ikiwa ni karibu sana na rangi kuu (mfano nyeusi juu ya
    nyeusi) maandishi ya dhahabu yangeonekana kama meza - hivyo tunarudi
    kwenye dhahabu ya jukwaa.
    """
    brand = _rgb(theme_brand(school))
    accent = getattr(_profile(school), 'accent_color', None)
    rgb = _rgb(accent)
    if _usable(accent) and brand and abs(_luminance(rgb) - _luminance(brand)) >= 0.18:
        return accent.strip()
    return GOLD
