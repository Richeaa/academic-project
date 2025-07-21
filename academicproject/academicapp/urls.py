from django.urls import path
from . import views
from .views import studyprogram

urlpatterns = [
    path('', views.signin, name='signin'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('lecturer/', views.lecturer, name = 'lecturer'),
    path('add/',views.addLecturer, name ='addLecturer' ),
    path('edit/',views.editLecturer, name ='editLecturer' ),
    path('studyprogram/<str:semester_url>/', studyprogram, name='studyprogram'),
    path('assignlecturer/create/', views.assignlecturer_create, name='assignlecturer_create'),
    path('assign/delete/', views.assignlecturer_delete, name='assignlecturer_delete'),
    path('schedule20251/', views.schedule20251, name='schedule20251')

]