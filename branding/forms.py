from django import forms
from .models import (
    SchoolProfile, BrandingPost, LeadershipMember, AcademicProgram,
    Facility, Testimonial, AdmissionInquiry,
)

TW = 'border border-gray-300 rounded px-3 py-2 text-sm w-full'


class SchoolProfileForm(forms.ModelForm):
    class Meta:
        model = SchoolProfile
        fields = ['motto', 'about_text', 'mission', 'vision', 'contact_email', 'contact_phone',
                  'cover_image', 'facebook_url', 'instagram_url', 'primary_color', 'accent_color']
        labels = {
            'motto': 'Kaulimbiu (Motto)',
            'about_text': 'Kuhusu Shule (About)',
            'mission': 'Dhamira (Mission)',
            'vision': 'Dira (Vision)',
            'contact_email': 'Barua Pepe ya Mawasiliano',
            'contact_phone': 'Simu ya Mawasiliano',
            'cover_image': 'Picha Kuu ya Tovuti',
            'facebook_url': 'Facebook (hiari)',
            'instagram_url': 'Instagram (hiari)',
            'primary_color': 'Rangi Kuu ya Brand (hiari)',
            'accent_color': 'Rangi ya Pili ya Brand (hiari)',
        }
        widgets = {
            'motto': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Elimu Bora, Malezi Bora'}),
            'about_text': forms.Textarea(attrs={'class': TW, 'rows': 5}),
            'mission': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'vision': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'contact_email': forms.EmailInput(attrs={'class': TW}),
            'contact_phone': forms.TextInput(attrs={'class': TW}),
            'facebook_url': forms.URLInput(attrs={'class': TW}),
            'instagram_url': forms.URLInput(attrs={'class': TW}),
            'primary_color': forms.TextInput(attrs={'class': TW, 'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'class': TW, 'type': 'color'}),
        }


class BrandingPostForm(forms.ModelForm):
    class Meta:
        model = BrandingPost
        fields = ['category', 'title', 'body', 'image', 'is_published']
        labels = {
            'category': 'Aina ya Chapisho',
            'title': 'Kichwa cha Habari',
            'body': 'Maudhui',
            'image': 'Picha Kuu (hiari)',
            'is_published': 'Ionekane Papo Hapo Tovuti',
        }
        widgets = {
            'category': forms.Select(attrs={'class': TW}),
            'title': forms.TextInput(attrs={'class': TW}),
            'body': forms.Textarea(attrs={'class': TW, 'rows': 6}),
        }


class LeadershipMemberForm(forms.ModelForm):
    class Meta:
        model = LeadershipMember
        fields = ['full_name', 'role_title', 'photo', 'bio', 'order', 'is_published']
        labels = {
            'full_name': 'Jina Kamili', 'role_title': 'Cheo', 'photo': 'Picha',
            'bio': 'Wasifu Mfupi', 'order': 'Mpangilio (namba ndogo kwanza)',
            'is_published': 'Ionekane Papo Hapo Tovuti',
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'class': TW}),
            'role_title': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Mkuu wa Shule'}),
            'bio': forms.Textarea(attrs={'class': TW, 'rows': 4}),
            'order': forms.NumberInput(attrs={'class': TW}),
        }


class AcademicProgramForm(forms.ModelForm):
    class Meta:
        model = AcademicProgram
        fields = ['level', 'name', 'description', 'requirements', 'order', 'is_published']
        labels = {
            'level': 'Ngazi', 'name': 'Jina la Programu/Mchepuo',
            'description': 'Maelezo', 'requirements': 'Masharti ya Kujiunga',
            'order': 'Mpangilio', 'is_published': 'Ionekane Papo Hapo Tovuti',
        }
        widgets = {
            'level': forms.Select(attrs={'class': TW}),
            'name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Sayansi (PCB)'}),
            'description': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'requirements': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': TW}),
        }


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'icon', 'description', 'image', 'order', 'is_published']
        labels = {
            'name': 'Jina la Kifaa/Sehemu', 'icon': 'Emoji (hiari)', 'description': 'Maelezo',
            'image': 'Picha', 'order': 'Mpangilio', 'is_published': 'Ionekane Papo Hapo Tovuti',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Maabara ya Kemia'}),
            'icon': forms.TextInput(attrs={'class': TW, 'placeholder': '🔬'}),
            'description': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': TW}),
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['author_name', 'author_role', 'quote', 'photo', 'order', 'is_published']
        labels = {
            'author_name': 'Jina la Mtoa Maoni', 'author_role': 'Uhusiano na Shule',
            'quote': 'Maoni', 'photo': 'Picha (hiari)', 'order': 'Mpangilio',
            'is_published': 'Ionekane Papo Hapo Tovuti',
        }
        widgets = {
            'author_name': forms.TextInput(attrs={'class': TW}),
            'author_role': forms.Select(attrs={'class': TW}),
            'quote': forms.Textarea(attrs={'class': TW, 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': TW}),
        }


class AdmissionInquiryForm(forms.ModelForm):
    class Meta:
        model = AdmissionInquiry
        fields = ['student_name', 'parent_name', 'phone', 'email', 'class_interested', 'message']
        labels = {
            'student_name': 'Jina la Mwanafunzi', 'parent_name': 'Jina la Mzazi/Mlezi',
            'phone': 'Namba ya Simu', 'email': 'Barua Pepe (hiari)',
            'class_interested': 'Darasa Analotaka Kujiunga', 'message': 'Ujumbe (hiari)',
        }
        widgets = {
            'student_name': forms.TextInput(attrs={'class': TW}),
            'parent_name': forms.TextInput(attrs={'class': TW}),
            'phone': forms.TextInput(attrs={'class': TW, 'placeholder': '07XXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': TW}),
            'class_interested': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Form One 2027'}),
            'message': forms.Textarea(attrs={'class': TW, 'rows': 3}),
        }
