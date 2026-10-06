import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import (
    Profile, Subject, Task, ScheduleItem, StudySession,
    Goal, DailyChallenge, Exam, Habit, HabitLog, Note, Notification
)

class Command(BaseCommand):
    help = 'Seeds initial study data for default user (omm_owner)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Study data...')

        user, created = User.objects.get_or_create(
            username='omm_owner',
            defaults={
                'email': 'omm@example.com',
                'first_name': 'Omm',
                'last_name': 'Prasad Jena',
            }
        )
        if created:
            user.set_password('study_owner_pass_2026')
            user.save()
            self.stdout.write(f'Created default user: {user.username}')

        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={
                'display_name': 'Omm',
                'email': 'omm@example.com',
                'avatar': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
                'bio': 'Computer Science Student & Developer',
                'daily_study_goal_minutes': 240,
            }
        )

        today = timezone.now().date()

        # 1. Subjects
        subjects_data = [
            {'name': 'Mathematics', 'color': '#8b5cf6', 'icon': 'BookOpen', 'target_minutes': 120, 'description': 'Calculus & Linear Algebra'},
            {'name': 'DSA', 'color': '#3b82f6', 'icon': 'BookOpen', 'target_minutes': 150, 'description': 'Data Structures & Algorithms'},
            {'name': 'Python', 'color': '#10b981', 'icon': 'BookOpen', 'target_minutes': 90, 'description': 'Advanced Python & Backend'},
            {'name': 'DBMS', 'color': '#f59e0b', 'icon': 'BookOpen', 'target_minutes': 90, 'description': 'Database Systems & SQL'},
            {'name': 'Operating Systems', 'color': '#ec4899', 'icon': 'BookOpen', 'target_minutes': 120, 'description': 'Kernel, Memory & Threads'},
        ]

        subjects_dict = {}
        for s_info in subjects_data:
            subj, _ = Subject.objects.get_or_create(
                user=user,
                name=s_info['name'],
                defaults=s_info
            )
            subjects_dict[subj.name] = subj

        # 2. Tasks
        tasks_data = [
            {'title': 'Revise Binary Search Trees', 'subject': subjects_dict['DSA'], 'duration_minutes': 45, 'status': 'todo', 'priority': 'high', 'scheduled_date': today},
            {'title': 'Complete Linear Algebra Assignment', 'subject': subjects_dict['Mathematics'], 'duration_minutes': 60, 'status': 'in_progress', 'priority': 'high', 'scheduled_date': today},
            {'title': 'Practice SQL Joins & Subqueries', 'subject': subjects_dict['DBMS'], 'duration_minutes': 45, 'status': 'completed', 'completed': True, 'priority': 'medium', 'scheduled_date': today},
            {'title': 'OS Process Scheduling Algorithms', 'subject': subjects_dict['Operating Systems'], 'duration_minutes': 50, 'status': 'todo', 'priority': 'medium', 'scheduled_date': today},
            {'title': 'Python AsyncIO Deep Dive', 'subject': subjects_dict['Python'], 'duration_minutes': 40, 'status': 'todo', 'priority': 'low', 'scheduled_date': today + datetime.timedelta(days=1)},
        ]

        for t_info in tasks_data:
            Task.objects.get_or_create(
                user=user,
                title=t_info['title'],
                defaults=t_info
            )

        # 3. Schedule Items
        schedule_data = [
            {'title': 'DSA BST Revision', 'subject': subjects_dict['DSA'], 'date': today, 'start_time': datetime.time(9, 0), 'end_time': datetime.time(10, 30), 'type': 'study', 'color': '#3b82f6'},
            {'title': 'Linear Algebra', 'subject': subjects_dict['Mathematics'], 'date': today, 'start_time': datetime.time(10, 45), 'end_time': datetime.time(12, 0), 'type': 'study', 'color': '#8b5cf6'},
            {'title': 'Lunch & Break', 'date': today, 'start_time': datetime.time(12, 30), 'end_time': datetime.time(13, 30), 'type': 'break', 'color': '#10b981'},
            {'title': 'SQL Practice', 'subject': subjects_dict['DBMS'], 'date': today, 'start_time': datetime.time(14, 0), 'end_time': datetime.time(15, 30), 'type': 'study', 'completed': True, 'color': '#f59e0b'},
        ]

        for sch in schedule_data:
            ScheduleItem.objects.get_or_create(
                user=user,
                title=sch['title'],
                date=sch['date'],
                start_time=sch['start_time'],
                defaults=sch
            )

        # 4. Daily Challenge
        DailyChallenge.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'title': 'Master 5 LeetCode Problems',
                'description': 'Solve 3 Medium and 2 Easy problems on Arrays & Trees',
                'target_minutes': 90,
                'completed_minutes': 45,
                'completed': False,
            }
        )

        # 5. Goals
        Goal.objects.get_or_create(
            user=user,
            name='Daily 4 Hours Focus',
            defaults={'target_minutes': 240, 'period': 'daily', 'start_date': today}
        )
        Goal.objects.get_or_create(
            user=user,
            name='Weekly 25 Hours Focus',
            defaults={'target_minutes': 1500, 'period': 'weekly', 'start_date': today}
        )

        # 6. Exams
        Exam.objects.get_or_create(
            user=user,
            title='Data Structures Mid-Term Exam',
            defaults={
                'subject': subjects_dict['DSA'],
                'exam_date': today + datetime.timedelta(days=5),
                'exam_time': datetime.time(10, 0),
                'priority': 'high',
                'status': 'upcoming',
                'description': 'Covers Stacks, Queues, Trees & Graphs'
            }
        )
        Exam.objects.get_or_create(
            user=user,
            title='DBMS Semester Assessment',
            defaults={
                'subject': subjects_dict['DBMS'],
                'exam_date': today + datetime.timedelta(days=12),
                'exam_time': datetime.time(14, 0),
                'priority': 'medium',
                'status': 'upcoming',
                'description': 'Normalization, SQL, Indexing'
            }
        )

        # 7. Habits
        h1, _ = Habit.objects.get_or_create(user=user, name='Morning Code Warmup', defaults={'description': '30 mins problem solving'})
        h2, _ = Habit.objects.get_or_create(user=user, name='Night Notes Revision', defaults={'description': '15 mins reading summary'})

        HabitLog.objects.get_or_create(habit=h1, date=today, defaults={'completed': True})
        HabitLog.objects.get_or_create(habit=h2, date=today, defaults={'completed': False})

        # 8. Notes
        Note.objects.get_or_create(
            user=user,
            title='Graph Traversal Algorithms (BFS / DFS)',
            defaults={
                'subject': subjects_dict['DSA'],
                'content': 'BFS uses a Queue while DFS uses a Stack/Recursion. Time complexity: O(V + E).',
                'tags': ['dsa', 'graphs', 'algorithms']
            }
        )
        Note.objects.get_or_create(
            user=user,
            title='ACID Properties in Relational Databases',
            defaults={
                'subject': subjects_dict['DBMS'],
                'content': 'Atomicity, Consistency, Isolation, Durability guarantee transaction reliability.',
                'tags': ['dbms', 'sql', 'theory']
            }
        )

        # 9. Notifications
        Notification.objects.get_or_create(
            user=user,
            title='Upcoming Exam: Data Structures Mid-Term',
            defaults={
                'message': 'Your DSA exam is scheduled in 5 days.',
                'type': 'exam',
                'read': False
            }
        )
        Notification.objects.get_or_create(
            user=user,
            title='Daily Goal 50% Complete',
            defaults={
                'message': 'You have studied for 2 hours today. Keep it up!',
                'type': 'goal',
                'read': True
            }
        )

        # 10. Study Sessions (Past completed)
        StudySession.objects.get_or_create(
            user=user,
            title='DSA Session',
            started_at=timezone.now() - datetime.timedelta(hours=3),
            defaults={
                'subject': subjects_dict['DSA'],
                'ended_at': timezone.now() - datetime.timedelta(hours=1, minutes=30),
                'duration_seconds': 5400,
                'status': 'completed',
                'notes': 'Focused on binary trees and traversals.'
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded Study data into PostgreSQL!'))
