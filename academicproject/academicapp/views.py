from django.shortcuts import render
from django.shortcuts import redirect
from .models import profile


def dashboard(request):
    return render(request, 'dashboard.html')
def lecturer(request):
    return render(request, 'lecturer.html')
def addLecturer(request):
    return render(request, 'addLecturer.html')
def editLecturer(request):
    return render(request, 'editLecturer.html')

def signin(request):
    users = profile.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = profile.objects.get(username=username)
            if user.password == password:
                return redirect('dashboard')
            else:
                return render(request, 'signin.html', {
                    'error': 'Incorrect password',
                    'users': users
                })
        except profile.DoesNotExist:
            return render(request, 'signin.html', {
                'error': 'User does not exist',
                'users': users
            })

    return render(request, 'signin.html', {'users': users})

def logout(request):
    return redirect('signin')

