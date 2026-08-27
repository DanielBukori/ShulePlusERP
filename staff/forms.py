from django import forms
from django.core.exceptions import ValidationError
from shule_core.models import Staff, Subject, SchoolClass, Combination, SubjectAssignment, CustomUser


class TeacherRegistrationForm(forms.Form):
    """
    Taarifa za msingi za mfanyakazi (mwalimu au cheo kingine). Account
    (CustomUser) na Staff profile zinatengenezwa kwenye view - form hii
    ni ya taarifa tu.
    """
    # Cheo anachopewa mfanyakazi huyu. HEADMASTER haipo hapa kwa makusudi -
    # shule ina Mkuu mmoja tu, na huyo huwa amesajiliwa wakati wa
    # kusajili shule (register_school), siyo hapa.
    STAFF_ROLE_CHOICES = [
        ('TEACHER', 'Mwalimu'),
        ('ACADEMIC', 'Academic Master'),
        ('SECOND_MASTER', 'Second Master'),
        ('DISCIPLINE', 'Mwalimu wa Nidhamu'),
        ('ACCOUNTANT', 'Mhasibu'),
    ]

    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, label='Cheo',
                              widget=forms.Select(attrs={'class': 'form-select'}))
    first_name = forms.CharField(max_length=50, label='Jina la Kwanza', 
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jina la kwanza'}))
    last_name = forms.CharField(max_length=50, label='Jina la Mwisho', 
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jina la mwisho'}))
    phone = forms.CharField(max_length=15, label='Namba ya Simu (itakuwa username)',
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXX'}))
    tsc_number = forms.CharField(max_length=50, required=False, label='Namba ya TSC (hiari)',
                                  widget=forms.TextInput(attrs={'class': 'form-control',  'placeholder': 'Namba ya TSC'}))
    email = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email yako'}))

    qualification = forms.CharField(max_length=100, required=False, label='Taaluma (Diploma/Degree)', 
                                     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Diploma/Degree'}))
    is_store_keeper = forms.BooleanField(required=False, label='Mteue kuwa Store Keeper')

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) < 9:
            raise ValidationError('Namba ya simu si sahihi (angalau tarakimu 9).')
        if self.school:
            username = f"{self.school.subdomain}{digits}"
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError('Mwalimu mwenye namba hii tayari yupo kwenye shule hii.')
        return phone

    def clean_tsc_number(self):
        tsc = self.cleaned_data.get('tsc_number')
        if tsc and Staff.objects.filter(tsc_number=tsc).exists():
            raise ValidationError('Namba hii ya TSC tayari imesajiliwa.')
        return tsc


class SubjectAssignmentForm(forms.ModelForm):
    """
    Kumpangia mwalimu somo + darasa moja. Inaitwa mara kadhaa (moja kwa
    kila somo/darasa anayofundisha mwalimu huyu).
    """
    class Meta:
        model = SubjectAssignment
        fields = ['subject', 'school_class', 'combination', 'academic_year']
        labels = {
            'subject': 'Somo',
            'school_class': 'Darasa',
            'combination': 'Combination (A-Level tu)',
            'academic_year': 'Mwaka wa Masomo',
        }
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'combination': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['combination'].required = False
        if school:
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['combination'].queryset = Combination.objects.all()
