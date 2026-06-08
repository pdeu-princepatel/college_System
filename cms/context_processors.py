from django.db.models import Q

from .models import Notice, NoticeRead


def student_nav_context(request):
    """Shared nav context for logged-in students."""
    student_id = request.session.get('student_id')
    if not student_id:
        return {}

    from .models import Student

    try:
        student = Student.objects.select_related('department').get(id=student_id)
    except Student.DoesNotExist:
        return {}

    notices_qs = Notice.objects.filter(
        Q(department__isnull=True) | Q(department=student.department),
        Q(semester='') | Q(semester=student.semester),
    )
    unread_notice_count = notices_qs.exclude(reads__student=student).count()

    return {
        'nav_student': student,
        'unread_notice_count': unread_notice_count,
    }
