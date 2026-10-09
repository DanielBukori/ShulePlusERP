from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from shule_core.models import Student
from .forms import ContributionRequirementForm, StudentContributionForm, StockAdjustmentForm, ContributionSpreadsheetFilterForm
from .models import ContributionRequirement, StudentContribution, StoreStock, StockMovement
from audit.utils import log_action


MANAGER_ROLES = ['HEADMASTER', 'SECOND_MASTER', 'ACADEMIC']


def _get_school(request):
    return getattr(request, 'school', None)


def _is_store_keeper(user):
    staff = getattr(user, 'staff_profile', None)
    return bool(staff and staff.is_store_keeper)


def requirement_manager_required(view_func):
    """Kuweka 'kinachotakiwa kuletwa' ni kazi ya Headmaster/Second Master/Academic tu."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in MANAGER_ROLES:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")
        return view_func(request, *args, **kwargs)
    return wrapper


def store_keeper_required(view_func):
    """
    Kurekodi michango na stock ni kazi ya Store Keeper (mwalimu aliyeteuliwa
    - is_store_keeper=True kwenye Staff), au wakuu (Headmaster/Second Master)
    kwa uangalizi.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        allowed = request.user.role in ('HEADMASTER', 'SECOND_MASTER') or _is_store_keeper(request.user)
        if not allowed:
            return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu - wewe si Store Keeper.")
        return view_func(request, *args, **kwargs)
    return wrapper


from notifications.utils import notify
from shule_core.models import CustomUser


def _notify_low_stock(stock):
    """
    Inatuma bell + SMS kwa Headmaster/Second Master wote wa shule,
    kuwajulisha kifaa kimeisha stock.
    """
    heads = CustomUser.objects.filter(
        school=stock.school, role__in=['HEADMASTER', 'SECOND_MASTER']
    ).exclude(phone__isnull=True).exclude(phone='')
    message = (
        f"ShulePlusERP Store: '{stock.item_name}' zimebaki {stock.quantity_in_stock} tu "
        f"(chini ya kiwango cha {stock.low_stock_threshold})."
    )
    for head in heads:
        notify(head, stock.school, message, link='/store/dashboard/')


@store_keeper_required
def store_dashboard_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    stocks = StoreStock.objects.filter(school=school).order_by('item_name')
    low_stock_items = [s for s in stocks if s.is_low]

    requirements = ContributionRequirement.objects.filter(school=school).order_by('-academic_year', 'term')

    pending = StudentContribution.objects.filter(school=school).select_related('student', 'requirement')
    pending_debts = [c for c in pending if not c.is_complete]

    context = {
        'school': school,
        'stocks': stocks,
        'low_stock_items': low_stock_items,
        'requirements': requirements,
        'pending_debts': pending_debts,
    }
    return render(request, 'store/store_dashboard.html', context)


@store_keeper_required
def full_report_view(request):
    """
    Ripoti KAMILI ya michango - kila sharti (kifaa+darasa+muhula+mwaka)
    likionyesha wanafunzi WOTE wanaohusika, kiasi walicholeta, na
    waliokosa - ili iwe rahisi kuona 'nani hajatoa' kwa mtazamo mmoja,
    bila kuchagua sharti moja moja.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    academic_year = int(request.GET.get('academic_year') or timezone.now().year)

    requirements = ContributionRequirement.objects.filter(
        school=school, academic_year=academic_year
    ).select_related('school_class').order_by('school_class__name', 'term', 'item_name')

    report_groups = []
    for req in requirements:
        contributions = StudentContribution.objects.filter(requirement=req).select_related('student')
        contrib_map = {c.student_id: c.quantity_brought for c in contributions}

        if req.school_class:
            students = Student.objects.filter(school=school, school_class=req.school_class)
        else:
            students = Student.objects.filter(school=school, school_class__isnull=False)

        rows = []
        complete_count = 0
        for s in students:
            brought = contrib_map.get(s.id, 0)
            owed = max(req.quantity_required - brought, 0)
            if owed == 0 and s.id in contrib_map:
                complete_count += 1
            rows.append({'student': s, 'brought': brought, 'owed': owed})

        rows.sort(key=lambda r: (-r['owed'], r['student'].reg_number))

        report_groups.append({
            'requirement': req,
            'rows': rows,
            'total_students': len(rows),
            'complete_count': complete_count,
            'incomplete_count': len(rows) - complete_count,
        })

    context = {
        'school': school,
        'academic_year': academic_year,
        'report_groups': report_groups,
    }
    return render(request, 'store/full_report.html', context)


@requirement_manager_required
def add_requirement_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = ContributionRequirementForm(request.POST, school=school)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.school = school
            requirement.created_by = request.user
            requirement.save()

            # Hakikisha StoreStock ya kifaa hiki ipo (hata kama bado ni 0)
            StoreStock.objects.get_or_create(school=school, item_name=requirement.item_name)

            messages.success(request, f"Sharti la '{requirement.item_name}' limewekwa.")
            return redirect('store:add_requirement')
    else:
        form = ContributionRequirementForm(school=school)

    requirements = ContributionRequirement.objects.filter(school=school).order_by('-academic_year', 'term')
    context = {'school': school, 'form': form, 'requirements': requirements}
    return render(request, 'store/add_requirement.html', context)


@requirement_manager_required
def publish_requirement_view(request, requirement_id):
    """
    Kutengeneza deni (StudentContribution, quantity_brought=0) kwa
    wanafunzi WOTE wanaohusika na sharti hili - kwa mpigo mmoja - ili
    lionekane kwenye ripoti ya mzazi na kwa Store Keeper hata kama
    Store Keeper bado hajamgusa mwanafunzi huyo. Wanafunzi wenye rekodi
    tayari (waliokwishaletewa kitu) hawaguswi - get_or_create haiwafutii
    walicholeta.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    requirement = get_object_or_404(ContributionRequirement, id=requirement_id, school=school)

    if request.method == 'POST':
        if requirement.school_class:
            students = Student.objects.filter(school=school, school_class=requirement.school_class)
        else:
            students = Student.objects.filter(school=school, school_class__isnull=False)

        created_count = 0
        with transaction.atomic():
            for student in students:
                _, created = StudentContribution.objects.get_or_create(
                    student=student, requirement=requirement,
                    defaults={'school': school, 'quantity_brought': 0, 'recorded_by': request.user},
                )
                if created:
                    created_count += 1

            requirement.is_published = True
            requirement.published_at = timezone.now()
            requirement.save(update_fields=['is_published', 'published_at'])

        messages.success(
            request,
            f"'{requirement.item_name}' imechapishwa - deni limewekwa kwa wanafunzi {created_count} wapya "
            f"(sasa linaonekana kwenye ripoti za wazazi na kwa Store Keeper)."
        )
        log_action(
            request.user, school, 'CONTRIBUTION_PUBLISHED',
            f"Amechapisha sharti la '{requirement.item_name}' - wanafunzi {created_count} wameongezewa deni."
        )
    return redirect('store:add_requirement')


@store_keeper_required
def record_contribution_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = StudentContributionForm(request.POST, school=school)
        if form.is_valid():
            with transaction.atomic():
                existing = StudentContribution.objects.filter(
                    student=form.cleaned_data['student'],
                    requirement=form.cleaned_data['requirement'],
                ).first()
                qty_now = form.cleaned_data['quantity_brought']
                total_brought = (existing.quantity_brought if existing else 0) + qty_now

                contribution, created = StudentContribution.objects.update_or_create(
                    student=form.cleaned_data['student'],
                    requirement=form.cleaned_data['requirement'],
                    defaults={
                        'school': school,
                        'quantity_brought': total_brought,
                        'recorded_by': request.user,
                        'notes': form.cleaned_data.get('notes', ''),
                    },
                )

                # Ongeza kwenye StoreStock + StockMovement kwa kile kilicholetwa SASA (siyo jumla)
                stock, _ = StoreStock.objects.get_or_create(
                    school=school, item_name=contribution.requirement.item_name
                )
                qty = form.cleaned_data['quantity_brought']
                if qty > 0:
                    stock.quantity_in_stock += qty
                    stock.save()
                    StockMovement.objects.create(
                        school=school, stock=stock, quantity_change=qty,
                        reason='STUDENT_CONTRIBUTION', recorded_by=request.user,
                        notes=f"Kutoka kwa {contribution.student}",
                    )

            if contribution.is_complete:
                messages.success(request, f"{contribution.student} amekamilisha mchango wa {contribution.requirement.item_name}.")
            else:
                messages.success(
                    request,
                    f"{contribution.student} amerekodiwa. Anadaiwa {contribution.quantity_owed} ya "
                    f"{contribution.requirement.item_name} bado."
                )
            return redirect('store:record_contribution')
    else:
        form = StudentContributionForm(school=school)

    # Orodha ya wanafunzi wenye deni (haijakamilika)
    pending = StudentContribution.objects.filter(school=school).select_related('student', 'requirement')
    pending_debts = [c for c in pending if not c.is_complete]

    context = {'school': school, 'form': form, 'pending_debts': pending_debts}
    return render(request, 'store/record_contribution.html', context)


@store_keeper_required
def record_contribution_spreadsheet_view(request):
    """
    Rekodi mchango kwa WINGI - kama Marks Entry: chagua Sharti (Kifaa +
    Darasa + Muhula + Mwaka), wanafunzi WOTE wa darasa husika
    wanaonekana kwenye jedwali moja, 'Hifadhi Yote' moja inarekodi
    mchango wa wote kwa pamoja.

    Kiasi kilichoingizwa kwenye kila kiini kinaONGEZWA juu ya
    alichokwishaleta hapo awali (siyo kubadilishwa) - sawa kabisa na
    record_contribution_view ya mwanafunzi mmoja mmoja.
    """
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    filter_form = ContributionSpreadsheetFilterForm(request.GET or None, school=school)
    students = []
    requirement = None

    if filter_form.is_valid():
        requirement = filter_form.cleaned_data['requirement']

        if requirement.school_class:
            student_qs = Student.objects.filter(school=school, school_class=requirement.school_class)
        else:
            student_qs = Student.objects.filter(school=school, school_class__isnull=False)

        existing_map = {
            c.student_id: c.quantity_brought
            for c in StudentContribution.objects.filter(requirement=requirement)
        }

        for s in student_qs:
            brought = existing_map.get(s.id, 0)
            students.append({
                'student': s,
                'brought': brought,
                'owed': max(requirement.quantity_required - brought, 0),
            })

        if request.method == 'POST':
            saved_count = 0
            with transaction.atomic():
                for s in student_qs:
                    raw_qty = request.POST.get(f'qty_{s.id}', '').strip()
                    if not raw_qty:
                        continue
                    try:
                        qty_now = int(raw_qty)
                    except ValueError:
                        continue
                    if qty_now <= 0:
                        continue

                    existing = StudentContribution.objects.filter(student=s, requirement=requirement).first()
                    total_brought = (existing.quantity_brought if existing else 0) + qty_now

                    StudentContribution.objects.update_or_create(
                        student=s, requirement=requirement,
                        defaults={
                            'school': school,
                            'quantity_brought': total_brought,
                            'recorded_by': request.user,
                        },
                    )
                    saved_count += 1

                    stock, _ = StoreStock.objects.get_or_create(school=school, item_name=requirement.item_name)
                    stock.quantity_in_stock += qty_now
                    stock.save()
                    StockMovement.objects.create(
                        school=school, stock=stock, quantity_change=qty_now,
                        reason='STUDENT_CONTRIBUTION', recorded_by=request.user,
                        notes=f"[Spreadsheet] Kutoka kwa {s}",
                    )

            messages.success(request, f"Mchango wa wanafunzi {saved_count} umerekodiwa - {requirement}.")
            log_action(
                request.user, school, 'CONTRIBUTION_RECORDED',
                f"[Spreadsheet] Amerekodi mchango wa wanafunzi {saved_count} - {requirement}."
            )
            return redirect(f"{request.path}?{request.GET.urlencode()}")

    context = {'school': school, 'filter_form': filter_form, 'students': students, 'requirement': requirement}
    return render(request, 'store/record_contribution_spreadsheet.html', context)


@store_keeper_required
def stock_adjustment_view(request):
    school = _get_school(request)
    if not school:
        return HttpResponseForbidden("Hauruhusiwi kufikia ukurasa huu.")

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST, school=school)
        if form.is_valid():
            stock = form.cleaned_data['stock']
            qty = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            with transaction.atomic():
                stock.quantity_in_stock += qty
                stock.save()
                StockMovement.objects.create(
                    school=school, stock=stock, quantity_change=qty, reason=reason,
                    recorded_by=request.user, notes=form.cleaned_data.get('notes', ''),
                )

            if stock.is_low:
                _notify_low_stock(stock)
                messages.warning(request, f"Stock ya '{stock.item_name}' iko chini ({stock.quantity_in_stock}). Wajulishe wakuu.")
            else:
                messages.success(request, f"Stock ya '{stock.item_name}' imesasishwa: sasa ni {stock.quantity_in_stock}.")
            log_action(
                request.user, school, 'STOCK_ADJUSTED',
                f"Amerekebisha stock ya '{stock.item_name}' kwa {qty:+d} ({reason}). Sasa: {stock.quantity_in_stock}."
            )
            return redirect('store:stock_adjustment')
    else:
        form = StockAdjustmentForm(school=school)

    context = {'school': school, 'form': form}
    return render(request, 'store/stock_adjustment.html', context)
