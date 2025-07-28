from .ml.predict import run_prediction
from .models import (
    semester20251, semester20252,
    assignlecturer20251, assignlecturer20252
)
from datetime import datetime
import re
import pandas as pd

def run_prediction_and_assign(semester):
    try:
        if semester == '20251':
            SemesterModel = semester20251
            AssignModel = assignlecturer20251
        else:
            SemesterModel = semester20252
            AssignModel = assignlecturer20252
        
        assigned_ids = AssignModel.objects.values_list('semester_id', flat=True)
        unassigned = SemesterModel.objects.exclude(semester_id__in=assigned_ids)
        
        if not unassigned.exists():
            return True, "No unassigned classes found"
            
        unassigned_df = pd.DataFrame.from_records(unassigned.values())
        
        predicted_df = run_prediction(unassigned_df)
        
        # Save
        created_count = 0
        for _, row in predicted_df.iterrows():
            if pd.isna(row['Room']) or pd.isna(row['Sched. Time']):
                continue
                
            time_match = re.match(r"(\w{3}), (\d{2}:\d{2})-(\d{2}:\d{2})", row['Sched. Time'])
            if not time_match:
                continue
                
            day, start_time, end_time = time_match.groups()
            semester_obj = SemesterModel.objects.get(semester_id=row['No'])
            
            AssignModel.objects.create(
                semester=semester_obj,
                lecturer_day=day,
                room=row['Room'],
                start_time=datetime.strptime(start_time, '%H:%M').time(),
                end_time=datetime.strptime(end_time, '%H:%M').time()
            )
            created_count += 1
        
        return True, f"Assigned {created_count} new classes"
        
    except Exception as e:
        return False, f"Error: {str(e)}"