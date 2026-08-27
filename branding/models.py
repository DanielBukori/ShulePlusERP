from django.db import models
from shule_core.models import School, CustomUser
from shule_core.upload_paths import branding_upload_path, post_image_upload_path


class SchoolProfile(models.Model):
    """
    Taarifa za 'About/Contact' za tovuti ya umma ya shule - kitu kimoja
    tu kwa shule (OneToOne). Headmaster/Second Master ndio wanaohariri.
    """
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='public_profile')
    motto = models.CharField(max_length=200, blank=True, null=True, help_text='Mfano: "Elimu Bora, Malezi Bora"')
    about_text = models.TextField(blank=True, null=True, help_text='Historia/maelezo ya shule')
    mission = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    cover_image = models.ImageField(upload_to=branding_upload_path, blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    primary_color = models.CharField(max_length=7, blank=True, null=True, help_text='Mfano: #0B2545 (hiari - rangi kuu ya brand ya shule)')
    accent_color = models.CharField(max_length=7, blank=True, null=True, help_text='Mfano: #D4AF37 (hiari - rangi ya pili ya brand)')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile ya {self.school.name}"

    def is_complete(self):
        return bool(self.about_text and self.cover_image and self.mission and self.vision)


class BrandingPost(models.Model):
    """
    Chapisho la umma - admissions, matokeo ya NECTA, mahafali, mafanikio,
    matukio, gallery ya picha za majengo, n.k. Headmaster/Second Master
    ndio wanaoandika.
    """
    CATEGORY_CHOICES = [
        ('ADMISSIONS', 'Admissions'),
        ('NECTA_RESULTS', 'Matokeo ya NECTA'),
        ('EVENT', 'Tukio/Mahafali'),
        ('ACHIEVEMENT', 'Mafanikio'),
        ('GALLERY', 'Gallery (Majengo/Picha)'),
        ('GENERAL', 'Taarifa ya Jumla'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='branding_posts', db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.ImageField(upload_to=branding_upload_path, blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['school', 'category', 'is_published'])]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class PostImage(models.Model):
    """Picha za ziada kwa chapisho moja (album/gallery ya tukio moja)."""
    post = models.ForeignKey(BrandingPost, on_delete=models.CASCADE, related_name='extra_images')
    image = models.ImageField(upload_to=post_image_upload_path)
    caption = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"Picha ya {self.post.title}"


class LeadershipMember(models.Model):
    """Wasifu wa uongozi - Headmaster, Second Master, HODs n.k."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='leadership_members', db_index=True)
    full_name = models.CharField(max_length=150)
    role_title = models.CharField(max_length=100, help_text='Mfano: Mkuu wa Shule, Mkuu wa Taaluma')
    photo = models.ImageField(upload_to=branding_upload_path, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text='Namba ndogo inaonekana kwanza')
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'full_name']

    def __str__(self):
        return f"{self.full_name} - {self.role_title}"


class AcademicProgram(models.Model):
    """Mchepuo/programu ya kitaaluma - O-Level, A-Level (Sayansi/Sanaa), n.k."""
    LEVEL_CHOICES = [('O', 'O-Level'), ('A', 'A-Level'), ('BOTH', 'O-Level na A-Level')]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='academic_programs', db_index=True)
    level = models.CharField(max_length=4, choices=LEVEL_CHOICES)
    name = models.CharField(max_length=150, help_text='Mfano: Sayansi (PCB/PCM), Sanaa (HGL/EGM)')
    description = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True, help_text='Masharti ya kujiunga')
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class Facility(models.Model):
    """Miundombinu - maabara, maktaba, bweni, uwanja n.k."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='facilities', db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=branding_upload_path, blank=True, null=True)
    icon = models.CharField(max_length=10, blank=True, null=True, help_text='Emoji moja, mfano: 🔬 au 📚')
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Facilities'

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    """Maoni ya wazazi/wahitimu waliofanikiwa."""
    ROLE_CHOICES = [('PARENT', 'Mzazi'), ('ALUMNI', 'Mhitimu'), ('STUDENT', 'Mwanafunzi'), ('OTHER', 'Mwingine')]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='testimonials', db_index=True)
    author_name = models.CharField(max_length=150)
    author_role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PARENT')
    quote = models.TextField()
    photo = models.ImageField(upload_to=branding_upload_path, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.author_name} ({self.get_author_role_display()})"


class AdmissionInquiry(models.Model):
    """Ombi la kujiunga - linatumwa kutoka ukurasa wa umma wa Admissions."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='admission_inquiries', db_index=True)
    student_name = models.CharField(max_length=150)
    parent_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    class_interested = models.CharField(max_length=100, blank=True, null=True, help_text='Mfano: Form One 2027')
    message = models.TextField(blank=True, null=True)
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Admission Inquiries'

    def __str__(self):
        return f"{self.student_name} - {self.parent_name}"
