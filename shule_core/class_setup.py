from shule_core.models import SchoolClass

STANDARD_CLASSES = (
    ('Form I', 'O'),
    ('Form II', 'O'),
    ('Form III', 'O'),
    ('Form IV', 'O'),
    ('Form V', 'A'),
    ('Form VI', 'A'),
)

SCHOOL_LEVEL_CLASSES = {
    'O': {'O'},
    'A': {'A'},
    'B': {'O', 'A'},
}


def ensure_standard_classes(school):
    """Create missing standard forms without changing any existing class records."""
    levels = SCHOOL_LEVEL_CLASSES.get(school.school_level, {'O', 'A'})
    standard_classes = [(name, level) for name, level in STANDARD_CLASSES if level in levels]
    existing_names = {
        name.casefold()
        for name in school.classes.filter(stream='GENERAL').values_list('name', flat=True)
    }
    SchoolClass.objects.bulk_create(
        [
            SchoolClass(
                school=school,
                name=name,
                level=level,
                stream='GENERAL',
            )
            for name, level in standard_classes
            if name.casefold() not in existing_names
        ],
        ignore_conflicts=True,
    )
