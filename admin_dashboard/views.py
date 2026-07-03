from django.db.models import Count
from django.shortcuts import render
from admin_dashboard.decorators import staff_login_required
from cms.models import Student, Faculty, Attendance ,Message
from django.shortcuts import render, redirect ,get_object_or_404
from .forms import *
from django.contrib.auth.hashers import check_password,make_password
from .models import Staff # Your custom staff model

from django.contrib import messages

def staff_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = Staff.objects.filter(username=username).first()
        
        # Verify user and password
        if user and check_password(password, user.password):
            request.session.set_expiry(3600)  # Session lasts 1 hour
            request.session['staff_id'] = user.id
            return redirect('staff_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'staff/login.html')

def staff_logout(request):
    # Clears all session data and the session cookie
    request.session.flush()
    return redirect('staff_login')


from django.db.models import Count, Q, Case, When, IntegerField
@staff_login_required
def dashboard_home(request):
    # 1. Basic Counts
    total_students = Student.objects.count()
    total_faculty = Faculty.objects.count()
    unread_messages = Message.objects.filter(is_read=False).count()
    
    # 2. Get Data using the manual loop method
    health_data = []
    departments = Department.objects.all()
    
    for d in departments:
        # Counts via related names (student_set is the default reverse FK)
        s_count = d.student_set.count()
        f_count = d.faculty.count()
        
        # Manual Attendance Aggregation
        att_total = Attendance.objects.filter(student__department=d).count()
        att_present = Attendance.objects.filter(student__department=d, status='present').count()
        
        att_pct = (att_present / att_total * 100) if att_total > 0 else 0
        ratio = s_count / f_count if f_count > 0 else s_count
        score = att_pct / ratio if ratio > 0 else 0
        MAX_SCALE = 10 
    
        health_data.append({
            'name': d.name,
            's_total': s_count,
            'f_total': f_count,
            'score': score,
            # Calculate width dynamically
            's_width': (s_count / MAX_SCALE) * 100,
            'f_width': (f_count / MAX_SCALE) * 100
        })
    # Sort for top/worst performance
    sorted_health = sorted(health_data, key=lambda x: x['score'], reverse=True)
    
    context = {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'unread_messages': unread_messages,
        'dept_data': health_data,      # Used for the Stacked Bar
        'health_data': health_data,   # Used for the Health Index
        'top_dept': sorted_health[0] if sorted_health else {'name': 'N/A'},
        'worst_dept': sorted_health[-1] if sorted_health else {'name': 'N/A'},
    }
    
    return render(request, 'staff/dashboard.html', context)


@staff_login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.password = make_password(form.cleaned_data['password'])
            student.save()
            return redirect('staff_students')
    else:
        form = StudentForm()
    return render(request, 'staff/add_student.html', {'form': form})


from cms.models import Student, Department  # Import Department
@staff_login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        # Pass 'instance' so Django knows we are updating, not creating new
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('staff_students')
    else:
        form = StudentForm(instance=student)
        
    return render(request, 'staff/edit_student.html', {'form': form, 'student': student})

@staff_login_required
def manage_students(request):
    query = request.GET.get('q', '')
    dept_id = request.GET.get('department', '')

    students = Student.objects.all()
    if query:
        students = students.filter(name__icontains=query)
    if dept_id:
        students = students.filter(department_id=dept_id)

    # Pass departments to the template
    departments = Department.objects.all()
    return render(request, 'staff/students.html', {
        'students': students,
        'departments': departments,
        'selected_dept': dept_id
    })
@staff_login_required
def add_faculty(request):
    if request.method == 'POST':
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff_faculty')
    else:
        form = FacultyForm()
    return render(request, 'staff/add_faculty.html', {'form': form})

@staff_login_required
def edit_faculty(request, faculty_id):
    faculty = get_object_or_404(Faculty, id=faculty_id)
    if request.method == 'POST':
        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            form.save()
            return redirect('staff_faculty')
    else:
        form = FacultyForm(instance=faculty)
    return render(request, 'staff/edit_faculty.html', {'form': form, 'faculty': faculty})
from cms.models import Faculty, Department # Ensure Department is imported

@staff_login_required
def manage_faculty(request):
    # 1. Get query parameters
    query = request.GET.get('q', '')
    dept_id = request.GET.get('department', '')
    
    # 2. Base QuerySet with select_related for performance
    faculty = Faculty.objects.all().select_related('department')
    
    # 3. Apply Filters
    if query:
        faculty = faculty.filter(name__icontains=query)
    if dept_id:
        faculty = faculty.filter(department_id=dept_id)
        
    # 4. Fetch departments for the filter dropdown
    departments = Department.objects.all()
    
    context = {
        'faculty': faculty,
        'departments': departments,
        'selected_dept': dept_id
    }
    return render(request, 'staff/faculty.html', context)
@staff_login_required
def manage_attendance(request):
    # Fetch all records, optionally filter by date if provided via GET
    attendance_records = Attendance.objects.all().order_by('-date')
    context = {'attendance': attendance_records}
    return render(request, 'staff/attendance.html', context)

@staff_login_required
def manage_messages(request):
    # Fetch all messages meant for the admin
    messages = Message.objects.filter(recipient_type='admin').order_by('-created_at')
    context = {'messages': messages}
    return render(request, 'staff/messages.html', context)
