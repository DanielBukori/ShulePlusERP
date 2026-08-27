from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# 1. KUREKEBISHA ADMIN YA USER WETU
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'school', 'phone', 'is_staff')
    list_filter = ('role', 'school', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'phone')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Taarifa za Shule', {'fields': ('role', 'school', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Taarifa za Shule', {'fields': ('role', 'school', 'phone')}),
    )

# 2. ADMIN YA SHULE
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_level', 'subdomain', 'created_at')
    search_fields = ('name', 'subdomain')
    prepopulated_fields = {'subdomain': ('name',)} # Itajaza subdomain yenyewe

# 3. ADMIN YA MADARASA, MASOMO, COMBINATION
@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'stream', 'level', 'school')
    list_filter = ('school', 'level', 'stream')
    search_fields = ('name',)

@admin.register(Combination)
class CombinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'level', 'combination', 'school')
    list_filter = ('school', 'level')
    search_fields = ('name', 'code')

# 4. ADMIN YA MWANAFUNZI NA STAFF
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('reg_number', 'full_name', 'school_class', 'school', 'parent_phone')
    list_filter = ('school', 'school_class', 'combination')
    search_fields = ('reg_number', 'first_name', 'last_name', 'parent_phone')
    
    def full_name(self, obj):
        return obj.__str__()
    full_name.short_description = 'Jina Kamili'

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'tsc_number', 'is_teaching_staff')
    list_filter = ('school', 'is_teaching_staff')
    search_fields = ('user__username', 'tsc_number')

# 5. ADMIN YA ALAMA NA MALIPO
@admin.register(SubjectAssignment)
class SubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class', 'academic_year')
    list_filter = ('school', 'academic_year')

@admin.register(AcademicResult)
class AcademicResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'score', 'grade', 'exam_type', 'term', 'academic_year')
    list_filter = ('school', 'term', 'exam_type', 'academic_year')
    search_fields = ('student__reg_number',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'date_paid', 'receipt_number', 'bank_name')
    list_filter = ('school', 'bank_name', 'date_paid')
    search_fields = ('student__reg_number', 'receipt_number')

