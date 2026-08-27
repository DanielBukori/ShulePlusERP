from django import forms
from shule_core.models import SubjectAssignment, AcademicResult, Subject, SchoolClass, Combination
from .models import HomePackage

TW = 'border border-gray-300 rounded px-3 py-2 text-sm w-full'

# Raw exam types kwa kila muhula - hizi ndizo column za spreadsheet ya
# marks entry. MID_TERM/TERMINAL/ANNUAL ni COMPUTED (angalia academic/grading.py).
RAW_EXAM_TYPES_TERM_1 = [
    ('TEST_1_A', 'Test 1 (Robo I)'),
    ('TEST_2_A', 'Test 2 (Robo I)'),
    ('MID_TERM_EXAM', 'Mid-Term Exam'),
    ('TEST_1_B', 'Test 1 (Robo II)'),
    ('TEST_2_B', 'Test 2 (Robo II)'),
    ('TERMINAL_EXAM', 'Terminal Exam'),
]
RAW_EXAM_TYPES_TERM_2 = [
    ('TEST_1_A', 'Test 1 (Robo I)'),
    ('TEST_2_A', 'Test 2 (Robo I)'),
    ('MID_TERM_EXAM', 'Mid-Term Exam'),
    ('TEST_1_B', 'Test 1 (Robo II)'),
    ('TEST_2_B', 'Test 2 (Robo II)'),
    ('ANNUAL_EXAM', 'Annual Exam'),
]

# Mitihani ya Maandalizi (Series) - HIARI, kwa Form IV/VI kujiandaa na
# National Exam. Hizi ni column za ZIADA kwenye spreadsheet - HAZIINGII
# kwenye ukokotoaji wa MID_TERM/TERMINAL/ANNUAL (angalia academic/grading.py,
# haziguswi popote pale kwa makusudi). Ni taarifa ya maendeleo tu kwa wazazi.
SERIES_EXAM_TYPES = [
    ('SERIES_1', 'Series 1'),
    ('SERIES_2', 'Series 2'),
    ('SERIES_3', 'Series 3'),
    ('SERIES_4', 'Series 4'),
    ('SERIES_5', 'Series 5'),
]


class MarksFilterForm(forms.Form):
    """
    Mwalimu anachagua somo/darasa lake (kutoka SubjectAssignment zake
    mwenyewe tu) + term/year. HAKUNA exam_type - marks entry sasa ni
    spreadsheet moja yenye column zote za CA kwa pamoja.
    """
    assignment = forms.ModelChoiceField(
        queryset=SubjectAssignment.objects.none(),
        widget=forms.Select(attrs={'class': TW}),
        label='Somo / Darasa',
    )
    term = forms.ChoiceField(
        choices=AcademicResult.TERM_CHOICES,
        widget=forms.Select(attrs={'class': TW}),
        label='Muhula',
    )
    academic_year = forms.IntegerField(
        min_value=2020, max_value=2100, initial=2026,
        widget=forms.NumberInput(attrs={'class': TW}),
        label='Mwaka wa Masomo',
    )

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['assignment'].queryset = SubjectAssignment.objects.filter(
                teacher=teacher
            ).select_related('subject', 'school_class', 'combination')


class EmergencyMarksFilterForm(forms.Form):
    """
    Kwa Academic/Headmaster/Second Master TU - 'dharura' access ya
    kujaza marks za somo lolote/darasa lolote, hata kama hawajapangiwa
    somo hilo rasmi (SubjectAssignment).
    """
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.Select(attrs={'class': TW}),
        label='Somo',
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': TW}),
        label='Darasa',
    )
    combination = forms.ModelChoiceField(
        queryset=Combination.objects.all(), required=False,
        widget=forms.Select(attrs={'class': TW}),
        label='Combination (A-Level tu)',
    )
    term = forms.ChoiceField(
        choices=AcademicResult.TERM_CHOICES,
        widget=forms.Select(attrs={'class': TW}),
        label='Muhula',
    )
    academic_year = forms.IntegerField(
        min_value=2020, max_value=2100, initial=2026,
        widget=forms.NumberInput(attrs={'class': TW}),
        label='Mwaka wa Masomo',
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)


class StatsFilterForm(forms.Form):
    """Kwa subject_stats_view - hii bado inahitaji exam_type (raw AU computed)."""
    assignment = forms.ModelChoiceField(
        queryset=SubjectAssignment.objects.none(),
        widget=forms.Select(attrs={'class': TW}),
        label='Somo / Darasa',
    )
    exam_type = forms.ChoiceField(
        choices=RAW_EXAM_TYPES_TERM_1 + [
            ('MID_TERM', 'Mid-Term (Kikokotolewa)'),
            ('TERMINAL', 'Terminal (Kikokotolewa)'),
            ('ANNUAL', 'Annual (Kikokotolewa)'),
        ],
        widget=forms.Select(attrs={'class': TW}),
        label='Aina ya Matokeo',
    )
    term = forms.ChoiceField(
        choices=AcademicResult.TERM_CHOICES,
        widget=forms.Select(attrs={'class': TW}),
        label='Muhula',
    )
    academic_year = forms.IntegerField(
        min_value=2020, max_value=2100, initial=2026,
        widget=forms.NumberInput(attrs={'class': TW}),
        label='Mwaka wa Masomo',
    )

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['assignment'].queryset = SubjectAssignment.objects.filter(
                teacher=teacher
            ).select_related('subject', 'school_class', 'combination')


class HomePackageForm(forms.ModelForm):
    class Meta:
        model = HomePackage
        fields = ['subject', 'school_class', 'term', 'academic_year', 'title', 'file']
        labels = {
            'subject': 'Somo',
            'school_class': 'Darasa',
            'term': 'Muhula',
            'academic_year': 'Mwaka wa Masomo',
            'title': 'Kichwa cha Kazi',
            'file': 'Faili (PDF/Word)',
        }
        widgets = {
            'subject': forms.Select(attrs={'class': TW}),
            'school_class': forms.Select(attrs={'class': TW}),
            'term': forms.Select(attrs={'class': TW}),
            'academic_year': forms.NumberInput(attrs={'class': TW}),
            'title': forms.TextInput(attrs={'class': TW}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            assignments = SubjectAssignment.objects.filter(teacher=teacher)
            subject_ids = assignments.values_list('subject_id', flat=True)
            class_ids = assignments.values_list('school_class_id', flat=True)
            self.fields['subject'].queryset = self.fields['subject'].queryset.model.objects.filter(id__in=subject_ids)
            self.fields['school_class'].queryset = self.fields['school_class'].queryset.model.objects.filter(id__in=class_ids)
