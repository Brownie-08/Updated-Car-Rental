"""
Email utility functions for the car rental system.
Handles professional email notifications with proper error handling.
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

# Import Car model (avoiding circular import by importing within functions if needed)


def send_booking_confirmation_email(order, selected_car=None):
    """
    Send a professional booking confirmation email to the customer.
    
    Args:
        order: Order instance
        selected_car: Car instance (optional)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get customer email
        customer_email = None
        if order.customer and order.customer.email:
            customer_email = order.customer.email
        elif hasattr(order.customer, 'email') and order.customer.email:
            customer_email = order.customer.email
        
        if not customer_email:
            logger.warning(f"No email found for order {order.order_number}")
            return False
        
        # Email subject
        subject = f"🚗 Booking Confirmation #{order.order_number} - Brownie Car Rental"
        
        # Email context
        context = {
            'order': order,
            'selected_car': selected_car,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
            'support_email': 'support@browniecarrental.com',
            'support_phone': '+1 (555) 123-4567',
        }
        
        # Render email templates
        html_content = render_to_string('emails/booking_confirmation.html', context)
        text_content = render_to_string('emails/booking_confirmation.txt', context)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
            reply_to=['support@browniecarrental.com']
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        # Update order email tracking
        order.email_sent = True
        order.email_sent_at = timezone.now()
        order.save(update_fields=['email_sent', 'email_sent_at'])
        
        logger.info(f"Booking confirmation email sent successfully for order {order.order_number} to {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email for order {order.order_number}: {str(e)}")
        return False


def send_admin_notification_email(order, selected_car=None):
    """
    Send notification email to admin about new booking.
    
    Args:
        order: Order instance
        selected_car: Car instance (optional)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Admin email subject
        subject = f"🔔 New Booking Alert #{order.order_number} - Brownie Car Rental"
        
        # Email context
        context = {
            'order': order,
            'selected_car': selected_car,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        
        # Render admin email templates
        html_content = render_to_string('emails/admin_booking_notification.html', context)
        text_content = render_to_string('emails/admin_booking_notification.txt', context)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.DEFAULT_FROM_EMAIL],
            reply_to=['support@browniecarrental.com']
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"Admin notification email sent successfully for order {order.order_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification email for order {order.order_number}: {str(e)}")
        return False


def send_booking_status_update_email(order, old_status, new_status):
    """
    Send email notification when booking status changes.
    
    Args:
        order: Order instance
        old_status: Previous status
        new_status: New status
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get customer email
        customer_email = None
        if order.customer and order.customer.email:
            customer_email = order.customer.email
        
        if not customer_email:
            logger.warning(f"No email found for order {order.order_number}")
            return False
        
        # Email subject based on status
        status_subjects = {
            'confirmed': f"✅ Booking Confirmed #{order.order_number}",
            'cancelled': f"❌ Booking Cancelled #{order.order_number}",
            'completed': f"🎉 Booking Completed #{order.order_number}",
        }
        
        subject = status_subjects.get(new_status, f"📋 Booking Status Update #{order.order_number}")
        
        # Status-specific messages
        status_messages = {
            'confirmed': "Great news! Your booking has been confirmed and is ready for pickup.",
            'cancelled': "Your booking has been cancelled. If you have any questions, please contact our support team.",
            'completed': "Thank you for choosing Brownie Car Rental! Your booking has been completed successfully.",
        }
        
        message = status_messages.get(new_status, f"Your booking status has been updated to {new_status}.")
        
        # Email content
        email_content = f"""
Dear {order.dealer_name},

{message}

Order Details:
Order Number: {order.order_number}
Car: {order.car_name}
Status: {order.get_status_display()}
Total Amount: ${order.total_amount}

If you have any questions, please don't hesitate to contact our support team:
Phone: +1 (555) 123-4567
Email: support@browniecarrental.com

Thank you for choosing Brownie Car Rental!

---
Brownie Car Rental Team
        """
        
        from django.core.mail import send_mail
        
        send_mail(
            subject=subject,
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Status update email sent successfully for order {order.order_number} to {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send status update email for order {order.order_number}: {str(e)}")
        return False


def send_order_approval_notification(order, approving_admin=None):
    """
    Send a professional order approval and payment confirmation email to customer.
    
    Args:
        order: Order instance
        approving_admin: User who approved the order (optional)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get customer email
        customer_email = None
        customer_name = "Valued Customer"
        
        if order.customer and order.customer.email:
            customer_email = order.customer.email
            customer_name = order.customer.get_full_name() or order.customer.username
        elif hasattr(order, 'dealer_name') and order.dealer_name:
            customer_name = order.dealer_name
        
        if not customer_email:
            logger.warning(f"No customer email found for order {order.order_number}")
            return False
        
        # Get car details
        try:
            from .models import Car
            selected_car = Car.objects.get(car_name=order.car_name)
            car_details = {
                'name': selected_car.car_name,
                'company': selected_car.company_name,
                'seats': selected_car.num_of_seats,
                'image_url': selected_car.image.url if selected_car.image else None
            }
        except:
            car_details = {
                'name': order.car_name,
                'company': 'Premium Vehicle',
                'seats': 'N/A',
                'image_url': None
            }
        
        # Email subject
        subject = f"🎉 Booking Approved & Payment Confirmed - Order #{order.order_number}"
        
        # Professional HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Booking Approved - Brownie Car Rental</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background: white;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 40px 20px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
                    <h1 style="margin: 0; font-size: 28px; font-weight: 700;">Booking Approved!</h1>
                    <p style="margin: 10px 0 0; font-size: 16px; opacity: 0.9;">Your car rental has been confirmed and is ready for pickup</p>
                </div>
                
                <!-- Success Badge -->
                <div style="text-align: center; padding: 20px;">
                    <div style="display: inline-block; background: #d4edda; color: #155724; padding: 12px 24px; border-radius: 25px; font-weight: 600; border: 2px solid #c3e6cb;">
                        ✅ PAYMENT CONFIRMED & BOOKING APPROVED
                    </div>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 0 30px;">
                    <p style="font-size: 18px; color: #333; margin-bottom: 25px;">Dear {customer_name},</p>
                    
                    <p style="font-size: 16px; color: #555; line-height: 1.6; margin-bottom: 20px;">
                        Excellent news! Your car rental booking has been <strong style="color: #28a745;">approved and confirmed</strong>. 
                        Your payment has been processed successfully, and your vehicle is reserved and ready for pickup.
                    </p>
                    
                    <!-- Booking Details Card -->
                    <div style="background: #f8f9fa; border-left: 4px solid #28a745; padding: 25px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                        <h3 style="margin: 0 0 20px; color: #333; font-size: 20px;">📋 Confirmed Booking Details</h3>
                        
                        <div style="display: grid; gap: 15px;">
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef;">
                                <span style="font-weight: 600; color: #666;">Order Number:</span>
                                <span style="font-weight: 700; color: #28a745; font-size: 16px;">#{order.order_number}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef;">
                                <span style="font-weight: 600; color: #666;">Vehicle:</span>
                                <span style="font-weight: 600; color: #333;">{car_details['name']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef;">
                                <span style="font-weight: 600; color: #666;">Manufacturer:</span>
                                <span style="color: #555;">{car_details['company']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef;">
                                <span style="font-weight: 600; color: #666;">Rental Period:</span>
                                <span style="color: #555;">{order.date_from.strftime('%b %d, %Y')} - {order.date_to.strftime('%b %d, %Y')}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e9ecef;">
                                <span style="font-weight: 600; color: #666;">Duration:</span>
                                <span style="color: #555;">{order.get_rental_duration_display()}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                                <span style="font-weight: 600; color: #666;">Total Amount:</span>
                                <span style="font-weight: 700; color: #28a745; font-size: 18px;">${order.total_amount}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Payment Status -->
                    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f1f8e9 100%); padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <h3 style="margin: 0 0 15px; color: #1976d2; font-size: 18px;">💳 Payment Confirmation</h3>
                        <p style="margin: 0; color: #555; line-height: 1.5;">
                            <strong>✅ Payment Status: CONFIRMED</strong><br>
                            Your payment of <strong>${order.total_amount}</strong> has been successfully processed and confirmed. 
                            You will receive a separate receipt for your records.
                        </p>
                    </div>
                    
                    <!-- Next Steps -->
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <h3 style="margin: 0 0 15px; color: #856404; font-size: 18px;">📞 Next Steps</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #856404; line-height: 1.7;">
                            <li>Our team will contact you within <strong>24 hours</strong> to arrange pickup details</li>
                            <li>Please bring a <strong>valid driver's license</strong> and a <strong>major credit card</strong></li>
                            <li>Vehicle inspection will be conducted before and after rental</li>
                            <li>Arrive <strong>15 minutes early</strong> for pickup to complete paperwork</li>
                        </ul>
                    </div>
                    
                    <!-- Contact Information -->
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <h3 style="margin: 0 0 15px; color: #333; font-size: 18px;">📞 Contact Information</h3>
                        <div style="display: grid; gap: 8px;">
                            <p style="margin: 0; color: #555;"><strong>📞 Phone:</strong> +1 (555) 123-4567</p>
                            <p style="margin: 0; color: #555;"><strong>📧 Email:</strong> support@browniecarrental.com</p>
                            <p style="margin: 0; color: #555;"><strong>🕐 Hours:</strong> 24/7 Customer Support</p>
                            <p style="margin: 0; color: #555;"><strong>📍 Address:</strong> 123 Premium Drive, Downtown</p>
                        </div>
                    </div>
                    
                    <p style="font-size: 16px; color: #555; line-height: 1.6; margin: 30px 0;">
                        Thank you for choosing Brownie Car Rental! We're committed to providing you with an exceptional 
                        car rental experience. If you have any questions or concerns, please don't hesitate to contact our 
                        24/7 support team.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #343a40; color: white; padding: 30px 20px; text-align: center;">
                    <div style="margin-bottom: 15px;">
                        <h3 style="margin: 0; font-size: 24px; color: #20c997;">🚗 Brownie Car Rental</h3>
                        <p style="margin: 5px 0 0; opacity: 0.8; font-size: 14px;">Premium Car Rental Service</p>
                    </div>
                    
                    <div style="font-size: 14px; opacity: 0.7; line-height: 1.5;">
                        <p style="margin: 0;">This email was sent to confirm your booking approval and payment.</p>
                        <p style="margin: 5px 0 0;">© 2025 Brownie Car Rental. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_content = f"""
        🎉 BOOKING APPROVED & PAYMENT CONFIRMED
        
        Dear {customer_name},
        
        Excellent news! Your car rental booking has been approved and confirmed.
        Your payment has been processed successfully, and your vehicle is reserved.
        
        CONFIRMED BOOKING DETAILS:
        ========================
        Order Number: #{order.order_number}
        Vehicle: {car_details['name']}
        Manufacturer: {car_details['company']}
        Rental Period: {order.date_from.strftime('%b %d, %Y')} - {order.date_to.strftime('%b %d, %Y')}
        Duration: {order.get_rental_duration_display()}
        Total Amount: ${order.total_amount}
        
        PAYMENT CONFIRMATION:
        ====================
        ✅ Payment Status: CONFIRMED
        Your payment of ${order.total_amount} has been successfully processed.
        
        NEXT STEPS:
        ===========
        • Our team will contact you within 24 hours for pickup arrangements
        • Bring valid driver's license and major credit card
        • Arrive 15 minutes early for pickup
        • Vehicle inspection will be conducted
        
        CONTACT INFORMATION:
        ===================
        Phone: +1 (555) 123-4567
        Email: support@browniecarrental.com
        Hours: 24/7 Customer Support
        Address: 123 Premium Drive, Downtown
        
        Thank you for choosing Brownie Car Rental!
        
        Best regards,
        Brownie Car Rental Team
        
        ---
        This email confirms your booking approval and payment.
        © 2025 Brownie Car Rental. All rights reserved.
        """
        
        # Create and send email
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
            reply_to=['support@browniecarrental.com']
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        # Log the email activity
        try:
            from .models import EmailLog
            EmailLog.objects.create(
                recipient_email=customer_email,
                sender_email=settings.DEFAULT_FROM_EMAIL,
                subject=subject,
                email_type='booking_status_update',
                status='sent',
                user=order.customer,
                order=order,
                html_content=html_content,
                text_content=text_content,
                sent_at=timezone.now()
            )
        except Exception as log_error:
            logger.warning(f"Could not log email for order {order.order_number}: {str(log_error)}")
        
        # Update order email tracking
        if hasattr(order, 'email_sent'):
            order.email_sent = True
            order.email_sent_at = timezone.now()
            order.save(update_fields=['email_sent', 'email_sent_at'])
        
        logger.info(f"Order approval email sent successfully for {order.order_number} to {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order approval email for {order.order_number}: {str(e)}")
        return False


def send_message_response(message_obj, response_text, admin_user):
    """
    Send response email to customer who submitted a message through contact form
    """
    try:
        # Prepare context for email template
        context = {
            'customer_name': message_obj.name,
            'original_message': message_obj.message,
            'response_message': response_text,
            'admin_name': admin_user.get_full_name() or admin_user.username,
            'admin_title': 'Customer Support Specialist',
            'company_name': 'Brownie Car Rental',
            'company_phone': '+1 (555) 123-4567',
            'company_email': settings.DEFAULT_FROM_EMAIL,
            'response_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
            'website_url': 'http://localhost:8000',  # Update with actual domain
        }
        
        # Email subject
        subject_prefix = f"Re: {message_obj.subject}" if message_obj.subject else "Response to Your Inquiry"
        subject = f"{subject_prefix} - Brownie Car Rental Support"
        
        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Response to Your Inquiry</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; }}
                .container {{ max-width: 700px; margin: 0 auto; background: white; }}
                .header {{ background: linear-gradient(135deg, #2c5aa0 0%, #1e4084 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 40px; }}
                .original-message {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0; border-radius: 5px; }}
                .response-message {{ background: #e8f5e8; padding: 25px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 5px; }}
                .footer {{ background: #f8f9fa; padding: 25px; text-align: center; border-top: 1px solid #dee2e6; }}
                .signature {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; }}
                .contact-info {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .btn {{ display: inline-block; background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .highlight {{ color: #007bff; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 {context['company_name']}</h1>
                    <p>Customer Support Response</p>
                </div>
                
                <div class="content">
                    <h2>Hello {context['customer_name']},</h2>
                    
                    <p>Thank you for contacting us! We've received your message and are pleased to provide you with a response.</p>
                    
                    <div class="original-message">
                        <h4>📩 Your Original Message:</h4>
                        <p><em>"{context['original_message']}"</em></p>
                    </div>
                    
                    <div class="response-message">
                        <h4>💬 Our Response:</h4>
                        <p>{context['response_message']}</p>
                    </div>
                    
                    <div class="contact-info">
                        <h4>📞 Need Further Assistance?</h4>
                        <p>If you have additional questions or need more help, please don't hesitate to contact us:</p>
                        <ul style="list-style: none; padding: 0;">
                            <li>📧 <strong>Email:</strong> {context['company_email']}</li>
                            <li>📱 <strong>Phone:</strong> {context['company_phone']}</li>
                            <li>🌐 <strong>Website:</strong> <a href="{context['website_url']}">{context['website_url']}</a></li>
                        </ul>
                    </div>
                    
                    <p>We appreciate your interest in {context['company_name']} and look forward to serving you!</p>
                    
                    <div class="signature">
                        <p><strong>{context['admin_name']}</strong><br>
                        {context['admin_title']}<br>
                        {context['company_name']}<br>
                        <em>Responded on {context['response_date']}</em></p>
                    </div>
                </div>
                
                <div class="footer">
                    <p><small>This email was sent in response to your inquiry submitted through our website contact form.<br>
                    {context['company_name']} - Your Trusted Car Rental Partner</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        CUSTOMER SUPPORT RESPONSE - {context['company_name']}
        
        Hello {context['customer_name']},
        
        Thank you for contacting us! We've received your message and are pleased to provide you with a response.
        
        YOUR ORIGINAL MESSAGE:
        "{context['original_message']}"
        
        OUR RESPONSE:
        {context['response_message']}
        
        NEED FURTHER ASSISTANCE?
        If you have additional questions or need more help, please contact us:
        - Email: {context['company_email']}
        - Phone: {context['company_phone']}
        - Website: {context['website_url']}
        
        We appreciate your interest in {context['company_name']} and look forward to serving you!
        
        Best regards,
        {context['admin_name']}
        {context['admin_title']}
        {context['company_name']}
        
        Responded on {context['response_date']}
        
        ---
        This email was sent in response to your inquiry submitted through our website contact form.
        {context['company_name']} - Your Trusted Car Rental Partner
        """
        
        # Create and send email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[message_obj.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send the email
        result = msg.send()
        
        if result:
            logger.info(f"Message response email sent successfully to {message_obj.email}")
            print(f"Message response email sent successfully to {message_obj.email}")
            return True
        else:
            logger.error(f"Failed to send message response email to {message_obj.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending message response email to {message_obj.email if message_obj else 'unknown'}: {str(e)}")
        return False
