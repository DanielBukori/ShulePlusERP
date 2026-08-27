"""
Functions za 'upload_to' kwa ajili ya FileField/ImageField zote za mfumo.
Kila function inahakikisha faili za shule moja haziwezi kamwe kuchanganyika
na za shule nyingine, kwa sababu subdomain ya shule ndio sehemu ya kwanza
ya path kila wakati.

MATUMIZI: kwenye models.py, badala ya:
    logo = models.ImageField(upload_to='school_logos/')
tumia:
    from .upload_paths import school_logo_path
    logo = models.ImageField(upload_to=school_logo_path)
"""


def school_logo_path(instance, filename):
    return f"schools/{instance.subdomain}/logo/{filename}"


def receipt_upload_path(instance, filename):
    # instance = Payment; inahitaji instance.school na instance.date_paid
    year = instance.date_paid.year if instance.date_paid else 'unknown'
    month = instance.date_paid.month if instance.date_paid else 'unknown'
    return f"schools/{instance.school.subdomain}/receipts/{year}/{month}/{filename}"


def home_package_upload_path(instance, filename):
    # instance = HomePackage (subject, school_class, school)
    return (
        f"schools/{instance.school.subdomain}/home_packages/"
        f"{instance.school_class.name}/{instance.subject.code}/{filename}"
    )


def result_report_upload_path(instance, filename):
    # instance = ripoti ya broadsheet iliyo-generate kwa PDF
    return (
        f"schools/{instance.school.subdomain}/result_reports/"
        f"{instance.academic_year}/{instance.term}/{filename}"
    )


def discipline_upload_path(instance, filename):
    return f"schools/{instance.school.subdomain}/discipline/{filename}"


def store_item_upload_path(instance, filename):
    return f"schools/{instance.school.subdomain}/store/{filename}"


def branding_upload_path(instance, filename):
    return f"schools/{instance.school.subdomain}/branding/{filename}"


def post_image_upload_path(instance, filename):
    # instance = PostImage - HAINA 'school' moja kwa moja (ina 'post' tu,
    # na school ipo ndani ya post.school) - tofauti na models mengine ya
    # branding (LeadershipMember, Facility n.k.) ambazo zina 'school' FK
    # moja kwa moja. Kutumia branding_upload_path hapa kunavunjika kwa
    # AttributeError: 'PostImage' object has no attribute 'school'.
    return f"schools/{instance.post.school.subdomain}/branding/gallery/{filename}"
