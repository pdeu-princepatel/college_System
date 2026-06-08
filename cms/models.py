from django.db import models

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100)
    DOB = models.DateField()
    roll_no = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20, blank=True, default='')
    password = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} ({self.roll_no}) - Sem {self.semester}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    semester = models.CharField(max_length=20)
    course = models.CharField(max_length=100)
    grade = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.roll_no}: {self.course} - Sem {self.semester} ({self.grade})"


class Attendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LATE = 'late'
    STATUS_EXCUSED = 'excused'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_EXCUSED, 'Excused'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    subject = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'date'],
                name='unique_student_attendance_per_day',
            ),
        ]

    def __str__(self):
        return f"{self.student.roll_no} | {self.date} | {self.get_status_display()}"

    @property
    def counts_as_present(self):
        return self.status in (self.STATUS_PRESENT, self.STATUS_LATE, self.STATUS_EXCUSED)


class Notice(models.Model):
    title = models.CharField(max_length=140)
    message = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    semester = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        scope = []
        if self.department:
            scope.append(self.department.name)
        if self.semester:
            scope.append(f"Sem {self.semester}")
        scope_str = f" [{', '.join(scope)}]" if scope else ""
        return f"{self.title[:50]}{scope_str}"


class NoticeRead(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notice_reads')
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'notice'],
                name='unique_notice_read_per_student',
            ),
        ]

    def __str__(self):
        return f"{self.student.roll_no} read '{self.notice.title[:20]}...'"


class Faculty(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, default='')
    designation = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='faculty')
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Faculty'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.designation})"


class ContentStore(models.Model):
    TYPE_NOTES = 'notes'
    TYPE_SYLLABUS = 'syllabus'
    TYPE_RESOURCE = 'resource'
    TYPE_ANNOUNCEMENT = 'announcement'

    TYPE_CHOICES = [
        (TYPE_NOTES, 'Notes'),
        (TYPE_SYLLABUS, 'Syllabus'),
        (TYPE_RESOURCE, 'Resource'),
        (TYPE_ANNOUNCEMENT, 'Announcement'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    content_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_RESOURCE)
    body = models.TextField(blank=True, default='')
    external_url = models.URLField(blank=True, default='')
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, null=True, blank=True, related_name='content_items'
    )
    faculty = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='content_items'
    )
    semester = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"


class Message(models.Model):
    RECIPIENT_FACULTY = 'faculty'
    RECIPIENT_STUDENT = 'student'
    RECIPIENT_ADMIN = 'admin'

    RECIPIENT_CHOICES = [
        (RECIPIENT_FACULTY, 'Faculty'),
        (RECIPIENT_STUDENT, 'Student'),
        (RECIPIENT_ADMIN, 'College Admin'),
    ]

    sender = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sent_messages')
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)
    faculty = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, null=True, blank=True, related_name='messages'
    )
    recipient_student = models.ForeignKey(
        Student, on_delete=models.CASCADE, null=True, blank=True, related_name='received_messages'
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From: {self.sender.roll_no} | To: {self.recipient_type} | {self.subject[:30]}"


class Timetable(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='timetables')
    semester = models.CharField(max_length=20)
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES)
    subject = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_classes')
    classroom = models.CharField(max_length=50, blank=True, default='')
    is_essential = models.BooleanField(default=False, verbose_name="Essential Lecture")

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Timetable Entry'
        verbose_name_plural = 'Timetable Entries'

    def __str__(self):
        return f"{self.day_of_week} | {self.start_time.strftime('%H:%M')} | {self.subject}"