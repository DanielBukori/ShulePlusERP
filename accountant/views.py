from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models as dj_models
from django.db import transaction
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from shule_core.models import Student, Payment
from .forms import FeeStructureForm, OtherChargeForm, PaymentForm, PaymentSpreadsheetFilterForm
from .models import (
    FeeStructure,
    OtherCharge,
    StudentFeeAssessment,
    get_student_debt,
    get_student_debts,
)


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
    Inatengeneza (au KUSASISHA) StudentFeeAssessment (invoice) kwa kila
    mwanafunzi wa shule kwa mwaka uliochaguliwa, kwa kutumia FeeStructure
    + OtherCharge za SASA HIVI. Tofauti na awali: SASA hairuki wanafunzi
    wenye assessment iliyopo tayari - inai-SASISHA (update_or_create) ili
    kiasi kiendane na Fee Structure/Michango vya sasa. Hii inaruhusu
    Headmaster kubonyeza 'Tengeneza Tathmini' tena baada ya kuongeza
    Mahafali/kubadilisha ada, bila kuhofia 'imeruka kwa sababu ipo tayari'.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        academic_year = int(request.POST.get('academic_year'))
        created_count = 0
        updated_count = 0
        skipped_no_fee = []

        with transaction.atomic():
            students = Student.objects.filter(school=school).select_related('school_class')
            for student in students:
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

                _, created = StudentFeeAssessment.objects.update_or_create(
                    student=student, academic_year=academic_year,
                    defaults={
                        'school': school,
                        'school_class_at_time': student.school_class,
                        'amount_required': fee.amount + charges_total,
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        messages.success(
            request,
            f"Tathmini mpya {created_count} zimetengenezwa, na {updated_count} zilizokuwepo zimesasishwa "
            f"kwa mwaka {academic_year}."
        )
        log_action(
            request.user, school, 'ASSESSMENTS_GENERATED',
            f"Ametengeneza/kusasisha tathmini za ada kwa mwaka {academic_year} "
            f"(mpya: {created_count}, zilizosasishwa: {updated_count})."
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
def full_report_view(request):
    """
    Ripoti KAMILI ya fedha - inaonekana kwa Accountant, Headmaster, na
    Second Master wote. Inaonyesha kwa mwaka mmoja: Fee Structure zote
    zilizowekwa, Michango Mingine (Other Charges) zote, muhtasari wa
    fedha (zinazotakiwa/zilizokusanywa/zinazobaki), na orodha kamili ya
    wanafunzi wenye deni - kila kitu mahali pamoja.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    academic_year = int(request.GET.get('academic_year') or timezone.now().year)

    fee_structures = FeeStructure.objects.filter(
        school=school, academic_year=academic_year
    ).select_related('school_class').order_by('school_class__name')

    other_charges = OtherCharge.objects.filter(
        school=school, academic_year=academic_year
    ).select_related('school_class', 'authorized_by').order_by('school_class__name', 'name')

    assessments = StudentFeeAssessment.objects.filter(
        school=school, academic_year=academic_year
    ).select_related('student', 'school_class_at_time')

    total_required = assessments.aggregate(total=dj_models.Sum('amount_required'))['total'] or 0
    total_assessed_students = assessments.count()

    all_payments_total = Payment.objects.filter(
        school=school, student__in=[a.student_id for a in assessments]
    ).aggregate(total=dj_models.Sum('amount'))['total'] or 0

    paid_by_student = dict(
        Payment.objects.filter(
            school=school,
            student_id__in=assessments.values('student_id'),
        )
        .values('student_id')
        .annotate(total=dj_models.Sum('amount'))
        .values_list('student_id', 'total')
    )
    debtor_rows = []
    for a in assessments:
        paid = paid_by_student.get(a.student_id, 0)
        debt = a.amount_required - paid
        if debt > 0:
            debtor_rows.append({
                'student': a.student, 'school_class': a.school_class_at_time,
                'required': a.amount_required, 'paid': paid, 'debt': debt,
            })
    debtor_rows.sort(key=lambda r: r['debt'], reverse=True)

    context = {
        'school': school,
        'academic_year': academic_year,
        'fee_structures': fee_structures,
        'other_charges': other_charges,
        'total_required': total_required,
        'total_collected': all_payments_total,
        'total_outstanding': total_required - all_payments_total,
        'total_assessed_students': total_assessed_students,
        'debtor_rows': debtor_rows,
    }
    return render(request, 'accountant/full_report.html', context)


@accountant_required
def accountant_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    students = list(Student.objects.filter(school=school).select_related('school_class'))
    debts_by_student = get_student_debts(student.pk for student in students)
    debtors = []
    total_outstanding = 0
    for s in students:
        debt = debts_by_student[s.pk]
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


@accountant_required
def record_payment_spreadsheet_view(request):
    """
    Rekodi malipo kwa WINGI - kama Marks Entry: chagua Darasa + Mwaka,
    wanafunzi WOTE wanaonekana kwenye jedwali moja, na 'Hifadhi Malipo
    Yote' moja inarekodi malipo ya wote kwa pamoja.

    TOFAUTI na Marks Entry: hakuna 'Muhula' hapa - ada ni ya MWAKA
    MZIMA (FeeStructure ni ya mwaka, siyo muhula). Kila mstari una
    safu 4: Kiasi Kipya, Namba ya Risiti (LAZIMA, ya kipekee ndani ya
    shule), Benki, na Picha ya Risiti (hiari) - safu iliyoachwa bila
    Kiasi inarukwa.

    Kila malipo yanayotumwa hapa ni REKODI MPYA kabisa (ledger entry -
    kama Payment zote), YAANI hayabadilishi/kufuta malipo ya awali ya
    mwanafunzi - yanaongezeka juu yake (jumla inakokotolewa na
    get_student_debt kwa kujumlisha Payment zote).
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    filter_form = PaymentSpreadsheetFilterForm(request.GET or None, school=school)
    students = []
    school_class = None
    academic_year = None

    if filter_form.is_valid():
        school_class = filter_form.cleaned_data['school_class']
        academic_year = filter_form.cleaned_data['academic_year']

        student_qs = Student.objects.filter(school=school, school_class=school_class)
        student_list = list(student_qs)
        assessments_by_student = {
            assessment.student_id: assessment
            for assessment in StudentFeeAssessment.objects.filter(
                school=school,
                academic_year=academic_year,
                student_id__in=[student.pk for student in student_list],
            )
        }
        paid_by_student = dict(
            Payment.objects.filter(
                school=school,
                student_id__in=[student.pk for student in student_list],
            )
            .values('student_id')
            .annotate(total=dj_models.Sum('amount'))
            .values_list('student_id', 'total')
        )

        for s in student_list:
            assessment = assessments_by_student.get(s.pk)
            required = assessment.amount_required if assessment else 0
            paid_total = paid_by_student.get(s.pk, 0)
            students.append({
                'student': s,
                'required': required,
                'paid_total': paid_total,
                'remaining': required - paid_total,
            })

        if request.method == 'POST':
            saved_count = 0
            skipped_duplicate = []
            skipped_no_receipt = []

            with transaction.atomic():
                for s in student_list:
                    amount_raw = request.POST.get(f'amount_{s.id}', '').strip()
                    if not amount_raw:
                        continue
                    try:
                        amount_val = float(amount_raw)
                    except ValueError:
                        continue
                    if amount_val <= 0:
                        continue

                    receipt_no = request.POST.get(f'receipt_{s.id}', '').strip()
                    if not receipt_no:
                        skipped_no_receipt.append(str(s))
                        continue

                    if Payment.objects.filter(school=school, receipt_number=receipt_no).exists():
                        skipped_duplicate.append(f"{s} (risiti {receipt_no})")
                        continue

                    bank_name = request.POST.get(f'bank_{s.id}', '').strip()
                    receipt_file = request.FILES.get(f'receipt_file_{s.id}')

                    payment = Payment.objects.create(
                        school=school, student=s, amount=amount_val,
                        date_paid=timezone.now().date(),
                        bank_name=bank_name, receipt_number=receipt_no,
                        receipt_file=receipt_file,
                        recorded_by=request.user,
                    )
                    saved_count += 1
                    _notify_payment_recorded(payment)

            if saved_count:
                messages.success(request, f"Malipo {saved_count} yamerekodiwa kwa {school_class} ({academic_year}).")
                log_action(
                    request.user, school, 'PAYMENT_RECORDED',
                    f"[Spreadsheet] Amerekodi malipo {saved_count} - {school_class} ({academic_year})."
                )
            if skipped_no_receipt:
                messages.warning(
                    request,
                    f"Zimerukwa (hazina Namba ya Risiti): {', '.join(skipped_no_receipt)}."
                )
            if skipped_duplicate:
                messages.warning(
                    request,
                    f"Zimerukwa (namba za risiti zilizotumika tayari): {', '.join(skipped_duplicate)}."
                )
            return redirect(f"{request.path}?{request.GET.urlencode()}")

    context = {
        'school': school, 'filter_form': filter_form, 'students': students,
        'school_class': school_class, 'academic_year': academic_year,
    }
    return render(request, 'accountant/record_payment_spreadsheet.html', context)


@accountant_required
def student_debt_search_view(request):
    """
    Tafuta mwanafunzi kwa JINA (au reg_number) - inaonyesha TAARIFA ZAKE
    ZOTE za kifedha TANGU FORM ONE hadi sasa (miaka YOTE, siyo mwaka
    mmoja tu) - muhimu kwa mwanafunzi anayemaliza shule: kama ana deni
    lolote lililobaki kutoka mwaka wowote uliopita, litaonekana hapa
    hata kama halionekani kwenye Ripoti Kamili ya mwaka wa sasa.

    Payment (shule_core) haina 'academic_year' - ni ledger inayohusu
    mwanafunzi mzima maisha yake yote shuleni, siyo mwaka mmoja - kwa
    hiyo get_student_debt() tayari ni jumla ya miaka YOTE kiasili.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    query = request.GET.get('q', '').strip()
    student_id = request.GET.get('student_id')

    matches = Student.objects.none()
    if query:
        matches = Student.objects.filter(school=school).filter(
            dj_models.Q(first_name__icontains=query) |
            dj_models.Q(last_name__icontains=query) |
            dj_models.Q(reg_number__icontains=query)
        ).select_related('school_class').order_by('first_name', 'last_name')

    selected_student = None
    if student_id:
        selected_student = get_object_or_404(Student, id=student_id, school=school)
    elif query and matches.count() == 1:
        selected_student = matches.first()

    assessments = []
    payments = []
    total_required = 0
    total_paid = 0
    total_debt = 0

    if selected_student:
        assessments = StudentFeeAssessment.objects.filter(
            student=selected_student
        ).order_by('academic_year')
        payments = Payment.objects.filter(
            student=selected_student
        ).order_by('date_paid')

        total_required = assessments.aggregate(total=dj_models.Sum('amount_required'))['total'] or 0
        total_paid = payments.aggregate(total=dj_models.Sum('amount'))['total'] or 0
        total_debt = total_required - total_paid

    context = {
        'school': school,
        'query': query,
        'matches': matches,
        'selected_student': selected_student,
        'assessments': assessments,
        'payments': payments,
        'total_required': total_required,
        'total_paid': total_paid,
        'total_debt': total_debt,
    }
    return render(request, 'accountant/student_debt_search.html', context)


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
