from django.shortcuts import render
from django.shortcuts import redirect
from .models import profile


def dashboard(request):
    return render(request, 'dashboard.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = profile.objects.get(username=username)
            if user.password == password:
                request.session['user_id'] = user.profile_id 
                request.session['username'] = user.username
                return redirect('dashboard')
            else:
                return render(request, 'signin.html', {'error': 'Incorrect password'})
        except profile.DoesNotExist:
            return render(request, 'signin.html', {'error': 'User does not exist'})

    users = profile.objects.all()
    return render(request, 'signin.html', {'users': users})

def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['username']
    return redirect('signin')
