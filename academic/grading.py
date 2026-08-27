"""
GRADING LOGIC - academic/grading.py

Hesabu ya Midterm/Terminal/Annual kwa mfumo wa Continuous Assessment (CA)
unaotumika shuleni kwako:

  Robo 1: Test1_A + Test2_A + Mid-Term Exam -> wastani -> MID_TERM
  Robo 2: Test1_B + Test2_B + Terminal Exam -> wastani -> "Robo-2 Result"
  TERMINAL (Muhula 1, inayochapishwa) = wastani wa (MID_TERM + Robo-2 Result)

  ANNUAL (mwisho wa mwaka, inayochapishwa) =
      wastani wa (TERMINAL ya Muhula 1 + Annual Exam ya Muhula 2)

MUHIMU: Mwalimu HAJAZAI 'MID_TERM'/'TERMINAL'/'ANNUAL' moja kwa moja - hizo
zinahesabiwa na recompute_derived_results() kila mara raw score inapohifadhiwa.
"""
from shule_core.models import AcademicResult


def _get_score(student, subject, exam_type, term, academic_year):
    r = AcademicResult.objects.filter(
        student=student, subject=subject, exam_type=exam_type,
        term=term, academic_year=academic_year,
    ).first()
    return float(r.score) if r else None


def _average(*scores):
    valid = [s for s in scores if s is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)


def recompute_derived_results(school, student, subject, term, academic_year, school_class):
    """
    Inaitwa baada ya kila raw score kuhifadhiwa (TEST_1_A, TEST_2_A,
    MID_TERM_EXAM, TEST_1_B, TEST_2_B, TERMINAL_EXAM/ANNUAL_EXAM).
    Inahesabu upya MID_TERM na TERMINAL/ANNUAL (computed) kwa mchanganyiko
    huo wa student+subject+term+academic_year, na kuzihifadhi/kuzisasisha
    kwenye AcademicResult.
    """
    # --- Robo 1 -> MID_TERM ---
    test1_a = _get_score(student, subject, 'TEST_1_A', term, academic_year)
    test2_a = _get_score(student, subject, 'TEST_2_A', term, academic_year)
    midterm_exam = _get_score(student, subject, 'MID_TERM_EXAM', term, academic_year)

    midterm_score = _average(test1_a, test2_a, midterm_exam)

    if midterm_score is not None:
        AcademicResult.objects.update_or_create(
            student=student, subject=subject, exam_type='MID_TERM',
            term=term, academic_year=academic_year,
            defaults={'school': school, 'school_class': school_class, 'score': midterm_score},
        )

    # --- Robo 2 -> Terminal/Annual exam raw ---
    test1_b = _get_score(student, subject, 'TEST_1_B', term, academic_year)
    test2_b = _get_score(student, subject, 'TEST_2_B', term, academic_year)

    if term == 'TERM_1':
        final_exam_raw = _get_score(student, subject, 'TERMINAL_EXAM', term, academic_year)
        quarter2_score = _average(test1_b, test2_b, final_exam_raw)

        if midterm_score is not None and quarter2_score is not None:
            terminal_score = _average(midterm_score, quarter2_score)
            AcademicResult.objects.update_or_create(
                student=student, subject=subject, exam_type='TERMINAL',
                term=term, academic_year=academic_year,
                defaults={'school': school, 'school_class': school_class, 'score': terminal_score},
            )

    elif term == 'TERM_2':
        # ANNUAL = wastani wa (TERMINAL ya Muhula 1 + Annual Exam ya Muhula 2)
        terminal_term1 = _get_score(student, subject, 'TERMINAL', 'TERM_1', academic_year)
        annual_exam_raw = _get_score(student, subject, 'ANNUAL_EXAM', term, academic_year)

        annual_score = _average(terminal_term1, annual_exam_raw)
        if annual_score is not None:
            AcademicResult.objects.update_or_create(
                student=student, subject=subject, exam_type='ANNUAL',
                term=term, academic_year=academic_year,
                defaults={'school': school, 'school_class': school_class, 'score': annual_score},
            )
