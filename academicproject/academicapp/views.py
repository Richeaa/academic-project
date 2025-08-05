from django.db import models
from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from .models import profile, semester20251, semester20252, semester20253, semester20243, assignlecturer20251, assignlecturer20252, assignlecturer20253, Lecturer, LecturerPreference
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from .datasubject import subjects
from .ml.predict import run_ml_prediction
from .ml.utils import get_combined_schedule_data
import traceback
import logging
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime
from collections import Counter
import json
from django.core.serializers.json import DjangoJSONEncoder

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
    
    semester_data = semester20251.objects.all()
    
    all_lecturers = set()
    for item in semester_data:
        if item.lecturer_1:
            all_lecturers.add(item.lecturer_1)
        if item.lecturer_2:
            all_lecturers.add(item.lecturer_2)
        if item.lecturer_3:
            all_lecturers.add(item.lecturer_3)
    
    courses_per_major = (
        semester20251.objects
        .values('major')
        .annotate(total_courses=Count('subject', distinct=True))
        .order_by('-total_courses')[:10]
    )

    class_curriculum = (
        semester20251.objects
        .values('curriculum')
        .annotate(total_classes=Count('subject'))
        .order_by('-total_classes')[:10]  
    )

    sks_per_major = (
        semester20251.objects
        .values('major')
        .annotate(total_sks=Sum('credit'))
        .order_by('-total_sks')[:10]
    )

    classes_per_lecturer = (
        semester20251.objects
        .exclude(lecturer_1__isnull=True)
        .exclude(lecturer_1__iexact='(Tba)')
        .exclude(lecturer_1__exact='')
        .values('lecturer_1')
        .annotate(total_classes=Count('subject'))
        .order_by('-total_classes')[:10]
    )

    # total_lecturers = Lecturer.objects.count()
    active_lecturers = Lecturer.objects.count()
    total_courses = semester20251.objects.values('subject').distinct().count()
    new_courses_this_semester = 3
    total_classes = semester20251.objects.count()
    class_delta_percent = -12

    semester_20251_data = list(semester20251.objects.values('major', 'subject', 'credit', 'curriculum', 'lecturer_1'))
    semester_20252_data = list(semester20252.objects.values('major', 'subject', 'credit', 'curriculum', 'lecturer_1'))
    form20253_data = list(semester20243.objects.values('major', 'subject', 'credit', 'curriculum', 'lecturer_1'))

    
    context = {
        'courses_per_major_labels': json.dumps([d['major'] for d in courses_per_major]),
        'courses_per_major_data': json.dumps([d['total_courses'] for d in courses_per_major]),

        'curriculum_labels': json.dumps([d['curriculum'] for d in class_curriculum]),
        'curriculum_data': json.dumps([d['total_classes'] for d in class_curriculum]),

        'sks_labels': json.dumps([d['major'] for d in sks_per_major]),
        'sks_data': json.dumps([float(d['total_sks']) for d in sks_per_major]),

        'lecturer_labels': json.dumps([d['lecturer_1'] for d in classes_per_lecturer]),
        'lecturer_data': json.dumps([d['total_classes'] for d in classes_per_lecturer]),

        'lecturer_count': len(all_lecturers),
        'active_lecturer_count': active_lecturers,
        'course_count': total_courses,
        'new_courses': new_courses_this_semester,
        'class_count': total_classes,
        'class_delta_percent': class_delta_percent,

        'data_20251': json.dumps(semester_20251_data, cls=DjangoJSONEncoder),
        'data_20252': json.dumps(semester_20252_data, cls=DjangoJSONEncoder),
        'data_20253': json.dumps(form20253_data, cls=DjangoJSONEncoder),
    }


    return render(request, 'dashboard_hsp.html', context)

def courses_per_major_api(request, semester_code):
    if semester_code == '20251':
        queryset = semester20251.objects
    elif semester_code == '20252':
        queryset = semester20252.objects
    elif semester_code == '20253':
        queryset = semester20253.objects
    else:
        return JsonResponse({'labels': [], 'values': []})

    data = (
        queryset.values('major')
        .annotate(total_courses=Count('subject', distinct=True))
        .order_by('-total_courses')[:10]
    )

    labels = [d['major'] for d in data]
    values = [d['total_courses'] for d in data]

    return JsonResponse({'labels': labels, 'values': values})



def dashboard_lecturer_view(request):
    if 'user_id' not in request.session:
        return redirect('signin')
    
    if request.session.get('username') == 'academic':
        return HttpResponse("Unauthorized", status=403)
    elif request.session.get('username') == 'Head of Study Program':
        return HttpResponse("Unauthorized", status=403)

    context = {
        "show_dashboard": True,
    }
    lecturer_name = request.session.get('name', '')
    from collections import defaultdict

# Group schedule by day



    semester_model = {
        '20251': assignlecturer20251,
        '20252': assignlecturer20252,
        '20253': assignlecturer20253,
    }

    schedule_choice = request.GET.get('schedule_choice', '20251')

    room_counts = {}

    schedule_model = semester_model.get(schedule_choice)

    day = request.GET.get('day', '').strip()

    schedule_data = schedule_model.objects.select_related('semester').order_by('lecturer_day', 'start_time')

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(semester__lecturer_1__icontains=lecturer_name) | 
            Q(semester__lecturer_2__icontains=lecturer_name) | 
            Q(semester__lecturer_3__icontains=lecturer_name)
        )

    if day:
        schedule_data = schedule_data.filter(lecturer_day__icontains=day)

    no_schedule_warning = not schedule_data.exists()

    if schedule_model:
        schedules = schedule_model.objects.filter(
            Q(semester__lecturer_1__icontains=lecturer_name) |
            Q(semester__lecturer_2__icontains=lecturer_name) |
            Q(semester__lecturer_3__icontains=lecturer_name)
        )  

        for schedule in schedules:
            try:
                
                rooms = schedule.room.split('/')  
                for room in rooms:
                    room = room.strip()  
                    if room:
                        room_counts[room] = room_counts.get(room, 0) + 1 
            except AttributeError:
                continue

    room_labels = [room[0] for room in room_counts.items()]  
    room_values = [room[1] for room in room_counts.items()]

    no_room_distribution_warning = not room_values  
  
    day_counts = {'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0}

    if schedule_model:
        schedules = schedule_model.objects.filter(
            Q(semester__lecturer_1__icontains=lecturer_name) |
            Q(semester__lecturer_2__icontains=lecturer_name) |
            Q(semester__lecturer_3__icontains=lecturer_name)
        )  
        for schedule in schedules:
            try:
                day = schedule.lecturer_day.strip() 
                if day in day_counts:
                    day_counts[day] += 1
            except AttributeError:
                continue

    day_counts_values = list(day_counts.values())
    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    no_classes_warning = day_counts_values == [0, 0, 0, 0, 0]

    context.update({
        'lecturer_name': lecturer_name,
        'day_counts_values': day_counts_values,
        'labels': labels,
        'schedule_choice': schedule_choice,
        'no_classes_warning': no_classes_warning,
        'no_room_distribution_warning': no_room_distribution_warning,
        'room_labels': room_labels,
        'room_values': room_values,
        'schedule_data': schedule_data,
        'no_schedule_warning': no_schedule_warning,
    })

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


    context.update({
        'lecturer_name': lecturer_name,
        'day_counts_values': day_counts_values,
        'labels': labels,
        'schedule_choice': schedule_choice,
        'no_classes_warning': no_classes_warning,
        'room_labels': room_labels,
        'room_values': room_values,
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'total_lecturers': total_lecturers,
        'total_classes': total_classes,
        'total_subjects': total_subjects
    })

    
    return render(request, 'dashboard_lecturer_view.html', context)



def signin(request):
    users = profile.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')

        try:
            user = profile.objects.get(username=username)
            if user.password == password:
                request.session['name'] = user.name
                if username == 'academic':
                    request.session['user_id'] = user.profile_id  
                    request.session['username'] = user.username
                    return redirect('dashboard')
                elif username == 'Head of Study Program':
                    request.session['user_id'] = user.profile_id  
                    request.session['username'] = user.username
                    return redirect('dashboard_hsp')
                # elif username == 'lecturer':
                #     request.session['user_id'] = user.profile_id  
                #     request.session['username'] = user.username
                #     return redirect('dashboard_lecturer') 
                else :
                    request.session['user_id'] = user.profile_id  
                    request.session['username'] = user.username
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
    '20253': semester20253,
}

assign_model_title = {
    '20251': assignlecturer20251,
    '20252': assignlecturer20252,
    '20253': assignlecturer20253,
}

def studyprogram(request, semester_url='20251'):
    semester_model = semester_title.get(semester_url)
    if not semester_model:
        return HttpResponse("Semester not found", status=404)

    program_filter = request.GET.get('program_session', '')
    search_term = request.GET.get('search', '')

    semester_queryset = semester_model.objects.all()

    if program_filter and program_filter in ['M', 'N']:
        semester_queryset = semester_queryset.filter(program_session__icontains=program_filter)
    
    if search_term:
        semester_queryset = semester_queryset.filter(
            Q(semester_id__icontains=search_term) |
            Q(program_session__icontains=search_term) |
            Q(major__icontains=search_term) |
            Q(curriculum__icontains=search_term) |
            Q(major_class__icontains=search_term) |
            Q(subject__icontains=search_term) |
            Q(lecturer_1__icontains=search_term) |
            Q(lecturer_2__icontains=search_term) |
            Q(lecturer_3__icontains=search_term)
        )

    semester_data = semester_queryset.order_by('semester_id')

    assign_model = assign_model_title.get(semester_url)
    assignments = assign_model.objects.select_related('semester').all()
    assignment_map = {a.semester.semester_id: a for a in assignments}

    for item in semester_data:
        assignment = assignment_map.get(item.semester_id)
        item.is_assigned = bool(assignment)
        item.assign_id = assignment.assign_id if assignment else None

    paginator = Paginator(semester_data, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    block_size = 5
    current_block = (page_obj.number - 1) // block_size
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
        'current_program_filter': program_filter,
        'current_search': search_term,
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
            elif semester_url == '20253':
                semester_model = semester20253
                assign_model = assignlecturer20253
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
            elif semester_url == '20253':
                model = semester20253
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
        elif semester_url == '20253':
            assign_model = assignlecturer20253
            semester_model = semester20253
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
            daily_entries = sorted(room_schedule[room][day], key=lambda x: x.start_time)
            
            for i in range(len(daily_entries)):
                for j in range(i + 1, len(daily_entries)):
                    entry1 = daily_entries[i]
                    entry2 = daily_entries[j]
                    
                    if entry1.end_time > entry2.start_time and entry1.start_time < entry2.end_time:
                        conflict_ids.add(entry1.assign_id)
                        conflict_ids.add(entry2.assign_id)
                        has_conflicts = True

                        pair_id = tuple(sorted((entry1.assign_id, entry2.assign_id)))
                        existing_conflict_ids = {tuple(sorted((d['entry1_id'], d['entry2_id']))) for d in conflict_details}
                        
                        if pair_id not in existing_conflict_ids:
                            conflict_details.append({
                                'room': room,
                                'day': day,
                                'subject1': entry1.semester.subject,
                                'subject2': entry2.semester.subject,
                                'time1': f"{entry1.start_time.strftime('%H:%M')} - {entry1.end_time.strftime('%H:%M')}",
                                'time2': f"{entry2.start_time.strftime('%H:%M')} - {entry2.end_time.strftime('%H:%M')}",
                                'entry1_id': entry1.assign_id,
                                'entry2_id': entry2.assign_id,
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

def schedule20253(request):
    schedule = assignlecturer20253.objects.select_related('semester').order_by('room', 'lecturer_day', 'start_time')

    room_schedule = defaultdict(lambda: defaultdict(list))
    conflict_ids = set() 
    has_conflicts = False
    conflict_details = []

    for entry in schedule:
        room_schedule[entry.room][entry.lecturer_day].append(entry)

    for room in room_schedule:
        for day in room_schedule[room]:
            daily_entries = sorted(room_schedule[room][day], key=lambda x: x.start_time)
            
            for i in range(len(daily_entries)):
                for j in range(i + 1, len(daily_entries)):
                    entry1 = daily_entries[i]
                    entry2 = daily_entries[j]
                    
                    if entry1.end_time > entry2.start_time and entry1.start_time < entry2.end_time:
                        conflict_ids.add(entry1.assign_id)
                        conflict_ids.add(entry2.assign_id)
                        has_conflicts = True
                        
                        if entry1.assign_id < entry2.assign_id:  
                            conflict_details.append({
                                'room': room,
                                'day': day,
                                'subject1': entry1.semester.subject,
                                'subject2': entry2.semester.subject,
                                'time1': f"{entry1.start_time.strftime('%H:%M')} - {entry1.end_time.strftime('%H:%M')}",
                                'time2': f"{entry2.start_time.strftime('%H:%M')} - {entry2.end_time.strftime('%H:%M')}",
                                'entry1_id': entry1.assign_id,
                                'entry2_id': entry2.assign_id,
                            })

    context = {
        'room_schedule': dict(room_schedule),
        'conflict_ids': conflict_ids,
        'has_conflicts': has_conflicts,
        'conflict_details': conflict_details,
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    }
    return render(request, 'schedule20253.html', context)

def lecturer(request):
    lecturer_name = request.GET.get('lecturer_name', '')
    job = request.GET.get('job', '')

    lecturers = Lecturer.objects.all()

    if lecturer_name:
        lecturers = lecturers.filter(lecturer_name__icontains=lecturer_name)

    if job:
        lecturers = lecturers.filter(job=job)

    paginator = Paginator(lecturers, 30)  
    page = request.GET.get('page')
    lecturers_page = paginator.get_page(page)

    job_choices = Lecturer.objects.values_list('job', flat=True).distinct()

    page_range = paginator.get_elided_page_range(number=lecturers_page.number, on_each_side=1, on_ends=1)

    return render(request, 'lecturer.html', {
        'lecturers': lecturers_page,
        'page_range': page_range,
        'job_choices': job_choices,
    })


def formstudyprogram(request, semester_url='20251'): 
    semester_model = semester_title.get(semester_url)
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

def viewschedule20251(request):
    lecturer_name = request.session.get('name', '')

    day = request.GET.get('day', '').strip()
    room_schedule = defaultdict(lambda: defaultdict(list))

    schedule_data = assignlecturer20251.objects.select_related('semester').order_by('lecturer_day', 'start_time')

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(semester__lecturer_1__icontains=lecturer_name) | 
            Q(semester__lecturer_2__icontains=lecturer_name) | 
            Q(semester__lecturer_3__icontains=lecturer_name)
        )

    if day:
        schedule_data = schedule_data.filter(lecturer_day__icontains=day)

    no_schedule_warning = not schedule_data.exists()

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']


    return render(request, 'viewschedule20251.html', {
        'days': days,
        'room_schedule': dict(room_schedule),
        'schedule_data': schedule_data,
        'lecturer_name': lecturer_name,
        'day': day, 
        'no_schedule_warning': no_schedule_warning
    })

def viewschedule20252(request):
    lecturer_name = request.session.get('name', '')

    day = request.GET.get('day', '').strip()

    schedule_data = assignlecturer20252.objects.select_related('semester').order_by('lecturer_day', 'start_time')

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(semester__lecturer_1__icontains=lecturer_name) | 
            Q(semester__lecturer_2__icontains=lecturer_name) | 
            Q(semester__lecturer_3__icontains=lecturer_name)
        )

    if day:
        schedule_data = schedule_data.filter(lecturer_day__icontains=day)

    no_schedule_warning = not schedule_data.exists()

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    return render(request, 'viewschedule20252.html', {
        'schedule_data': schedule_data,
        'lecturer_name': lecturer_name,
        'day': day, 
        'days': days,
        'no_schedule_warning': no_schedule_warning
    })

def viewschedule20253(request):
    lecturer_name = request.session.get('name', '')

    day = request.GET.get('day', '').strip()

    schedule_data = assignlecturer20253.objects.select_related('semester').order_by('lecturer_day', 'start_time')

    if lecturer_name:
        schedule_data = schedule_data.filter(
            Q(semester__lecturer_1__icontains=lecturer_name) | 
            Q(semester__lecturer_2__icontains=lecturer_name) | 
            Q(semester__lecturer_3__icontains=lecturer_name)
        )

    if day:
        schedule_data = schedule_data.filter(lecturer_day__icontains=day)

    no_schedule_warning = not schedule_data.exists()

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    return render(request, 'viewschedule20253.html', {
        'schedule_data': schedule_data,
        'lecturer_name': lecturer_name,
        'days': days,
        'day': day, 
        'no_schedule_warning': no_schedule_warning
    })




@csrf_exempt
@require_http_methods(["POST"])
def add_academic_module(request, semester_url):
    if request.method == 'POST':
        semester_model = semester_title.get(semester_url)
        if not semester_model:
            return JsonResponse({'success': False, 'error': 'Semester tidak ditemukan'}, status=404)

        try:
            max_id = semester_model.objects.all().aggregate(models.Max('semester_id'))['semester_id__max'] or 0
            new_id = max_id + 1
            
            if semester_url == '20253':
              
                for i in range(2):
                    semester_model.objects.create(
                        semester_id=new_id + i,
                        program_session = request.POST.get('program_session'),
                        major = request.POST.get('major'),
                        curriculum = request.POST.get('curriculum'),
                        major_class = request.POST.get('major_class'),
                        subject = request.POST.get('subject'),
                        credit = request.POST.get('credit'),
                        lecturer_1 = request.POST.get('lecturer_1'),
                        lecturer_2 = request.POST.get('lecturer_2'),
                        lecturer_3 = request.POST.get('lecturer_3'),
                    )
            else:
                semester_model.objects.create(
                    semester_id=new_id,
                    program_session = request.POST.get('program_session'),
                    major = request.POST.get('major'),
                    curriculum = request.POST.get('curriculum'),
                    major_class = request.POST.get('major_class'),
                    subject = request.POST.get('subject'),
                    credit = request.POST.get('credit'),
                    lecturer_1 = request.POST.get('lecturer_1'),
                    lecturer_2 = request.POST.get('lecturer_2'),
                    lecturer_3 = request.POST.get('lecturer_3'),
                )

            return JsonResponse({'success': True, 'message': 'Data berhasil ditambahkan'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@csrf_exempt
@require_http_methods(["POST"])
def edit_academic_module(request, semester_url):
    try:
        semester_model = semester_title.get(semester_url)
        if not semester_model:
            return JsonResponse({'success': False, 'error': 'Semester not found'}, status=404)

       
        record_id = request.POST.get('record_id')
        program_session = request.POST.get('program_session')
        major = request.POST.get('major')
        curriculum = request.POST.get('curriculum')
        major_class = request.POST.get('major_class')
        subject = request.POST.get('subject')
        credit = request.POST.get('credit')
        lecturer_1 = request.POST.get('lecturer_1')
        lecturer_2 = request.POST.get('lecturer_2')
        lecturer_3 = request.POST.get('lecturer_3')

        if semester_url == '20253':
            
            if not record_id:
                return JsonResponse({'success': False, 'error': 'Record ID is required'}, status=400)
                
            try:
             
                clicked_record = semester_model.objects.get(semester_id=record_id)
                print(f"Clicked record ID: {record_id}")
                print(f"Clicked record data: {clicked_record}")
            except semester_model.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Clicked record not found'}, status=404)
       
            filter_conditions = []
            
         
            if clicked_record.program_session:
                filter_conditions.append(Q(program_session=clicked_record.program_session))
            else:
                filter_conditions.append(Q(program_session__isnull=True) | Q(program_session=''))
            
         
            if clicked_record.major:
                filter_conditions.append(Q(major=clicked_record.major))
            else:
                filter_conditions.append(Q(major__isnull=True) | Q(major=''))
            
            
            if clicked_record.curriculum:
                filter_conditions.append(Q(curriculum=clicked_record.curriculum))
            else:
                filter_conditions.append(Q(curriculum__isnull=True) | Q(curriculum=''))
            
          
            if clicked_record.major_class:
                filter_conditions.append(Q(major_class=clicked_record.major_class))
            else:
                filter_conditions.append(Q(major_class__isnull=True) | Q(major_class=''))
            
            
            if clicked_record.subject:
                filter_conditions.append(Q(subject=clicked_record.subject))
            else:
                filter_conditions.append(Q(subject__isnull=True) | Q(subject=''))
            
            
            if clicked_record.credit:
                filter_conditions.append(Q(credit=clicked_record.credit))
            else:
                filter_conditions.append(Q(credit__isnull=True) | Q(credit=''))
            
            combined_filter = Q()
            for condition in filter_conditions:
                combined_filter &= condition
            
            records = semester_model.objects.filter(combined_filter)
            
            print(f"Filter conditions: {filter_conditions}")
            print(f"Found {records.count()} matching records")
            print(f"Record IDs: {[r.semester_id for r in records]}")
            
            if not records.exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'No matching records found',
                    'details': f'Looking for records matching clicked record {record_id}'
                }, status=404)

           
            updated_count = 0
            updated_ids = []
            for record in records:
                record.program_session = program_session
                record.major = major
                record.curriculum = curriculum
                record.major_class = major_class
                record.subject = subject
                record.credit = credit
                record.lecturer_1 = lecturer_1
                record.lecturer_2 = lecturer_2
                record.lecturer_3 = lecturer_3
                record.save()
                updated_count += 1
                updated_ids.append(record.semester_id)
                
            print(f"Updated record IDs: {updated_ids}")
                
            return JsonResponse({
                'success': True, 
                'message': f'Successfully updated {updated_count} academic module record(s)',
                'updated_ids': updated_ids
            })
            
        else:
           
            if not record_id:
                return JsonResponse({'success': False, 'error': 'Record ID is required'}, status=400)

            try:
                record = semester_model.objects.get(semester_id=record_id)
            except semester_model.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)

            record.program_session = program_session
            record.major = major
            record.curriculum = curriculum
            record.major_class = major_class
            record.subject = subject
            record.credit = credit
            record.lecturer_1 = lecturer_1
            record.lecturer_2 = lecturer_2
            record.lecturer_3 = lecturer_3
            record.save()
            
            return JsonResponse({'success': True, 'message': 'Academic module updated successfully'})

    except Exception as e:
        print(f"Exception in edit_academic_module: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def delete_academic_module(request, semester_url, semester_id): 
    if request.method == 'POST':
        model = semester_title.get(semester_url)
        if not model:
            return JsonResponse({'success': False, 'error': 'Invalid semester.'})

        try:
            if semester_url == '20253':
              
                reference = model.objects.get(pk=semester_id)
               
                deleted, _ = model.objects.filter(
                    program_session=reference.program_session,
                    major=reference.major,
                    curriculum=reference.curriculum,
                    major_class=reference.major_class,
                    subject=reference.subject,
                    credit=reference.credit
                ).delete()
                return JsonResponse({'success': True, 'message': f'{deleted} record(s) deleted successfully.'})
            else:
                obj = model.objects.get(pk=semester_id)
                obj.delete()
                return JsonResponse({'success': True, 'message': 'Record deleted successfully.'})
        except model.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Record not found.'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
def subject_list(request):
    return JsonResponse(subjects, safe=False)

logger = logging.getLogger(__name__)

def prediction_view(request):
    return render(request, 'prediction.html')

@csrf_exempt
@require_http_methods(["POST"])
def predict_schedule(request):
    try:
        data = json.loads(request.body)
        semester_choice = data.get('semester')
        
        if not semester_choice:
            return JsonResponse({
                'success': False,
                'error': 'Semester selection is required'
            }, status=400)
        
        if semester_choice not in ['20251', '20252', '20253']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid semester choice'
            }, status=400)
        
        # Run ML
        logger.info(f"Starting ML prediction for semester {semester_choice}")
        success, message, saved_count = run_ml_prediction(semester_choice)
        
        if success:
            logger.info(f"ML prediction completed: {message}")
            return JsonResponse({
                'success': True,
                'message': message,
                'saved_count': saved_count
            })
        else:
            logger.error(f"ML prediction failed: {message}")
            return JsonResponse({
                'success': False,
                'error': message
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in predict_schedule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_schedule(request):
    try:
        # request schedule data
        data = json.loads(request.body)
        semester_choice = data.get('semester')
        page = int(data.get('page', 1))
        page_size = int(data.get('page_size', 10))
        
        sort_by = data.get('sort_by', '')
        filter_status = data.get('filter_status', 'all')  
        
        if not semester_choice:
            return JsonResponse({
                'success': False,
                'error': 'Semester selection is required'
            }, status=400)
        
        if semester_choice not in ['20251', '20252','20253']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid semester choice'
            }, status=400)
        
        schedule_data = get_combined_schedule_data(
            semester_choice, page, page_size, sort_by, filter_status
        )
        
        return JsonResponse({
            'success': True,
            **schedule_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in get_schedule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to load schedule: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def clear_assignments(request):
    try:
        data = json.loads(request.body)
        semester_choice = data.get('semester')
        
        if not semester_choice:
            return JsonResponse({
                'success': False,
                'error': 'Semester selection is required'
            }, status=400)
        
        if semester_choice not in ['20251', '20252','20253']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid semester choice'
            }, status=400)
        
        if semester_choice == '20251':
            from .models import assignlecturer20251 as AssignModel
        elif semester_choice == '20252':
            from .models import assignlecturer20252 as AssignModel
        else:
            from .models import assignlecturer20253 as AssignModel
        
        # Clear all assignments
        deleted_count = AssignModel.objects.all().count()
        AssignModel.objects.all().delete()
        
        logger.info(f"Cleared {deleted_count} assignments for semester {semester_choice}")
        
        return JsonResponse({
            'success': True,
            'message': f'Cleared {deleted_count} assignments',
            'deleted_count': deleted_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in clear_assignments: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to clear assignments: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def prediction_stats(request):
    try:
        semester_choice = request.GET.get('semester')
        
        if not semester_choice:
            return JsonResponse({
                'success': False,
                'error': 'Semester parameter is required'
            }, status=400)
        
        if semester_choice not in ['20251', '20252', '20253']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid semester choice'
            }, status=400)
        
        if semester_choice == '20251':
            from .models import semester20251 as SemesterModel
            from .models import assignlecturer20251 as AssignModel
        
        elif semester_choice == '20252':
            from .models import semester20252 as SemesterModel
            from .models import assignlecturer20252 as AssignModel
        else:
            from .models import semester20253 as SemesterModel
            from .models import assignlecturer20253 as AssignModel
        
        # calculate percentage
        total_classes = SemesterModel.objects.count()
        assigned_classes = AssignModel.objects.count()
        unassigned_classes = total_classes - assigned_classes
        
        assigned_percentage = (assigned_classes / total_classes * 100) if total_classes > 0 else 0
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_classes': total_classes,
                'assigned_classes': assigned_classes,
                'unassigned_classes': unassigned_classes,
                'assigned_percentage': round(assigned_percentage, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in prediction_stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to get statistics: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def debug_unassigned(request):
    try:
        semester_choice = request.GET.get('semester', '20251')
        
        from .ml.utils import get_unassigned_classes
        unassigned_df = get_unassigned_classes(semester_choice)
        
        unassigned_data = unassigned_df.to_dict('records') if not unassigned_df.empty else []
        
        return JsonResponse({
            'success': True,
            'semester': semester_choice,
            'count': len(unassigned_data),
            'unassigned_classes': unassigned_data[:10]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def preference_view(request):
    lecturerpreference = LecturerPreference.objects.all()
    lecturerpreference = lecturerpreference.order_by('lecturer_name')
    
    return render(request, 'lecturerpref.html', {'lecturerpreference': lecturerpreference})

def add_preference(request):
    if request.method == 'POST':
        LecturerPreference.objects.create(
            lecturer_name=request.POST.get('lecturer_name'),
            time_preference=request.POST.get('time_preference'),
            day_preference=request.POST.get('day_preference'),
            room_preference=request.POST.get('room_preference'),
            notes=request.POST.get('notes')
        )
        messages.success(request, "Added successfully.")
        return redirect('preference')
    
def delete_preference(request):
    if request.method == 'POST':
        pref_id = request.POST.get('pref_id')
        try:
            LecturerPreference.objects.get(id=pref_id).delete()
        except LecturerPreference.DoesNotExist:
            pass
    messages.success(request, "Deleted successfully.")
    return redirect('preference')

def edit_preference(request, pref_id):
    pref = get_object_or_404(LecturerPreference, pk=pref_id)

    if request.method == 'POST':
        pref.lecturer_name = request.POST.get('lecturer_name')
        pref.time_preference = request.POST.get('time_preference')
        pref.day_preference = request.POST.get('day_preference')
        pref.room_preference = request.POST.get('room_preference')
        pref.notes = request.POST.get('notes')
        pref.save()
        messages.success(request, "Updated successfully.")
        return redirect('preference')