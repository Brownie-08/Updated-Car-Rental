"""
Management command for email system operations.
Provides functionality to retry failed emails, get statistics, and manage email logs.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from system.models import EmailLog
import json


class Command(BaseCommand):
    help = 'Manage email system operations'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['test', 'stats'],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for statistics (default: 30)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'stats':
            self.show_statistics(options)
        elif action == 'test':
            self.test_email_system(options)

    def show_statistics(self, options):
        """Display email statistics"""
        days = options['days']
        
        self.stdout.write(
            self.style.SUCCESS(f'📊 Email Statistics (Last {days} days)')
        )
        self.stdout.write('=' * 50)
        
        from datetime import timedelta
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get basic statistics
        total_logs = EmailLog.objects.filter(created_at__gte=start_date).count()
        sent_logs = EmailLog.objects.filter(created_at__gte=start_date, status='sent').count()
        failed_logs = EmailLog.objects.filter(created_at__gte=start_date, status='failed').count()
        pending_logs = EmailLog.objects.filter(created_at__gte=start_date, status='pending').count()
        
        self.stdout.write(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        self.stdout.write(f"📧 Total Emails: {total_logs}")
        self.stdout.write(f"✅ Sent: {sent_logs}")
        self.stdout.write(f"❌ Failed: {failed_logs}")
        self.stdout.write(f"⏳ Pending: {pending_logs}")
        
        if total_logs > 0:
            success_rate = (sent_logs / total_logs * 100)
            self.stdout.write(f"📈 Success Rate: {success_rate:.1f}%")

    def test_email_system(self, options):
        """Test email system functionality"""
        self.stdout.write(
            self.style.SUCCESS('🧪 Testing email system...')
        )
        
        # Test 1: Check email configuration
        self.stdout.write('\n1. Testing email configuration...')
        try:
            from django.conf import settings
            from django.core.mail import get_connection
            
            connection = get_connection()
            self.stdout.write(f"   Backend: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"   Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
            self.stdout.write(f"   Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
            self.stdout.write(f"   From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}")
            self.stdout.write('   ✅ Configuration loaded successfully')
        except Exception as e:
            self.stdout.write(f'   ❌ Configuration error: {e}')
        
        # Test 2: Check database models
        self.stdout.write('\n2. Testing database models...')
        try:
            total_logs = EmailLog.objects.count()
            recent_logs = EmailLog.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            
            self.stdout.write(f"   Total email logs: {total_logs}")
            self.stdout.write(f"   Recent logs (7 days): {recent_logs}")
            self.stdout.write('   ✅ Database models working correctly')
        except Exception as e:
            self.stdout.write(f'   ❌ Database error: {e}')
        
        # Test 3: Check templates
        self.stdout.write('\n3. Testing email templates...')
        try:
            from django.template.loader import get_template
            
            templates = [
                'emails/booking_confirmation.html',
                'emails/booking_confirmation.txt',
            ]
            
            for template_name in templates:
                template = get_template(template_name)
                self.stdout.write(f"   ✅ {template_name} found")
                
        except Exception as e:
            self.stdout.write(f'   ❌ Template error: {e}')
        
        # Test 4: Basic functionality
        self.stdout.write('\n4. Testing basic functionality...')
        try:
            from system.email_utils import send_booking_confirmation_email
            self.stdout.write('   ✅ Email utility functions accessible')
        except Exception as e:
            self.stdout.write(f'   ❌ Email utility error: {e}')
        
        self.stdout.write('\n🎉 Email system test completed!')
