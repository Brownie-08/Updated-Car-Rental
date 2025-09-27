# 🚗 Brownie Car Rental System

**Modern AI-Powered Car Rental Platform**

Welcome to Brownie Car Rental System - a state-of-the-art web application built with Django that revolutionizes the car rental experience. This platform combines traditional car rental functionality with cutting-edge AI technology to provide an intelligent, user-friendly experience for both customers and rental businesses.

## 🌟 Key Features

### 🤖 AI-Powered Assistant
- **Intelligent Chat Support**: Advanced AI assistant that helps users find cars, get pricing information, and complete bookings
- **Natural Language Processing**: Users can ask questions in natural language and get intelligent responses
- **Visual Car Cards**: AI displays car information with images, specifications, and interactive booking options
- **Smart Recommendations**: AI suggests cars based on user preferences and booking history
- **24/7 Availability**: AI assistant provides round-the-clock support for customers

### 🔐 User Authentication & Management
- **Secure Authentication**: Robust login and registration system with password encryption
- **User Profiles**: Comprehensive user profile management with avatar system
- **Password Recovery**: Secure password reset functionality with email verification
- **Role-based Access**: Different access levels for customers, staff, and administrators
- **Session Management**: Secure session handling and user context tracking

### 🚙 Advanced Car Management
- **Dynamic Car Database**: Comprehensive car listings with detailed specifications
- **Image Management**: High-quality car images with fallback handling
- **Real-time Availability**: Live availability checking and booking conflict prevention
- **Car Categories**: Organized by luxury, SUV, sedan, compact, and convertible categories
- **Feature Detection**: Automatic feature extraction from car descriptions
- **Popularity Tracking**: User engagement metrics and car popularity rankings

### 📱 Modern Booking System
- **Multi-step Booking Flow**: Intuitive booking process with real-time validation
- **Payment Integration**: Multiple payment options (Stripe, Paystack, Pay Later)
- **Booking Management**: Comprehensive order tracking and status updates
- **Calendar Integration**: Date picker with availability checking
- **Pricing Calculator**: Dynamic pricing with tax calculation and billing breakdown
- **PDF Receipts**: Professional PDF receipt generation with detailed information

### 💬 Enhanced Communication
- **AI Chat Interface**: Interactive chat system with rich message types
- **Contact Forms**: Direct communication channels with rental business
- **Email Notifications**: Automated email confirmations and updates
- **Message Management**: Admin panel for managing customer inquiries
- **Response Tracking**: Message status tracking and response management

### 📊 Admin Dashboard & Analytics
- **Comprehensive Dashboard**: Real-time analytics and business metrics
- **Revenue Tracking**: Revenue analytics with growth calculations
- **Customer Management**: User management with behavioral insights
- **Order Management**: Complete order lifecycle management
- **Reporting System**: Detailed reports and data visualization
## 🛠 Technology Stack

### Backend
- **Django 5.1**: Modern Python web framework with advanced features
- **Django REST Framework**: Powerful API development toolkit
- **PostgreSQL/SQLite**: Robust database management systems
- **Redis**: Session management and caching (optional)

### Frontend
- **Bootstrap 5.1.3**: Modern responsive UI framework
- **Font Awesome 6.0**: Comprehensive icon library
- **Vanilla JavaScript**: Clean, modern JavaScript implementation
- **CSS3**: Advanced styling with animations and responsive design

### AI & NLP
- **Custom AI Assistant**: Built-in natural language processing
- **Session Context Management**: Intelligent conversation tracking
- **Intent Recognition**: Advanced user intent classification
- **Entity Extraction**: Smart data extraction from user messages

### Payment Integration
- **Stripe**: International payment processing
- **Paystack**: African payment gateway integration
- **Multiple Payment Options**: Flexible payment methods

### Additional Features
- **ReportLab**: Professional PDF generation
- **Email Integration**: SMTP email notifications
- **Image Processing**: Car image management and optimization
- **Security**: CSRF protection, secure authentication, input validation

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/brownie-car-rental.git
   cd brownie-car-rental
   ```

2. **Create virtual environment**
   ```bash
   python -m venv car_rental_env
   
   # On Windows
   car_rental_env\Scripts\activate
   
   # On macOS/Linux
   source car_rental_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   cd brownie_car_rent
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Load sample data (optional)**
   ```bash
   python manage.py populate_bot_responses
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:8000`
   - Admin panel: `http://127.0.0.1:8000/admin`
   - AI Chat: `http://127.0.0.1:8000/chat`

## 🎯 Usage Guide

### For Customers
1. **Browse Cars**: View available cars with detailed information
2. **Use AI Assistant**: Ask questions like "Show me luxury cars" or "What are your prices?"
3. **Book a Car**: Select dates, choose payment method, complete booking
4. **Manage Bookings**: View and manage your rental history
5. **Get Support**: Use the AI chat for instant help

### For Administrators
1. **Access Admin Panel**: Use `/admin` to manage the system
2. **Manage Cars**: Add, edit, or remove car listings
3. **Handle Orders**: Process bookings and manage customer orders
4. **View Analytics**: Monitor business metrics and performance
5. **Customer Support**: Respond to customer inquiries

## 🤖 AI Assistant Features

The AI assistant can help with:
- **Car Search**: "Show me available SUVs" or "Cars under $100/day"
- **Booking Assistance**: Guide users through the booking process
- **Price Inquiries**: Provide pricing information by category
- **Policy Questions**: Answer questions about rental policies
- **Support Escalation**: Connect users with human agents when needed

## 📁 Project Structure

```
brownie-car-rental/
├── brownie_car_rent/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── system/
│   ├── models.py
│   ├── views.py
│   ├── ai_assistant_service.py
│   ├── session_model_service.py
│   └── payment_services.py
├── account/
│   ├── models.py
│   ├── views.py
│   └── forms.py
├── api/
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── templates/
├── static/
├── media/
└── requirements.txt
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3

# Email Configuration (use environment variables - NEVER commit real credentials)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Your Site <noreply@yoursite.com>

# Payment Gateway Keys (use environment variables - NEVER commit real keys)
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_paystack_public_key
PAYSTACK_SECRET_KEY=sk_test_your_paystack_secret_key

# Security Warning: 
# - Copy the .env.example file to .env and fill in your actual values
# - NEVER commit your .env file to version control
# - Use strong, unique passwords and API keys
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific tests
python manage.py test system.tests
python manage.py test api.tests
```

## 🔒 Security

### Important Security Notes
- **Never commit sensitive credentials** to version control
- Use environment variables for all sensitive configuration
- Keep your `.env` file in `.gitignore`
- Use strong, unique passwords for all accounts
- Regularly rotate API keys and passwords
- Enable 2FA on all external services (Stripe, Paystack, email providers)
- Use test/sandbox keys during development
- Review and audit dependencies regularly

### Production Security Checklist
- [ ] All sensitive data is in environment variables
- [ ] Debug mode is disabled in production
- [ ] HTTPS is enabled
- [ ] Database has strong passwords
- [ ] Static files are served securely
- [ ] Security headers are configured
- [ ] Regular security updates are applied

## 📈 Recent Updates

### Version 2.0 (Latest)
- ✅ Complete AI Assistant implementation
- ✅ Visual car cards with images
- ✅ Enhanced payment processing
- ✅ Modern UI/UX improvements
- ✅ Advanced session management
- ✅ Comprehensive error handling
- ✅ Mobile-responsive design
- ✅ Performance optimizations

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 coding standards
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support, email support@browniecarrental.com or join our community discussions.

## 🌟 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive UI components
- All contributors who helped improve this project

---

**Made with ❤️ by the Brownie Car Rental Team**
