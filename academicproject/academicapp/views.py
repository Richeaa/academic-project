from django.shortcuts import render
from django.shortcuts import redirect
from .models import profile, semester20251, semester20252
from django.http import HttpResponse
from django.core.paginator import Paginator


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

semester_title = {
    '20251': semester20251,
    '20252': semester20252,
}

def studyprogram(request, semester_url='20251'):
    semester_model = semester_title.get(semester_url)
    if not semester_model:
        return HttpResponse("Semester not found", status=404)

    semester_data = semester_model.objects.all()

    paginator = Paginator(semester_data, 10)  
    page_number = int(request.GET.get('page', 1))
    page_obj = paginator.get_page(page_number)

    block_size = 5
    current_block = (page_number - 1) // block_size
    start_block = current_block * block_size + 1
    end_block = min(start_block + block_size - 1, paginator.num_pages)
    page_range = range(start_block, end_block + 1)


    rooms1 = [f'B{str(i).zfill(3)}' for i in range(101, 110)]
    rooms2 = [f'B{str(i).zfill(3)}' for i in range(201, 211)]
    rooms3 = [f'B{str(i).zfill(3)}' for i in range(301, 311)]
    rooms4 = [f'B{str(i).zfill(3)}' for i in range(401, 411)]
    
    context = {
        'semester_data': page_obj,  
        'active_semester': semester_url,
        'semester_title': semester_url,
        'page_title': semester_url,
        'page_obj': page_obj,  
        'page_range': page_range,
        'rooms1': rooms1,
        'rooms2': rooms2,
        'rooms3': rooms3,
        'rooms4': rooms4,
    }
    return render(request, 'studyprogram.html', context)