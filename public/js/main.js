document.addEventListener('DOMContentLoaded', () => {
    // Contact Form Handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Sending...';

            const formData = new FormData(contactForm);
            
            // Clear previous messages
            const flashContainer = document.getElementById('contact-flash-messages');
            if(flashContainer) flashContainer.innerHTML = '';

            try {
                const response = await fetch('/api/v1/contact', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showMessage('success', result.message || 'Message sent successfully!');
                    contactForm.reset();
                    // Reset ALTCHA if possible (might need to reload widget)
                    // document.querySelector('altcha-widget').reload(); // Hypothetical method
                } else {
                    showMessage('error', result.detail || 'Failed to send message.');
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('error', 'An unexpected error occurred. Please try again.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
        });
    }

    function showMessage(type, text) {
        const flashContainer = document.getElementById('contact-flash-messages');
        if (!flashContainer) return;

        const alertDiv = document.createElement('div');
        // Replicating the inline styles from the template for consistency
        alertDiv.className = `alert alert-${type}`;
        alertDiv.style.padding = '1rem';
        alertDiv.style.marginBottom = '2rem';
        alertDiv.style.borderRadius = '8px';
        alertDiv.style.background = type === 'success' ? '#dcfce7' : '#fee2e2';
        alertDiv.style.color = type === 'success' ? '#166534' : '#991b1b';
        alertDiv.textContent = text;
        
        flashContainer.innerHTML = '';
        flashContainer.appendChild(alertDiv);
        
        // Auto scroll to message
        flashContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
