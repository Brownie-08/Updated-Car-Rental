from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse , HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
# from xhtml2pdf import pisa
from django.template.loader import render_to_string
from .models import Car, Order, PrivateMsg
from .forms import CarForm, OrderForm, MessageForm
from .email_utils import send_order_approval_notification, send_message_response
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()



def home(request):
    context = {
        "title" : "Car Rental"
    }
    return render(request,'home.html', context)

def car_list(request):
    car = Car.objects.all().order_by('id')  # Add ordering to fix pagination warning

    query = request.GET.get('q')
    if query:
        car = car.filter(
            Q(car_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(num_of_seats__icontains=query) |
            Q(cost_par_day__icontains=query) |
            Q(like__icontains=query)
        ).order_by('id')  # Maintain ordering even when filtered

    # pagination
    paginator = Paginator(car, 12)  # Show 12 cars per page
    page = request.GET.get('page')
    try:
        car = paginator.page(page)
    except PageNotAnInteger:
        car = paginator.page(1)
    except EmptyPage:
        car = paginator.page(paginator.num_pages)

    context = {
        'car': car,
    }
    return render(request, 'car_list.html', context)




def car_detail(request, id=None):
    detail = get_object_or_404(Car,id=id)
    context = {
        "detail": detail
    }
    return render(request, 'car_detail.html', context)

def car_created(request):
    form = CarForm(request.POST or None, request.FILES or None)
    
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        return HttpResponseRedirect("/")
    context = {
        "form" : form,
        "title": "Create Car"
    }
    return render(request, 'car_create.html', context)

@login_required
def car_update(request, id=None):
    detail = get_object_or_404(Car, id=id)
    form = CarForm(request.POST or None, instance=detail)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
        "title": "Update Car"
    }
    return render(request, 'car_create.html', context)

@login_required
def car_delete(request,id=None):
    query = get_object_or_404(Car,id = id)
    query.delete()

    car = Car.objects.all()
    context = {
        'car': car,
    }
    return render(request, 'admin_index.html', context)

#order

@login_required
def order_list(request):
    order = Order.objects.all().order_by('-id')  # Add ordering to fix pagination warning

    query = request.GET.get('q')
    if query:
        order = order.filter(
            Q(car_name__icontains=query)|
            Q(dealer_name__icontains=query)|
            Q(customer__username__icontains=query)|
            Q(customer__email__icontains=query)
        )

    # pagination
    paginator = Paginator(order, 4)  # Show 15 contacts per page
    page = request.GET.get('page')
    try:
        order = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        order = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        order = paginator.page(paginator.num_pages)
    context = {
        'order': order,
    }
    return render(request, 'order_list.html', context)

@login_required
def order_detail(request, id=None):
    detail = get_object_or_404(Order, id=id)
    context = {
        "detail": detail,
    }
    return render(request, 'order_detail.html', context) 

@login_required
def generate_receipt(request, id):
    try:
        detail = get_object_or_404(Order, id=id)
        
        # Get customer information (prioritize order customer over request user)
        customer = detail.customer if detail.customer else request.user
        customer_name = f"{customer.first_name} {customer.last_name}" if customer.first_name and customer.last_name else customer.username
        customer_email = customer.email if customer else 'N/A'
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()

        # Create a canvas object
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Define colors
        from reportlab.lib.colors import Color, black, white, darkblue, lightgrey
        header_color = Color(0.4, 0.49, 0.92)  # Blue gradient color
        
        # Company Header with background
        p.setFillColor(header_color)
        p.rect(0, height - 120, width, 120, fill=1, stroke=0)
        
        # Company Name
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 28)
        p.drawCentredString(width/2, height - 50, "Brownie Car Rental")
        
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 75, "Your Premium Car Rental Service")
        
        # Status Badge
        p.setFillColor(Color(0.06, 0.72, 0.51))  # Green color
        p.rect(width/2 - 60, height - 100, 120, 20, fill=1, stroke=0)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(width/2, height - 90, "BOOKING CONFIRMED")
        
        # Reset to black text
        p.setFillColor(black)
        
        # Order Number Box
        y_pos = height - 160
        p.setFont("Helvetica-Bold", 20)
        order_display = f"Order #{detail.order_number}" if detail.order_number else f"Order #{detail.id}"
        p.drawCentredString(width/2, y_pos, order_display)
        
        # Car Information Box
        y_pos = height - 200
        p.setFillColor(header_color)
        p.rect(80, y_pos - 30, width - 160, 50, fill=1, stroke=0)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, y_pos - 10, detail.car_name or "N/A")
        
        # Get car details
        try:
            selected_car = Car.objects.get(car_name=detail.car_name)
            company_name = selected_car.company_name
        except Car.DoesNotExist:
            company_name = "Premium Vehicle"
        
        p.setFont("Helvetica", 12)
        p.drawCentredString(width/2, y_pos - 25, company_name)
        
        # Booking Details Section
        p.setFillColor(black)
        y_pos = height - 270
        p.setFont("Helvetica-Bold", 14)
        p.drawString(80, y_pos, "Booking Details")
        
        # Draw a line under the section title
        p.line(80, y_pos - 5, width - 80, y_pos - 5)
        
        # Customer details with better error handling
        y_pos -= 30
        p.setFont("Helvetica", 11)
        details = [
            ("Customer Name:", customer_name or "N/A"),
            ("Phone Number:", detail.cell_no or "N/A"),
            ("Email Address:", customer_email),
            ("Address:", detail.address or "N/A"),
            ("Rental Period:", f"{detail.date_from.strftime('%B %d, %Y') if detail.date_from else 'N/A'} - {detail.date_to.strftime('%B %d, %Y') if detail.date_to else 'N/A'}"),
            ("Duration:", detail.get_rental_duration_display() if hasattr(detail, 'get_rental_duration_display') else "N/A"),
            ("Status:", detail.get_status_display() if hasattr(detail, 'get_status_display') else "Confirmed"),
            ("Booking Date:", detail.created_at.strftime('%B %d, %Y at %I:%M %p') if detail.created_at else 'N/A')
        ]
        
        for label, value in details:
            p.setFont("Helvetica-Bold", 11)
            p.drawString(80, y_pos, label)
            p.setFont("Helvetica", 11)
            p.drawString(200, y_pos, str(value))
            y_pos -= 20
        
        # Billing Section with error handling
        y_pos -= 20
        p.setFont("Helvetica-Bold", 14)
        p.drawString(80, y_pos, "Billing Summary")
        p.line(80, y_pos - 5, width - 80, y_pos - 5)
        
        # Billing details with null checks
        y_pos -= 30
        p.setFont("Helvetica", 11)
        
        # Handle billing fields safely
        daily_rate = getattr(detail, 'daily_rate', 0) or 0
        rental_days = getattr(detail, 'rental_days', 1) or 1
        subtotal = getattr(detail, 'subtotal', daily_rate * rental_days)
        tax_rate = getattr(detail, 'tax_rate', 10)
        tax_amount = getattr(detail, 'tax_amount', subtotal * (tax_rate / 100))
        total_amount = getattr(detail, 'total_amount', subtotal + tax_amount)
        
        billing_details = [
            ("Daily Rate:", f"${daily_rate:.2f}"),
            ("Rental Days:", f"{rental_days} day{'s' if rental_days > 1 else ''}"),
            ("Subtotal:", f"${subtotal:.2f}"),
            (f"Tax ({tax_rate}%):", f"${tax_amount:.2f}"),
        ]
        
        for label, value in billing_details:
            p.setFont("Helvetica-Bold", 11)
            p.drawString(80, y_pos, label)
            p.setFont("Helvetica", 11)
            p.drawString(200, y_pos, value)
            y_pos -= 20
        
        # Total amount with background
        y_pos -= 10
        p.setFillColor(lightgrey)
        p.rect(80, y_pos - 15, width - 160, 25, fill=1, stroke=1)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(90, y_pos - 5, "Total Amount:")
        p.drawRightString(width - 90, y_pos - 5, f"${total_amount:.2f}")
        
        # Important Information
        y_pos -= 50
        p.setFillColor(Color(0.94, 0.96, 1))  # Light blue background
        p.rect(80, y_pos - 100, width - 160, 110, fill=1, stroke=1)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(90, y_pos - 15, "Important Information")
        
        important_notes = [
            "• Please bring a valid driver's license for vehicle pickup",
            "• Payment can be made at pickup or delivery",
            "• Free cancellation up to 24 hours before rental",
            "• Vehicle inspection will be conducted at pickup and return",
            "• Late return charges may apply after grace period"
        ]
        
        y_pos -= 35
        p.setFont("Helvetica", 10)
        for note in important_notes:
            p.drawString(90, y_pos, note)
            y_pos -= 15
        
        # Contact Information
        y_pos -= 30
        p.setFillColor(Color(0.96, 0.96, 0.96))  # Light grey background
        p.rect(80, y_pos - 60, width - 160, 70, fill=1, stroke=1)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(90, y_pos - 15, "Need Help?")
        
        p.setFont("Helvetica-Bold", 10)
        p.drawString(90, y_pos - 35, "24/7 Customer Support")
        p.setFont("Helvetica", 10)
        p.drawString(90, y_pos - 50, "Phone: +1 (555) 123-4567")
        p.drawString(250, y_pos - 50, "Email: support@browniecarrental.com")
        
        # Footer
        p.setFont("Helvetica", 8)
        p.drawCentredString(width/2, 50, "Thank you for choosing Brownie Car Rental!")
        p.drawCentredString(width/2, 35, "© 2024 Brownie Car Rental. All rights reserved.")
        
        # Save the PDF file
        p.showPage()
        p.save()

        # Get PDF data from buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create HTTP response with PDF data
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"BookingReceipt_{detail.order_number or detail.id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF receipt for order {id}: {str(e)}")
        messages.error(request, "There was an error generating the PDF receipt. Please try again or contact support.")
        return redirect('order_detail', id=id)



@login_required
def order_created(request, car_id=None):
    selected_car = None
    if car_id:
        selected_car = get_object_or_404(Car, id=car_id)
    
    form = OrderForm(request.POST or None)
    
    # Pre-fill car name if a car is selected
    if selected_car and request.method == 'GET':
        form.fields['car_name'].initial = selected_car.car_name
        form.fields['car_name'].widget.attrs['readonly'] = True
    
    if form.is_valid():
        instance = form.save(commit=False)
        instance.customer = request.user
        
        # Set billing information from selected car
        if selected_car:
            instance.daily_rate = selected_car.cost_par_day
        else:
            # If no car_id was provided but car_name is in form, try to find the car
            car_name = form.cleaned_data.get('car_name')
            if car_name:
                try:
                    car = Car.objects.get(car_name=car_name)
                    instance.daily_rate = car.cost_par_day
                except Car.DoesNotExist:
                    # Car name doesn't match any existing car - daily_rate will remain default (0)
                    pass
        
        instance.save()
        
        # Get selected payment method
        payment_method = form.cleaned_data.get('payment_method', 'pay_later')
        
        # Process payment based on selected method
        if payment_method == 'stripe':
            # Redirect to payment processing
            from .payment_services import StripePaymentService
            
            result = StripePaymentService.create_payment_intent(instance)
            if result['success']:
                # Redirect to Stripe checkout
                return render(request, 'system/payment/stripe_checkout.html', {
                    'order': instance,
                    'client_secret': result['client_secret'],
                    'transaction': result['transaction'],
                    'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
                    'selected_car': selected_car
                })
            else:
                messages.error(request, f"Payment initialization failed: {result['error']}")
                return HttpResponseRedirect(instance.get_absolute_url())
        
        elif payment_method == 'pay_later':
            # Handle pay-later option
            from .payment_services import PayLaterService
            
            result = PayLaterService.create_pay_later_order(instance)
            if result['success']:
                # Send booking confirmation emails
                from .email_utils import send_booking_confirmation_email, send_admin_notification_email
                
                try:
                    # Send customer confirmation email
                    email_sent = send_booking_confirmation_email(instance, selected_car)
                    
                    # Send admin notification email
                    admin_email_sent = send_admin_notification_email(instance, selected_car)
                    
                    if email_sent:
                        messages.success(request, 
                            f'🎉 Booking confirmed! Order #{instance.order_number} has been created. '
                            f'You can pay at pickup/delivery. A confirmation email has been sent to {request.user.email}.')
                    else:
                        messages.warning(request, 
                            f'Booking created successfully (Order #{instance.order_number}), but we couldn\'t send the confirmation email. '
                            f'Please check your email settings or contact support.')
                            
                except Exception as e:
                    logger.error(f"Error sending booking emails for order {instance.order_number}: {str(e)}")
                    messages.warning(request, 
                        f'Booking created successfully (Order #{instance.order_number}), but there was an issue sending emails. '
                        f'Please contact support if you need assistance.')
            else:
                messages.error(request, f"Booking failed: {result['error']}")
                return render(request, 'order_create.html', {
                    'form': form,
                    'title': 'Create Order',
                    'selected_car': selected_car
                })
        
        else:
            # Unsupported payment method - default to pay later
            messages.warning(request, f"Payment method '{payment_method}' not yet supported. Booking created with pay-later option.")
        
        return HttpResponseRedirect(instance.get_absolute_url())

    context = {
        "form": form,
        "title": "Create Order",
        "selected_car": selected_car
    }
    return render(request, 'order_create.html', context)

@login_required
def order_update(request, id=None):
    detail = get_object_or_404(Order, id=id)
    form = OrderForm(request.POST or None, instance=detail)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
        "title": "Update Order"
    }
    return render(request, 'order_create.html', context)

@login_required
def order_delete(request, id=None):
    """Enhanced order cancellation with email notifications and better handling"""
    order = get_object_or_404(Order, id=id)
    
    # Store order details for emails before deletion
    order_details = {
        'order_number': order.order_number,
        'car_name': order.car_name,
        'customer_email': order.customer.email if order.customer else None,
        'customer_name': order.customer.get_full_name() if order.customer else 'N/A',
        'pick_up_location': order.pick_up_location,
        'drop_off_location': order.drop_off_location,
        'pick_up_date': order.pick_up_date,
        'drop_off_date': order.drop_off_date,
        'total_amount': order.total_amount,
    }
    
    try:
        # Send cancellation notification emails
        from .email_utils import send_cancellation_notification_email, send_admin_cancellation_notification_email
        
        email_sent = False
        admin_email_sent = False
        
        # Send customer cancellation email
        if order_details['customer_email']:
            email_sent = send_cancellation_notification_email(order_details)
        
        # Send admin cancellation notification
        admin_email_sent = send_admin_cancellation_notification_email(order_details)
        
        # Delete the order
        order.delete()
        
        # Success message with email status
        if email_sent:
            messages.success(request, 
                f'🗑️ Order #{order_details["order_number"]} has been cancelled successfully! '
                f'A cancellation confirmation has been sent to {order_details["customer_email"]}.')
        else:
            messages.warning(request, 
                f'Order #{order_details["order_number"]} has been cancelled, but we couldn\'t send the confirmation email. '
                f'Please check your email settings or contact support.')
                
    except Exception as e:
        logger.error(f"Error during order cancellation for order {order_details['order_number']}: {str(e)}")
        
        # Still delete the order even if email fails
        order.delete()
        
        messages.warning(request, 
            f'Order #{order_details["order_number"]} has been cancelled, but there was an issue sending notification emails. '
            f'Please contact support if you need assistance.')
    
    # Conditional redirect based on user role
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponseRedirect("/admin_dash/")
    else:
        return HttpResponseRedirect("/booking/")

def newcar(request):
    new = Car.objects.order_by('-id')
    #seach
    query = request.GET.get('q')
    if query:
        new = new.filter(
            Q(car_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(num_of_seats__icontains=query) |
            Q(cost_par_day__icontains=query) |
            Q(like__icontains=query) 
        )

    # pagination
    paginator = Paginator(new, 12)  # Show 15 contacts per page
    page = request.GET.get('page')
    try:
        new = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        new = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        new = paginator.page(paginator.num_pages)
    context = {
        'car': new,
    }
    return render(request, 'new_car.html', context)

def like_update(request, id=None):
    """Like functionality for both authenticated and unauthenticated users"""
    if request.method == 'POST':
        try:
            car = get_object_or_404(Car, id=id)
            car.like += 1
            car.save()
            return JsonResponse({
                'success': True,
                'likes': car.like,
                'message': 'Car liked successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def popular_car(request):
    new = Car.objects.order_by('-like')
    # seach
    query = request.GET.get('q')
    if query:
        new = new.filter(
            Q(car_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(num_of_seats__icontains=query) |
            Q(cost_par_day__icontains=query) |
            Q(like__icontains=query)   
        )

    # pagination
    paginator = Paginator(new, 12)  # Show 15 contacts per page
    page = request.GET.get('page')
    try:
        new = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        new = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        new = paginator.page(paginator.num_pages)
    context = {
        'car': new,
    }
    return render(request, 'new_car.html', context)

def contact(request):
    """Enhanced contact form view with better error handling and email notifications"""
    form = MessageForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        try:
            # Save the message
            instance = form.save(commit=False)
            instance.save()
            
            # Send email notification to admin
            try:
                subject = f"🚗 New Contact Message from {instance.name}"
                
                # HTML email content
                html_message = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                        <h2>🚗 New Contact Message</h2>
                        <p>Brownie Car Rental - Contact Form</p>
                    </div>
                    
                    <div style="padding: 20px; background: #f8f9fa;">
                        <h3>Contact Details:</h3>
                        <p><strong>Name:</strong> {instance.name}</p>
                        <p><strong>Email:</strong> {instance.email}</p>
                        <p><strong>Submitted:</strong> {instance.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        
                        <h3>Message:</h3>
                        <div style="background: white; padding: 15px; border-left: 4px solid #667eea; margin: 10px 0;">
                            {instance.message}
                        </div>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                            <p><strong>Next Steps:</strong></p>
                            <ul>
                                <li>Review the message in the admin panel</li>
                                <li>Respond to the customer within 24 hours</li>
                                <li>Mark as read when processed</li>
                            </ul>
                        </div>
                    </div>
                </div>
                """
                
                # Plain text version
                plain_message = f"""
                New Contact Message Received
                
                Name: {instance.name}
                Email: {instance.email}
                Submitted: {instance.created_at.strftime('%B %d, %Y at %I:%M %p')}
                
                Message:
                {instance.message}
                
                Please respond within 24 hours.
                """
                
                # Send email to admin
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Send confirmation email to customer
                customer_subject = "Thank you for contacting Brownie Car Rental!"
                customer_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                        <h2>🚗 Thank You for Your Message!</h2>
                        <p>Brownie Car Rental</p>
                    </div>
                    
                    <div style="padding: 20px; background: #f8f9fa;">
                        <p>Dear {instance.name},</p>
                        
                        <p>Thank you for contacting Brownie Car Rental. We have received your message and will respond within 24 hours.</p>
                        
                        <div style="background: white; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0;">
                            <p><strong>Your Message:</strong></p>
                            <p>{instance.message}</p>
                        </div>
                        
                        <p>In the meantime, feel free to browse our car rental options or contact us directly:</p>
                        <ul>
                            <li><strong>Phone:</strong> +1 (555) 123-4567</li>
                            <li><strong>Email:</strong> info@browniecarrental.com</li>
                            <li><strong>Hours:</strong> 24/7 Customer Support</li>
                        </ul>
                        
                        <p>Best regards,<br><strong>Brownie Car Rental Team</strong></p>
                    </div>
                </div>
                """
                
                customer_plain = f"""
                Dear {instance.name},
                
                Thank you for contacting Brownie Car Rental. We have received your message and will respond within 24 hours.
                
                Your Message:
                {instance.message}
                
                Contact Information:
                Phone: +1 (555) 123-4567
                Email: info@browniecarrental.com
                Hours: 24/7 Customer Support
                
                Best regards,
                Brownie Car Rental Team
                """
                
                # Send confirmation to customer
                send_mail(
                    subject=customer_subject,
                    message=customer_plain,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    html_message=customer_html,
                    fail_silently=True,  # Don't fail if customer email fails
                )
                
                messages.success(request, 
                    f'Thank you {instance.name}! Your message has been sent successfully. '
                    f'We will get back to you within 24 hours at {instance.email}.')
                
            except Exception as e:
                # Log the error but don't fail the form submission
                logger.error(f"Failed to send contact form emails: {str(e)}")
                messages.warning(request, 
                    'Your message was saved successfully, but we couldn\'t send email notifications. '
                    'We will still review your message and get back to you.')
            
            return HttpResponseRedirect("/car/contact/")
            
        except Exception as e:
            logger.error(f"Failed to save contact form: {str(e)}")
            messages.error(request, 
                'There was an error saving your message. Please try again or contact us directly.')
    
    context = {
        "form": form,
        "title": "Contact Us - Brownie Car Rental",
    }
    return render(request, 'contact.html', context)

def about(request):
    """About page view"""
    context = {
        "title": "About Us - Brownie Car Rental",
    }
    return render(request, 'about.html', context)

def services(request):
    """Services page view"""
    context = {
        "title": "Our Services - Brownie Car Rental",
    }
    return render(request, 'services.html', context)

def reviews(request):
    """Reviews page view with sample review data"""
    # Sample review data (you can replace this with actual database queries later)
    sample_reviews = [
        {
            'id': 1,
            'customer_name': 'John Smith',
            'rating': 5,
            'review_text': 'Exceptional service and premium vehicles! The booking process was seamless, and the car was in perfect condition. Will definitely book again.',
            'created_at': '2024-01-15',
        },
        {
            'id': 2,
            'customer_name': 'Sarah Johnson',
            'rating': 5,
            'review_text': 'Outstanding experience from start to finish. Professional staff, clean cars, and competitive prices. Highly recommended for anyone looking for quality car rental.',
            'created_at': '2024-01-10',
        },
        {
            'id': 3,
            'customer_name': 'Michael Brown',
            'rating': 4,
            'review_text': 'Great variety of cars to choose from. The luxury sedan I rented was perfect for my business trip. Customer service was very helpful.',
            'created_at': '2024-01-05',
        },
        {
            'id': 4,
            'customer_name': 'Emily Davis',
            'rating': 5,
            'review_text': 'Perfect for family vacation! Rented an SUV and it was spacious, comfortable, and reliable. The pickup and drop-off process was very convenient.',
            'created_at': '2023-12-28',
        },
        {
            'id': 5,
            'customer_name': 'David Wilson',
            'rating': 5,
            'review_text': 'Best car rental experience I have ever had. Fair pricing, excellent vehicles, and top-notch customer service. Will be my go-to rental company.',
            'created_at': '2023-12-20',
        },
        {
            'id': 6,
            'customer_name': 'Lisa Thompson',
            'rating': 5,
            'review_text': 'Needed a pickup truck for moving and they had exactly what I needed. Clean, reliable, and affordable. The team went above and beyond to help.',
            'created_at': '2023-12-15',
        },
    ]
    
    context = {
        "title": "Customer Reviews - Brownie Car Rental",
        "reviews": sample_reviews,
    }
    return render(request, 'reviews.html', context)

def booking(request):
    """Booking page view with form handling"""
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                
                # Associate with logged-in user if authenticated
                if request.user.is_authenticated:
                    instance.customer = request.user
                
                instance.save()
                
                # Send confirmation email to customer
                try:
                    customer_subject = f'Booking Confirmation - Order #{instance.id}'
                    customer_html = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 28px;">🚗 Booking Confirmed!</h1>
                        </div>
                        
                        <div style="padding: 20px; background: #f8f9fa;">
                            <p>Dear {instance.name},</p>
                            
                            <p>Thank you for choosing Brownie Car Rental! Your booking has been confirmed.</p>
                            
                            <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                                <h3 style="margin-top: 0; color: #333;">Booking Details:</h3>
                                <p><strong>Order ID:</strong> #{instance.id}</p>
                                <p><strong>Car:</strong> {instance.car_name}</p>
                                <p><strong>Pick-up Date:</strong> {instance.pick_up_date}</p>
                                <p><strong>Drop-off Date:</strong> {instance.drop_off_date}</p>
                                <p><strong>Pick-up Location:</strong> {instance.pick_up_location}</p>
                                <p><strong>Drop-off Location:</strong> {instance.drop_off_location}</p>
                                <p><strong>Phone:</strong> {instance.phone}</p>
                                <p><strong>Email:</strong> {instance.email}</p>
                            </div>
                            
                            <p>We will contact you within 24 hours to confirm availability and provide final details.</p>
                            
                            <p>For any questions, feel free to contact us:</p>
                            <ul>
                                <li><strong>Phone:</strong> +1 (555) 123-4567</li>
                                <li><strong>Email:</strong> info@browniecarrental.com</li>
                                <li><strong>Hours:</strong> 24/7 Customer Support</li>
                            </ul>
                            
                            <p>Best regards,<br><strong>Brownie Car Rental Team</strong></p>
                        </div>
                    </div>
                    """
                    
                    customer_plain = f"""
                    Dear {instance.name},
                    
                    Thank you for choosing Brownie Car Rental! Your booking has been confirmed.
                    
                    Booking Details:
                    Order ID: #{instance.id}
                    Car: {instance.car_name}
                    Pick-up Date: {instance.pick_up_date}
                    Drop-off Date: {instance.drop_off_date}
                    Pick-up Location: {instance.pick_up_location}
                    Drop-off Location: {instance.drop_off_location}
                    Phone: {instance.phone}
                    Email: {instance.email}
                    
                    We will contact you within 24 hours to confirm availability and provide final details.
                    
                    Contact Information:
                    Phone: +1 (555) 123-4567
                    Email: info@browniecarrental.com
                    Hours: 24/7 Customer Support
                    
                    Best regards,
                    Brownie Car Rental Team
                    """
                    
                    # Send confirmation to customer
                    send_mail(
                        subject=customer_subject,
                        message=customer_plain,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[instance.email],
                        html_message=customer_html,
                        fail_silently=True
                    )
                    
                    # Send notification to admin
                    admin_subject = f'New Car Booking - Order #{instance.id}'
                    admin_message = f"""
                    New car booking received:
                    
                    Order ID: #{instance.id}
                    Customer: {instance.name}
                    Car: {instance.car_name}
                    Pick-up Date: {instance.pick_up_date}
                    Drop-off Date: {instance.drop_off_date}
                    Pick-up Location: {instance.pick_up_location}
                    Drop-off Location: {instance.drop_off_location}
                    Phone: {instance.phone}
                    Email: {instance.email}
                    
                    Please follow up within 24 hours.
                    """
                    
                    send_mail(
                        subject=admin_subject,
                        message=admin_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else ['admin@browniecarrental.com'],
                        fail_silently=True
                    )
                    
                    messages.success(request, 
                        f'Thank you {instance.name}! Your booking has been confirmed. '
                        f'Confirmation details have been sent to {instance.email}.')
                        
                except Exception as e:
                    logger.error(f"Failed to send booking confirmation emails: {str(e)}")
                    messages.warning(request, 
                        'Your booking was saved successfully, but we couldn\'t send email confirmations. '
                        'We will still process your booking and contact you soon.')
                
                return HttpResponseRedirect(f"/order-detail/{instance.id}/")
                
            except Exception as e:
                logger.error(f"Failed to save booking: {str(e)}")
                messages.error(request, 
                    'There was an error processing your booking. Please try again.')
    else:
        form = OrderForm()
        
        # Pre-fill car name if provided in GET parameters
        car_name = request.GET.get('car')
        if car_name:
            form.initial['car_name'] = car_name
    
    context = {
        "form": form,
        "title": "Book Your Car - Brownie Car Rental",
    }
    return render(request, 'booking.html', context)

def test_car_list(request):
    """Test version of car_list view for debugging"""
    car = Car.objects.all().order_by('id')
    
    query = request.GET.get('q')
    if query:
        car = car.filter(
            Q(car_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(num_of_seats__icontains=query) |
            Q(cost_par_day__icontains=query) |
            Q(like__icontains=query)
        ).order_by('id')

    # pagination
    paginator = Paginator(car, 12)
    page = request.GET.get('page')
    try:
        car = paginator.page(page)
    except PageNotAnInteger:
        car = paginator.page(1)
    except EmptyPage:
        car = paginator.page(paginator.num_pages)

    context = {
        'car': car,
        'title': 'Test Car List'
    }
    return render(request, 'test_content.html', context)

def test_booking(request):
    """Test version of booking view for debugging"""
    form = OrderForm()
    
    context = {
        'form': form,
        'title': 'Test Booking Form'
    }
    return render(request, 'test_content.html', context)

def debug_info(request):
    """Debug information view for troubleshooting content display issues"""
    from django.conf import settings
    
    # Get sample data
    sample_cars = Car.objects.all()[:3]  # First 3 cars
    
    context = {
        "title": "Debug Information",
        "debug": settings.DEBUG,
        "car_count": Car.objects.count(),
        "order_count": Order.objects.count(),
        "user_count": User.objects.count(),
        "sample_cars": sample_cars,
    }
    return render(request, 'debug_info.html', context)

#-----------------Admin Section-----------------
@login_required
def base_dash(request):
    """Enhanced admin dashboard with comprehensive analytics"""
    from django.db.models import Count, Sum, Q, F
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    now = timezone.now()
    last_month = now - timedelta(days=30)
    current_month_start = now.replace(day=1)
    
    # Basic metrics
    total_orders = Order.objects.count()
    total_cars = Car.objects.count()
    available_cars = total_cars  # All cars are available in current model
    total_customers = User.objects.filter(is_staff=False).count()
    
    # Revenue calculations
    total_revenue = Order.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        created_at__gte=current_month_start
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Growth calculations
    last_month_orders = Order.objects.filter(
        created_at__gte=last_month,
        created_at__lt=current_month_start
    ).count()
    
    current_month_orders = Order.objects.filter(
        created_at__gte=current_month_start
    ).count()
    
    orders_growth = 0
    if last_month_orders > 0:
        orders_growth = round(((current_month_orders - last_month_orders) / last_month_orders) * 100, 1)
    
    # Recent activity
    recent_orders = Order.objects.select_related('customer').order_by('-id')[:10]
    popular_cars = Car.objects.order_by('-like')[:5]
    
    # New customers this month
    new_customers = User.objects.filter(
        is_staff=False,
        date_joined__gte=current_month_start
    ).count()
    
    # System alerts
    pending_orders_count = Order.objects.filter(status='pending').count() if hasattr(Order, 'status') else 0
    
    # Revenue data for chart (last 6 months)
    revenue_data = []
    revenue_labels = []
    
    for i in range(6):
        month_start = (now.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_revenue = Order.objects.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_data.insert(0, float(month_revenue))
        revenue_labels.insert(0, month_start.strftime('%b %Y'))
    
    # Additional context
    context = {
        'total_orders': total_orders,
        'total_cars': total_cars,
        'available_cars': available_cars,
        'total_customers': total_customers,
        'total_revenue': f"{total_revenue:,.2f}",
        'monthly_revenue': f"{monthly_revenue:,.2f}",
        'orders_growth': orders_growth,
        'new_customers': new_customers,
        'recent_orders': recent_orders,
        'popular_cars': popular_cars,
        'pending_orders_count': pending_orders_count,
        'revenue_data': revenue_data,
        'revenue_labels': revenue_labels,
        'last_backup': now - timedelta(hours=2),  # Mock data
        'low_stock_cars': Car.objects.filter(like__gt=50).count() > 0,  # Mock condition
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def admin_reports(request):
    """Admin reports and analytics view"""
    from django.db.models import Count, Sum, Q, F, Avg
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    now = timezone.now()
    
    # Sample report data (replace with actual calculations)
    context = {
        'period_revenue': '45,250',
        'revenue_growth': '12.5',
        'period_bookings': Order.objects.count(),
        'avg_daily_bookings': round(Order.objects.count() / 30, 1),
        'utilization_rate': '78',
        'active_vehicles': Car.objects.count(),
        'new_customers_period': User.objects.filter(
            is_staff=False,
            date_joined__gte=now - timedelta(days=30)
        ).count(),
        'customer_retention': '85',
        'avg_bookings_per_customer': '2.3',
        'avg_customer_value': '1,250',
        'top_cars': Car.objects.order_by('-like')[:5],
        'top_customers': User.objects.filter(is_staff=False)[:5],
    }
    
    return render(request, 'admin_reports.html', context)

@login_required
def admin_car_list(request):
    car = Car.objects.order_by('-id')

    query = request.GET.get('q')
    if query:
        car = car.filter(
            Q(car_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(num_of_seats__icontains=query) |
            Q(cost_par_day__icontains=query) |
            Q(like__icontains=query) 
        )

    # pagination
    paginator = Paginator(car, 12)  # Show 15 contacts per page
    page = request.GET.get('page')
    try:
        car = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        car = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        car = paginator.page(paginator.num_pages)
    context = {
        'car': car,
    }
    return render(request, 'admin_index.html', context)

@login_required
def admin_msg(request):
    """Admin messages view with pagination"""
    messages_list = PrivateMsg.objects.order_by('-id')
    
    # Search functionality (optional)
    query = request.GET.get('q')
    if query:
        messages_list = messages_list.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(sub__icontains=query) |
            Q(msg__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(messages_list, 10)  # Show 10 messages per page
    page = request.GET.get('page')
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        messages = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        messages = paginator.page(paginator.num_pages)
    
    context = {
        'messages': messages,
        'total_messages': PrivateMsg.objects.count(),
        'query': query,
    }
    return render(request, 'admin_msg.html', context)


@login_required
@require_POST
def update_order_status(request, id):
    """Update order status from pending to confirmed with email notification"""
    order = get_object_or_404(Order, id=id)
    old_status = order.status
    
    if order.status == 'pending':
        order.status = 'confirmed'
        order.save()
        
        # Send professional email notification to customer
        try:
            email_sent = send_order_approval_notification(order, request.user)
            
            if email_sent:
                messages.success(request, 
                    f'✅ Order #{order.order_number} has been approved and confirmed! '
                    f'Customer notification email sent to {order.customer.email if order.customer else "customer"}.')
            else:
                messages.warning(request, 
                    f'Order #{order.order_number} has been approved, but we couldn\'t send the confirmation email. '
                    f'Please contact the customer manually.')
        except Exception as e:
            logger.error(f"Error sending order approval email for {order.order_number}: {str(e)}")
            messages.warning(request, 
                f'Order #{order.order_number} has been approved, but there was an issue sending the notification email.')
    else:
        messages.info(request, f'Order #{order.order_number} is already processed (Status: {order.get_status_display()}).')
    
    return redirect('order_list')

def msg_delete(request,id=None):
    query = get_object_or_404(PrivateMsg, id=id)
    query.delete()
    return HttpResponseRedirect("/message/")

@login_required
@require_POST
def admin_msg_respond(request, id=None):
    """Handle admin response to customer messages"""
    message = get_object_or_404(PrivateMsg, id=id)
    
    response_text = request.POST.get('response_message', '').strip()
    
    if not response_text:
        messages.error(request, 'Response message cannot be empty.')
        return HttpResponseRedirect('/message/')
    
    try:
        # Send response email to customer
        email_sent = send_message_response(message, response_text, request.user)
        
        if email_sent:
            # Update message status
            message.response_message = response_text
            message.mark_as_replied(request.user)
            message.mark_as_read()
            
            messages.success(request, 
                f'✅ Response sent successfully to {message.name} ({message.email})! '
                f'Message has been marked as replied.')
        else:
            messages.error(request, 
                f'Failed to send response to {message.name} ({message.email}). '
                f'Please check the email configuration or try again.')
                
    except Exception as e:
        logger.error(f"Error sending message response to {message.email}: {str(e)}")
        messages.error(request, 
            f'There was an error sending the response to {message.name}. '
            f'Please try again or contact support.')
    
    return HttpResponseRedirect('/message/')
