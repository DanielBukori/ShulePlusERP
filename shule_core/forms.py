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
        fields = ['name', 'subdomain', 'sender_id', 'school_level', 'address', 'phone', 'email', 'logo', 'primary_color']
        labels = {
            'name': 'Jina la Shule',
            'subdomain': 'Subdomain (mfano: sehisco - acha wazi litazalishwa kiotomatiki kutoka jina)',
            'sender_id': 'Sender ID ya SMS (herufi/namba 11 - jina litakaloonekana kwa mzazi kwenye SMS)',
            'school_level': 'Kiwango cha Shule',
            'address': 'Anwani',
            'phone': 'Simu ya Shule',
            'email': 'Email ya Shule',
            'logo': 'Logo ya Shule',
            'primary_color': 'Rangi ya Shule',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'subdomain': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm', 'placeholder': 'mfano: sehisco'}),
            'sender_id': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm', 'maxlength': 11, 'placeholder': 'mfano: SEHISCO'}),
            'school_level': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'address': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'value': '#0F3460'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subdomain'].required = False
        self.fields['sender_id'].required = False

    def clean_subdomain(self):
        """
        Subdomain hutumika kwenye URL/DNS (mfano sehisco.shuleplus.co.tz) -
        lazima iwe herufi ndogo na namba TU, bila nafasi wala alama. Ukiacha
        wazi, School.save() itaizalisha kiotomatiki kutoka jina la shule.
        """
        subdomain = self.cleaned_data.get('subdomain', '').strip().lower()
        if subdomain and not subdomain.isalnum():
            raise forms.ValidationError(
                'Subdomain iwe herufi na namba tu, bila nafasi wala alama (mfano: sehisco, siyo sehisco-high).'
            )
        if subdomain and School.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError('Subdomain hii tayari inatumika na shule nyingine.')
        return subdomain

    def clean_headmaster_username(self):
        username = self.cleaned_data['headmaster_username']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Jina hili la mtumiaji tayari limetumika.')
        return username
