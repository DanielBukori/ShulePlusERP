"""
STORE MODELS
============
Hizi zinaenda kwenye 'store/models.py'. Zinaingiza (import) School, Student,
SchoolClass, CustomUser kutoka shule_core (chanzo cha models zote).

MUHIMU: pia ongeza field hii kwenye Staff model iliyopo shule_core/models.py:

    is_store_keeper = models.BooleanField(default=False)

(Store Keeper si role mpya - ni "duty flag" juu ya Mwalimu, kama
tulivyokubaliana.)
"""
from django.db import models
from shule_core.models import School, Student, SchoolClass, CustomUser
from shule_core.upload_paths import store_item_upload_path


class ContributionRequirement(models.Model):
    """
    Kile Academic/Second Master anachoweka: 'Muhula huu kila mwanafunzi
    analeta Ream 1, Omo 2, Mifagio 1'. Inaweza kuwa kwa darasa maalum
    (school_class) au shule nzima (school_class=None).
    """
    TERM_CHOICES = [('TERM_1', 'Muhula wa Kwanza'), ('TERM_2', 'Muhula wa Pili')]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='contribution_requirements', db_index=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='contribution_requirements',
                                       help_text='Acha wazi kama ni shule nzima')
    term = models.CharField(max_length=20, choices=TERM_CHOICES, db_index=True)
    academic_year = models.IntegerField(default=2026, db_index=True)
    item_name = models.CharField(max_length=100)  # mfano: Ream, Omo, Mfagio
    quantity_required = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'school_class', 'term', 'academic_year', 'item_name')
        indexes = [models.Index(fields=['school', 'term', 'academic_year'])]

    def __str__(self):
        target = self.school_class if self.school_class else 'Shule Nzima'
        return f"{self.item_name} x{self.quantity_required} - {target} ({self.term} {self.academic_year})"


class StudentContribution(models.Model):
    """
    Kile Store Keeper anachorekodi mwanafunzi akileta (mfano akirudi likizo).
    Deni linahesabiwa moja kwa moja: quantity_required - quantity_brought.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='student_contributions', db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='contributions', db_index=True)
    requirement = models.ForeignKey(ContributionRequirement, on_delete=models.CASCADE, related_name='records')
    quantity_brought = models.PositiveIntegerField(default=0)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    date_recorded = models.DateField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('student', 'requirement')
        indexes = [models.Index(fields=['school', 'student'])]

    @property
    def quantity_owed(self):
        owed = self.requirement.quantity_required - self.quantity_brought
        return max(owed, 0)

    @property
    def is_complete(self):
        return self.quantity_owed == 0

    def __str__(self):
        return f"{self.student} - {self.requirement.item_name}: {self.quantity_brought}/{self.requirement.quantity_required}"


class StoreStock(models.Model):
    """
    Jumla ya vifaa vilivyopo ghalani kwa sasa. Inaongezeka wanafunzi
    wanapoleta michango, na inapungua shule inapotumia.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='store_stock', db_index=True)
    item_name = models.CharField(max_length=100)
    quantity_in_stock = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    photo = models.ImageField(upload_to=store_item_upload_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('school', 'item_name')

    @property
    def is_low(self):
        return self.quantity_in_stock <= self.low_stock_threshold

    def __str__(self):
        return f"{self.item_name} - {self.quantity_in_stock} zilizopo ({self.school.name})"


class StockMovement(models.Model):
    """
    Historia ya kila mabadiliko ya stock - hii ndio 'audit trail' ya Store
    yenyewe: nani ameongeza/ametoa nini, lini, na kwa sababu gani.
    """
    REASON_CHOICES = [
        ('STUDENT_CONTRIBUTION', 'Mchango wa Mwanafunzi'),
        ('SCHOOL_USE', 'Matumizi ya Shule'),
        ('PURCHASE', 'Ununuzi'),
        ('ADJUSTMENT', 'Marekebisho'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='stock_movements', db_index=True)
    stock = models.ForeignKey(StoreStock, on_delete=models.CASCADE, related_name='movements')
    quantity_change = models.IntegerField(help_text='Chanya (+) kwa kuongeza, hasi (-) kwa kutoa')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['school', 'stock', 'created_at'])]

    def __str__(self):
        sign = '+' if self.quantity_change >= 0 else ''
        return f"{self.stock.item_name} {sign}{self.quantity_change} ({self.get_reason_display()})"
