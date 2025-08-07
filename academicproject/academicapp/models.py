from django.db import models

# Create your models here.
class profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=250, unique=True)
    password = models.CharField(max_length=250)
    name = models.CharField(max_length=250)


    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'profile'
        managed = False

class semester20251(models.Model):
    semester_id = models.AutoField(primary_key=True)
    program_session = models.CharField(max_length=10)
    major = models.CharField(max_length=50)
    curriculum = models.CharField(max_length=50)
    major_class = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    credit = models.DecimalField(max_digits=4, decimal_places=2)
    lecturer_1 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_2 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_3 = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.program_session} - {self.subject}"

    class Meta:
        db_table = 'semester_20251'
        managed = False


class semester20252(models.Model):
    semester_id = models.AutoField(primary_key=True)
    program_session = models.CharField(max_length=10)
    major = models.CharField(max_length=50)
    curriculum = models.CharField(max_length=50)
    major_class = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    credit = models.DecimalField(max_digits=4, decimal_places=2)
    lecturer_1 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_2 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_3 = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.program_session} - {self.subject}"

    class Meta:
        db_table = 'semester_20252'
        managed = False
        
class semester20253(models.Model):
    semester_id = models.AutoField(primary_key=True)
    program_session = models.CharField(max_length=10)
    major = models.CharField(max_length=50)
    curriculum = models.CharField(max_length=50)
    major_class = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    credit = models.DecimalField(max_digits=4, decimal_places=2)
    lecturer_1 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_2 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_3 = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.program_session} - {self.subject}"

    class Meta:
        db_table = 'semester_20253'
        managed = False 

class semester20243(models.Model):
    semester_id = models.AutoField(primary_key=True)
    program_session = models.CharField(max_length=10)
    major = models.CharField(max_length=50)
    curriculum = models.CharField(max_length=50)
    major_class = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    credit = models.DecimalField(max_digits=4, decimal_places=2)
    lecturer_1 = models.CharField(max_length=100, blank=True, null=True)
    lecturer_2 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.program_session} - {self.subject}"

    class Meta:
        db_table = 'semester_20243'
        managed = False

class assignlecturer20251(models.Model):
    assign_id = models.AutoField(primary_key=True)
    semester = models.ForeignKey(semester20251, on_delete=models.CASCADE)
    lecturer_day = models.CharField(max_length=10)
    room = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Assignment {self.assign_id} for {self.semester_id} on {self.lecturer_day} from {self.start_time} to {self.end_time} in {self.room}"

    class Meta:
        db_table = 'assignlecturer20251'
        managed = True

class assignlecturer20252(models.Model):
    assign_id = models.AutoField(primary_key=True)
    semester = models.ForeignKey(semester20252, on_delete=models.CASCADE)
    lecturer_day = models.CharField(max_length=10)
    room = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Assignment {self.assign_id} for {self.semester_id} on {self.lecturer_day} from {self.start_time} to {self.end_time} in {self.room}"

    class Meta:
        db_table = 'assignlecturer20252'
        managed = True

        
class assignlecturer20253(models.Model):
    assign_id = models.AutoField(primary_key=True)
    semester = models.ForeignKey(semester20253, on_delete=models.CASCADE)
    lecturer_day = models.CharField(max_length=10)
    room = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Assignment {self.assign_id} for {self.semester_id} on {self.lecturer_day} from {self.start_time} to {self.end_time} in {self.room}"

    class Meta:
        db_table = 'assignlecturer20253'
        managed = True

        
class Lecturer(models.Model):
    lecturer_id = models.AutoField(primary_key=True)
    lecturer_name = models.CharField(max_length=100)
    lecturer_type = models.CharField(max_length=50, blank=True, null=True)
    job = models.CharField(max_length=100, blank=True, null=True)
    current_working_day = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.lecturer_name

    class Meta:
        db_table = 'lecturer'
        managed = False

class LecturerPreference(models.Model):
    lecturer_name = models.CharField(max_length=100)
    time_preference = models.CharField(max_length=100, blank=True, null=True)
    day_preference = models.CharField(max_length=100, blank=True, null=True)
    room_preference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.lecturer_name
    
    class Meta:
        db_table = 'lecturer_preferences'
        managed = False

class Viewschedule20251(models.Model):
    id = models.AutoField(primary_key=True)
    lecturer1 = models.CharField(max_length=255)
    lecturer2 = models.CharField(max_length=255, blank=True, null=True)
    lecturer3 = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    schedule_time = models.CharField()
    room = models.CharField(max_length=255)

    class Meta:
        db_table = 'schedule20251'

class Viewschedule20252(models.Model):
    id = models.AutoField(primary_key=True)
    lecturer1 = models.CharField(max_length=255)
    lecturer2 = models.CharField(max_length=255, blank=True, null=True)
    lecturer3 = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    schedule_time = models.CharField(max_length=255)
    room = models.CharField(max_length=255)

    class Meta:
        db_table = 'schedule20252'

class Viewschedule20253(models.Model):
    id = models.AutoField(primary_key=True)
    lecturer1 = models.CharField(max_length=255)
    lecturer2 = models.CharField(max_length=255, blank=True, null=True)
    lecturer3 = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    schedule_time = models.CharField(max_length=255)
    room = models.CharField(max_length=255)

    class Meta:
        db_table = 'schedule20253'