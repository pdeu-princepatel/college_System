from django.shortcuts import redirect

def staff_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'staff_id' not in request.session:
            return redirect('staff_login')
        return view_func(request, *args, **kwargs)
    return wrapper