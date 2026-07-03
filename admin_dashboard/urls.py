from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('logout/', views.staff_logout, name='staff_logout'),
    path('dashboard/', views.dashboard_home, name='staff_dashboard'),
    path('students/', views.manage_students, name='staff_students'),
    path('students/add/', views.add_student, name='staff_add_student'),
    path('students/edit/<int:student_id>/', views.edit_student, name='staff_edit_student'),
    path('faculty/', views.manage_faculty, name='staff_faculty'),
    path('faculty/add/', views.add_faculty, name='staff_add_faculty'),
    path('faculty/edit/<int:faculty_id>/', views.edit_faculty, name='staff_edit_faculty'),
    path('attendance/', views.manage_attendance, name='staff_attendance'),
    path('messages/', views.manage_messages, name='staff_messages'),

]