from django.urls import path
from .views import health_check, setup_db_view, contact_view, chat_view
from .private_views import (
    private_unlock_view, private_session_view, private_logout_view, get_csrf_token_view,
    dashboard_view,
    subjects_list_create_view, subjects_detail_view,
    tasks_list_create_view, tasks_detail_view,
    schedule_list_create_view, schedule_detail_view,
    study_sessions_list_view, study_sessions_current_view, study_sessions_start_view, study_sessions_stop_view,
    exams_list_create_view, exams_detail_view,
    notes_list_create_view, notes_detail_view,
    habits_list_create_view, habits_detail_view,
    analytics_overview_view, analytics_study_time_view, analytics_subjects_view,
    notifications_list_view, notifications_mark_read_view,
    search_view
)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('setup-db/', setup_db_view, name='setup_db'),
    path('contact/', contact_view, name='contact'),
    path('chat/', chat_view, name='chat'),
    path('auth/csrf/', get_csrf_token_view, name='csrf_token'),

    path('private/unlock/', private_unlock_view, name='private_unlock'),
    path('private/session/', private_session_view, name='private_session'),
    path('private/logout/', private_logout_view, name='private_logout'),

    path('private/dashboard/', dashboard_view, name='dashboard'),

    path('private/subjects/', subjects_list_create_view, name='subjects_list_create'),
    path('private/subjects/<int:pk>/', subjects_detail_view, name='subjects_detail'),

    path('private/tasks/', tasks_list_create_view, name='tasks_list_create'),
    path('private/tasks/<int:pk>/', tasks_detail_view, name='tasks_detail'),

    path('private/schedule/', schedule_list_create_view, name='schedule_list_create'),
    path('private/schedule/<int:pk>/', schedule_detail_view, name='schedule_detail'),

    path('private/study-sessions/', study_sessions_list_view, name='study_sessions_list'),
    path('private/study-sessions/current/', study_sessions_current_view, name='study_sessions_current'),
    path('private/study-sessions/start/', study_sessions_start_view, name='study_sessions_start'),
    path('private/study-sessions/<int:pk>/stop/', study_sessions_stop_view, name='study_sessions_stop'),

    path('private/exams/', exams_list_create_view, name='exams_list_create'),
    path('private/exams/<int:pk>/', exams_detail_view, name='exams_detail'),

    path('private/notes/', notes_list_create_view, name='notes_list_create'),
    path('private/notes/<int:pk>/', notes_detail_view, name='notes_detail'),

    path('private/habits/', habits_list_create_view, name='habits_list_create'),
    path('private/habits/<int:pk>/', habits_detail_view, name='habits_detail'),

    path('private/analytics/overview/', analytics_overview_view, name='analytics_overview'),
    path('private/analytics/study-time/', analytics_study_time_view, name='analytics_study_time'),
    path('private/analytics/subjects/', analytics_subjects_view, name='analytics_subjects'),

    path('private/notifications/', notifications_list_view, name='notifications_list'),
    path('private/notifications/<int:pk>/read/', notifications_mark_read_view, name='notifications_mark_read'),

    path('private/search/', search_view, name='search'),
]
