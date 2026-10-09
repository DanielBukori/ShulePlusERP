from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator 
from django.core.exceptions import ValidationError
from .upload_paths import school_logo_path, receipt_upload_path

# 0. USER MMOJA KWA ROLES ZOTE 8
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('HEADMASTER', 'Mkuu wa Shule'),
        ('SECOND_MASTER', 'Second Master'),
        ('ACADEMIC', 'Academic Master'), 
        ('TEACHER', 'Mwalimu'),
        ('DISCIPLINE', 'Mwalimu wa Nidhamu'),
        ('ACCOUNTANT', 'Mhasibu'),
        ('PARENT', 'Mzazi'),
        ('STUDENT', 'Mwanafunzi'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TEACHER', db_index=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='users', db_index=True)
    phone = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    email = models.EmailField(max_length=50, unique=True, blank=True, null=True) 
    must_change_password = models.BooleanField(default=True)
    school_registration_pending = models.BooleanField(default=False, db_index=True)
    class Meta:
        indexes = [ models.Index(fields=['school', 'role']) ]

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

# 1. SHULE - MSINGI WA KILA KITU
class School(models.Model):
    LEVEL_CHOICES = [('O', 'O-Level Only'), ('A', 'Advanced Level Only'), ('B', 'Both O-Level and A-Level')]
    
    name = models.CharField(max_length=255, unique=True, db_index=True)
    subdomain = models.CharField(max_length=100, unique=True, blank=True, db_index=True)
    school_level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default='B')
    logo = models.ImageField(upload_to=school_logo_path, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#7E22CE')
    sender_id = models.CharField(max_length=11, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    email = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    discipline_starting_score = models.PositiveIntegerField(default=100)
    discipline_alert_score = models.PositiveIntegerField(default=50)
    is_approved = models.BooleanField(default=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.subdomain:
            self.subdomain = slugify(self.name).replace('-', '')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# 2. DARASA
class SchoolClass(models.Model):
    STREAM_CHOICES = [('GENERAL', 'General'), ('SCIENCE', 'Science'), ('ARTS', 'Arts'), ('S1', 'Stream 1'), ('S2', 'Stream 2')]
    
    name = models.CharField(max_length=50, db_index=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes', db_index=True)
    level = models.CharField(max_length=1, choices=[('O', 'O-Level'), ('A', 'A-Level')], db_index=True)
    stream = models.CharField(max_length=10, choices=STREAM_CHOICES, default='GENERAL', blank=True, null=True)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_as_class_teacher",
        limit_choices_to={"role": "TEACHER"},
    )

    class Meta:
        verbose_name_plural = "School Classes"
        unique_together = ('name', 'stream', 'school')
        indexes = [ models.Index(fields=['school', 'level']) ]

    def __str__(self):
        if self.stream and self.stream != 'GENERAL':
            return f"{self.name} {self.stream}"
        return f"{self.name}"

# 3. COMBINATION
class Combination(models.Model):
    name = models.CharField(max_length=10, db_index=True)
    level = models.CharField(max_length=1, choices=[('A', 'A-Level')], default='A')
    
    class Meta: unique_together = ('name', 'level')
    def __str__(self): return self.name

# 4. SOMO
class Subject(models.Model):
    LEVEL_CHOICES = [('O', 'O-Level'), ('A', 'A-Level')]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subjects', db_index=True)
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=10)
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, db_index=True)
    combination = models.ForeignKey(Combination, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)

    class Meta:
        unique_together = ('code', 'level', 'combination', 'school')
        indexes = [ models.Index(fields=['school', 'level']) ]

    def __str__(self):
        if self.level == 'A' and self.combination:
            return f"{self.code} - {self.name} [{self.combination.name}]"
        return f"{self.code} - {self.name}"

# 5. MWANAFUNZI
class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students', db_index=True)
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name='students', null=True, blank=True, db_index=True)
    combination = models.ForeignKey(Combination, on_delete=models.PROTECT, related_name='students', null=True, blank=True)
    
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    reg_number = models.CharField(max_length=30, db_index=True)
    
    parent = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'PARENT'}, related_name='children')
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15, db_index=True)
    created_at = models.DateField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.school_class:
            if self.school_class.level == 'A' and not self.combination:
                raise ValidationError({
                    'combination': 'Mwanafunzi wa A-Level lazima awe na Combination.'
                })
            if self.school_class.level == 'O' and self.combination:
                raise ValidationError({
                    'combination': 'Mwanafunzi wa O-Level hapaswi kuwa na Combination.'  })

    class Meta:
        unique_together = ('reg_number', 'school', 'school_class')
        indexes = [ models.Index(fields=['school', 'school_class']), models.Index(fields=['school', 'combination']) ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.reg_number}"

# 6. WAFANYAKAZI / STAFF - HII NDIO ILIYOKOSEKA
class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff_profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='staff', db_index=True)
    
    tsc_number = models.CharField(max_length=50, blank=True, null=True, unique=True) # Namba ya TSC
    employment_date = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=100, blank=True, null=True) # Diploma, Degree
    email = models.CharField(max_length=50, unique=True)
    is_teaching_staff = models.BooleanField(default=True) # Ili kujua ni mwalimu au mhasibu tu
    is_store_keeper = models.BooleanField(default=False)
    class Meta:
        unique_together = ('user', 'school') # Mtu hawezi kuwa staff mara 2 shule 1
        indexes = [models.Index(fields=['school', 'is_store_keeper'])]
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.name}"

# 7. UGAVANJI WA MASOMO
class SubjectAssignment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_index=True)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assignments', limit_choices_to={'role__in': ['TEACHER', 'ACADEMIC', 'SECOND_MASTER']}, db_index=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assigned_teachers', db_index=True) 
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, db_index=True)
    combination = models.ForeignKey(Combination, on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.IntegerField(default=2026, db_index=True)
    is_principal = models.BooleanField(default=True)
    class Meta:
        unique_together = ('teacher', 'subject', 'school_class', 'combination', 'academic_year')
        indexes = [ models.Index(fields=['school', 'academic_year']) ]

# 8. ALAMA
class AcademicResult(models.Model):  
    EXAM_TYPE_CHOICES = [('TEST_1_A', 'Test 1 - Robo ya Kwanza'),
        ('TEST_2_A', 'Test 2 - Robo ya Kwanza'),
        ('MID_TERM_EXAM', 'Mtihani wa Mid-Term'),
        ('TEST_1_B', 'Test 1 - Robo ya Pili'),
        ('TEST_2_B', 'Test 2 - Robo ya Pili'),
        ('TERMINAL_EXAM', 'Mtihani wa Terminal (Muhula 1)'),
        ('ANNUAL_EXAM', 'Mtihani wa Annual (Muhula 2)'),
        ('NATIONAL', 'National Exam'),
        # --- MPYA: Mitihani ya Maandalizi (Series) - kwa Form IV/VI
        # kabla ya National Exam. HAYAINGII kwenye ukokotoaji wa
        # MID_TERM/TERMINAL/ANNUAL - ni taarifa ya maendeleo TU kwa
        # wazazi (angalia academic/grading.py - haziguswi popote pale).
        ('SERIES_1', 'Series 1'),
        ('SERIES_2', 'Series 2'),
        ('SERIES_3', 'Series 3'),
        ('SERIES_4', 'Series 4'),
        ('SERIES_5', 'Series 5'),
        ]
    TERM_CHOICES = [('TERM_1', 'Muhula wa Kwanza'), ('TERM_2', 'Muhula wa Pili')
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results', db_index=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results', db_index=True) 
    combination = models.ForeignKey(Combination, on_delete=models.CASCADE, related_name='results', null=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='results')
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES, db_index=True)
    term = models.CharField(max_length=20, choices=TERM_CHOICES, db_index=True)
    academic_year = models.IntegerField(default=2026, db_index=True)

    score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.00), MaxValueValidator(100.00)])
    is_published = models.BooleanField(default=False, db_index=True)   #  ONGEZA HII
    is_auto_absent = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Alama F(0) iliwekwa kiotomatiki wakati wa Publish - mwanafunzi hakuwa na alama ya somo hili lililofanyiwa mtihani (siyo F halisi aliyoipata).',
    )
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True) 
    
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
   

    class Meta:
        unique_together = ('student', 'subject', 'exam_type', 'term', 'academic_year')
        indexes = [
            models.Index(fields=['school', 'subject', 'term', 'academic_year']),
            models.Index(fields=['school', 'student', 'academic_year']),
        ]

    def grade(self):
        level = self.subject.level 
        if level == 'A':
            if self.score >= 80: return 'A'
            elif self.score >= 70: return 'B'
            elif self.score >= 60: return 'C'
            elif self.score >= 50: return 'D'
            elif self.score >= 40: return 'E'
            elif self.score >= 35: return 'S'
            else: return 'F'
        else:
            if self.score >= 75: return 'A'
            elif self.score >= 65: return 'B'
            elif self.score >= 45: return 'C'
            elif self.score >= 30: return 'D'
            else: return 'F'
    
    def points(self):
        # POINTS KAMA ZA NECTA
        level = self.subject.level
        g = self.grade()
        
        if level == 'A': # A-LEVEL POINTS
            grades = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'S': 6, 'F': 7}
            return grades.get(g, 7)
        else: # O-LEVEL POINTS
            grades = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'F': 5}
            return grades.get(g, 5)

    def __str__(self):
        return f"{self.student.reg_number} - {self.subject.name}: {self.score}"

# 9. MALIPO V1
class Payment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField(db_index=True)
    bank_name = models.CharField(max_length=50)
    receipt_number = models.CharField(max_length=100)
    receipt_file = models.FileField(upload_to=receipt_upload_path)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'receipt_number')
        indexes = [
            models.Index(fields=['school', 'date_paid']),
        ]

# Ongeza hii kwenye shule_core/models.py (mwishoni, baada ya AcademicResult)

class ConductReport(models.Model):
    """
    Tabia/Mwenendo wa mwanafunzi kwa muhula fulani - kama ile section ya
    'PUPILS CONDUCT AND PROGRESS' kwenye ripoti halisi za shule (Work
    Determination, Cooperation, Discipline n.k. + Maoni ya Class Teacher
    na Headteacher). KILA FIELD NI HIARI (blank=True, null=True) -
    Class Teacher anajaza kile anachotaka tu, siyo lazima kila kimoja.
    """
    GRADE_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('F', 'F')]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='conduct_reports')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='conduct_reports')
    term = models.CharField(max_length=10, choices=[('TERM_1', 'Term 1'), ('TERM_2', 'Term 2')])
    academic_year = models.IntegerField()

    # Vigezo vya tabia - vyote hiari (A/B/C/D/F kila kimoja)
    work_determination = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Bidii Kazini')
    class_attendance = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Uwepo Darasani')
    caring_for_resources = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Utunzaji wa Vifaa')
    keenness_in_class = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Umakini Darasani')
    cooperation = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Ushirikiano')
    respect = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Heshima')
    leadership = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Uongozi')
    self_discipline = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Nidhamu Binafsi')
    self_cleanliness = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Usafi Binafsi')
    work_consideration = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Kujituma Kazini')
    proactiveness = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Kujitolea/Ubunifu')
    sporting = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='Michezo')
    general_behavior = models.CharField(max_length=50, blank=True, null=True, verbose_name='Mwenendo kwa Ujumla', help_text='Mfano: GOOD, VERY GOOD')

    # Maoni ya maandishi - hiari
    class_teacher_remarks = models.TextField(blank=True, null=True, verbose_name='Maoni ya Mwalimu wa Darasa')
    headteacher_remarks = models.TextField(blank=True, null=True, verbose_name='Maoni ya Mkuu wa Shule')

    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'term', 'academic_year')
        indexes = [models.Index(fields=['school', 'student', 'term', 'academic_year'])]

    def has_any_data(self):
        """True kama Class Teacher amejaza angalau kitu kimoja."""
        conduct_fields = [
            self.work_determination, self.class_attendance, self.caring_for_resources,
            self.keenness_in_class, self.cooperation, self.respect, self.leadership,
            self.self_discipline, self.self_cleanliness, self.work_consideration,
            self.proactiveness, self.sporting, self.general_behavior,
            self.class_teacher_remarks, self.headteacher_remarks,
        ]
        return any(conduct_fields)

    def conduct_items(self):
        """Orodha ya (jina, alama) kwa vigezo vilivyojazwa TU - kwa template."""
        fields = [
            ('Bidii Kazini', self.work_determination), ('Uwepo Darasani', self.class_attendance),
            ('Utunzaji wa Vifaa', self.caring_for_resources), ('Umakini Darasani', self.keenness_in_class),
            ('Ushirikiano', self.cooperation), ('Heshima', self.respect), ('Uongozi', self.leadership),
            ('Nidhamu Binafsi', self.self_discipline), ('Usafi Binafsi', self.self_cleanliness),
            ('Kujituma Kazini', self.work_consideration), ('Kujitolea/Ubunifu', self.proactiveness),
            ('Michezo', self.sporting),
        ]
        return [(label, grade) for label, grade in fields if grade]

    def __str__(self):
        return f"Tabia ya {self.student} - {self.term} {self.academic_year}"
