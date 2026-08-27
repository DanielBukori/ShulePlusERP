from django import forms
from .models import School, CustomUser


class SchoolRegistrationForm(forms.ModelForm):
    """
    Fomu ya kusajili SHULE MPYA kabisa kwenye mfumo (siyo mwanafunzi/mwalimu -
    hiyo iko kwenye academic/staff apps). Hii inaunda School + Headmaster
    wa kwanza wa shule hiyo.
    """
    headmaster_username = forms.CharField(
        label="Jina la Mtumiaji la Mkuu", max_length=150,
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
    )
    headmaster_password = forms.CharField(
        label="Nywila",
        widget=forms.PasswordInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
    )
    headmaster_phone = forms.CharField(
        label="Simu ya Mkuu", max_length=15,
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
    )
    headmaster_email = forms.EmailField(
        label="Barua Pepe ya Mkuu (kwa Magic Link ya kuingia)",
        widget=forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
    )

    class Meta:
        model = School
        fields = ['name', 'school_level', 'address', 'phone', 'email', 'logo', 'primary_color']
        labels = {
            'name': 'Jina la Shule',
            'school_level': 'Kiwango cha Shule',
            'address': 'Anwani',
            'phone': 'Simu ya Shule',
            'email': 'Email ya Shule',
            'logo': 'Logo ya Shule',
            'primary_color': 'Rangi ya Shule',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'school_level': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'address': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'value': '#0F3460'}),
        }

    def clean_headmaster_username(self):
        username = self.cleaned_data['headmaster_username']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Jina hili la mtumiaji tayari limetumika.')
        return username
