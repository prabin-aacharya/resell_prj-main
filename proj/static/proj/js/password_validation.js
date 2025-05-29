function validateOldPassword(input) {
    const feedback = getOrCreateFeedback(input);
    const oldPassword = input.value;
    
    if (oldPassword.length === 0) {
        showFeedback(feedback, 'Please enter your old password', 'text-danger');
        return;
    }

    // Get CSRF token from cookie
    const csrftoken = getCookie('csrftoken');
    
    // Make AJAX request to validate old password
    fetch(input.dataset.validateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            old_password: oldPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            showFeedback(feedback, 'Old password is correct', 'text-success');
        } else {
            showFeedback(feedback, 'Your old password was entered incorrectly. Please enter it again.', 'text-danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideFeedback(feedback);
    });
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
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

function validateNewPassword(input) {
    const feedback = getOrCreateFeedback(input);
    const password = input.value;
    
    // Check password requirements
    const hasLetter = /[A-Za-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[@$!%*#?&]/.test(password);
    const isLongEnough = password.length >= 8;
    
    let message = '';
    if (!isLongEnough) {
        message = 'Password must be at least 8 characters long';
    } else if (!hasLetter) {
        message = 'Password must include at least one letter';
    } else if (!hasNumber) {
        message = 'Password must include at least one number';
    } else if (!hasSpecial) {
        message = 'Password must include at least one special character (@$!%*#?&)';
    }
    
    if (message) {
        showFeedback(feedback, message, 'text-danger');
    } else {
        showFeedback(feedback, 'Password meets all requirements', 'text-success');
    }
    
    // Also validate confirm password if it has a value
    const confirmInput = document.getElementById('id_new_password2');
    if (confirmInput && confirmInput.value) {
        validateConfirmPassword(confirmInput);
    }
}

function validateConfirmPassword(input) {
    const feedback = getOrCreateFeedback(input);
    const newPassword = document.getElementById('id_new_password1').value;
    
    if (input.value.length === 0) {
        showFeedback(feedback, 'Please confirm your password', 'text-danger');
    } else if (input.value !== newPassword) {
        showFeedback(feedback, 'Passwords do not match', 'text-danger');
    } else {
        showFeedback(feedback, 'Passwords match', 'text-success');
    }
}

function getOrCreateFeedback(input) {
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('password-feedback')) {
        feedback = document.createElement('div');
        feedback.className = 'password-feedback mt-1';
        input.parentNode.insertBefore(feedback, input.nextSibling);
    }
    return feedback;
}

function showFeedback(element, message, className) {
    element.textContent = message;
    element.className = 'password-feedback mt-1 ' + className;
}

function hideFeedback(element) {
    element.textContent = '';
    element.className = 'password-feedback mt-1';
} 