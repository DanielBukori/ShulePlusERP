from django import forms
from .models import Attendance
from shule_core.models import ConductReport


class AttendanceDateForm(forms.Form):
    """Fomu ndogo ya kuchagua tarehe ya mahudhurio (default: leo)."""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none",
        })
    )


class StudentAttendanceForm(forms.Form):
    """
    Fomu ya mwanafunzi mmoja ndani ya orodha (formset-style manual).
    Tunatumia hii kujenga dropdown ya status kwa kila mwanafunzi kwenye template.
    """
    student_id = forms.IntegerField(widget=forms.HiddenInput())
    status = forms.ChoiceField(
        choices=Attendance.STATUS_CHOICES,
        widget=forms.Select(attrs={
            "class": "attendance-status border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none w-full",
        })
    )
# === 1. Ongeza kwenye IMPORTS za juu ya attendance/forms.py ===


# === 2. Ongeza CLASS hii MWISHONI kabisa mwa attendance/forms.py ===

class ConductReportForm(forms.ModelForm):
    """Fomu ya Class Teacher kujaza tabia/mwenendo - kila field ni hiari."""

    GRADE_FIELDS = [
        'work_determination', 'class_attendance', 'caring_for_resources', 'keenness_in_class',
        'cooperation', 'respect', 'leadership', 'self_discipline', 'self_cleanliness',
        'work_consideration', 'proactiveness', 'sporting',
    ]

    class Meta:
        model = ConductReport
        fields = [
            'work_determination', 'class_attendance', 'caring_for_resources', 'keenness_in_class',
            'cooperation', 'respect', 'leadership', 'self_discipline', 'self_cleanliness',
            'work_consideration', 'proactiveness', 'sporting', 'general_behavior',
            'class_teacher_remarks', 'headteacher_remarks',
        ]
        widgets = {
            'work_determination': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'class_attendance': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'caring_for_resources': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'keenness_in_class': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'cooperation': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'respect': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'leadership': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'self_discipline': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'self_cleanliness': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'work_consideration': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'proactiveness': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'sporting': forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'}),
            'general_behavior': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full', 'placeholder': 'Mfano: GOOD'}),
            'class_teacher_remarks': forms.Textarea(attrs={
                'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full', 'rows': 3,
                'placeholder': 'Maoni ya Mwalimu wa Darasa (hiari)'}),
            'headteacher_remarks': forms.Textarea(attrs={
                'class': 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full', 'rows': 3,
                'placeholder': 'Maoni ya Mkuu wa Shule (hiari)'}),
        }
        labels = {
            'work_determination': 'Bidii Kazini', 'class_attendance': 'Uwepo Darasani',
            'caring_for_resources': 'Utunzaji wa Vifaa', 'keenness_in_class': 'Umakini Darasani',
            'cooperation': 'Ushirikiano', 'respect': 'Heshima', 'leadership': 'Uongozi',
            'self_discipline': 'Nidhamu Binafsi', 'self_cleanliness': 'Usafi Binafsi',
            'work_consideration': 'Kujituma Kazini', 'proactiveness': 'Kujitolea/Ubunifu',
            'sporting': 'Michezo', 'general_behavior': 'Mwenendo kwa Ujumla',
            'class_teacher_remarks': 'Maoni ya Mwalimu wa Darasa', 'headteacher_remarks': 'Maoni ya Mkuu wa Shule',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fields ZOTE ni hiari kabisa - Model ina blank=True/null=True, lakini
        # Django forms bado inaziona 'required' kidefault mpaka tuzime hapa.
        for f in self.fields.values():
            f.required = False
