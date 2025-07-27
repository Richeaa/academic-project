from django.urls import path
from . import views
from .views import studyprogram, formstudyprogram

urlpatterns = [
    path('', views.signin, name='signin'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/academic/', views.dashboard, name='dashboard'),
    path('lecturer/', views.lecturer, name='lecturer'),
    path('lecturer/add/', views.addLecturer, name='addLecturer'),
    path('lecturer/edit/<int:lecturer_id>/', views.editLecturer, name='editLecturer'),
    path('lecturer/delete/<int:lecturer_id>/', views.deleteLecturer, name='deleteLecturer'),
    path('formstudyprogram/<str:semester_url>/', formstudyprogram, name='formstudyprogram'),
    path('add-academic-module/<str:semester_url>/', views.add_academic_module, name='add_academic_module'),
    path('edit-academic-module/<str:semester_url>/', views.edit_academic_module, name='edit_academic_module'),
    path('delete-academic-module/<str:semester_url>/<int:semester_id>/', views.delete_academic_module, name='delete_academic_module'),
    path('studyprogram/<str:semester_url>/', studyprogram, name='studyprogram'),
    path('assignlecturer/create/', views.assignlecturer_create, name='assignlecturer_create'),
    path('assign/delete/', views.assignlecturer_delete, name='assignlecturer_delete'),
    path('schedule/delete/', views.schedulelecturer_delete, name='schedulelecturer_delete'),
    path('schedule20251/', views.schedule20251, name='schedule20251'),
    path('schedule20252/', views.schedule20252, name='schedule20252'),
    path('dashboard/hsp/', views.dashboard_hsp, name='dashboard_hsp'),
    path('dashboard/lecturer/', views.dashboard_lecturer, name='dashboard_lecturer'),
]