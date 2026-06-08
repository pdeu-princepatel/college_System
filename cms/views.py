from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps
from django.db.models import Q
from .models import (
    Department,
    Student,
    Result,
    Attendance,
    Notice,
    NoticeRead,
    Faculty,
    ContentStore,
    Message,
    Timetable,
)


def _get_logged_in_student(request):
    student_id = request.session.get('student_id')
    try:
        return Student.objects.select_related('department').get(id=student_id)
    except Student.DoesNotExist:
        request.session.flush()
        return None


def _get_logged_in_faculty(request):
    faculty_id = request.session.get('faculty_id')
    try:
        return Faculty.objects.select_related('department').get(id=faculty_id, is_active=True)
    except Faculty.DoesNotExist:
        if 'faculty_id' in request.session:
            request.session.pop('faculty_id', None)
        return None


def _attendance_stats(student):
    records = Attendance.objects.filter(student=student)
    total = records.count()
    if total == 0:
        return {'total': 0, 'present': 0, 'percentage': None}
    present = records.filter(
        status__in=(
            Attendance.STATUS_PRESENT,
            Attendance.STATUS_LATE,
            Attendance.STATUS_EXCUSED,
        )
    ).count()
    percentage = round((present / total) * 100, 1)
    return {'total': total, 'present': present, 'percentage': percentage}


def _notice_queryset_for_student(student):
    return Notice.objects.filter(
        Q(department__isnull=True) | Q(department=student.department),
        Q(semester='') | Q(semester=student.semester),
    )


def _apply_department_filter(qs, dept_id, field_name='department_id'):
    if dept_id:
        return qs.filter(**{field_name: dept_id})
    return qs


def _content_for_student(student, dept_id=None):
    qs = ContentStore.objects.select_related('department', 'faculty').filter(
        Q(department__isnull=True) | Q(department=student.department),
        Q(semester='') | Q(semester=student.semester),
    )
    return _apply_department_filter(qs, dept_id)


# Custom Session-based Login Required Decorator
def student_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'student_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def faculty_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'faculty_id' not in request.session:
            return redirect('faculty_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@student_login_required
def index(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    peer_count = Student.objects.filter(department=student.department).count()
    attendance = _attendance_stats(student)
    notices_qs = _notice_queryset_for_student(student)
    latest_notices = notices_qs[:3]
    unread_notice_count = notices_qs.exclude(reads__student=student).count()
    faculty_count = Faculty.objects.filter(department=student.department, is_active=True).count()

    context = {
        'student': student,
        'peer_count': peer_count,
        'faculty_count': faculty_count,
        'attendance_total': attendance['total'],
        'attendance_present': attendance['present'],
        'attendance_percentage': attendance['percentage'],
        'latest_notices': latest_notices,
        'unread_notice_count': unread_notice_count,
    }
    return render(request, 'index.html', context)


@student_login_required
def students(request):
    dept_id = request.GET.get('department')
    qs = Student.objects.select_related('department').all()
    qs = _apply_department_filter(qs, dept_id)
    departments = Department.objects.all()
    return render(request, 'list.html', {
        'students': qs,
        'departments': departments,
        'selected_department': dept_id or '',
    })


@student_login_required
def faculty_list(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    dept_id = request.GET.get('department') or str(student.department_id)
    qs = Faculty.objects.filter(is_active=True).select_related('department')
    if dept_id:
        qs = qs.filter(department_id=dept_id)

    departments = Department.objects.all()
    return render(request, 'faculty_list.html', {
        'student': student,
        'faculty_list': qs,
        'departments': departments,
        'selected_department': dept_id,
    })


@student_login_required
def content_list(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    dept_id = request.GET.get('department') or ''
    content_type = request.GET.get('type') or ''
    qs = _content_for_student(student, dept_id if dept_id else None)
    if content_type:
        qs = qs.filter(content_type=content_type)

    departments = Department.objects.all()
    return render(request, 'content_list.html', {
        'student': student,
        'content_items': qs,
        'departments': departments,
        'selected_department': dept_id,
        'selected_type': content_type,
        'type_choices': ContentStore.TYPE_CHOICES,
    })


@student_login_required
def contact_view(request):
    """Directory to contact faculty, peers, or college admin."""
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    dept_id = request.GET.get('department') or ''
    tab = request.GET.get('tab', 'faculty')

    faculty_qs = Faculty.objects.filter(is_active=True).select_related('department')
    student_qs = Student.objects.select_related('department').exclude(id=student.id)

    if dept_id:
        faculty_qs = faculty_qs.filter(department_id=dept_id)
        student_qs = student_qs.filter(department_id=dept_id)

    departments = Department.objects.all()
    return render(request, 'contact.html', {
        'student': student,
        'faculty_contacts': faculty_qs,
        'student_contacts': student_qs,
        'departments': departments,
        'selected_department': dept_id,
        'active_tab': tab,
    })


@student_login_required
def message_compose(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    recipient_type = request.GET.get('type') or request.POST.get('recipient_type')
    faculty_id = request.GET.get('faculty') or request.POST.get('faculty_id')
    recipient_student_id = request.GET.get('student') or request.POST.get('recipient_student_id')

    error = None
    success = None
    faculty = None
    recipient_student = None
    recipient_label = 'College Admin'

    if recipient_type == Message.RECIPIENT_FACULTY and faculty_id:
        faculty = get_object_or_404(Faculty, id=faculty_id, is_active=True)
        recipient_label = faculty.name
    elif recipient_type == Message.RECIPIENT_STUDENT and recipient_student_id:
        recipient_student = get_object_or_404(Student, id=recipient_student_id)
        if recipient_student.id == student.id:
            error = 'You cannot message yourself.'
        else:
            recipient_label = recipient_student.name
    elif recipient_type != Message.RECIPIENT_ADMIN:
        error = 'Please choose a valid recipient.'

    if request.method == 'POST' and not error:
        subject = (request.POST.get('subject') or '').strip()
        body = (request.POST.get('body') or '').strip()
        rtype = request.POST.get('recipient_type')

        if not subject or not body:
            error = 'Subject and message are required.'
        elif rtype == Message.RECIPIENT_FACULTY:
            fid = request.POST.get('faculty_id')
            fac = get_object_or_404(Faculty, id=fid, is_active=True)
            Message.objects.create(
                sender=student,
                recipient_type=Message.RECIPIENT_FACULTY,
                faculty=fac,
                subject=subject,
                body=body,
            )
            success = f'Message sent to {fac.name}.'
        elif rtype == Message.RECIPIENT_STUDENT:
            sid = request.POST.get('recipient_student_id')
            peer = get_object_or_404(Student, id=sid)
            if peer.id == student.id:
                error = 'You cannot message yourself.'
            else:
                Message.objects.create(
                    sender=student,
                    recipient_type=Message.RECIPIENT_STUDENT,
                    recipient_student=peer,
                    subject=subject,
                    body=body,
                )
                success = f'Message sent to {peer.name}.'
        elif rtype == Message.RECIPIENT_ADMIN:
            Message.objects.create(
                sender=student,
                recipient_type=Message.RECIPIENT_ADMIN,
                subject=subject,
                body=body,
            )
            success = 'Message sent to College Admin.'
        else:
            error = 'Invalid recipient.'

    if success:
        return render(request, 'message_compose.html', {
            'student': student,
            'recipient_type': recipient_type,
            'faculty': faculty,
            'recipient_student': recipient_student,
            'recipient_label': recipient_label,
            'success': success,
        })

    return render(request, 'message_compose.html', {
        'student': student,
        'recipient_type': recipient_type or Message.RECIPIENT_ADMIN,
        'faculty': faculty,
        'recipient_student': recipient_student,
        'recipient_label': recipient_label,
        'error': error,
        'success': success,
    })


@student_login_required
def my_messages(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    sent = Message.objects.filter(sender=student).select_related('faculty', 'recipient_student')
    return render(request, 'my_messages.html', {
        'student': student,
        'sent_messages': sent,
    })


def faculty_login_view(request):
    if request.session.get('faculty_id'):
        return redirect('faculty_dashboard')

    error = None
    if request.method == 'POST':
        employee_id = (request.POST.get('employee_id') or '').strip()
        password = request.POST.get('password')
        try:
            faculty = Faculty.objects.get(employee_id=employee_id, is_active=True)
            if check_password(password, faculty.password):
                request.session['faculty_id'] = faculty.id
                return redirect('faculty_dashboard')
            error = 'Invalid Employee ID or Password.'
        except Faculty.DoesNotExist:
            error = 'Invalid Employee ID or Password.'

    return render(request, 'faculty_login.html', {'error': error})


def faculty_logout_view(request):
    request.session.pop('faculty_id', None)
    return redirect('faculty_login')


@faculty_login_required
def faculty_inbox(request):
    faculty = _get_logged_in_faculty(request)
    if faculty is None:
        return redirect('faculty_login')

    messages_qs = Message.objects.filter(
        recipient_type=Message.RECIPIENT_FACULTY,
        faculty=faculty,
    ).select_related('sender', 'sender__department').order_by('-created_at')

    if request.method == 'POST':
        msg_id = request.POST.get('message_id')
        if msg_id:
            Message.objects.filter(id=msg_id, faculty=faculty).update(is_read=True)
        return redirect('faculty_inbox')

    unread_count = messages_qs.filter(is_read=False).count()
    return render(request, 'faculty_inbox.html', {
        'faculty': faculty,
        'inbox_messages': messages_qs,
        'unread_count': unread_count,
    })


def addstudent(request):
    if request.method == "POST":
        dept_id = request.POST.get('department')
        if not dept_id or dept_id == '':
            departments = Department.objects.all()
            return render(request, 'add.html', {
                "departments": departments,
                "error": "Please select a valid department."
            })

        try:
            select_dept = Department.objects.get(id=dept_id)
        except Department.DoesNotExist:
            departments = Department.objects.all()
            return render(request, 'add.html', {
                "departments": departments,
                "error": "Please select a valid department."
            })

        roll_no = request.POST.get('roll_no')
        if Student.objects.filter(roll_no=roll_no).exists():
            departments = Department.objects.all()
            return render(request, 'add.html', {
                "departments": departments,
                "error": f"Roll Number '{roll_no}' already exists in our records."
            })

        Student.objects.create(
            name=request.POST.get('name'),
            roll_no=roll_no,
            DOB=request.POST.get('DOB'),
            department=select_dept,
            semester=(request.POST.get('semester') or '').strip(),
            password=make_password(request.POST.get('password'))
        )
        return redirect('login')

    departments = Department.objects.all()
    return render(request, 'add.html', {"departments": departments})


def login_view(request):
    if 'student_id' in request.session:
        return redirect('index')

    error = None
    if request.method == "POST":
        roll_no = request.POST.get('roll_no')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(roll_no=roll_no)
            if check_password(password, student.password):
                request.session['student_id'] = student.id
                return redirect('index')
            else:
                error = "Invalid Roll Number or Password."
        except Student.DoesNotExist:
            error = "Invalid Roll Number or Password."

    return render(request, 'login.html', {"error": error})


def logout_view(request):
    request.session.flush()
    return redirect('login')


@student_login_required
def edit_profile(request):
    student_id = request.session.get('student_id')
    try:
        student = Student.objects.select_related('department').get(id=student_id)
    except Student.DoesNotExist:
        request.session.flush()
        return redirect('login')

    error = None
    success = None

    if request.method == "POST":
        name = request.POST.get('name')
        dob = request.POST.get('DOB')
        semester = (request.POST.get('semester') or '').strip()
        new_password = request.POST.get('password')

        if not name or name.strip() == '' or not dob:
            error = "Full Name and Date of Birth are required."
        else:
            student.name = name
            student.DOB = dob
            student.semester = semester
            if new_password and new_password.strip() != "":
                student.password = make_password(new_password)
            student.save()
            success = "Your profile has been updated successfully!"

    context = {
        'student': student,
        'error': error,
        'success': success,
    }
    return render(request, 'edit_profile.html', context)


@student_login_required
def results_view(request):
    student_id = request.session.get('student_id')
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        request.session.flush()
        return redirect('login')
    results = Result.objects.filter(student=student).order_by('-created_at')
    context = {
        'student': student,
        'results': results,
    }
    return render(request, 'results.html', context)


@student_login_required
def attendance_view(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    records = Attendance.objects.filter(student=student)
    stats = _attendance_stats(student)

    context = {
        'student': student,
        'records': records,
        'attendance_total': stats['total'],
        'attendance_present': stats['present'],
        'attendance_percentage': stats['percentage'],
    }
    return render(request, 'attendance.html', context)


@student_login_required
def notices_view(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    notices_qs = _notice_queryset_for_student(student)
    notices = list(notices_qs)

    NoticeRead.objects.bulk_create(
        [NoticeRead(student=student, notice=n) for n in notices],
        ignore_conflicts=True,
    )

    context = {
        'student': student,
        'notices': notices,
    }
    return render(request, 'notices.html', context)


@student_login_required
def timetable_view(request):
    student = _get_logged_in_student(request)
    if student is None:
        return redirect('login')

    entries = Timetable.objects.filter(
        department=student.department,
        semester=student.semester
    ).select_related('faculty').order_by('start_time')

    # Group entries by day of week in standard calendar order
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    timetable_by_day = {day: [] for day in days_order}

    for entry in entries:
        if entry.day_of_week in timetable_by_day:
            timetable_by_day[entry.day_of_week].append(entry)

    # Remove empty days from the display to keep it clean, but keep active days ordered
    active_timetable = {day: lectures for day, lectures in timetable_by_day.items() if lectures}

    context = {
        'student': student,
        'timetable': active_timetable,
        'has_timetable': any(active_timetable.values())
    }
    return render(request, 'timetable.html', context)


# =========================================================================
#  Faculty Portal Views
# =========================================================================

@faculty_login_required
def faculty_dashboard(request):
    faculty = _get_logged_in_faculty(request)
    if faculty is None:
        return redirect('faculty_login')

    student_count = Student.objects.filter(department=faculty.department).count()
    faculty_count = Faculty.objects.filter(department=faculty.department, is_active=True).count()
    unread_count = Message.objects.filter(
        recipient_type=Message.RECIPIENT_FACULTY,
        faculty=faculty,
        is_read=False,
    ).count()

    context = {
        'faculty': faculty,
        'student_count': student_count,
        'faculty_count': faculty_count,
        'unread_count': unread_count,
    }
    return render(request, 'faculty_dashboard.html', context)


@faculty_login_required
def faculty_attendance(request):
    faculty = _get_logged_in_faculty(request)
    if faculty is None:
        return redirect('faculty_login')

    error = None
    success = None

    # Filter parameters
    semester = request.GET.get('semester', '') or request.POST.get('semester', '')
    subject = request.GET.get('subject', '') or request.POST.get('subject', '')
    date_str = request.GET.get('date', '') or request.POST.get('date', '')

    students_list = []
    existing_records = {}

    if semester and date_str:
        students_list = Student.objects.filter(
            department=faculty.department,
            semester=semester,
        ).order_by('roll_no')

        # Load existing attendance for this date
        existing = Attendance.objects.filter(
            student__in=students_list,
            date=date_str,
        )
        existing_records = {a.student_id: a for a in existing}

    if request.method == 'POST' and semester and date_str:
        if not students_list.exists():
            error = 'No students found for the selected semester.'
        else:
            updated = 0
            created = 0
            for student in students_list:
                status = request.POST.get(f'status_{student.id}', '')
                if status in dict(Attendance.STATUS_CHOICES):
                    if student.id in existing_records:
                        rec = existing_records[student.id]
                        rec.status = status
                        rec.subject = subject
                        rec.save()
                        updated += 1
                    else:
                        Attendance.objects.create(
                            student=student,
                            date=date_str,
                            subject=subject,
                            status=status,
                        )
                        created += 1

            success = f'Attendance saved! {created} new records, {updated} updated.'
            # Reload existing records after save
            existing = Attendance.objects.filter(
                student__in=students_list,
                date=date_str,
            )
            existing_records = {a.student_id: a for a in existing}

    # Annotate students with current status for template
    students_with_status = []
    for s in students_list:
        rec = existing_records.get(s.id)
        students_with_status.append({
            'student': s,
            'current_status': rec.status if rec else '',
        })

    context = {
        'faculty': faculty,
        'semester': semester,
        'subject': subject,
        'date': date_str,
        'students_with_status': students_with_status,
        'status_choices': Attendance.STATUS_CHOICES,
        'error': error,
        'success': success,
    }
    return render(request, 'faculty_attendance.html', context)


@faculty_login_required
def faculty_results(request):
    faculty = _get_logged_in_faculty(request)
    if faculty is None:
        return redirect('faculty_login')

    error = None
    success = None

    semester = request.GET.get('semester', '') or request.POST.get('semester', '')
    course = request.GET.get('course', '') or request.POST.get('course', '')

    students_list = []
    existing_results = {}

    if semester and course:
        students_list = Student.objects.filter(
            department=faculty.department,
            semester=semester,
        ).order_by('roll_no')

        existing = Result.objects.filter(
            student__in=students_list,
            semester=semester,
            course=course,
        )
        existing_results = {r.student_id: r for r in existing}

    grade_choices = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']

    if request.method == 'POST' and semester and course:
        if not students_list.exists():
            error = 'No students found for the selected semester.'
        else:
            updated = 0
            created = 0
            for student in students_list:
                grade = request.POST.get(f'grade_{student.id}', '').strip()
                if grade:
                    if student.id in existing_results:
                        rec = existing_results[student.id]
                        rec.grade = grade
                        rec.save()
                        updated += 1
                    else:
                        Result.objects.create(
                            student=student,
                            semester=semester,
                            course=course,
                            grade=grade,
                        )
                        created += 1

            success = f'Results saved! {created} new records, {updated} updated.'
            # Reload
            existing = Result.objects.filter(
                student__in=students_list,
                semester=semester,
                course=course,
            )
            existing_results = {r.student_id: r for r in existing}

    students_with_grades = []
    for s in students_list:
        rec = existing_results.get(s.id)
        students_with_grades.append({
            'student': s,
            'current_grade': rec.grade if rec else '',
        })

    context = {
        'faculty': faculty,
        'semester': semester,
        'course': course,
        'students_with_grades': students_with_grades,
        'grade_choices': grade_choices,
        'error': error,
        'success': success,
    }
    return render(request, 'faculty_results.html', context)


@faculty_login_required
def faculty_edit_profile(request):
    faculty = _get_logged_in_faculty(request)
    if faculty is None:
        return redirect('faculty_login')

    error = None
    success = None

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        new_password = request.POST.get('password')

        if not name or not email:
            error = 'Name and Email are required.'
        else:
            faculty.name = name
            faculty.email = email
            faculty.phone = phone
            if new_password and new_password.strip():
                faculty.password = make_password(new_password)
            faculty.save()
            success = 'Your profile has been updated successfully!'

    context = {
        'faculty': faculty,
        'error': error,
        'success': success,
    }
    return render(request, 'faculty_edit_profile.html', context)

