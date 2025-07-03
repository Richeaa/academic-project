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