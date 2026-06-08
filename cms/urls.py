from django.urls import path
from . views import *

urlpatterns = [
    path("", index, name="index"),
    path("students/", students, name="students"),
    path("faculty/", faculty_list, name="faculty_list"),
    path("content/", content_list, name="content_list"),
    path("contact/", contact_view, name="contact"),
    path("messages/compose/", message_compose, name="message_compose"),
    path("messages/sent/", my_messages, name="my_messages"),
    path("add/", addstudent, name="addstudent"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("faculty/login/", faculty_login_view, name="faculty_login"),
    path("faculty/logout/", faculty_logout_view, name="faculty_logout"),
    path("faculty/inbox/", faculty_inbox, name="faculty_inbox"),
    path("faculty/dashboard/", faculty_dashboard, name="faculty_dashboard"),
    path("faculty/attendance/", faculty_attendance, name="faculty_attendance"),
    path("faculty/results/", faculty_results, name="faculty_results"),
    path("faculty/profile/edit/", faculty_edit_profile, name="faculty_edit_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("results/", results_view, name="results"),
    path("attendance/", attendance_view, name="attendance"),
    path("notices/", notices_view, name="notices"),
    path("timetable/", timetable_view, name="timetable"),
]