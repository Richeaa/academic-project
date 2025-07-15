from django.db import models

# Create your models here.
class profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=250, unique=True)
    password = models.CharField(max_length=250)

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

    def __str__(self):
        return f"{self.program_session} - {self.subject}"

    class Meta:
        db_table = 'semester_20252'
        managed = False