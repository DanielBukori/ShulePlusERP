from django.apps import AppConfig
from django.db.backends.signals import connection_created


def tune_sqlite(sender, connection, **kwargs):
    """WAL + busy_timeout: msomaji asivunjike ukima mtu mwingine anaandika."""
    if connection.vendor != 'sqlite':
        return
    try:
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode=WAL;')
            cursor.execute('PRAGMA busy_timeout=15000;')
            cursor.execute('PRAGMA synchronous=NORMAL;')
    except Exception:
        # Hali ya juu ya kufuli (mfano wakati wa kizania cha data) - jaribu tena
        # kwenye muunganisho unaofuata badala ya kuvunja ombi.
        pass


class ShuleCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shule_core'
    verbose_name = 'Msingi wa Shule'

    def ready(self):
        connection_created.connect(tune_sqlite)
