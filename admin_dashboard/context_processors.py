def sidebar_links(request):
    return {
        'admin_nav':
            [
                {'name': 'Dashboard', 'url': 'staff_dashboard', 'icon': '📊'},
                {'name': 'Students', 'url': 'staff_students', 'icon': '🎓'},
                {'name': 'Faculty', 'url': 'staff_faculty', 'icon': '💼'},
                {'name': 'Attendance', 'url': 'staff_attendance', 'icon': '✅'},
                {'name': 'Messages', 'url': 'staff_messages', 'icon': '✉️'},
            ]
    }