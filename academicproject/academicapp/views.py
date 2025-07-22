from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import redirect, get_object_or_404
from .models import profile, semester20251, semester20252, assignlecturer20251, assignlecturer20252, formsemester20251, formsemester20252, formsemester20253, formsemester20261, Lecturer
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def dashboard(request):
    return render(request, 'dashboard.html')


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

semester_academic_model = {
    '20251': formsemester20251,
    '20252': formsemester20252,
    '20253': formsemester20253,
    '20261': formsemester20261,
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
        'current_page': page_number,
    }
    return render(request, 'studyprogram.html', context)


def assignlecturer_create(request):
    if request.method == 'POST':
        semester_id = request.POST.get('semester_id')
        entry_id = request.POST.get('entry_id')

        try:
            semester_instance = semester20251.objects.get(semester_id=semester_id)
        except semester20251.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Semester not found.'}, status=404)

        try:
            if entry_id:
                assign_obj = assignlecturer20251.objects.get(assign_id=entry_id)
                assign_obj.semester = semester_instance
                assign_obj.lecturer_day = request.POST.get('day')
                assign_obj.room = request.POST.get('room')
                assign_obj.start_time = request.POST.get('time')
                assign_obj.end_time = request.POST.get('time2')
                assign_obj.save()
                return JsonResponse({'success': True, 'message': 'Assignment updated successfully'})
            else:
                assignlecturer20251.objects.create(
                    semester=semester_instance,
                    lecturer_day=request.POST.get('day'),
                    room=request.POST.get('room'),
                    start_time=request.POST.get('time'),
                    end_time=request.POST.get('time2')
                )
                return JsonResponse({'success': True, 'message': 'Assignment created successfully'})
        except assignlecturer20251.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Assignment not found.'}, status=404)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    

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
    

def schedule20251(request):
    schedule = assignlecturer20251.objects.select_related('semester')

    room_schedule = defaultdict(lambda: defaultdict(list))
    for entry in schedule:
        room = entry.room
        day = entry.lecturer_day
        room_schedule[room][day].append(entry)

    for room in room_schedule:
        for day in room_schedule[room]:
            room_schedule[room][day].sort(key=lambda x: x.start_time)

    context = {
        'room_schedule': dict(room_schedule),
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    }
    return render(request, 'schedule20251.html', context)

def lecturer(request):
    lecturers = Lecturer.objects.all()

    lecturer_name = request.GET.get('lecturer_name')
    job = request.GET.get('job')

    if lecturer_name:
        lecturers = lecturers.filter(lecturer_name__icontains=lecturer_name)

    if job:
        lecturers = lecturers.filter(job__iexact=job)

    job_choices = Lecturer.objects.exclude(job__isnull=True).exclude(job__exact='').values_list('job', flat=True).distinct()
    
    paginator = Paginator(lecturers, 50)  
    page_number = int(request.GET.get('page', 1))
    page_obj = paginator.get_page(page_number)

    block_size = 5
    current_block = (page_number - 1) // block_size
    start_block = current_block * block_size + 1
    end_block = min(start_block + block_size - 1, paginator.num_pages)
    page_range = range(start_block, end_block + 1)

    context = {
        'lecturers': page_obj,      
        'page_range': page_range,
        'job_choices': job_choices,   
    }
    return render(request, 'lecturer.html', context)


def addLecturer(request):
    if request.method == 'POST':
        Lecturer.objects.create(
            lecturer_name=request.POST.get('name'),
            lecturer_type=request.POST.get('type'),
            job=request.POST.get('job'),
            current_working_day=request.POST.get('working_days'),
            time_preferences=request.POST.get('time_preferences'),
            day_preferences=request.POST.get('day_preferences'),
            room_preferences=request.POST.get('room_preferences'),
            notes=request.POST.get('notes'),
        )
        return redirect('lecturer')  
    return render(request, 'addLecturer.html')

def editLecturer(request, lecturer_id):
    lecturer = get_object_or_404(Lecturer, pk=lecturer_id)

    if request.method == 'POST':
        lecturer.lecturer_name = request.POST.get('name')
        lecturer.lecturer_type = request.POST.get('type')
        lecturer.job = request.POST.get('job')
        lecturer.current_working_day = request.POST.get('working_days')
        lecturer.time_preferences = request.POST.get('time_preferences')
        lecturer.day_preferences = request.POST.get('day_preferences')
        lecturer.room_preferences = request.POST.get('room_preferences')
        lecturer.notes = request.POST.get('notes')
        lecturer.save()
        return redirect('lecturer')

    return render(request, 'editLecturer.html', {'lecturer': lecturer})

def deleteLecturer(request, lecturer_id):
    lecturer = get_object_or_404(Lecturer, pk=lecturer_id)
    
    if request.method == 'POST':
        lecturer.delete()
        return redirect('lecturer')  

    return render(request, 'deleteLecturer.html', {'lecturer': lecturer})

def formstudyprogram(request, semester_url='20251'): 
    semester_model = semester_academic_model.get(semester_url)
    if not semester_model:
        return HttpResponse("Semester not found", status=404)

    semester_data = semester_model.objects.all().order_by('semester_id')
    paginator = Paginator(semester_data, 100)  
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
    return render(request, 'formstudyprogram.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def add_academic_module(request, semester_url):
    try:
        semester_model = semester_academic_model.get(semester_url)
        if not semester_model:
            return JsonResponse({'success': False, 'error': 'Semester not found'}, status=404)
        data = {
            'program_session': request.POST.get('program_session'),
            'major': request.POST.get('major'),
            'curriculum': request.POST.get('curriculum'),
            'major_class': request.POST.get('major_class'),
            'subject': request.POST.get('subject'),
            'credit': request.POST.get('credit'),
            'lecturer_1': request.POST.get('lecturer_1', ''),
            'lecturer_2': request.POST.get('lecturer_2', ''),
            'lecturer_3': request.POST.get('lecturer_3', ''),
        }

     
        required_fields = ['program_session', 'major', 'curriculum', 'major_class', 'subject', 'credit']
        for field in required_fields:
            if not data[field]:
                return JsonResponse({'success': False, 'error': f'{field} is required'}, status=400)

       
        new_record = semester_model.objects.create(**data)
        
        return JsonResponse({
            'success': True, 
            'message': 'Academic module added successfully',
            'record_id': new_record.semester_id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def edit_academic_module(request, semester_url):
    try:
        semester_model = semester_academic_model.get(semester_url)
        if not semester_model:
            return JsonResponse({'success': False, 'error': 'Semester not found'}, status=404)

        record_id = request.POST.get('record_id')
        if not record_id:
            return JsonResponse({'success': False, 'error': 'Record ID is required'}, status=400)

        try:
            record = semester_model.objects.get(semester_id=record_id)
        except semester_model.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)

        record.program_session = request.POST.get('program_session', record.program_session)
        record.major = request.POST.get('major', record.major)
        record.curriculum = request.POST.get('curriculum', record.curriculum)
        record.major_class = request.POST.get('major_class', record.major_class)
        record.subject = request.POST.get('subject', record.subject)
        record.credit = request.POST.get('credit', record.credit)
        record.lecturer_1 = request.POST.get('lecturer_1', record.lecturer_1)
        record.lecturer_2 = request.POST.get('lecturer_2', record.lecturer_2)
        record.lecturer_3 = request.POST.get('lecturer_3', record.lecturer_3)

        record.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Academic module updated successfully'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def delete_academic_module(request, semester_url, semester_id): 
    if request.method == 'POST':
        model = semester_academic_model.get(semester_url)
        if not model:
            return JsonResponse({'success': False, 'error': 'Invalid semester.'})

        try:
            obj = model.objects.get(pk=semester_id)
            obj.delete()
            return JsonResponse({'success': True, 'message': 'Record deleted successfully.'})
        except model.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Record not found.'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})