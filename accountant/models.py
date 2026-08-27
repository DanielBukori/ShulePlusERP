"""
ACCOUNTANT MODELS - inaenda 'accountant/models.py'.
Payment model tayari ipo shule_core/models.py - HAIBADILIKI, tunaingiza tu.
"""
from django.db import models
from shule_core.models import School, SchoolClass, Student, CustomUser, Payment


class FeeStructure(models.Model):
    """
    Kiasi cha ada ya mwaka kwa darasa fulani. Headmaster/Second Master
    ndio wanaoweka hii - ni 'rate' tu, siyo deni la mwanafunzi bado.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_structures', db_index=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.IntegerField(default=2026, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'school_class', 'academic_year')

    def __str__(self):
        return f"{self.school_class} - {self.academic_year}: {self.amount}"


class OtherCharge(models.Model):
    """
    Michango mingine (mfano: Mahafali, Michezo). Headmaster/Second Master
    wanaweza kuweka moja kwa moja. Accountant anaweza kuweka TU akiwa
    ameelekezwa na Mkuu/Bodi - ndiyo maana 'authorized_by' ni lazima
    ikiwa aliyeunda ni Accountant.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='other_charges', db_index=True)
    name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='other_charges', help_text='Acha wazi kama ni shule nzima')
    academic_year = models.IntegerField(default=2026, db_index=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='charges_created')
    authorized_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='charges_authorized',
                                        help_text='Lazima ijazwe kama muundaji ni Accountant')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.amount} ({self.academic_year})"


class StudentFeeAssessment(models.Model):
    """
    'Invoice' ya mwaka mmoja kwa mwanafunzi mmoja - inatengenezwa (snapshot)
    kutoka FeeStructure + OtherCharge zilizopo wakati wa kuizalisha.
    HAIBADILIKI baadaye hata mwanafunzi akipanda darasa - ndiyo maana deni
    linaendelea kuonekana/kufuatiliwa mwaka hadi mwaka.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_assessments', db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_assessments', db_index=True)
    academic_year = models.IntegerField(db_index=True)
    school_class_at_time = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True)
    amount_required = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'academic_year')

    def __str__(self):
        return f"{self.student} - {self.academic_year}: {self.amount_required}"


def get_student_debt(student):
    """
    Deni la jumla la mwanafunzi (all-time, linalofuatana naye hadi
    anapopanda darasa): jumla ya tathmini zote - jumla ya malipo yote.
    """
    total_required = StudentFeeAssessment.objects.filter(student=student).aggregate(
        total=models.Sum('amount_required')
    )['total'] or 0
    total_paid = Payment.objects.filter(student=student).aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    return total_required - total_paid
