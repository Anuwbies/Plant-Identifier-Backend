from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    @classmethod
    def generate_code(cls, user):
        # Invalidate any existing codes
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        return cls.objects.create(user=user, code=code)
    
    def is_expired(self):
        from django.conf import settings
        expiry_time = getattr(settings, 'OTP_EXPIRY_TIME', 600)  # 10 minutes default
        return (timezone.now() - self.created_at).total_seconds() > expiry_time
    
    def __str__(self):
        return f"Reset code for {self.user.email}: {self.code}"

# Create your models here.
