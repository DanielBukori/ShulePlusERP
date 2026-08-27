from django import forms
from django.core.exceptions import ValidationError
from shule_core.models import SchoolClass, Subject, AcademicResult, Student, Combination


# Muhula gani unaruhusu 'matokeo yaliyokamilika' gani (kwa ajili ya
# validation). Hizi ni COMPUTED exam types pekee - mwalimu hajazai hizi
# moja kwa moja, mfumo unazihesabu (angalia academic/grading.py).
# Raw components (Test1_A, Test2_A, n.k.) zinajazwa na mwalimu kwenye
# teacher_portal, siyo hapa kwenye broadsheet/publish.
TERM_EXAM_MAP = {
    'TERM_1': ['MID_TERM', 'TERMINAL'],
    'TERM_2': ['MID_TERM', 'ANNUAL'],
}

# Broadsheet na 'Chapisha Matokeo' zinaonyesha matokeo yaliyokamilika
# (computed) pekee - siyo raw components za CA.
EXAM_CHOICES = [
    ('MID_TERM', 'Mid-Term (Kikokotolewa)'),
    ('TERMINAL', 'Terminal (Kikokotolewa)'),
    ('ANNUAL', 'Annual (Kikokotolewa)'),
]


class ResultFilterForm(forms.Form):
    """
    Fomu ya kuchuja matokeo: kuchagua Mtihani, Darasa, na Muhula
    ili mfumo uonyeshe ripoti husika (class-wise results).
    """
    LEVEL_CHOICES = [
        ('O', 'O-Level (Form I - IV)'),
        ('A', 'A-Level (Form V - VI)'),
    ]

    education_level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Kiwango cha Elimu',
    )
    term = forms.ChoiceField(
        choices=AcademicResult.TERM_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Muhula (Term)',
    )
    exam_type = forms.ChoiceField(
        choices=EXAM_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Aina ya Mtihani',
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Darasa',
    )
    academic_year = forms.IntegerField(
        min_value=2020,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'placeholder': 'Mfano: 2026'}),
        label='Mwaka wa Masomo',
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school_class'].required = False  # haitumiki kwenye logic - class_id inatoka URL
        if school:
            # Punguza madarasa yawe ya shule hii pekee
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)

    def clean(self):
        cleaned = super().clean()
        term = cleaned.get('term')
        exam_type = cleaned.get('exam_type')

        if term and exam_type:
            ruhusiwa = TERM_EXAM_MAP.get(term, [])
            if exam_type not in ruhusiwa:
                jina_mtihani = dict(AcademicResult.EXAM_TYPE_CHOICES).get(exam_type)
                jina_muhula = dict(AcademicResult.TERM_CHOICES).get(term)
                self.add_error(
                    'exam_type',
                    f"'{jina_mtihani}' haipo kwenye '{jina_muhula}'. Chagua tena."
                )
        return cleaned


class SubjectScoreFilterForm(forms.Form):
    """
    Fomu ya kuchagua somo mahususi kwa ajili ya kuona ufaulu
    wa Subject-wise (jinsi somo hilo lilivyofanya kwa wanafunzi wote).
    """
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Somo',
    )
    term = forms.ChoiceField(
        choices=AcademicResult.TERM_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Muhula (Term)',
    )
    exam_type = forms.ChoiceField(
        choices=EXAM_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Aina ya Mtihani',
    )
    academic_year = forms.IntegerField(
        min_value=2020,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'placeholder': 'Mfano: 2026'}),
        label='Mwaka wa Masomo',
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            # Punguza masomo yawe ya shule hii pekee
            self.fields['subject'].queryset = Subject.objects.filter(school=school)

    def clean(self):
        cleaned = super().clean()
        term = cleaned.get('term')
        exam_type = cleaned.get('exam_type')

        if term and exam_type:
            ruhusiwa = TERM_EXAM_MAP.get(term, [])
            if exam_type not in ruhusiwa:
                jina_muhula = dict(AcademicResult.TERM_CHOICES).get(term)
                self.add_error(
                    'exam_type',
                    f"Mtihani huu haupo kwenye '{jina_muhula}'. Chagua tena."
                )
        return cleaned


class ReportPublishForm(forms.Form):
    """
    Fomu inayomruhusu Academic Master 'kufungua' (publish) matokeo
    ya darasa zima kwa mtihani fulani ili yaonekane kwa wazazi na wanafunzi.

    Muhimu: Fomu hii haihifadhi kwenye model moja kwa moja. View itakayoitumia
    itachukua vigezo hivi (school_class + term + exam_type + academic_year),
    kutafuta AcademicResult zote zinazolingana, na kuzibadilisha status yake
    kuwa 'zimechapishwa'. Kwa hilo kufanya kazi vizuri, AcademicResult model
    inahitaji field ya ziada, mfano: is_published = models.BooleanField(default=False).
    """
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Darasa',
    )
    term = forms.ChoiceField(
        choices=AcademicResult.TERM_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Muhula (Term)',
    )
    exam_type = forms.ChoiceField(
        choices=EXAM_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Aina ya Mtihani',
    )
    academic_year = forms.IntegerField(
        min_value=2020,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'placeholder': 'Mfano: 2026'}),
        label='Mwaka wa Masomo',
    )
    confirm = forms.BooleanField(
        required=True,
        label='Nathibitisha kutuma matokeo haya kwa wazazi na wanafunzi',
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 accent-navy2'}),
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)

    def clean(self):
        cleaned = super().clean()
        term = cleaned.get('term')
        exam_type = cleaned.get('exam_type')

        if term and exam_type:
            ruhusiwa = TERM_EXAM_MAP.get(term, [])
            if exam_type not in ruhusiwa:
                jina_muhula = dict(AcademicResult.TERM_CHOICES).get(term)
                self.add_error(
                    'exam_type',
                    f"Mtihani huu haupo kwenye '{jina_muhula}'. Chagua tena."
                )
        return cleaned


class LeveledClassSelect(forms.Select):
    """
    Select ya school_class ambayo inaweka data-level="O"/"A" kwenye kila
    option, ili JavaScript iweze kuonyesha/kuficha Combination bila
    kuhitaji ombi jipya kwa server.
    """
    def __init__(self, *args, level_map=None, **kwargs):
        self.level_map = level_map or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        key = str(value.value) if hasattr(value, 'value') else str(value)
        if key in self.level_map:
            option['attrs']['data-level'] = self.level_map[key]
        return option


class StudentRegistrationForm(forms.ModelForm):
    """
    Fomu ya kusajili mwanafunzi. Combination ni lazima kwa A-Level na
    haitakiwi kwa O-Level - validation inafanyika kwenye clean().
    Akaunti za CustomUser (mwanafunzi + mzazi) zinatengenezwa kwenye view,
    siyo hapa kwenye form.
    """
    class Meta:
        model = Student
        fields = [
            'first_name', 'middle_name', 'last_name', 'reg_number',
            'school_class', 'combination', 'parent_name', 'parent_phone',
        ]
        labels = {
            'first_name': 'Jina la Kwanza',
            'middle_name': 'Jina la Kati',
            'last_name': 'Jina la Mwisho',
            'reg_number': 'Reg Number',
            'school_class': 'Darasa',
            'combination': 'Combination (A-Level tu)',
            'parent_name': 'Jina la Mzazi/Mlezi',
            'parent_phone': 'Simu ya Mzazi/Mlezi',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'middle_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'reg_number': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'parent_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'parent_phone': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'placeholder': '07XXXXXXXX'}),
            'combination': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        self.fields['combination'].required = False

        if school:
            classes = SchoolClass.objects.filter(school=school)
            level_map = {str(c.pk): c.level for c in classes}
            # MUHIMU: widget lazima iwekwe KABLA ya queryset - kwa sababu
            # kuweka .queryset kunatuma 'choices' moja kwa moja kwenye
            # widget iliyopo WAKATI HUO (self.widget.choices = ...).
            # Ukiweka queryset kwanza kisha ukabadilisha widget, choices
            # zinabaki kwenye widget ya ZAMANI iliyofutwa, na widget mpya
            # (LeveledClassSelect) inabaki na choices=() tupu - dropdown
            # inaonekana tupu kabisa hata kama madarasa yapo.
            self.fields['school_class'].widget = LeveledClassSelect(
                level_map=level_map,
                attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'id': 'id_school_class'},
            )
            self.fields['school_class'].queryset = classes
            self.fields['combination'].queryset = Combination.objects.all()
            self.fields['combination'].widget.attrs.update({'id': 'id_combination'})

    def clean_parent_phone(self):
        phone = self.cleaned_data['parent_phone']
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) < 9:
            raise ValidationError('Namba ya simu ya mzazi si sahihi (angalau tarakimu 9).')
        return phone

    def clean(self):
        cleaned = super().clean()
        school_class = cleaned.get('school_class')
        combination = cleaned.get('combination')
        reg_number = cleaned.get('reg_number')

        if school_class:
            if school_class.level == 'A' and not combination:
                self.add_error('combination', 'Mwanafunzi wa A-Level lazima awe na Combination.')
            if school_class.level == 'O' and combination:
                self.add_error('combination', 'Mwanafunzi wa O-Level hapaswi kuwa na Combination.')

            # Reg Number ni ya kipekee KWA DARASA (siyo shule nzima) - reg
            # number "0001" inaweza kutumika Form One NA Form Two wakati
            # mmoja, mradi ni darasa tofauti.
            if reg_number and self.school and Student.objects.filter(
                school=self.school, school_class=school_class, reg_number=reg_number
            ).exists():
                self.add_error(
                    'reg_number',
                    f"Reg Number '{reg_number}' tayari ipo kwenye darasa la {school_class}."
                )
        return cleaned
