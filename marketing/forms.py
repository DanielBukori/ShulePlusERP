from django import forms
from .models import DemoRequest

TW = 'w-full border border-gray-300 rounded px-3 py-2.5 text-sm'


class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = ['school_name', 'contact_name', 'phone', 'email', 'student_count', 'message']
        labels = {
            'school_name': 'Jina la Shule',
            'contact_name': 'Jina Lako',
            'phone': 'Namba ya Simu',
            'email': 'Barua Pepe (hiari)',
            'student_count': 'Idadi ya Wanafunzi (takriban)',
            'message': 'Ujumbe (hiari)',
        }
        widgets = {
            'school_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Mwanga Secondary School'}),
            'contact_name': forms.TextInput(attrs={'class': TW}),
            'phone': forms.TextInput(attrs={'class': TW, 'placeholder': '07XXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': TW}),
            'student_count': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: 300-800'}),
            'message': forms.Textarea(attrs={'class': TW, 'rows': 3}),
        }
