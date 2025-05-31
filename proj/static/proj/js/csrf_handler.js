// Function to get CSRF token from cookie
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to update CSRF token in all forms
function updateCSRFTokens() {
    const token = getCSRFToken();
    if (!token) return;

    // Update all forms
    document.querySelectorAll('form').forEach(form => {
        const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            csrfInput.value = token;
        }
    });
}

// Function to handle form submissions
function handleFormSubmit(event) {
    const form = event.target;
    const token = getCSRFToken();
    
    if (!token) {
        event.preventDefault();
        return;
    }
    
    // Update the CSRF token before submission
    const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        csrfInput.value = token;
    }
}

// Add event listeners when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Update CSRF tokens initially
    updateCSRFTokens();
    
    // Add submit handlers to all forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // Clear the needs_refresh flag without showing a message
    sessionStorage.removeItem('needs_refresh');
}); 