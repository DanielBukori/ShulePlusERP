from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from accountant.forms import PaymentForm
from accountant.models import StudentFeeAssessment, get_student_debts
from shule_core.models import Payment, School, Student


class SchoolScopedPaymentFormTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.school = School.objects.create(
            name='Payment School One',
            subdomain='paymentschoolone',
            email='paymentschoolone@example.com',
            phone='255700000041',
        )
        self.other_school = School.objects.create(
            name='Payment School Two',
            subdomain='paymentschooltwo',
            email='paymentschooltwo@example.com',
            phone='255700000042',
        )
        self.student = self.create_student(self.school, 'PAY001')
        self.other_student = self.create_student(self.other_school, 'PAY002')

    def create_student(self, school, reg_number):
        return Student.objects.create(
            school=school,
            first_name='Test',
            last_name='Student',
            reg_number=reg_number,
            parent_name='Parent',
            parent_phone='255700000043',
        )

    def payment_data(self, student, receipt_number):
        return {
            'student': student.pk,
            'amount': '10000.00',
            'date_paid': timezone.localdate().isoformat(),
            'bank_name': 'Test Bank',
            'receipt_number': receipt_number,
        }

    def receipt_file(self):
        return SimpleUploadedFile('receipt.png', b'receipt bytes', content_type='image/png')

    def test_payment_form_limits_students_and_receipt_numbers_to_current_school(self):
        Payment.objects.create(
            school=self.school,
            student=self.student,
            amount='10000.00',
            date_paid=timezone.localdate(),
            bank_name='Test Bank',
            receipt_number='SHARED-001',
            receipt_file=self.receipt_file(),
        )

        other_school_form = PaymentForm(
            self.payment_data(self.other_student, 'SHARED-001'),
            {'receipt_file': self.receipt_file()},
            school=self.other_school,
        )
        same_school_duplicate = PaymentForm(
            self.payment_data(self.student, 'SHARED-001'),
            {'receipt_file': self.receipt_file()},
            school=self.school,
        )

        self.assertEqual(list(other_school_form.fields['student'].queryset), [self.other_student])
        self.assertTrue(other_school_form.is_valid(), other_school_form.errors)
        self.assertFalse(same_school_duplicate.is_valid())
        self.assertIn('receipt_number', same_school_duplicate.errors)

    def test_bulk_debt_lookup_aggregates_once_per_model_and_scopes_school(self):
        StudentFeeAssessment.objects.create(
            school=self.school,
            student=self.student,
            academic_year=2026,
            amount_required='50000.00',
        )
        Payment.objects.create(
            school=self.school,
            student=self.student,
            amount='15000.00',
            date_paid=timezone.localdate(),
            bank_name='Test Bank',
            receipt_number='SCHOOL-001',
        )
        Payment.objects.create(
            school=self.other_school,
            student=self.other_student,
            amount='100000.00',
            date_paid=timezone.localdate(),
            bank_name='Test Bank',
            receipt_number='SCHOOL-002',
        )

        with self.assertNumQueries(2):
            debts = get_student_debts([self.student.pk, self.other_student.pk])

        self.assertEqual(debts, {self.student.pk: 35000, self.other_student.pk: -100000})
