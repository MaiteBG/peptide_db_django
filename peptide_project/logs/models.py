from django.contrib.auth.models import User
from django.db import models


class UserActionLog(models.Model):
    """
    Logs user interactions with the system.
    Includes contact details and information about the performed action.
    """
    log_date = models.DateTimeField(auto_now_add=True)
    contact_name = models.CharField(max_length=100)
    organization_name = models.CharField(max_length=100)
    email = models.EmailField()
    action = models.CharField(max_length=20)
    action_info = models.TextField(blank=True, null=True)
    allow_commercial = models.BooleanField()

    def __str__(self):
        """
        Returns a summary of the logged action.
        Example: "download by Alice Smith on 2025-05-23"
        """
        return f"{self.action} by {self.contact_name} on {self.log_date:%Y-%m-%d}"


class ModelChangeLog(models.Model):
    """
    Logs changes made to specific models for traceability or audit purposes.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    change_type = models.CharField(max_length=10,
                                   choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete')])
    change_details = models.TextField()

    def __str__(self):
        return f"{self.change_type} on {self.model_name} (ID: {self.object_id}) at {self.timestamp:%Y-%m-%d %H:%M}"


class ErrorLog(models.Model):
    """
    Stores information about system or user-generated errors.
    Useful for debugging and support.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    endpoint = models.CharField(max_length=200)
    error_message = models.TextField()
    traceback = models.TextField(blank=True, null=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Error at {self.endpoint} on {self.timestamp:%Y-%m-%d %H:%M}"
