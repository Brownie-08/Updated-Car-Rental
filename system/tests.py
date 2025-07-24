"""
Tests for Payment System
Tests payment models, services, views, and integration
"""

import json
from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import date, timedelta

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from system.models import Car, Order
from system.payment_models import (
    PaymentMethod, PaymentTransaction, PaymentReceipt, 
    RefundRequest, PaymentWebhook
)
from system.payment_services import StripePaymentService, PayLaterService
from system.forms import OrderForm

User = get_user_model()


class PaymentModelsTestCase(TestCase):
    """Test payment models functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.car = Car.objects.create(
            car_name='Test Car',
            company_name='Test Company',
            num_of_seats=4,
            cost_par_day=50.00,
            content='Test car description'
        )
        
        self.order = Order.objects.create(
            customer=self.user,
            car_name='Test Car',
            dealer_name='Test User',
            cell_no='1234567890',
            address='123 Test St',
            date_from=date.today(),
            date_to=date.today() + timedelta(days=3),
            daily_rate=50.00
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='stripe',
            display_name='Credit/Debit Card',
            description='Secure payment via Stripe',
            processing_fee_percentage=Decimal('2.9')
        )
    
    def test_payment_method_creation(self):
        """Test PaymentMethod model creation"""
        self.assertEqual(self.payment_method.name, 'stripe')
        self.assertEqual(self.payment_method.display_name, 'Credit/Debit Card')
        self.assertTrue(self.payment_method.is_active)
        self.assertEqual(str(self.payment_method), 'Credit/Debit Card')
    
    def test_payment_transaction_creation(self):
        """Test PaymentTransaction model creation"""
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=Decimal('165.00'),
            currency='USD',
            status='pending',
            transaction_type='payment',
            description='Test payment'
        )
        
        self.assertEqual(transaction.order, self.order)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, Decimal('165.00'))
        self.assertEqual(transaction.status, 'pending')
        self.assertIsNotNone(transaction.transaction_id)
    
    def test_mark_transaction_as_completed(self):
        """Test marking transaction as completed"""
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=Decimal('165.00'),
            status='pending'
        )
        
        transaction.mark_as_completed()
        self.assertEqual(transaction.status, 'completed')
        self.assertIsNotNone(transaction.processed_at)
    
    def test_mark_transaction_as_failed(self):
        """Test marking transaction as failed"""
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=Decimal('165.00'),
            status='pending'
        )
        
        transaction.mark_as_failed('Test error')
        self.assertEqual(transaction.status, 'failed')
        self.assertIn('Test error', transaction.notes)
    
    def test_payment_receipt_generation(self):
        """Test PaymentReceipt model"""
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            user=self.user,
            payment_method=self.payment_method,
            amount=Decimal('165.00'),
            status='completed'
        )
        
        receipt = PaymentReceipt.objects.create(
            transaction=transaction,
            receipt_data={'test': 'data'}
        )
        
        self.assertIsNotNone(receipt.receipt_number)
        self.assertTrue(receipt.receipt_number.startswith('RCP-'))
        self.assertEqual(receipt.transaction, transaction)


class PaymentServicesTestCase(TestCase):
    """Test payment services"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            customer=self.user,
            car_name='Test Car',
            dealer_name='Test User',
            cell_no='1234567890',
            address='123 Test St',
            date_from=date.today(),
            date_to=date.today() + timedelta(days=3),
            daily_rate=50.00,
            total_amount=165.00
        )
    
    @patch('system.payment_services.stripe.PaymentIntent.create')
    def test_stripe_payment_intent_creation(self, mock_stripe_create):
        """Test Stripe payment intent creation"""
        mock_stripe_create.return_value = Mock(
            id='pi_test123',
            client_secret='pi_test123_secret',
            status='requires_payment_method'
        )
        
        result = StripePaymentService.create_payment_intent(self.order)
        
        self.assertTrue(result['success'])
        self.assertIn('client_secret', result)
        self.assertIn('transaction', result)
        
        # Check that transaction was created
        transaction = PaymentTransaction.objects.filter(order=self.order).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, 'pending')
    
    @patch('system.payment_services.stripe.PaymentIntent.retrieve')
    def test_stripe_payment_confirmation(self, mock_stripe_retrieve):
        """Test Stripe payment confirmation"""
        # Create a pending transaction first
        payment_method = PaymentMethod.objects.create(
            name='stripe',
            display_name='Credit/Debit Card'
        )
        
        transaction = PaymentTransaction.objects.create(
            order=self.order,
            user=self.user,
            payment_method=payment_method,
            amount=self.order.total_amount,
            status='pending',
            external_transaction_id='pi_test123'
        )
        
        mock_stripe_retrieve.return_value = Mock(
            id='pi_test123',
            status='succeeded'
        )
        
        result = StripePaymentService.confirm_payment('pi_test123')
        
        self.assertTrue(result['success'])
        
        # Check that transaction was marked as completed
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'completed')
        
        # Check that order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
    
    def test_pay_later_service(self):
        """Test PayLaterService functionality"""
        result = PayLaterService.create_pay_later_order(self.order)
        
        self.assertTrue(result['success'])
        self.assertIn('transaction', result)
        
        # Check that transaction was created
        transaction = PaymentTransaction.objects.filter(order=self.order).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, 'pending')
        self.assertIn('pay-later', transaction.description.lower())


class OrderFormTestCase(TestCase):
    """Test enhanced OrderForm with payment methods"""
    
    def test_order_form_payment_method_choices(self):
        """Test that payment method choices are available"""
        form = OrderForm()
        
        payment_choices = form.fields['payment_method'].choices
        choice_values = [choice[0] for choice in payment_choices]
        
        self.assertIn('stripe', choice_values)
        self.assertIn('paypal', choice_values)
        self.assertIn('pay_later', choice_values)
        self.assertIn('bank_transfer', choice_values)
    
    def test_order_form_validation(self):
        """Test form validation"""
        form_data = {
            'car_name': 'Test Car',
            'dealer_name': 'Test User',
            'cell_no': '1234567890',
            'address': '123 Test St',
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=3),
            'payment_method': 'stripe'
        }
        
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_order_form_date_validation(self):
        """Test date validation in form"""
        # Test end date before start date
        form_data = {
            'car_name': 'Test Car',
            'dealer_name': 'Test User',
            'cell_no': '1234567890',
            'address': '123 Test St',
            'date_from': date.today() + timedelta(days=3),
            'date_to': date.today(),
            'payment_method': 'stripe'
        }
        
        form = OrderForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('End date cannot be before start date', str(form.errors))


class PaymentViewsTestCase(TestCase):
    """Test payment views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            customer=self.user,
            car_name='Test Car',
            dealer_name='Test User',
            cell_no='1234567890',
            address='123 Test St',
            date_from=date.today(),
            date_to=date.today() + timedelta(days=3),
            daily_rate=50.00,
            total_amount=165.00
        )
        
        self.client.force_login(self.user)
    
    def test_order_creation_with_pay_later(self):
        """Test order creation with pay-later option"""
        car = Car.objects.create(
            car_name='Test Car 2',
            company_name='Test Company',
            num_of_seats=4,
            cost_par_day=60.00,
            content='Test description'
        )
        
        form_data = {
            'car_name': car.car_name,
            'dealer_name': 'Test Customer',
            'cell_no': '9876543210',
            'address': '456 Test Ave',
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=2),
            'payment_method': 'pay_later'
        }
        
        print(f"DEBUG: Posting form data: {form_data}")
        print(f"DEBUG: User authenticated: {self.user.is_authenticated}")
        print(f"DEBUG: User ID: {self.user.id}")
        
        response = self.client.post(
            reverse('system:order_created'), 
            data=form_data,
            follow=True
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response content preview: {response.content[:200]}")
        
        # Check that order was created successfully
        self.assertEqual(response.status_code, 200)
        
        # Check that order exists
        order = Order.objects.filter(car_name=car.car_name).first()
        print(f"DEBUG: Order found: {order}")
        if order:
            print(f"DEBUG: Order ID: {order.id}, Customer: {order.customer}")
        else:
            print("DEBUG: No order found, checking all orders:")
            all_orders = Order.objects.all()
            for o in all_orders:
                print(f"  Order: {o.id}, car_name: {o.car_name}, customer: {o.customer}")
        
        self.assertIsNotNone(order)
        self.assertEqual(order.customer, self.user)
        
        # Check that payment transaction was created
        transaction = PaymentTransaction.objects.filter(order=order).first()
        print(f"DEBUG: Transaction found: {transaction}")
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, 'pending')


class PaymentIntegrationTestCase(TestCase):
    """Integration tests for the complete payment flow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.car = Car.objects.create(
            car_name='Integration Test Car',
            company_name='Test Company',
            num_of_seats=4,
            cost_par_day=75.00,
            content='Integration test car'
        )
        
        self.client.force_login(self.user)
    
    def test_complete_booking_flow_pay_later(self):
        """Test complete booking flow with pay-later option"""
        # Step 1: Create order with pay-later
        form_data = {
            'car_name': self.car.car_name,
            'dealer_name': 'Integration Test User',
            'cell_no': '5551234567',
            'address': '789 Integration Ave',
            'date_from': date.today() + timedelta(days=1),
            'date_to': date.today() + timedelta(days=4),
            'payment_method': 'pay_later'
        }
        
        response = self.client.post(
            reverse('system:order_created'),
            data=form_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Verify order was created
        order = Order.objects.filter(car_name=self.car.car_name).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'pending')
        
        # Step 3: Verify payment transaction was created
        transaction = PaymentTransaction.objects.filter(order=order).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, 'pending')
        self.assertEqual(transaction.transaction_type, 'payment')
        
        # Step 4: Verify payment method
        self.assertEqual(transaction.payment_method.name, 'pay_later')
    
    @patch('system.payment_services.stripe.PaymentIntent.create')
    def test_stripe_integration_flow(self, mock_stripe_create):
        """Test Stripe integration flow"""
        mock_stripe_create.return_value = Mock(
            id='pi_integration_test',
            client_secret='pi_integration_test_secret',
            status='requires_payment_method'
        )
        
        form_data = {
            'car_name': self.car.car_name,
            'dealer_name': 'Stripe Test User',
            'cell_no': '5551234567',
            'address': '789 Stripe Ave',
            'date_from': date.today() + timedelta(days=1),
            'date_to': date.today() + timedelta(days=3),
            'payment_method': 'stripe'
        }
        
        response = self.client.post(
            reverse('system:order_created'),
            data=form_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Debug: Print response content to see what we got
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response content[:500]: {response.content.decode()[:500]}")
        print(f"DEBUG: 'client_secret' in response: {'client_secret' in response.content.decode()}")
        print(f"DEBUG: Mock client secret in response: {'pi_integration_test_secret' in response.content.decode()}")
        
        # Check that we got the Stripe checkout template with the actual client secret value
        self.assertContains(response, 'pi_integration_test_secret')
        
        # Verify order and transaction creation
        order = Order.objects.filter(
            car_name=self.car.car_name,
            dealer_name='Stripe Test User'
        ).first()
        self.assertIsNotNone(order)
        
        transaction = PaymentTransaction.objects.filter(order=order).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, 'pending')
        self.assertEqual(transaction.payment_method.name, 'stripe')


def run_payment_tests():
    """Run all payment-related tests"""
    import sys
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests([
        'system.tests.PaymentModelsTestCase',
        'system.tests.PaymentServicesTestCase', 
        'system.tests.OrderFormTestCase',
        'system.tests.PaymentViewsTestCase',
        'system.tests.PaymentIntegrationTestCase'
    ])
    
    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_payment_tests()
