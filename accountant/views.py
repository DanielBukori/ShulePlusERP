from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models as dj_models
from django.db import transaction
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404

from shule_core.models import Student, Payment
from .forms import FeeStructureForm, OtherChargeForm, PaymentForm
from .models import FeeStructure, OtherCharge, StudentFeeAssessment, get_student_debt


ACCOUNTANT_ROLES = ['HEADMASTER', 'SECOND_MASTER', 'ACCOUNTANT']
FEE_MANAGER_ROLES = ['HEADMASTER', 'SECOND_MASTER']


def _get_school(request):
    return getattr(request, 'school', None)


def fee_manager_required(view_func):
    """Kuweka FeeStructure ni Headmaster/Second Master pekee."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in FEE_MANAGER_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def accountant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ACCOUNTANT_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


from notifications.utils import notify
from audit.utils import log_action


def _notify_payment_recorded(payment):
    """Bell + SMS kwa mzazi baada ya malipo kurekodiwa, ikionyesha deni lililobaki."""
    remaining = get_student_debt(payment.student)
    if payment.student.parent:
        message = (
            f"ShulePlusERP: Umefanikiwa kulipa TZS {payment.amount} kwa {payment.student}. "
            f"Deni lililobaki: TZS {remaining}."
        )
        notify(payment.student.parent, payment.school, message, link='/family/parent/dashboard/')


@fee_manager_required
def set_fee_structure_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, school=school)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.school = school
            fee.created_by = request.user
            fee.save()
            log_action(
                request.user, school, 'FEE_STRUCTURE_SET',
                f"Ameweka ada ya {fee.school_class} ({fee.academic_year}): TZS {fee.amount}."
            )
            messages.success(request, f"Ada ya {fee.school_class} ({fee.academic_year}) imewekwa: {fee.amount}.")
            return redirect('accountant:set_fee_structure')
    else:
        form = FeeStructureForm(school=school)

    fee_structures = FeeStructure.objects.filter(school=school).order_by('-academic_year', 'school_class__name')
    context = {'school': school, 'form': form, 'fee_structures': fee_structures}
    return render(request, 'accountant/set_fee_structure.html', context)


@accountant_required
def add_other_charge_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = OtherChargeForm(request.POST, school=school, creator_role=request.user.role)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.school = school
            charge.created_by = request.user
            if request.user.role in FEE_MANAGER_ROLES and not charge.authorized_by:
                charge.authorized_by = request.user
            charge.save()
            messages.success(request, f"Mchango '{charge.name}' umeongezwa.")
            return redirect('accountant:add_other_charge')
    else:
        form = OtherChargeForm(school=school, creator_role=request.user.role)

    charges = OtherCharge.objects.filter(school=school).order_by('-academic_year')
    context = {'school': school, 'form': form, 'charges': charges}
    return render(request, 'accountant/add_other_charge.html', context)


@fee_manager_required
def generate_assessments_view(request):
    """
    Inatengeneza StudentFeeAssessment (invoice) kwa kila mwanafunzi wa
    shule kwa mwaka uliochaguliwa, kwa kutumia FeeStructure + OtherCharge
    zilizopo wakati huo. Haiguzi wale ambao tayari wana assessment ya
    mwaka huo (ili isije ikaandika mara mbili).
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        academic_year = int(request.POST.get('academic_year'))
        created_count = 0
        skipped_no_fee = []

        with transaction.atomic():
            students = Student.objects.filter(school=school).select_related('school_class')
            for student in students:
                if StudentFeeAssessment.objects.filter(student=student, academic_year=academic_year).exists():
                    continue

                fee = FeeStructure.objects.filter(
                    school=school, school_class=student.school_class, academic_year=academic_year
                ).first()
                if not fee:
                    skipped_no_fee.append(str(student))
                    continue

                charges_total = OtherCharge.objects.filter(
                    school=school, academic_year=academic_year
                ).filter(
                    dj_models.Q(school_class=student.school_class) | dj_models.Q(school_class__isnull=True)
                ).aggregate(total=dj_models.Sum('amount'))['total'] or 0

                StudentFeeAssessment.objects.create(
                    school=school, student=student, academic_year=academic_year,
                    school_class_at_time=student.school_class,
                    amount_required=fee.amount + charges_total,
                )
                created_count += 1

        messages.success(request, f"Tathmini {created_count} zimetengenezwa kwa mwaka {academic_year}.")
        log_action(
            request.user, school, 'ASSESSMENTS_GENERATED',
            f"Ametengeneza tathmini {created_count} za ada kwa mwaka {academic_year}."
        )
        if skipped_no_fee:
            messages.warning(
                request,
                f"Wanafunzi {len(skipped_no_fee)} wameruka - hakuna FeeStructure ya darasa lao mwaka huu."
            )
        return redirect('accountant:generate_assessments')

    context = {'school': school}
    return render(request, 'accountant/generate_assessments.html', context)


@accountant_required
def accountant_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    students = Student.objects.filter(school=school).select_related('school_class')
    debtors = []
    total_outstanding = 0
    for s in students:
        debt = get_student_debt(s)
        if debt > 0:
            debtors.append({'student': s, 'debt': debt})
            total_outstanding += debt

    debtors.sort(key=lambda d: d['debt'], reverse=True)
    recent_payments = Payment.objects.filter(school=school).select_related('student').order_by('-created_at')[:10]

    context = {
        'school': school,
        'debtors': debtors,
        'total_outstanding': total_outstanding,
        'recent_payments': recent_payments,
    }
    return render(request, 'accountant/accountant_dashboard.html', context)


@accountant_required
def record_payment_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.school = school
            payment.recorded_by = request.user
            payment.save()

            remaining_debt = get_student_debt(payment.student)
            _notify_payment_recorded(payment)
            log_action(
                request.user, school, 'PAYMENT_RECORDED',
                f"Amerekodi malipo ya TZS {payment.amount} kwa {payment.student} "
                f"(risiti {payment.receipt_number})."
            )

            messages.success(
                request,
                f"Malipo ya {payment.student} ({payment.amount}) yamerekodiwa. "
                f"Deni lililobaki: {remaining_debt}."
            )
            return redirect('accountant:record_payment')
    else:
        form = PaymentForm(school=school)

    context = {'school': school, 'form': form}
    return render(request, 'accountant/record_payment.html', context)


@login_required
def view_receipt_view(request, payment_id):
    """
    Inaonyesha risiti ya malipo TU kwa: Accountant/Headmaster/Second
    Master, AU mzazi wa mwanafunzi husika mwenyewe. Faili haipo kwenye
    MEDIA_URL ya wazi - inapita hapa kila wakati.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    payment = get_object_or_404(Payment, id=payment_id, school=school)

    is_staff_allowed = request.user.role in ACCOUNTANT_ROLES
    is_owner_parent = request.user.role == 'PARENT' and payment.student.parent_id == request.user.id

    if not (is_staff_allowed or is_owner_parent):
        return HttpResponseForbidden("Hauruhusiwi kuona faili hii.")

    if not payment.receipt_file:
        raise Http404("Hakuna risiti iliyopakiwa kwa malipo haya.")

    filename = payment.receipt_file.name.split('/')[-1]
    return FileResponse(payment.receipt_file.open('rb'), filename=filename)
