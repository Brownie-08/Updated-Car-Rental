/**
 * AI Chat Widget for Car Rental System
 * Handles chat UI interactions, API calls, and booking flow
 */

class ChatWidget {
    constructor(options = {}) {
        this.options = {
            containerId: 'chat-widget',
            apiBase: '/api/ai-chat/',
            autoGreeting: true,
            ...options
        };
        
        this.sessionId = null;
        this.isInitialized = false;
        this.isTyping = false;
        this.messageQueue = [];
        this.apiClient = new ChatAPIClient(this.options.apiBase);
        
        // UI Elements (will be set after initialization)
        this.container = null;
        this.messagesContainer = null;
        this.inputField = null;
        this.sendButton = null;
        this.typingIndicator = null;
        
        this.init();
    }
    
    async init() {
        try {
            this.container = document.getElementById(this.options.containerId);
            if (!this.container) {
                console.error('Chat widget container not found:', this.options.containerId);
                return;
            }
            
            this.setupElements();
            this.attachEventListeners();
            
            // Initialize chat session
            await this.initializeSession();
            
            if (this.options.autoGreeting) {
                await this.sendMessage('hello');
            }
            
            this.isInitialized = true;
            console.log('Chat widget initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize chat widget:', error);
            this.showError('Failed to initialize chat. Please refresh and try again.');
        }
    }
    
    setupElements() {
        this.messagesContainer = this.container.querySelector('.chat-messages');
        this.inputField = this.container.querySelector('.chat-input input');
        this.sendButton = this.container.querySelector('.chat-input button');
        this.typingIndicator = this.container.querySelector('.typing-indicator');
        
        if (!this.messagesContainer || !this.inputField || !this.sendButton) {
            throw new Error('Required chat elements not found in container');
        }
    }
    
    attachEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.handleSendMessage());
        
        // Send message on Enter key
        this.inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Enable/disable send button based on input
        this.inputField.addEventListener('input', () => {
            this.sendButton.disabled = this.inputField.value.trim() === '' || this.isTyping;
        });
        
        // Handle quick reply clicks
        this.messagesContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-reply-btn')) {
                this.handleQuickReply(e.target);
            }
            
            if (e.target.classList.contains('car-select-btn')) {
                this.handleCarSelection(e.target);
            }
            
            if (e.target.classList.contains('booking-action-btn')) {
                this.handleBookingAction(e.target);
            }
        });
    }
    
    async initializeSession() {
        try {
            const response = await this.apiClient.createSession();
            this.sessionId = response.session_id;
            console.log('Chat session created:', this.sessionId);
        } catch (error) {
            console.error('Failed to create chat session:', error);
            throw error;
        }
    }
    
    async handleSendMessage() {
        const message = this.inputField.value.trim();
        if (!message || this.isTyping) return;
        
        await this.sendMessage(message);
        this.inputField.value = '';
        this.sendButton.disabled = true;
    }
    
    async sendMessage(message, action = null, actionData = {}) {
        if (!this.sessionId) {
            console.error('No active session');
            return;
        }
        
        try {
            // Show user message immediately
            if (message && !action) {
                this.addMessage('user', message);
            }
            
            this.showTyping();
            
            const response = await this.apiClient.sendMessage({
                session_id: this.sessionId,
                message: message,
                action: action,
                action_data: actionData
            });
            
            this.hideTyping();
            
            if (response.success) {
                this.handleResponse(response.response);
            } else {
                this.showError(response.message || 'Failed to send message');
            }
            
        } catch (error) {
            this.hideTyping();
            console.error('Error sending message:', error);
            this.showError('Connection error. Please try again.');
        }
    }
    
    handleResponse(responseData) {
        const { text, type, quick_replies, car_cards, booking_preview, actions } = responseData;
        
        // Add main response text
        if (text) {
            this.addMessage('bot', text);
        }
        
        // Handle car cards
        if (car_cards && car_cards.length > 0) {
            this.addCarCards(car_cards);
        }
        
        // Handle booking preview
        if (booking_preview) {
            this.addBookingPreview(booking_preview);
        }
        
        // Handle quick replies
        if (quick_replies && quick_replies.length > 0) {
            this.addQuickReplies(quick_replies);
        }
        
        // Handle special actions
        if (actions && actions.length > 0) {
            this.handleActions(actions);
        }
        
        this.scrollToBottom();
    }
    
    async handleQuickReply(button) {
        const action = button.dataset.action;
        const actionData = JSON.parse(button.dataset.actionData || '{}');
        const text = button.textContent;
        
        // Remove quick reply buttons after selection
        this.removeQuickReplies();
        
        // Send action to backend
        await this.sendMessage(text, action, actionData);
    }
    
    async handleCarSelection(button) {
        const carId = button.dataset.carId;
        const carName = button.dataset.carName;
        
        await this.sendMessage(`I want to select ${carName}`, 'select_car_for_booking', { car_id: carId });
    }
    
    async handleBookingAction(button) {
        const action = button.dataset.action;
        const actionData = JSON.parse(button.dataset.actionData || '{}');
        
        if (action === 'confirm_booking') {
            await this.confirmBooking();
        } else if (action === 'preview_booking') {
            await this.previewBooking();
        }
    }
    
    async previewBooking() {
        try {
            this.showTyping();
            const response = await this.apiClient.previewBooking(this.sessionId);
            this.hideTyping();
            
            if (response.success) {
                this.addBookingPreview(response.booking_preview);
            } else {
                this.showError(response.message || 'Failed to preview booking');
            }
        } catch (error) {
            this.hideTyping();
            console.error('Error previewing booking:', error);
            this.showError('Failed to preview booking. Please try again.');
        }
    }
    
    async confirmBooking(paymentMethod = 'paystack') {
        try {
            this.showTyping();
            const response = await this.apiClient.createBooking(this.sessionId, paymentMethod);
            this.hideTyping();
            
            if (response.success) {
                const order = response.order;
                const payment = response.payment;
                
                this.addMessage('bot', `✅ Booking confirmed! Order #${order.order_number}\n\nTotal: $${order.total_amount} ${order.currency}`);
                
                if (payment.payment_url) {
                    this.addPaymentLink(payment.payment_url, payment.method);
                }
            } else {
                this.showError(response.message || 'Failed to create booking');
            }
        } catch (error) {
            this.hideTyping();
            console.error('Error creating booking:', error);
            this.showError('Failed to create booking. Please try again.');
        }
    }
    
    addMessage(sender, content, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? 'U' : (sender === 'bot' ? '🤖' : '👤');
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = this.formatMessage(content);
        
        if (sender === 'user') {
            messageDiv.appendChild(bubble);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(bubble);
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addCarCards(cars) {
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'car-cards-container mb-3';
        
        cars.forEach(car => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'car-card';
            cardDiv.innerHTML = `
                <div class="car-card-image">
                    ${car.image ? `<img src="${car.image}" alt="${car.name}">` : '<div class="car-placeholder">🚗</div>'}
                </div>
                <div class="car-card-content">
                    <h5 class="car-name">${car.name}</h5>
                    <p class="car-category">${car.category}</p>
                    <p class="car-price">$${car.price_per_day}/${car.currency} per day</p>
                    <div class="car-features">
                        ${car.features.slice(0, 3).map(feature => `<span class="feature-tag">${feature}</span>`).join('')}
                    </div>
                    <div class="car-actions">
                        <button class="btn btn-primary btn-sm car-select-btn" 
                                data-car-id="${car.id}" 
                                data-car-name="${car.name}">
                            Select
                        </button>
                        <button class="btn btn-outline-primary btn-sm" 
                                onclick="this.showCarDetails(${car.id})">
                            Details
                        </button>
                    </div>
                </div>
            `;
            cardsContainer.appendChild(cardDiv);
        });
        
        this.messagesContainer.appendChild(cardsContainer);
        this.scrollToBottom();
    }
    
    addBookingPreview(preview) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'booking-preview mb-3';
        
        const { car, rental_period, location, pricing, customer } = preview;
        
        previewDiv.innerHTML = `
            <div class="booking-preview-header">
                <h5>🚗 Booking Summary</h5>
            </div>
            <div class="booking-preview-content">
                <div class="booking-section">
                    <h6>Vehicle</h6>
                    <p><strong>${car.name}</strong> - ${car.category}</p>
                </div>
                
                <div class="booking-section">
                    <h6>Rental Period</h6>
                    <p>${rental_period.pickup_date} to ${rental_period.dropoff_date}</p>
                    <p>${rental_period.rental_days} days</p>
                </div>
                
                <div class="booking-section">
                    <h6>Location</h6>
                    <p>Pickup: ${location.pickup_location}</p>
                    <p>Return: ${location.dropoff_location}</p>
                </div>
                
                <div class="booking-section">
                    <h6>Pricing</h6>
                    <div class="pricing-breakdown">
                        <div class="pricing-row">
                            <span>Daily Rate:</span>
                            <span>$${pricing.daily_rate}</span>
                        </div>
                        <div class="pricing-row">
                            <span>Subtotal (${rental_period.rental_days} days):</span>
                            <span>$${pricing.subtotal}</span>
                        </div>
                        <div class="pricing-row">
                            <span>Tax (${pricing.tax_rate}%):</span>
                            <span>$${pricing.tax_amount}</span>
                        </div>
                        <div class="pricing-row total">
                            <span><strong>Total:</strong></span>
                            <span><strong>$${pricing.total}</strong></span>
                        </div>
                    </div>
                </div>
                
                <div class="booking-actions">
                    <button class="btn btn-success booking-action-btn" data-action="confirm_booking">
                        Confirm Booking
                    </button>
                    <button class="btn btn-outline-secondary" onclick="this.editBooking()">
                        Edit Details
                    </button>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(previewDiv);
        this.scrollToBottom();
    }
    
    addQuickReplies(replies) {
        const repliesContainer = document.createElement('div');
        repliesContainer.className = 'quick-replies-container mb-3';
        
        replies.forEach(reply => {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary btn-sm quick-reply-btn me-2 mb-2';
            button.textContent = reply.text;
            button.dataset.action = reply.action;
            if (reply.action_data) {
                button.dataset.actionData = JSON.stringify(reply.action_data);
            }
            repliesContainer.appendChild(button);
        });
        
        this.messagesContainer.appendChild(repliesContainer);
        this.scrollToBottom();
    }
    
    addPaymentLink(paymentUrl, method) {
        const paymentDiv = document.createElement('div');
        paymentDiv.className = 'payment-link-container mb-3';
        paymentDiv.innerHTML = `
            <div class="payment-notice">
                <h6>💳 Complete Payment</h6>
                <p>Click the button below to complete your payment securely via ${method}.</p>
                <a href="${paymentUrl}" target="_blank" class="btn btn-success">
                    Pay Now - Secure Checkout
                </a>
            </div>
        `;
        
        this.messagesContainer.appendChild(paymentDiv);
        this.scrollToBottom();
    }
    
    removeQuickReplies() {
        const repliesContainers = this.messagesContainer.querySelectorAll('.quick-replies-container');
        repliesContainers.forEach(container => container.remove());
    }
    
    showTyping() {
        this.isTyping = true;
        this.sendButton.disabled = true;
        this.inputField.disabled = true;
        
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'block';
            this.typingIndicator.textContent = '🤖 Brownie Assistant is typing...';
        }
    }
    
    hideTyping() {
        this.isTyping = false;
        this.sendButton.disabled = this.inputField.value.trim() === '';
        this.inputField.disabled = false;
        
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message alert alert-danger';
        errorDiv.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        this.messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }
    
    handleActions(actions) {
        actions.forEach(action => {
            switch (action) {
                case 'escalate_to_human':
                    this.handleEscalation();
                    break;
                case 'show_welcome':
                    this.showWelcomeActions();
                    break;
                case 'end_conversation':
                    this.endConversation();
                    break;
            }
        });
    }
    
    async handleEscalation() {
        try {
            const response = await this.apiClient.escalateToHuman(this.sessionId);
            if (response.success) {
                this.addMessage('system', 'Your conversation has been escalated to our support team. A human agent will assist you shortly.');
            }
        } catch (error) {
            console.error('Error escalating to human:', error);
            this.showError('Failed to escalate to human agent. Please try again.');
        }
    }
    
    showWelcomeActions() {
        // Add any special welcome actions here
        console.log('Welcome actions triggered');
    }
    
    endConversation() {
        this.addMessage('system', 'Thank you for using Brownie Car Rentals! This conversation has ended.');
        this.inputField.disabled = true;
        this.sendButton.disabled = true;
    }
    
    formatMessage(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/\u2022/g, '•'); // Bullet points
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }
    
    // Public methods for external use
    async loadChatHistory() {
        try {
            const response = await this.apiClient.getChatHistory(this.sessionId);
            if (response.success) {
                this.messagesContainer.innerHTML = '';
                response.messages.forEach(msg => {
                    this.addMessage(msg.sender_type, msg.content, msg.created_at);
                });
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    destroy() {
        this.isInitialized = false;
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

/**
 * Chat API Client for backend communication
 */
class ChatAPIClient {
    constructor(apiBase) {
        this.apiBase = apiBase;
        this.csrfToken = this.getCSRFToken();
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async createSession(sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return await this.request(`session/create/${params}`, { method: 'GET' });
    }
    
    async sendMessage(data) {
        return await this.request('message/send/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    async previewBooking(sessionId) {
        return await this.request('booking/preview/', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
    }
    
    async createBooking(sessionId, paymentMethod = 'paystack') {
        return await this.request('booking/create/', {
            method: 'POST',
            body: JSON.stringify({ 
                session_id: sessionId, 
                payment_method: paymentMethod 
            })
        });
    }
    
    async getChatHistory(sessionId, limit = 50) {
        return await this.request(`history/?session_id=${sessionId}&limit=${limit}`, { 
            method: 'GET' 
        });
    }
    
    async escalateToHuman(sessionId) {
        return await this.request('escalate/', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-widget');
    if (chatContainer) {
        window.chatWidget = new ChatWidget();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatWidget, ChatAPIClient };
}