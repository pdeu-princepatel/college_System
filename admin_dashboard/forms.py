# admin_dashboard/forms.py
from django import forms
from cms.models import Student, Faculty

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'DOB', 'roll_no', 'department', 'semester', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cms-form-input'}),
            'DOB': forms.DateInput(attrs={'class': 'cms-form-input', 'type': 'date'}),
            'roll_no': forms.TextInput(attrs={'class': 'cms-form-input'}),
            'department': forms.Select(attrs={'class': 'cms-form-select'}),
            'semester': forms.NumberInput(attrs={'class': 'cms-form-input'}),
            'password': forms.PasswordInput(attrs={'class': 'cms-form-input'}),
        }

class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['name', 'designation', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'cms-form-input'}),
            'designation': forms.TextInput(attrs={'class': 'cms-form-input'}),
            'department': forms.Select(attrs={'class': 'cms-form-select'}),
        }