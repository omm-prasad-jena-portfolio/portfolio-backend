from rest_framework import serializers
from .models import ContactMessage


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
