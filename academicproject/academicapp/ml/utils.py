import pandas as pd
from django.apps import apps
from datetime import datetime, timedelta
import json
import os

def get_unassigned_classes(semester_choice):
    if semester_choice == '20251':
        SemesterModel = apps.get_model('academicapp', 'semester20251')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20251')
    elif semester_choice == '20252':
        SemesterModel = apps.get_model('academicapp', 'semester20252')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20252')
    elif semester_choice == '20253':
        SemesterModel = apps.get_model('academicapp', 'semester20253')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20253')
    else:
        raise ValueError(f"Invalid semester choice: {semester_choice}")
    
    semester_data = SemesterModel.objects.all().values(
        'semester_id', 'program_session', 'major', 'curriculum', 
        'major_class', 'subject', 'credit', 'lecturer_1', 'lecturer_2', 'lecturer_3'
    )
    
    df = pd.DataFrame(semester_data)
    
    if df.empty:
        return pd.DataFrame()
    
    df = df.rename(columns={
        'major_class': 'Class',
        'program_session': 'Program Session',
        'major': 'Major',
        'curriculum': 'Curriculum',
        'subject': 'Subject',
        'credit': 'Cr',
        'lecturer_1': '#1',
        'lecturer_2': '#2',
        'lecturer_3': '#3'
    })
    
    assigned_semester_ids = set(
        AssignModel.objects.values_list('semester_id', flat=True)
    )
    
    unassigned_df = df[~df['semester_id'].isin(assigned_semester_ids)].copy()
    
    return unassigned_df

def get_preferences_df():
    LecturerPreference = apps.get_model('academicapp', 'LecturerPreference')
    
    preferences_data = LecturerPreference.objects.all().values(
        'lecturer_name', 'time_preference', 'day_preference', 
        'room_preference', 'notes'
    )
    
    df = pd.DataFrame(preferences_data)
    
    if df.empty:
        return pd.DataFrame()
    
    df = df.rename(columns={
        'lecturer_name': 'Nama',
        'time_preference': 'Time Preference',
        'day_preference': 'Day Preference',
        'room_preference': 'Room Preference',
        'notes': 'Notes'
    })
    
    return df

def get_available_rooms():
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'model', 'rooms.json')
        with open(json_path, 'r') as f:
            rooms_data = json.load(f)
        return rooms_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading rooms JSON: {e}")
        # Fallback
        return [
            'A423 Moot Court Room', 'A429 (MMTek Classroom)', 'A428 (Lab Accounting)',
            'B109 (VCD)', 'B110 (VCD)', 'C201 (Interior Design Laboratory) (PUCC)',
        ]

def get_available_times():
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'model', 'available_times.json')
        with open(json_path, 'r') as f:
            times_data = json.load(f)
        return times_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading times JSON: {e}")
        # Fallback
        return [
            'Mon, 08:00-09:35', 'Mon, 09:45-11:20', 'Mon, 11:30-13:05',
            'Mon, 14:00-15:35', 'Mon, 15:45-17:20', 'Mon, 17:30-19:05',
            'Tue, 08:00-09:35', 'Tue, 09:45-11:20', 'Tue, 11:30-13:05',
            'Tue, 14:00-15:35', 'Tue, 15:45-17:20', 'Tue, 17:30-19:05',
            'Wed, 08:00-09:35', 'Wed, 09:45-11:20', 'Wed, 11:30-13:05',
            'Wed, 14:00-15:35', 'Wed, 15:45-17:20', 'Wed, 17:30-19:05',
            'Thu, 08:00-09:35', 'Thu, 09:45-11:20', 'Thu, 11:30-13:05',
            'Thu, 14:00-15:35', 'Thu, 15:45-17:20', 'Thu, 17:30-19:05',
            'Fri, 08:00-09:35', 'Fri, 09:45-11:20', 'Fri, 11:30-13:05',
            'Fri, 14:00-15:35', 'Fri, 15:45-17:20', 'Fri, 17:30-19:05',
        ]

def save_predictions_to_db(predictions_df, semester_choice):
    if semester_choice == '20251':
        AssignModel = apps.get_model('academicapp', 'assignlecturer20251')
        SemesterModel = apps.get_model('academicapp', 'semester20251')
    elif semester_choice == '20252':
        AssignModel = apps.get_model('academicapp', 'assignlecturer20252')
        SemesterModel = apps.get_model('academicapp', 'semester20252')
    elif semester_choice == '20253':
        SemesterModel = apps.get_model('academicapp', 'semester20253')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20253')
    else:
        raise ValueError(f"Invalid semester choice: {semester_choice}")
    
    saved_count = 0
    
    for _, row in predictions_df.iterrows():
        if pd.isna(row.get('Room')) or pd.isna(row.get('Sched. Time')) or \
           row.get('Room') == '-' or row.get('Sched. Time') == '-':
            continue
            
        try:
            # Parse schedule time
            schedule_time = row['Sched. Time']
            if ', ' in schedule_time and '-' in schedule_time:
                day_time_part = schedule_time.split(', ')[1]
                start_time_str, end_time_str = day_time_part.split('-')
                day = schedule_time.split(', ')[0]
                
                # Convert to time objects
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                # Get semester instance
                semester_instance = SemesterModel.objects.get(
                    semester_id=row['semester_id']
                )
                
                # Create assignment
                AssignModel.objects.create(
                    semester=semester_instance,
                    lecturer_day=day,
                    room=row['Room'],
                    start_time=start_time,
                    end_time=end_time
                )
                saved_count += 1
                
        except Exception as e:
            print(f"Error saving assignment for semester_id {row.get('semester_id')}: {e}")
            continue
    
    return saved_count

def get_combined_schedule_data(semester_choice, page=1, page_size=10): #Display
    if semester_choice == '20251':
        SemesterModel = apps.get_model('academicapp', 'semester20251')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20251')
    elif semester_choice == '20252':
        SemesterModel = apps.get_model('academicapp', 'semester20252')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20252')
    elif semester_choice == '20253':
        SemesterModel = apps.get_model('academicapp', 'semester20253')
        AssignModel = apps.get_model('academicapp', 'assignlecturer20253')
    else:
        raise ValueError(f"Invalid semester choice: {semester_choice}")
    
    semester_data = SemesterModel.objects.select_related().all()
    
    # Calculate pagination
    total_count = semester_data.count()
    total_pages = (total_count + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_data = semester_data[start_idx:end_idx]
    
    results = []
    for semester_item in paginated_data:
        try:
            assignment = AssignModel.objects.get(semester=semester_item)
            room = assignment.room
            schedule_time = f"{assignment.lecturer_day}, {assignment.start_time.strftime('%H:%M')}-{assignment.end_time.strftime('%H:%M')}"
        except AssignModel.DoesNotExist:
            room = None
            schedule_time = None
        
        results.append({
            'semester_id': semester_item.semester_id,
            'program_session': semester_item.program_session,
            'major': semester_item.major,
            'curriculum': semester_item.curriculum,
            'major_class': semester_item.major_class,
            'subject': semester_item.subject,
            'credit': float(semester_item.credit),
            'lecturer_1': semester_item.lecturer_1 or '-',
            'lecturer_2': semester_item.lecturer_2 or '-',
            'lecturer_3': semester_item.lecturer_3 or '-',
            'room': room,
            'schedule_time': schedule_time,
        })
    
    return {
        'results': results,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page
    }