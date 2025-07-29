import pandas as pd
import pickle
import os
from datetime import datetime, timedelta
import random
from collections import defaultdict

from .utils import (
    get_unassigned_classes, 
    get_preferences_df, 
    get_available_rooms, 
    get_available_times,
    save_predictions_to_db
)
from .constraints import (
    is_room_eligible,
    get_time_block,
    is_overlapping,
    parse_day_preference,
    parse_time_preference,
    matches_room_preference
)

def load_ml_models():
    base_path = os.path.join(os.path.dirname(__file__), 'model')
    
    with open(os.path.join(base_path, 'model_room.pkl'), 'rb') as f:
        model_room = pickle.load(f)
    
    with open(os.path.join(base_path, 'model_time.pkl'), 'rb') as f:
        model_time = pickle.load(f)
        
    with open(os.path.join(base_path, 'encoder.pkl'), 'rb') as f:
        encoder = pickle.load(f)
    
    return model_room, model_time, encoder

def run_ml_prediction(semester_choice):
    try:
        skeleton_df = get_unassigned_classes(semester_choice)
        
        if skeleton_df.empty:
            return True, "No unassigned classes found", 0
        
        print(f"Total unassigned classes: {len(skeleton_df)}")
        
        model_room, model_time, encoder = load_ml_models()
        
        preferences_df = get_preferences_df()
        available_rooms = get_available_rooms()
        available_times = get_available_times()
        
        print(f"Available rooms: {len(available_rooms)}")
        print(f"Available times: {len(available_times)}")
        
        categorical_cols = ['Program Session', 'Major', 'Curriculum', 'Class', 'Subject']
        features = categorical_cols + ['Cr']
        
        final_schedule = skeleton_df.copy()
        
        # Debug:
        # print("Data structure check:")
        # print(f"Columns: {list(final_schedule.columns)}")
        # print(f"First row type: {type(final_schedule.iloc[0])}")
        # if len(final_schedule) > 0:
        #     print(f"Sample row: {final_schedule.iloc[0].to_dict()}")
        
        if '#1' not in final_schedule.columns:
            print("WARNING: '#1' column not found in data!")
            final_schedule['#1'] = None
        
        for col in features:
            if col not in final_schedule.columns:
                final_schedule[col] = 'Unknown'
            final_schedule[col] = final_schedule[col].fillna('Unknown')
        
        lecturer_cols = ['#1', '#2', '#3']
        for col in lecturer_cols:
            if col not in final_schedule.columns:
                print(f"Adding missing column: {col}")
                final_schedule[col] = None
        
        try:
            X_new = encoder.transform(final_schedule[features].astype(str))
            predicted_rooms = model_room.predict(X_new)
            predicted_times = model_time.predict(X_new)
            
            final_schedule['Room'] = predicted_rooms
            final_schedule['Sched. Time'] = predicted_times
            
            print(f"ML predictions completed for {len(final_schedule)} classes")
            
            valid_room_predictions = sum(1 for r in predicted_rooms if r != '-' and str(r).strip() != '')
            valid_time_predictions = sum(1 for t in predicted_times if t != '-' and str(t).strip() != '')
            print(f"Valid room predictions: {valid_room_predictions}")
            print(f"Valid time predictions: {valid_time_predictions}")
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            # Fallback: assign default values
            final_schedule['Room'] = '-'
            final_schedule['Sched. Time'] = '-'
        
        print("Starting constraint-based scheduling...")
        final_schedule = apply_constraints_scheduling(
            final_schedule, preferences_df, available_rooms, available_times
        )
        
        successful_assignments = len(final_schedule[
            (final_schedule['Room'] != '-') & 
            (final_schedule['Sched. Time'] != '-')
        ])
        print(f"Successful assignments after constraints: {successful_assignments}")
        
        saved_count = save_predictions_to_db(final_schedule, semester_choice)
        
        
        return True, f"Successfully processed {len(final_schedule)} classes, saved {saved_count} assignments", saved_count
        
    except Exception as e:
        return False, f"Prediction failed: {str(e)}", 0

def apply_constraints_scheduling(schedule_df, preferences_df, available_rooms, available_times):
    room_day_time_blocks = defaultdict(lambda: defaultdict(list))
    class_day_time_blocks = defaultdict(lambda: defaultdict(list))
    class_day_subject_count = defaultdict(lambda: defaultdict(int))
    class_used_days = defaultdict(set)
    lecturer_time_blocks = defaultdict(lambda: defaultdict(list))
    lecturer_schedule = defaultdict(set)
    
    max_class_days = 5
    max_subjects_per_day = 3
    
    no_lecturer_count = 0
    assigned_count = 0
    conflict_count = 0
    
    lecturer_prefs = {}
    for _, row in preferences_df.iterrows():
        name = row['Nama']
        lecturer_prefs[name] = {
            'time': parse_time_preference(str(row['Time Preference'])),
            'days': parse_day_preference(str(row['Day Preference'])),
            'rooms': str(row['Room Preference']).strip(),
            'notes': str(row['Notes']).strip()
        }
    
    available_times_cleaned = [
        t for t in available_times
        if isinstance(t, str) and ',' in t and '(TBA)' not in t
    ]
    
    lecturer_assignments = {}
    print("Creating lecturer assignments lookup...")
    
    for idx, row in schedule_df.iterrows():
        try:
            key = (row['Curriculum'], row['Class'], row['Subject'])
            lecturer = row['#1'] if '#1' in row else None
            lecturer_assignments[key] = lecturer
            if idx < 5:  # Debug first 5 rows
                print(f"Row {idx}: {key} -> {lecturer}")
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            print(f"Row data: {row}")
    
    print(f"Created {len(lecturer_assignments)} lecturer assignments")
    
    def check_has_pref(row):
        try:
            key = (row['Curriculum'], row['Class'], row['Subject'])
            lecturer = lecturer_assignments.get(key)
            return lecturer in lecturer_prefs if lecturer else False
        except Exception as e:
            print(f"Error in has_pref check: {e}")
            return False
    
    schedule_df['has_pref'] = schedule_df.apply(check_has_pref, axis=1)
    schedule_df = schedule_df.sort_values(by='has_pref', ascending=False).reset_index(drop=True)
    
    for idx, row in schedule_df.iterrows():
        key_class = (row['Curriculum'], row['Class'])
        subject = row['Subject']
        major = row['Major']
        ps = row['Program Session']
        
        try:
            credit_str = str(row['Cr']).strip()
            # Handle decimal strings like '3.00' or '3.0'
            if '.' in credit_str:
                credit = int(float(credit_str))
            else:
                credit = int(credit_str)
        except (ValueError, TypeError):
            credit = 3  # Default credit value
            
        key_lecturer = (row['Curriculum'], row['Class'], subject)
        
        lecturer = lecturer_assignments.get(key_lecturer)
        
        if not lecturer or lecturer == 'Unknown' or pd.isna(lecturer) or str(lecturer).strip() == '':
            schedule_df.at[idx, '#1'] = '(Tba)'
            schedule_df.at[idx, 'Room'] = '-'
            schedule_df.at[idx, 'Sched. Time'] = '-'
            no_lecturer_count += 1
            continue
        
        prefs = lecturer_prefs.get(lecturer, {})
        
        # assign room and time
        assigned = False
        shuffled_times = available_times_cleaned.copy()
        random.shuffle(shuffled_times)
        
        for time in shuffled_times:
            try:
                day, start_str = map(str.strip, time.split(','))
                hour_str = start_str.split('-')[0]
                hour, minute = map(int, hour_str.split(':'))
                base_start = f"{day}, {hour_str}"
                start_dt, end_dt = get_time_block(base_start, credit)
                
                # Check constraints
                if (ps == 'N' and hour < 17) or (ps == 'M' and hour >= 17):
                    continue
                if 'No Schedule on Monday' in prefs.get('notes', '') and day == 'Mon':
                    continue
                if prefs.get('days') and day not in prefs['days']:
                    continue
                if prefs.get('time') and all(p not in hour_str for p in prefs['time']):
                    continue
                
                # Class constraints
                if class_day_subject_count[key_class][day] >= max_subjects_per_day: # max 3 subjects per day
                    continue
                if day in class_used_days[key_class] and len(class_used_days[key_class]) < max_class_days: # spread
                    continue
                
                if is_overlapping(start_dt, end_dt, lecturer_time_blocks[lecturer][day]):
                    continue
                if is_overlapping(start_dt, end_dt, class_day_time_blocks[key_class][day]):
                    continue
                
                available_rooms_shuffled = available_rooms.copy()
                random.shuffle(available_rooms_shuffled)
                
                for room in available_rooms_shuffled:
                    if not is_room_eligible(room, major, subject):
                        continue
                    if prefs.get('rooms') and not matches_room_preference(room, prefs['rooms']):
                        continue
                    if is_overlapping(start_dt, end_dt, room_day_time_blocks[room][day]):
                        continue
                    
                    schedule_df.at[idx, 'Room'] = room
                    schedule_df.at[idx, 'Sched. Time'] = f"{day}, {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
                    schedule_df.at[idx, '#1'] = lecturer
                    
                    room_day_time_blocks[room][day].append((start_dt, end_dt))
                    class_day_time_blocks[key_class][day].append((start_dt, end_dt))
                    class_day_subject_count[key_class][day] += 1
                    class_used_days[key_class].add(day)
                    lecturer_time_blocks[lecturer][day].append((start_dt, end_dt))
                    lecturer_schedule[lecturer].add(room)
                    
                    assigned_count += 1
                    assigned = True
                    break
                
                if assigned:
                    break
                    
            except Exception as e:
                print(f"Error processing time {time}: {e}")
                continue
        
        if not assigned:
            schedule_df.at[idx, 'Room'] = '-'
            schedule_df.at[idx, 'Sched. Time'] = '-'
            schedule_df.at[idx, '#1'] = lecturer
            conflict_count += 1
    
    print(f"Constraint scheduling results:")
    print(f"  - No lecturer: {no_lecturer_count}")
    print(f"  - Successfully assigned: {assigned_count}")
    print(f"  - Conflicts (couldn't assign): {conflict_count}")
    
    return schedule_df