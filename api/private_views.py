import os
import re
import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.utils import timezone
from django.db.models import Sum, Q

from .models import (
    Profile, Subject, Task, ScheduleItem, StudySession,
    Goal, DailyChallenge, Exam, Habit, HabitLog, Note, Notification
)
from .serializers import (
    ProfileSerializer, SubjectSerializer, TaskSerializer, ScheduleItemSerializer,
    StudySessionSerializer, GoalSerializer, DailyChallengeSerializer, ExamSerializer,
    HabitSerializer, HabitLogSerializer, NoteSerializer, NotificationSerializer
)

_CACHED_HASHED_PIN = None
_CACHED_RAW_PIN = None


def get_hashed_pin():
    global _CACHED_HASHED_PIN, _CACHED_RAW_PIN
    raw_pin = os.environ.get('PRIVATE_PIN', '1234').strip()
    if _CACHED_RAW_PIN != raw_pin or _CACHED_HASHED_PIN is None:
        _CACHED_RAW_PIN = raw_pin
        if raw_pin.startswith('pbkdf2_sha256$') or raw_pin.startswith('argon2'):
            _CACHED_HASHED_PIN = raw_pin
        else:
            _CACHED_HASHED_PIN = make_password(raw_pin)
    return _CACHED_HASHED_PIN


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def is_rate_limited(ip):
    cache_key = f"pin_attempts_{ip}"
    attempts = cache.get(cache_key, 0)
    return attempts >= 5


def record_failed_attempt(ip):
    cache_key = f"pin_attempts_{ip}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=300)


def clear_failed_attempts(ip):
    cache_key = f"pin_attempts_{ip}"
    cache.delete(cache_key)


def get_private_user(request):
    if not request.session.get('private_authenticated'):
        return None
    if request.user and request.user.is_authenticated:
        return request.user
    user = User.objects.filter(username='omm_owner').first()
    if not user:
        user, _ = User.objects.get_or_create(
            username='omm_owner',
            defaults={'email': 'omm@example.com', 'first_name': 'Omm', 'last_name': 'Prasad Jena'}
        )
    return user


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf_token_view(request):
    csrf_token = get_token(request)
    return Response({'csrftoken': csrf_token}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def private_unlock_view(request):
    if not isinstance(request.data, dict):
        return Response(
            {'success': False, 'authenticated': False, 'message': 'Invalid request body format.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    ip = get_client_ip(request)

    if is_rate_limited(ip):
        return Response(
            {'success': False, 'authenticated': False, 'message': 'Too many attempts. Try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    pin = request.data.get('pin')
    if not pin or not isinstance(pin, (str, int)):
        record_failed_attempt(ip)
        return Response(
            {'success': False, 'authenticated': False, 'message': 'Incorrect PIN.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    pin_str = str(pin).strip()
    if not re.match(r'^\d{4}$', pin_str):
        record_failed_attempt(ip)
        return Response(
            {'success': False, 'authenticated': False, 'message': 'Incorrect PIN.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    hashed_pin = get_hashed_pin()
    if check_password(pin_str, hashed_pin):
        clear_failed_attempts(ip)

        try:
            user, _ = User.objects.get_or_create(
                username='omm_owner',
                defaults={'email': 'omm@example.com', 'first_name': 'Omm', 'last_name': 'Prasad Jena'}
            )
        except Exception:
            from django.core.management import call_command
            call_command("migrate", interactive=False)
            user, _ = User.objects.get_or_create(
                username='omm_owner',
                defaults={'email': 'omm@example.com', 'first_name': 'Omm', 'last_name': 'Prasad Jena'}
            )
        login(request, user)
        request.session['private_authenticated'] = True
        request.session.modified = True

        return Response(
            {'success': True, 'authenticated': True},
            status=status.HTTP_200_OK
        )

    record_failed_attempt(ip)
    return Response(
        {'success': False, 'authenticated': False, 'message': 'Incorrect PIN.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def private_session_view(request):
    user = get_private_user(request)
    if user:
        return Response({'authenticated': True}, status=status.HTTP_200_OK)
    return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def private_logout_view(request):
    if not request.session.get('private_authenticated'):
        return Response({'success': False, 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    request.session.flush()
    return Response({'success': True, 'authenticated': False}, status=status.HTTP_200_OK)


# ============================================================
# DASHBOARD AGGREGATION API
# ============================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    today = timezone.now().date()
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'display_name': 'Omm', 'email': 'omm@example.com', 'daily_study_goal_minutes': 240}
    )

    daily_challenge = DailyChallenge.objects.filter(user=user, date=today).first()
    if not daily_challenge:
        daily_challenge, _ = DailyChallenge.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'title': 'Master 5 LeetCode Problems',
                'description': 'Solve 3 Medium and 2 Easy problems on Arrays & Trees',
                'target_minutes': 90,
                'completed_minutes': 45,
                'completed': False
            }
        )

    # Calculate today's study seconds
    completed_sessions = StudySession.objects.filter(
        user=user,
        status='completed',
        started_at__date=today
    ).aggregate(total_sec=Sum('duration_seconds'))['total_sec'] or 0

    study_minutes_today = round(completed_sessions / 60)
    target_hours = profile.daily_study_goal_minutes / 60.0
    current_hours = round(study_minutes_today / 60.0, 1)

    study_hours_data = {
        'current': current_hours,
        'target': target_hours,
        'progress_percent': min(100, int((study_minutes_today / max(1, profile.daily_study_goal_minutes)) * 100))
    }

    # Streak calculation
    streak_count = 7  # default active streak
    streak_data = {
        'count': streak_count,
        'status': 'on_fire'
    }

    # Current running session
    running_session = StudySession.objects.filter(
        user=user,
        status__in=['running', 'paused']
    ).first()

    # Weekly streak days
    start_of_week = today - datetime.timedelta(days=today.weekday())
    weekly_streak = []
    days_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i in range(7):
        day_date = start_of_week + datetime.timedelta(days=i)
        is_completed = day_date <= today
        weekly_streak.append({
            'day': days_map[i],
            'shortDate': day_date.strftime('%d'),
            'completed': is_completed,
            'isToday': day_date == today
        })

    # Today's plan
    today_plan_qs = ScheduleItem.objects.filter(user=user, date=today)
    today_plan_data = ScheduleItemSerializer(today_plan_qs, many=True).data

    # Learning Overview
    subjects = Subject.objects.filter(user=user)
    tasks = Task.objects.filter(user=user)
    completed_tasks_count = tasks.filter(completed=True).count()
    upcoming_exams_count = Exam.objects.filter(user=user, status='upcoming', exam_date__gte=today).count()

    learning_overview = {
        'hours_this_week': 24.5,
        'tasks_completed': completed_tasks_count,
        'total_tasks': tasks.count(),
        'exams_upcoming': upcoming_exams_count,
    }

    # Analytics summary
    subject_distribution = [
        {'name': subj.name, 'color': subj.color, 'hours': subj.target_minutes / 60.0}
        for subj in subjects
    ]

    history_data = [
        {'day': 'Mon', 'hours': 4.5},
        {'day': 'Tue', 'hours': 5.0},
        {'day': 'Wed', 'hours': 3.5},
        {'day': 'Thu', 'hours': 6.0},
        {'day': 'Fri', 'hours': 4.0},
        {'day': 'Sat', 'hours': 2.5},
        {'day': 'Sun', 'hours': 3.0},
    ]

    return Response({
        'profile': ProfileSerializer(profile).data,
        'date': today.strftime('%A, %b %d'),
        'daily_challenge': DailyChallengeSerializer(daily_challenge).data,
        'study_hours': study_hours_data,
        'streak': streak_data,
        'current_session': StudySessionSerializer(running_session).data if running_session else None,
        'weekly_streak': weekly_streak,
        'today_plan': today_plan_data,
        'learning_overview': learning_overview,
        'subjects': SubjectSerializer(subjects, many=True).data,
        'tasks': TaskSerializer(tasks, many=True).data,
        'analytics': {
            'subject_distribution': subject_distribution,
            'history': history_data
        }
    }, status=status.HTTP_200_OK)


# ============================================================
# SUBJECTS CRUD
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def subjects_list_create_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        subjects = Subject.objects.filter(user=user)
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def subjects_detail_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    subject = Subject.objects.filter(user=user, id=pk).first()
    if not subject:
        return Response({'error': 'Subject not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(SubjectSerializer(subject).data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = SubjectSerializer(subject, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        subject.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# TASKS CRUD
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def tasks_list_create_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        tasks = Task.objects.filter(user=user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def tasks_detail_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    task = Task.objects.filter(user=user, id=pk).first()
    if not task:
        return Response({'error': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            updated_task = serializer.save()
            if updated_task.completed and not updated_task.completed_at:
                updated_task.completed_at = timezone.now()
                updated_task.status = 'completed'
                updated_task.save()
            return Response(TaskSerializer(updated_task).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        task.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# SCHEDULE CRUD
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def schedule_list_create_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        items = ScheduleItem.objects.filter(user=user)
        serializer = ScheduleItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = ScheduleItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def schedule_detail_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    item = ScheduleItem.objects.filter(user=user, id=pk).first()
    if not item:
        return Response({'error': 'Schedule item not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ScheduleItemSerializer(item).data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = ScheduleItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# STUDY SESSIONS API
# ============================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def study_sessions_list_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    sessions = StudySession.objects.filter(user=user)
    return Response(StudySessionSerializer(sessions, many=True).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def study_sessions_current_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    session = StudySession.objects.filter(user=user, status__in=['running', 'paused']).first()
    if session:
        return Response(StudySessionSerializer(session).data, status=status.HTTP_200_OK)
    return Response({'session': None}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def study_sessions_start_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    # Cancel any running session
    running_sessions = StudySession.objects.filter(user=user, status='running')
    for s in running_sessions:
        s.status = 'cancelled'
        s.ended_at = timezone.now()
        s.save()

    subject_id = request.data.get('subject')
    task_id = request.data.get('task')
    title = request.data.get('title', 'Study Session')

    subject = Subject.objects.filter(user=user, id=subject_id).first() if subject_id else None
    task = Task.objects.filter(user=user, id=task_id).first() if task_id else None

    new_session = StudySession.objects.create(
        user=user,
        subject=subject,
        task=task,
        title=title,
        started_at=timezone.now(),
        status='running'
    )
    return Response(StudySessionSerializer(new_session).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def study_sessions_stop_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    session = StudySession.objects.filter(user=user, id=pk).first()
    if not session:
        return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)

    session.ended_at = timezone.now()
    session.status = 'completed'
    delta = (session.ended_at - session.started_at).total_seconds()
    session.duration_seconds = max(0, int(delta))
    session.notes = request.data.get('notes', session.notes)
    session.save()

    return Response(StudySessionSerializer(session).data, status=status.HTTP_200_OK)


# ============================================================
# EXAMS CRUD
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def exams_list_create_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        exams = Exam.objects.filter(user=user)
        return Response(ExamSerializer(exams, many=True).data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = ExamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def exams_detail_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    exam = Exam.objects.filter(user=user, id=pk).first()
    if not exam:
        return Response({'error': 'Exam not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ExamSerializer(exam).data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = ExamSerializer(exam, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        exam.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# NOTES CRUD
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def notes_list_create_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        notes = Note.objects.filter(user=user)
        return Response(NoteSerializer(notes, many=True).data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def notes_detail_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    note = Note.objects.filter(user=user, id=pk).first()
    if not note:
        return Response({'error': 'Note not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(NoteSerializer(note).data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = NoteSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        note.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# HABITS CRUD
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def habits_list_create_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        habits = Habit.objects.filter(user=user)
        return Response(HabitSerializer(habits, many=True).data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = HabitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def habits_detail_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    habit = Habit.objects.filter(user=user, id=pk).first()
    if not habit:
        return Response({'error': 'Habit not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(HabitSerializer(habit).data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        serializer = HabitSerializer(habit, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        habit.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


# ============================================================
# ANALYTICS API
# ============================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_overview_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    today = timezone.now().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())

    total_sessions = StudySession.objects.filter(user=user, status='completed')
    total_seconds = total_sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0

    week_sessions = total_sessions.filter(started_at__date__gte=start_of_week)
    week_seconds = week_sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0

    tasks = Task.objects.filter(user=user)
    completed_tasks = tasks.filter(completed=True).count()

    return Response({
        'total_study_hours': round(total_seconds / 3600.0, 1),
        'weekly_study_hours': round(week_seconds / 3600.0, 1),
        'total_tasks': tasks.count(),
        'completed_tasks': completed_tasks,
        'completion_rate_percent': round((completed_tasks / max(1, tasks.count())) * 100, 1)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_study_time_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    today = timezone.now().date()
    days = []
    days_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    start_of_week = today - datetime.timedelta(days=today.weekday())

    for i in range(7):
        day_date = start_of_week + datetime.timedelta(days=i)
        sec = StudySession.objects.filter(
            user=user,
            status='completed',
            started_at__date=day_date
        ).aggregate(total=Sum('duration_seconds'))['total'] or 0
        days.append({
            'day': days_map[i],
            'date': day_date.strftime('%Y-%m-%d'),
            'hours': round(sec / 3600.0, 1)
        })

    return Response({'history': days}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_subjects_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    subjects = Subject.objects.filter(user=user)
    data = []
    for s in subjects:
        sec = StudySession.objects.filter(
            user=user,
            subject=s,
            status='completed'
        ).aggregate(total=Sum('duration_seconds'))['total'] or 0
        data.append({
            'id': s.id,
            'name': s.name,
            'color': s.color,
            'hours': round(sec / 3600.0, 1)
        })
    return Response({'subjects': data}, status=status.HTTP_200_OK)


# ============================================================
# NOTIFICATIONS API
# ============================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def notifications_list_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    notifications = Notification.objects.filter(user=user)
    return Response(NotificationSerializer(notifications, many=True).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def notifications_mark_read_view(request, pk):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    notification = Notification.objects.filter(user=user, id=pk).first()
    if not notification:
        return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

    notification.read = True
    notification.save()
    return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)


# ============================================================
# SEARCH API
# ============================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def search_view(request):
    user = get_private_user(request)
    if not user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'subjects': [], 'tasks': [], 'notes': []}, status=status.HTTP_200_OK)

    subjects = Subject.objects.filter(user=user).filter(Q(name__icontains=query) | Q(description__icontains=query))
    tasks = Task.objects.filter(user=user).filter(Q(title__icontains=query) | Q(description__icontains=query))
    notes = Note.objects.filter(user=user).filter(Q(title__icontains=query) | Q(content__icontains=query))

    return Response({
        'subjects': SubjectSerializer(subjects, many=True).data,
        'tasks': TaskSerializer(tasks, many=True).data,
        'notes': NoteSerializer(notes, many=True).data
    }, status=status.HTTP_200_OK)
