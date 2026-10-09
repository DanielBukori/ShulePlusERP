from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.db import transaction
from .models import *

# 1. KUREKEBISHA ADMIN YA USER WETU
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'school', 'phone', 'is_staff')
    list_filter = ('role', 'school', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'phone')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Taarifa za Shule', {'fields': ('role', 'school', 'phone')}),
        ('Usajili wa Shule', {'fields': ('school_registration_pending',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Taarifa za Shule', {'fields': ('role', 'school', 'phone')}),
        ('Usajili wa Shule', {'fields': ('school_registration_pending',)}),
    )

# 2. ADMIN YA SHULE
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_level', 'subdomain', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'school_level')
    search_fields = ('name', 'subdomain')
    prepopulated_fields = {'subdomain': ('name',)} # Itajaza subdomain yenyewe
    readonly_fields = ('is_approved',)
    actions = ('approve_pending_registrations',)

    @admin.action(description='Approve selected pending school registrations')
    def approve_pending_registrations(self, request, queryset):
        approved = []
        skipped = []
        with transaction.atomic():
            for school in queryset.filter(is_approved=False).select_for_update():
                pending_owners = school.users.filter(
                    role='HEADMASTER',
                    school_registration_pending=True,
                    is_active=False,
                )
                if not pending_owners.exists():
                    skipped.append(school.name)
                    continue

                pending_owners.update(
                    is_active=True,
                    school_registration_pending=False,
                )
                school.is_approved = True
                school.save(update_fields=('is_approved',))
                approved.append(school.name)

        if approved:
            self.message_user(
                request,
                f"Shule zimeidhinishwa na akaunti za wakuu zimewezeshwa: {', '.join(approved)}.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Hazijaidhinishwa kwa kuwa akaunti ya mwombaji haipo au tayari imewezeshwa: {', '.join(skipped)}.",
                level=messages.WARNING,
            )

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
