/**
 * Brownie AI Chat Widget
 * Professional car rental chat assistant with guided booking flow
 */

class BrownieChatWidget {
    constructor(config = {}) {
        this.config = {
            apiBaseUrl: '/api/ai-chat/',
            sessionId: null,
            user: {
                authenticated: false,
                name: '',
                email: ''
            },
            autoStart: false,
            showWelcome: true,
            maxRetries: 3,
            retryDelay: 1000,
            typingDelay: 1000,
            ...config
        };
        
        this.isOpen = false;
        this.isTyping = false;
        this.messageHistory = [];
        this.currentBookingData = null;
        this.retryCount = 0;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        if (this.config.autoStart) {
            this.createSession();
        }
    }
    
    bindEvents() {
        // Toggle button click
        const toggleBtn = document.getElementById('chat-toggle-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleChat());
        }
        
        // Close and minimize buttons
        const closeBtn = document.getElementById('close-btn');
        const minimizeBtn = document.getElementById('minimize-btn');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeChat());
        }
        
        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', () => this.minimizeChat());
        }
        
        // Chat form submission
        const chatForm = document.getElementById('chat-form');
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        if (chatInput) {
            chatInput.addEventListener('input', () => this.handleInputChange());
            chatInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        }
        
        // Contact form modal
        const saveContactBtn = document.getElementById('save-contact-btn');
        if (saveContactBtn) {
            saveContactBtn.addEventListener('click', () => this.saveContactInfo());
        }
    }
    
    async createSession() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}session/create/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.config.sessionId = data.session_id;
                this.sessionModel = data.session_model;
                
                if (this.config.showWelcome) {
                    this.sendWelcomeMessage();
                }
                
                return true;
            } else {
                console.error('Failed to create chat session:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error creating chat session:', error);
            return false;
        }
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.minimizeChat();
        } else {
            this.openChat();
        }
    }
    
    async openChat() {
        if (!this.config.sessionId) {
            const sessionCreated = await this.createSession();
            if (!sessionCreated) {
                this.showError('Failed to start chat session. Please try again.');
                return;
            }
        }
        
        const chatWindow = document.getElementById('chat-window');
        const notificationBadge = document.getElementById('notification-badge');
        
        if (chatWindow) {
            chatWindow.style.display = 'flex';
            this.isOpen = true;
        }
        
        if (notificationBadge) {
            notificationBadge.style.display = 'none';
        }
        
        // Focus on input
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            setTimeout(() => chatInput.focus(), 100);
        }
    }
    
    minimizeChat() {
        const chatWindow = document.getElementById('chat-window');
        if (chatWindow) {
            chatWindow.style.display = 'none';
            this.isOpen = false;
        }
    }
    
    closeChat() {
        this.minimizeChat();
        // Could also end the session here if desired
    }
    
    handleInputChange() {
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        if (chatInput && sendBtn) {
            const hasContent = chatInput.value.trim().length > 0;
            sendBtn.disabled = !hasContent || this.isTyping;
        }
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter') {
            if (event.shiftKey) {
                // Allow new line with Shift+Enter
                return;
            } else {
                // Send message with Enter
                event.preventDefault();
                this.handleFormSubmit(event);
            }
        }
    }
    
    async handleFormSubmit(event) {
        event.preventDefault();
        
        const chatInput = document.getElementById('chat-input');
        if (!chatInput) return;
        
        const message = chatInput.value.trim();
        if (!message || this.isTyping) return;
        
        // Clear input
        chatInput.value = '';
        this.handleInputChange();
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Send message to API
        await this.sendMessage(message);
    }
    
    async sendMessage(message, action = null, actionData = null) {
        if (!this.config.sessionId) {
            this.showError('Chat session not initialized');
            return;
        }
        
        this.showTyping();
        
        try {
            const requestData = {
                session_id: this.config.sessionId,
                message: message
            };
            
            if (action) {
                requestData.action = action;
                requestData.action_data = actionData || {};
            }
            
            const response = await fetch(`${this.config.apiBaseUrl}message/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            this.hideTyping();
            
            if (data.success) {
                this.handleBotResponse(data.response);
                this.retryCount = 0; // Reset retry count on success
            } else {
                this.handleError(data.message);
            }
        } catch (error) {
            this.hideTyping();
            console.error('Error sending message:', error);
            
            if (this.retryCount < this.config.maxRetries) {
                this.retryCount++;
                setTimeout(() => {
                    this.sendMessage(message, action, actionData);
                }, this.config.retryDelay * this.retryCount);
            } else {
                this.showError('Connection error. Please try again.');
                this.retryCount = 0;
            }
        }
    }
    
    sendWelcomeMessage() {
        // Send a greeting to get the welcome response
        this.sendMessage('hello');
    }
    
    handleBotResponse(response) {
        // Add text message
        if (response.text) {
            this.addMessage(response.text, 'bot');
        }
        
        // Handle quick replies
        if (response.quick_replies && response.quick_replies.length > 0) {
            this.showQuickReplies(response.quick_replies);
        }
        
        // Handle car cards
        if (response.car_cards && response.car_cards.length > 0) {
            this.showCarCards(response.car_cards);
        }
        
        // Handle booking progress
        if (response.booking_step) {
            this.updateBookingProgress(response);
        }
        
        // Handle contact form
        if (response.type === 'contact_form') {
            this.showContactForm();
        }
        
        // Handle booking preview
        if (response.type === 'booking_preview' && response.booking_preview) {
            this.showBookingPreview(response.booking_preview);
        }
        
        // Handle special actions
        if (response.actions) {
            response.actions.forEach(action => this.handleAction(action));
        }
    }
    
    addMessage(content, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        if (sender === 'bot') {
            avatarDiv.innerHTML = '<i class=\"fas fa-robot\"></i>';
        } else {
            avatarDiv.innerHTML = '<i class=\"fas fa-user\"></i>';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Process content for markdown-like formatting
        const processedContent = this.processMessageContent(content);
        contentDiv.innerHTML = processedContent;
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    processMessageContent(content) {
        // Simple processing for basic formatting
        return content
            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')  // Bold
            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')  // Italic
            .replace(/\\n/g, '<br>')  // Line breaks
            .replace(/•/g, '&bull;');  // Bullet points
    }
    
    showTyping() {
        this.isTyping = true;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
            this.scrollToBottom();
        }
        
        // Disable send button
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.disabled = true;
        }
    }
    
    hideTyping() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
        
        // Re-enable send button if there's content
        this.handleInputChange();
    }
    
    showQuickReplies(quickReplies) {
        const container = document.getElementById('quick-replies');
        if (!container) return;
        
        container.innerHTML = '';
        container.style.display = 'block';
        
        quickReplies.forEach(reply => {
            const button = document.createElement('button');
            button.className = 'quick-reply-btn';
            button.textContent = reply.text;
            button.onclick = () => this.handleQuickReply(reply);
            container.appendChild(button);
        });
        
        this.scrollToBottom();
    }
    
    handleQuickReply(reply) {
        // Hide quick replies
        const container = document.getElementById('quick-replies');
        if (container) {
            container.style.display = 'none';
        }
        
        // Add user message
        this.addMessage(reply.text, 'user');
        
        // Send action to API
        this.sendMessage(reply.text, reply.action, reply);
    }
    
    showCarCards(carCards) {
        const container = document.getElementById('car-cards-container');
        if (!container) return;
        
        container.innerHTML = '';
        container.style.display = 'block';
        
        carCards.forEach(car => {
            const cardDiv = this.createCarCard(car);
            container.appendChild(cardDiv);
        });
        
        this.scrollToBottom();
    }
    
    createCarCard(car) {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'car-card';
        
        cardDiv.innerHTML = `
            <div class=\"car-card-image\">
                ${car.image ? `<img src=\"${car.image}\" alt=\"${car.name}\" style=\"width: 100%; height: 100%; object-fit: cover; border-radius: 8px;\">` : '<i class=\"fas fa-car\"></i>'}
            </div>
            <div class=\"car-card-title\">${car.name}</div>
            <div class=\"car-card-details\">
                ${car.seats} seats • ${car.transmission} • ${car.fuel_type}
            </div>
            <div class=\"car-card-price\">
                $${car.price_per_day}/day
                ${car.total_cost ? `<br><small>Total: $${car.total_cost}</small>` : ''}
            </div>
            <div class=\"car-card-actions\"></div>
        `;
        
        const actionsContainer = cardDiv.querySelector('.car-card-actions');
        
        if (car.actions) {
            car.actions.forEach(action => {
                const button = document.createElement('button');
                button.className = 'car-card-btn';
                if (action.text === 'Select This Car' || action.text === 'Select') {
                    button.classList.add('primary');
                }
                button.textContent = action.text;
                button.onclick = () => this.handleCarAction(action, car);
                actionsContainer.appendChild(button);
            });
        }
        
        return cardDiv;
    }
    
    handleCarAction(action, car) {
        if (action.action === 'view_details' || action.action === 'view_car_details') {
            this.showCarDetails(car);
        } else if (action.action === 'select_car_for_booking') {
            this.addMessage(`Selected ${car.name}`, 'user');
            this.sendMessage(`I want to select ${car.name}`, action.action, { car_id: car.id });
        } else {
            this.addMessage(action.text, 'user');
            this.sendMessage(action.text, action.action, action);
        }
    }
    
    showCarDetails(car) {
        const modal = new bootstrap.Modal(document.getElementById('carDetailsModal'));
        const content = document.getElementById('car-details-content');
        
        if (content) {
            content.innerHTML = `
                <div class=\"row\">
                    <div class=\"col-md-6\">
                        <div class=\"car-detail-image\">
                            ${car.image ? `<img src=\"${car.image}\" alt=\"${car.name}\" class=\"img-fluid rounded\">` : '<div class=\"bg-light p-5 text-center rounded\"><i class=\"fas fa-car fa-4x text-muted\"></i></div>'}
                        </div>
                    </div>
                    <div class=\"col-md-6\">
                        <h4>${car.name}</h4>
                        <p class=\"text-muted\">${car.company_name}</p>
                        <ul class=\"list-unstyled\">
                            <li><strong>Category:</strong> ${car.category}</li>
                            <li><strong>Seats:</strong> ${car.seats}</li>
                            <li><strong>Transmission:</strong> ${car.transmission}</li>
                            <li><strong>Fuel Type:</strong> ${car.fuel_type}</li>
                            <li><strong>Price:</strong> $${car.price_per_day}/day</li>
                        </ul>
                        ${car.features && car.features.length > 0 ? `
                            <h6>Features:</h6>
                            <div class=\"d-flex flex-wrap gap-2\">
                                ${car.features.map(feature => `<span class=\"badge bg-secondary\">${feature}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
            
            const selectCarBtn = document.getElementById('select-car-btn');
            if (selectCarBtn) {
                selectCarBtn.onclick = () => {
                    modal.hide();
                    this.addMessage(`Selected ${car.name}`, 'user');
                    this.sendMessage(`I want to select ${car.name}`, 'select_car_for_booking', { car_id: car.id });
                };
            }
        }
        
        modal.show();
    }
    
    updateBookingProgress(response) {
        const progressContainer = document.getElementById('booking-progress');
        const currentStep = document.getElementById('current-step');
        const totalSteps = document.getElementById('total-steps');
        const progressBar = document.getElementById('progress-bar');
        
        if (!progressContainer) return;
        
        const stepMap = {
            'dates': 1,
            'location': 2,
            'car_selection': 3,
            'contact_details': 4,
            'confirmation': 5
        };
        
        const currentStepNum = stepMap[response.booking_step] || 1;
        const totalStepsNum = 5;
        const progressPercent = (currentStepNum / totalStepsNum) * 100;
        
        if (currentStep) currentStep.textContent = currentStepNum;
        if (totalSteps) totalSteps.textContent = totalStepsNum;
        if (progressBar) progressBar.style.width = `${progressPercent}%`;
        
        progressContainer.style.display = 'block';
        this.scrollToBottom();
    }
    
    showContactForm() {
        const modal = new bootstrap.Modal(document.getElementById('contactFormModal'));
        modal.show();
    }
    
    saveContactInfo() {
        const nameInput = document.getElementById('customer-name');
        const emailInput = document.getElementById('customer-email');
        const phoneInput = document.getElementById('customer-phone');
        
        if (!nameInput || !emailInput || !phoneInput) return;
        
        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const phone = phoneInput.value.trim();
        
        if (!name || !email || !phone) {
            alert('Please fill in all required fields.');
            return;
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('contactFormModal'));
        modal.hide();
        
        // Send contact info as message
        const contactMessage = `My name is ${name}, email: ${email}, phone: ${phone}`;
        this.addMessage(contactMessage, 'user');
        this.sendMessage(contactMessage);
    }
    
    showBookingPreview(bookingData) {
        this.currentBookingData = bookingData;
        
        // Create preview content
        const previewContent = `
            <div class=\"booking-preview-content\">
                <div class=\"card\">
                    <div class=\"card-header\">
                        <h6>Booking Summary</h6>
                    </div>
                    <div class=\"card-body\">
                        <div class=\"price-breakdown\">
                            <div class=\"price-item\">
                                <span>Daily Rate (${bookingData.rental_period.rental_days} days)</span>
                                <span>$${bookingData.pricing.subtotal.toFixed(2)}</span>
                            </div>
                            <div class=\"price-item\">
                                <span>Tax & Fees</span>
                                <span>$${bookingData.pricing.tax_amount.toFixed(2)}</span>
                            </div>
                            <div class=\"price-item price-total\">
                                <span><strong>Total</strong></span>
                                <span><strong>$${bookingData.pricing.total.toFixed(2)}</strong></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.addMessage(previewContent, 'bot');
    }
    
    handleAction(action) {
        switch (action) {
            case 'show_welcome':
                // Could add special welcome animations here
                break;
            case 'end_conversation':
                setTimeout(() => this.minimizeChat(), 3000);
                break;
        }
    }
    
    handleError(message) {
        this.showError(message);
    }
    
    showError(message) {
        this.addMessage(`Sorry, there was an error: ${message}`, 'bot');
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
        }
    }
    
    getCSRFToken() {
        // Get CSRF token from cookie or meta tag
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        if (cookieValue) return cookieValue;
        
        // Try to get from meta tag
        const csrfMeta = document.querySelector('meta[name=csrf-token]');
        return csrfMeta ? csrfMeta.getAttribute('content') : '';
    }
    
    // Public methods
    sendCustomMessage(message) {
        this.addMessage(message, 'user');
        this.sendMessage(message);
    }
    
    triggerAction(action, actionData = {}) {
        this.sendMessage('', action, actionData);
    }
    
    getCurrentBookingData() {
        return this.currentBookingData;
    }
    
    getSessionModel() {
        return this.sessionModel;
    }
}