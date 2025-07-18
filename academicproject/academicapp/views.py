from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import redirect, get_object_or_404
from .models import profile, semester20251, semester20252, assignlecturer20251, assignlecturer20252
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages


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

assign_model_title = {
    '20251': assignlecturer20251,
    '20252': assignlecturer20252,
}


def studyprogram(request, semester_url='20251'):
    semester_model = semester_title.get(semester_url)
    if not semester_model:
        return HttpResponse("Semester not found", status=404)

    semester_data = semester_model.objects.all()

    assign_model = assign_model_title.get(semester_url)
    assignments = assign_model.objects.select_related('semester').all()
    assignment_map = {a.semester.semester_id: a for a in assignments}

    for item in semester_data:
        assignment = assignment_map.get(item.semester_id)
        item.is_assigned = bool(assignment)
        item.assign_id = assignment.assign_id if assignment else None

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


def assignlecturer_create(request):
    if request.method == 'POST':
        semester_id = request.POST.get('semester_id')
        entry_id = request.POST.get('entry_id')

        try:
            semester_instance = semester20251.objects.get(semester_id=semester_id)
        except semester20251.DoesNotExist:
            return redirect('studyprogram', semester_url='20251')
        
        if entry_id: 
            try:
                assign_obj = assignlecturer20251.objects.get(assign_id=entry_id)
                assign_obj.semester = semester_instance
                assign_obj.lecturer_day = request.POST.get('day')
                assign_obj.room = request.POST.get('room')
                assign_obj.start_time = request.POST.get('time')
                assign_obj.end_time = request.POST.get('time2')
                assign_obj.save()
                messages.success(request, 'Assignment updated successfully!')
            except assignlecturer20251.DoesNotExist:
                messages.error(request, 'Assignment record not found.')
        else:
            assignlecturer20251.objects.create(
                semester=semester_instance, 
                lecturer_day=request.POST.get('day'),
                room=request.POST.get('room'),
                start_time=request.POST.get('time'),
                end_time=request.POST.get('time2')
            )
        messages.success(request, 'Lecturer assignment saved successfully!')
        return redirect('studyprogram', semester_url='20251')
    
def assignlecturer_delete(request):
    if request.method == 'POST':
        semester_id = request.POST.get('semester_id')

        obj = get_object_or_404(semester20251, semester_id=semester_id)
        obj.delete()

        messages.success(request, "Data has been deleted.")
        return redirect('studyprogram', semester_id)
    else:
        messages.error(request, "Method Unallowed.")
        return redirect('studyprogram', '20251')  