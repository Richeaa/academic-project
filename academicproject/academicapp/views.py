from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import redirect, get_object_or_404
from .models import profile, semester20251, semester20252, assignlecturer20251, assignlecturer20252, formsemester20251, formsemester20252, formsemester20253, formsemester20261, Lecturer, Viewschedule20251, Viewschedule20252, Viewschedule20253
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from collections import defaultdict
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import traceback
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from collections import Counter

def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('signin')
    
    if request.session.get('username') != 'academic':
        return HttpResponse("Unauthorized", status=403)
    
    semester_data = semester20251.objects.all()

    all_lecturers = set()
    for item in semester_data:
        if item.lecturer_1:
            all_lecturers.add(item.lecturer_1)
        if item.lecturer_2:
            all_lecturers.add(item.lecturer_2)
        if item.lecturer_3:
            all_lecturers.add(item.lecturer_3)

    total_lecturers = len(all_lecturers)

    all_classes = set()
    for item in semester_data:
        if item.major_class:
            all_classes.add(item.major_class)

    total_classes = len(all_classes)

    all_subjects = set()
    for item in semester_data:
        if item.subject:
            all_subjects.add(item.subject)

    total_subjects = len(all_subjects)


    context = {
        'total_lecturers': total_lecturers,
        'total_classes': total_classes,
        'total_subject': total_subjects
    }

    return render(request, 'dashboard.html', context)


def dashboard_hsp(request):
    if 'user_id' not in request.session:
        return redirect('signin')
    
    if request.session.get('username') != 'Head of Study Program':
        return HttpResponse("Unauthorized", status=403)

    
    context = {
        "show_dashboard": True,
    }
    return render(request, 'dashboard_hsp.html', context)

def dashboard_lecturer_view(request):
    context = {
        "show_dashboard": True,
    }
    lecturer_name = request.session.get('user_name', '')

    semester_models = [Viewschedule20251, Viewschedule20252, Viewschedule20253]

    semester_model = {
        '20251': Viewschedule20251,
        '20252': Viewschedule20252,
        '20253': Viewschedule20253
    }

    # Get the selected schedule from the request
    schedule_choice_doughnut = request.GET.get('schedule_choice_doughnut', '20251')
    schedule_choice_bar = request.GET.get('schedule_choice_bar', '20251')

    #barchart for room distribution
    room_counts = {}

    # Get the schedules for the selected semester (no lecturer filter)
    schedule_model_bar = semester_model.get(schedule_choice_bar)

    if schedule_model_bar:
        schedules = schedule_model_bar.objects.filter(
            Q(lecturer1__icontains=lecturer_name) |
            Q(lecturer2__icontains=lecturer_name) |
            Q(lecturer3__icontains=lecturer_name)
        )  # Get all schedules, not just the lecturer's

        for schedule in schedules:
            try:
                # Split room if there are multiple rooms
                rooms = schedule.room.split('/')  # Split rooms (e.g., "B401/B203")
                for room in rooms:
                    room = room.strip()  # Clean the room name (remove spaces)
                    if room:
                        # Aggregate the counts for the same room (sum them)
                        room_counts[room] = room_counts.get(room, 0) + 1  # Sum values for the same room
            except AttributeError:
                continue

    # Sort room_counts in descending order and get the top 5 rooms
    sorted_rooms = sorted(room_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Get the top 5 room labels and values
    room_labels = [room[0] for room in sorted_rooms]  # Room names (e.g., B401, B402, etc.)
    room_values = [room[1] for room in sorted_rooms]

    # Doughnut chart (class distribution by day)
    day_counts = {'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0}

    schedule_model_doughnut = semester_model.get(schedule_choice_doughnut)

    if schedule_model_doughnut:
        schedules = schedule_model_doughnut.objects.filter(
            Q(lecturer1__icontains=lecturer_name) |
            Q(lecturer2__icontains=lecturer_name) |
            Q(lecturer3__icontains=lecturer_name)
        )  # Get all schedules, not just the lecturer's

        for schedule in schedules:
            try:
                # Split schedule time if there are multiple time slots (e.g., "Mon, 07:00-09:00 / Tue, 10:00-11:00")
                time_slots = schedule.schedule_time.split(' / ')  # Split time slots by '/'
                for time_slot in time_slots:
                    day_time = time_slot.split(', ')  # Split day and time (e.g., ["Mon", "07:00-09:00"])
                    if len(day_time) == 2:
                        day = day_time[0]  # Extract the day (e.g., "Mon")
                        if day in day_counts:
                            day_counts[day] += 1  # Increment the class count for that day
            except AttributeError:
                continue

    # Prepare the data for the doughnut chart (count per day)
    day_counts_values = list(day_counts.values())
    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    # Check if there are no classes
    no_classes_warning = day_counts_values == [0, 0, 0, 0, 0]

    # Update context with all the necessary data
    context.update({
        'lecturer_name': lecturer_name,
        'day_counts_values': day_counts_values,
        'labels': labels,
        'schedule_choice_doughnut': schedule_choice_doughnut,
        'no_classes_warning': no_classes_warning,
        'room_labels': room_labels,
        'room_values': room_values,
        'schedule_choice_bar': schedule_choice_bar,
    })


#dashboard for total courses, classes, and lecturers
    all_courses = []
    all_lecturers = []
    all_classes = []

    total_courses = 0
    total_classes = 0
    total_lecturers = 0

    for model in semester_models:
        courses = model.objects.filter(
                Q(subject__isnull=False) & ~Q(subject='(Tba)')
            ).values('subject').distinct()

        all_courses.extend([subject['subject'] for subject in courses])

        unique_courses = sorted(set(all_courses))
        total_courses = len(unique_courses)

        classes = model.objects.filter(
                Q(class_name__isnull=False) & ~Q(class_name='(Tba)')
            ).values('class_name').distinct()

        all_classes.extend([class_name['class_name'] for class_name in classes])

        unique_classes = sorted(set(all_classes))
        total_classes = len(unique_classes)

        lecturers = model.objects.filter(
                Q(lecturer1__isnull=False) & ~Q(lecturer1='(Tba)') |
                Q(lecturer2__isnull=False) & ~Q(lecturer2='(Tba)') |
                Q(lecturer3__isnull=False) & ~Q(lecturer3='(Tba)')
            ).values('lecturer1', 'lecturer2', 'lecturer3')

        for lecturer in lecturers:
                if lecturer['lecturer1']:
                    all_lecturers.append(lecturer['lecturer1'])
                if lecturer['lecturer2']:
                    all_lecturers.append(lecturer['lecturer2'])
                if lecturer['lecturer3']:
                    all_lecturers.append(lecturer['lecturer3'])

        unique_lecturers = set(all_lecturers)
        total_lecturers = len(unique_lecturers)

    context.update({
        'total_courses': total_courses,
        'total_classes': total_classes,
        'total_lecturers': total_lecturers,
        'lecturer_name': lecturer_name,
        'lecturer_name': lecturer_name,
        'day_counts_values': day_counts_values,
        'labels': labels,
        'schedule_choice_dougnut': schedule_choice_doughnut,
        'schedule_choice_bar': schedule_choice_bar,
    })

    return render(request, 'dashboard_lecturer_view.html', context)


def signin(request):
    users = profile.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = profile.objects.get(username=username)
            if user.password == password:
                if username == 'academic':
                    request.session['user_id'] = user.profile_id  
                    request.session['username'] = user.username
                    return redirect('dashboard')
                elif username == 'Head of Study Program':
                    request.session['user_id'] = user.profile_id  
                    request.session['username'] = user.username
                    return redirect('dashboard_hsp')
                elif username == 'lecturer':
                    request.session['user_id'] = user.profile_id  
                    request.session['username'] = user.username
                    return redirect('dashboard_lecturer') 
                else :
                    return redirect('dashboard_lecturer_view')
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
    return render(request, 'dashboard_hsp.html', context)

def dashboard_lecturer(request):
    if 'user_id' not in request.session:
        return redirect('signin')
    
    if request.session.get('username') != 'lecturer':
        return HttpResponse("Unauthorized", status=403)
    
    context = {
        "show_dashboard": True,
    }
    return render(request, 'dashboard_lecturer.html', context)


def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['username']
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

    semester_data = semester_model.objects.all().order_by('semester_id')

    assign_model = assign_model_title.get(semester_url)
    assignments = assign_model.objects.select_related('semester').all()
    assignment_map = {a.semester.semester_id: a for a in assignments}

    for item in semester_data:
        assignment = assignment_map.get(item.semester_id)
        item.is_assigned = bool(assignment)
        item.assign_id = assignment.assign_id if assignment else None

    paginator = Paginator(semester_data, 25)  
    page_number = int(request.GET.get('page', 1))
    page_obj = paginator.get_page(page_number)

    block_size = 5
    current_block = (page_number - 1) // block_size
    start_block = current_block * block_size + 1
    end_block = min(start_block + block_size - 1, paginator.num_pages)
    page_range = range(start_block, end_block + 1)


    rooms1 = [f'B{str(i).zfill(3)}' for i in range(101, 109)]
    rooms2 = [f'B{str(i).zfill(3)}' for i in range(201, 212)]
    rooms3 = [f'B{str(i).zfill(3)}' for i in range(301, 312)]
    rooms4 = [f'B{str(i).zfill(3)}' for i in range(401, 412)]
    
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
    try:
        if request.method == 'POST':
            semester_id = request.POST.get('semester_id')
            entry_id = request.POST.get('entry_id')
            semester_url = request.POST.get('semester_url')  

            if semester_url == '20251':
                semester_model = semester20251
                assign_model = assignlecturer20251
            elif semester_url == '20252':
                semester_model = semester20252
                assign_model = assignlecturer20252
            else:
                return JsonResponse({'success': False, 'error': 'Invalid semester'}, status=400)

            semester_instance = semester_model.objects.get(semester_id=semester_id)

            if entry_id:
                assign_obj = assign_model.objects.get(assign_id=entry_id)
                assign_obj.semester = semester_instance
                assign_obj.lecturer_day = request.POST.get('day')
                assign_obj.room = request.POST.get('room')
                assign_obj.start_time = request.POST.get('time')
                assign_obj.end_time = request.POST.get('time2')
                assign_obj.save()
                return JsonResponse({'success': True, 'message': 'Assignment updated successfully'})
            else:
                assign_model.objects.create(
                    semester=semester_instance,
                    lecturer_day=request.POST.get('day'),
                    room=request.POST.get('room'),
                    start_time=request.POST.get('time'),
                    end_time=request.POST.get('time2')
                )
                return JsonResponse({'success': True, 'message': 'Assignment created successfully'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

    
def assignlecturer_delete(request):
    if request.method == 'POST':
        semester_id = request.POST.get('semester_id')
        semester_url = request.POST.get('semester_url', '20251')
        
        try:
            if semester_url == '20251':
                model = semester20251
            elif semester_url == '20252':
                model = semester20252
            else:
                return JsonResponse({'success': False, 'error': 'Invalid semester'})
            
            obj = model.objects.get(semester_id=semester_id)
            obj.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                messages.success(request, "Data has been deleted successfully.")
                return redirect('studyprogram', semester_url)
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f"Error deleting data: {str(e)}")
                return redirect('studyprogram', semester_url)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    else:
        messages.error(request, "Invalid request method.")
        return redirect('studyprogram', '20251')
    

@require_POST
def schedulelecturer_delete(request):
    try:
        data = json.loads(request.body)
        assign_id = data.get('assign_id')
        semester_id = data.get('semester_id')
        semester_url = data.get('semester_url')

        if semester_url == '20251':
            assign_model = assignlecturer20251
            semester_model = semester20251
        elif semester_url == '20252':
            assign_model = assignlecturer20252
            semester_model = semester20252
        else:
            return JsonResponse({'success': False, 'error': 'Invalid semester'}, status=400)

        assign_model.objects.filter(assign_id=assign_id).delete()
        
        semester = semester_model.objects.get(semester_id=semester_id)
        semester.is_assigned = False
        semester.save()

        return JsonResponse({
            'success': True,
            'message': 'Assignment deleted successfully',
            'semester_id': semester_id
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

def schedule20251(request):
    schedule = assignlecturer20251.objects.select_related('semester').order_by('room', 'lecturer_day', 'start_time')

    room_schedule = defaultdict(lambda: defaultdict(list))
    conflict_ids = set() 
    has_conflicts = False
    conflict_details = []

    for entry in schedule:
        room_schedule[entry.room][entry.lecturer_day].append(entry)

        for room in room_schedule:
            for day in room_schedule[room]:
                daily_entries = room_schedule[room][day]

            for i in range(len(daily_entries)):
                for j in range(i + 1, len(daily_entries)):
                    entry1 = daily_entries[i]
                    entry2 = daily_entries[j]
                    
                    if entry1.end_time > entry2.start_time and entry1.start_time < entry2.end_time:
                        conflict_ids.add(entry1.assign_id)
                        conflict_ids.add(entry2.assign_id)
                        has_conflicts = True
                        conflict_details.append({
                            'room': room,
                            'day': day,
                            'subject1': entry1.semester.subject,
                            'subject2': entry2.semester.subject,
                            'time1': f"{entry1.start_time.strftime('%H:%M')} - {entry1.end_time.strftime('%H:%M')}",
                            'time2': f"{entry2.start_time.strftime('%H:%M')} - {entry2.end_time.strftime('%H:%M')}",
                        })

    context = {
        'room_schedule': dict(room_schedule),
        'conflict_ids': conflict_ids,
        'has_conflicts': has_conflicts,
        'conflict_details': conflict_details,
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    }
    return render(request, 'schedule20251.html', context)

def schedule20252(request):
    schedule = assignlecturer20252.objects.select_related('semester').order_by('room', 'lecturer_day', 'start_time')

    room_schedule = defaultdict(lambda: defaultdict(list))
    conflict_ids = set() 
    has_conflicts = False
    conflict_details = []

    for entry in schedule:
        room_schedule[entry.room][entry.lecturer_day].append(entry)

    for room in room_schedule:
        for day in room_schedule[room]:
            daily_entries = room_schedule[room][day]

            for i in range(len(daily_entries)):
                for j in range(i + 1, len(daily_entries)):
                    entry1 = daily_entries[i]
                    entry2 = daily_entries[j]
                    
                    if entry1.end_time > entry2.start_time and entry1.start_time < entry2.end_time:
                        conflict_ids.add(entry1.assign_id)
                        conflict_ids.add(entry2.assign_id)
                        has_conflicts = True
                        conflict_details.append({
                            'room': room,
                            'day': day,
                            'subject1': entry1.semester.subject,
                            'subject2': entry2.semester.subject,
                            'time1': f"{entry1.start_time.strftime('%H:%M')} - {entry1.end_time.strftime('%H:%M')}",
                            'time2': f"{entry2.start_time.strftime('%H:%M')} - {entry2.end_time.strftime('%H:%M')}",
                        })

    context = {
        'room_schedule': dict(room_schedule),
        'conflict_ids': conflict_ids,
        'has_conflicts': has_conflicts,
        'conflict_details': conflict_details,
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    }
    return render(request, 'schedule20252.html', context)

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

    rooms1 = [f'B{str(i).zfill(3)}' for i in range(101, 109)]
    rooms2 = [f'B{str(i).zfill(3)}' for i in range(201, 212)]
    rooms3 = [f'B{str(i).zfill(3)}' for i in range(301, 312)]
    rooms4 = [f'B{str(i).zfill(3)}' for i in range(401, 412)]
    
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

def viewschedule20251(request):
    lecturer_name = request.session.get('user_name', '') 

    schedule_data = Viewschedule20251.objects.all()

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(lecturer1__icontains=lecturer_name) |
            Q(lecturer2__icontains=lecturer_name) |
            Q(lecturer3__icontains=lecturer_name)
        )

    day = request.GET.get('day', '').strip()
    if day:
        schedule_data = schedule_data.filter(schedule_time__icontains=day)

    return render(request, 'viewschedule20251.html', {
        'schedule_data': schedule_data,
        'lecturer_name': lecturer_name,
        'day': day
    })

def viewschedule20252(request):
    lecturer_name = request.session.get('user_name', '') 

    schedule_data = Viewschedule20252.objects.all()

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(lecturer1__icontains=lecturer_name) |
            Q(lecturer2__icontains=lecturer_name) |
            Q(lecturer3__icontains=lecturer_name)
        )

    day = request.GET.get('day', '').strip()
    if day:
        schedule_data = schedule_data.filter(schedule_time__icontains=day)

    return render(request, 'viewschedule20252.html', {
        'schedule_data': schedule_data,
        'lecturer_name': lecturer_name,
        'day': day
    })

def viewschedule20253(request):
    lecturer_name = request.session.get('user_name', '') 

    schedule_data = Viewschedule20253.objects.all()

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(lecturer1__icontains=lecturer_name) |
            Q(lecturer2__icontains=lecturer_name) |
            Q(lecturer3__icontains=lecturer_name)
        )

    day = request.GET.get('day', '').strip()
    if day:
        schedule_data = schedule_data.filter(schedule_time__icontains=day)

    return render(request, 'viewschedule20253.html', {
        'schedule_data': schedule_data,
        'lecturer_name': lecturer_name,
        'day': day
    })

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