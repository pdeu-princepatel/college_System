from django.contrib import admin
from unfold.admin import ModelAdmin

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


@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    search_fields = ('name',)


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ('name', 'roll_no', 'department', 'semester')
    search_fields = ('name', 'roll_no')
    list_filter = ('department', 'semester')


@admin.register(NoticeRead)
class NoticeReadAdmin(ModelAdmin):
    list_display = ('student', 'notice', 'read_at')
    list_filter = ('read_at',)


@admin.register(Result)
class ResultAdmin(ModelAdmin):
    list_display = ('student', 'semester', 'course', 'grade', 'created_at')
    search_fields = ('student__roll_no', 'course', 'semester')
    readonly_fields = ('student', 'semester', 'course', 'grade', 'created_at')


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('student', 'date', 'subject', 'status', 'created_at')
    list_filter = ('status', 'date')
    search_fields = ('student__roll_no', 'student__name', 'subject')
    date_hierarchy = 'date'


@admin.register(Notice)
class NoticeAdmin(ModelAdmin):
    list_display = ('title', 'department', 'semester', 'created_at')
    list_filter = ('department', 'semester', 'created_at')
    search_fields = ('title', 'message')


@admin.register(Faculty)
class FacultyAdmin(ModelAdmin):
    list_display = ('employee_id', 'name', 'designation', 'department', 'email', 'is_active')
    list_filter = ('department', 'is_active', 'designation')
    search_fields = ('employee_id', 'name', 'email')


@admin.register(ContentStore)
class ContentStoreAdmin(ModelAdmin):
    list_display = ('title', 'content_type', 'department', 'faculty', 'semester', 'created_at')
    list_filter = ('content_type', 'department', 'semester', 'created_at')
    search_fields = ('title', 'description', 'body')


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = (
        'subject',
        'sender',
        'recipient_type',
        'faculty',
        'recipient_student',
        'is_read',
        'created_at',
    )
    list_filter = ('recipient_type', 'is_read', 'faculty__department', 'sender__department', 'created_at')
    search_fields = ('subject', 'body', 'sender__roll_no', 'sender__name', 'faculty__name')
    readonly_fields = ('sender', 'recipient_type', 'faculty', 'recipient_student', 'subject', 'body', 'created_at')

    def has_add_permission(self, request):
        return False


@admin.register(Timetable)
class TimetableAdmin(ModelAdmin):
    list_display = ('subject', 'department', 'semester', 'day_of_week', 'start_time', 'end_time', 'classroom', 'is_essential')
    list_filter = ('department', 'semester', 'day_of_week', 'is_essential')
    search_fields = ('subject', 'classroom', 'faculty__name')
