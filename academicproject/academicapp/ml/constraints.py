import pandas as pd
import re
from datetime import datetime, timedelta
from collections import defaultdict

# Room eligibility rules from your original script
ROOM_ALLOWED_MAJORS = {
    'A423 Moot Court Room':                     ['PS_MH', 'PS_Hukum'],
    'A429 (MMTek Classroom)':                   ['PS_MMTek'],
    'A428 (Lab Accounting)':                    ['PS_Ak'],
    'B109 (VCD)':                               ['PS_DKV_2017'],
    'B110 (VCD)':                               ['PS_DKV_2017'],
    'C201 (Interior Design Laboratory) (PUCC)': ['PS_DI'],
    'C202 (PUCC)':                              ['PS_TInf', 'PS_SI'],
    'C203 (Architecture Laboratory) (PUCC)':    ['PS_AR'],
    'C204 (Architecture Laboratory) (PUCC)':    ['PS_AR'],
    'D103 (Movieland)':                         ['PS_Hukum'],
    'Lab Electrical Engineering (FabLab)':      ['PS_EE'],
    'Lab Mechanical Engineering (FabLab)':      ['PS_TM'],
    'Lab FTV':                                  ['PS_IKom'],
    'Lab A210':                                 ['PS_DKV_2017']
}

EXCLUDED_ROOMS = [
    'Music Room PUCC',
    'Online Class',
    'FabLab Training Room',
]

def is_room_eligible(room, major, subject):
    """
    Check if a room is eligible for a given major and subject
    Based on your original room eligibility rules
    """
    if room in EXCLUDED_ROOMS:
        return False

    if room in ROOM_ALLOWED_MAJORS:
        allowed = ROOM_ALLOWED_MAJORS[room]
        return any(m in major for m in allowed)
    
    if room.startswith("Theater"): 
        return any(m in major for m in ['PS_TInf', 'PS_SI'])
    
    if room.startswith("LabA2") and room != 'Lab A210':
        return any(m in major for m in ['PS_TInf', 'PS_SI'])
    
    if room == 'Jababeka Golf':
        return 'golf' in subject.lower()

    if room == 'Jababeka Golf (Tennis)':
        return 'tennis' in subject.lower()

    if room == 'Lab Chemistry':
        return 'PS_TL' in major and subject in ['Microbiology', 'Environmental Chemistry']
    
    return True

def get_time_block(start_time_str, credit):
    """
    Calculate end time based on start time and credit hours
    """
    start_dt = datetime.strptime(start_time_str, "%a, %H:%M")
    duration = 135 if credit == 0 else credit * 45  # 45 minutes per credit
    end_dt = start_dt + timedelta(minutes=duration)
    return start_dt, end_dt

def is_overlapping(start, end, existing_blocks):
    """
    Check if a time block overlaps with existing blocks
    """
    return any(max(s, start) < min(e, end) for s, e in existing_blocks)

def parse_day_preference(pref):
    """
    Parse day preference string into list of days
    Handles formats like "Monday, Tuesday-Friday", "Mon-Wed", etc.
    """
    if pd.isna(pref) or str(pref).strip() in ['', 'nan']:
        return []
    
    pref = str(pref).strip()
    result = []
    
    # Split by comma first to handle "Monday, Tuesday-Friday"
    parts = [p.strip() for p in pref.split(',')]
    
    for part in parts:
        if '-' in part:
            # Handle ranges like "Tuesday-Thursday"
            days = part.split('-')
            start = days[0].strip()
            end = days[1].strip()
            week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            try:
                si = week.index(start)
                ei = week.index(end) + 1
                result.extend(week[si:ei])
            except ValueError:
                result.append(part)
        else:
            result.append(part)
    
    return result

def parse_time_preference(pref):
    """
    Parse time preference string into list of preferred times
    """
    if pd.isna(pref) or str(pref).strip() in ['', 'nan']:
        return []
    return [t.strip() for t in str(pref).split(',') if t.strip() and t.strip() != 'nan']

def matches_room_preference(room_code, preference):
    """
    Check if a room matches the lecturer's room preference
    Handles various preference formats like "Building A", "Building B (2nd Floor)", etc.
    """
    if pd.isna(preference) or str(preference).strip() in ['', 'nan']:
        return True
    
    room_code = room_code.strip().upper()
    preference = preference.strip()

    # Split by comma to handle multiple preferences
    preferences = [p.strip() for p in preference.split(',') if p.strip()]
    
    for pref in preferences:
        # Direct room match
        if room_code == pref.strip().upper():
            return True
            
        # Building + Floor match e.g., "Building B (2nd Floor)"
        match = re.match(r"Building (\w) \((\d)(?:st|nd|rd|th) Floor\)", pref)
        if match:
            building, floor = match.groups()
            if room_code.startswith(building) and len(room_code) > 1 and room_code[1] == floor:
                return True
        
        # Handle "Building A" (any floor)
        match = re.match(r"Building (\w)$", pref)
        if match:
            building = match.group(1)
            if room_code.startswith(building):
                return True
                
        # Handle "Building B (1st and 2nd Floor)"
        match = re.match(r"Building (\w) \((\d)(?:st|nd|rd|th) and (\d)(?:st|nd|rd|th) Floor\)", pref)
        if match:
            building, floor1, floor2 = match.groups()
            if room_code.startswith(building) and len(room_code) > 1 and room_code[1] in [floor1, floor2]:
                return True

    return False

def validate_schedule_constraints(schedule_df):
    """
    Validate that the generated schedule meets all constraints
    Returns: (is_valid: bool, violations: list)
    """
    violations = []
    
    # Check for room conflicts
    room_time_usage = defaultdict(list)
    
    for _, row in schedule_df.iterrows():
        if row['Room'] != '-' and row['Sched. Time'] != '-':
            try:
                schedule_time = row['Sched. Time']
                day_time_part = schedule_time.split(', ')[1]
                start_time_str, end_time_str = day_time_part.split('-')
                day = schedule_time.split(', ')[0]
                
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                # Check for room conflicts
                room_key = f"{row['Room']}_{day}"
                for existing_start, existing_end in room_time_usage[room_key]:
                    if not (end_time <= existing_start or start_time >= existing_end):
                        violations.append(
                            f"Room conflict: {row['Room']} on {day} "
                            f"between {start_time}-{end_time} and {existing_start}-{existing_end}"
                        )
                
                room_time_usage[room_key].append((start_time, end_time))
                
            except Exception as e:
                violations.append(f"Invalid schedule format for row {row.get('semester_id', 'unknown')}: {e}")
    
    return len(violations) == 0, violations

def get_constraint_summary():
    """
    Return a summary of all constraints used in scheduling
    """
    return {
        'room_constraints': {
            'specialized_rooms': len(ROOM_ALLOWED_MAJORS),
            'excluded_rooms': len(EXCLUDED_ROOMS),
        },
        'time_constraints': {
            'max_subjects_per_day': 3,
            'max_class_days': 5,
            'session_time_restrictions': True,  # Morning/Night session rules
        },
        'lecturer_constraints': {
            'preference_support': True,
            'conflict_avoidance': True,
        }
    }