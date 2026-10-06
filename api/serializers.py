from rest_framework import serializers
from .models import (
    ContactMessage, Profile, Subject, Task, ScheduleItem, StudySession,
    Goal, DailyChallenge, Exam, Habit, HabitLog, Note, Notification
)


class ContactMessageSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, required=True, trim_whitespace=True)
    email = serializers.EmailField(max_length=254, required=True, trim_whitespace=True)
    subject = serializers.CharField(max_length=200, required=True, trim_whitespace=True)
    message = serializers.CharField(max_length=5000, required=True, trim_whitespace=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at', 'is_read']
        read_only_fields = ['id', 'created_at', 'is_read']

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()

    def validate_subject(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Subject is required.")
        return value.strip()

    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message is required.")
        if len(value) > 5000:
            raise serializers.ValidationError("Message length exceeds 5000 characters limit.")
        return value.strip()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id', 'display_name', 'email', 'avatar', 'bio',
            'daily_study_goal_minutes', 'timezone', 'theme',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'description', 'color', 'icon',
            'target_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')
    subject_color = serializers.CharField(source='subject.color', read_only=True, default='#ff6b35')

    class Meta:
        model = Task
        fields = [
            'id', 'subject', 'subject_name', 'subject_color', 'title', 'description',
            'duration_minutes', 'due_date', 'scheduled_date', 'start_time', 'end_time',
            'status', 'priority', 'completed', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduleItemSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')

    class Meta:
        model = ScheduleItem
        fields = [
            'id', 'subject', 'subject_name', 'task', 'title', 'description',
            'date', 'start_time', 'end_time', 'type', 'color', 'completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudySessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')

    class Meta:
        model = StudySession
        fields = [
            'id', 'subject', 'subject_name', 'task', 'title', 'started_at',
            'ended_at', 'duration_seconds', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'id', 'name', 'target_minutes', 'period',
            'start_date', 'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChallenge
        fields = [
            'id', 'title', 'description', 'target_minutes', 'date',
            'completed_minutes', 'completed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExamSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')
    subject_color = serializers.CharField(source='subject.color', read_only=True, default='#ff6b35')

    class Meta:
        model = Exam
        fields = [
            'id', 'subject', 'subject_name', 'subject_color', 'title',
            'exam_date', 'exam_time', 'description', 'priority', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ['id', 'habit', 'date', 'completed', 'created_at']
        read_only_fields = ['id', 'created_at']


class HabitSerializer(serializers.ModelSerializer):
    logs = HabitLogSerializer(many=True, read_only=True)

    class Meta:
        model = Habit
        fields = [
            'id', 'name', 'description', 'frequency', 'target',
            'logs', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NoteSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')

    class Meta:
        model = Note
        fields = [
            'id', 'subject', 'subject_name', 'title', 'content', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'read', 'created_at']
        read_only_fields = ['id', 'created_at']

