from django import forms
from .models import Car, Order, PrivateMsg
from .payment_models import PaymentMethod

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            "image",
            "car_name",
            "company_name",
            "num_of_seats",
            "cost_par_day",
            "content",
        ]

class OrderForm(forms.ModelForm):
    PAYMENT_METHOD_CHOICES = [
        ('stripe', '💳 Credit/Debit Card (Stripe)'),
        ('paypal', '🅿️ PayPal'),
        ('pay_later', '⏰ Pay at Pickup/Delivery'),
        ('bank_transfer', '🏦 Bank Transfer'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'payment-method-radio'
        }),
        label='Payment Method',
        initial='stripe'
    )
    
    class Meta:
        model = Order
        fields = [
            "car_name",
            "dealer_name",
            "cell_no",
            "address",
            "date_from",
            "date_to",
        ]
        widgets = {
            'date_from': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'date_to': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'car_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter car name'
            }),
            'dealer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'cell_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your full address for delivery/pickup'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_to < date_from:
                raise forms.ValidationError('End date cannot be before start date.')
            
            from datetime import date
            if date_from < date.today():
                raise forms.ValidationError('Start date cannot be in the past.')
        
        return cleaned_data

class MessageForm(forms.ModelForm):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'autocomplete': 'name'
        }),
        label='Your Name',
        help_text='Please enter your full name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        label='Email Address',
        help_text='We will use this to respond to your message'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Please provide as much detail as possible about your inquiry...',
            'rows': 5,
            'cols': 50
        }),
        label='Your Message',
        help_text='Please provide as much detail as possible',
        min_length=10,
        max_length=1000
    )
    
    class Meta:
        model = PrivateMsg
        fields = ['name', 'email', 'message']
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.strip()) < 2:
            raise forms.ValidationError('Name must be at least 2 characters long.')
        return name.strip().title()
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 10:
            raise forms.ValidationError('Message must be at least 10 characters long.')
        if len(message.strip()) > 1000:
            raise forms.ValidationError('Message cannot exceed 1000 characters.')
        return message.strip()

class MessageResponseForm(forms.Form):
    response_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Type your response to the customer here...',
            'rows': 8,
            'cols': 50
        }),
        label='Response Message',
        help_text='This message will be sent to the customer via email',
        min_length=10,
        max_length=2000
    )
    
    priority = forms.ChoiceField(
        choices=PrivateMsg.PRIORITY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Priority Level',
        required=False,
        initial='normal'
    )
