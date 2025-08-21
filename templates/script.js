// Minimal Login Form JavaScript
class MinimalLoginForm {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.emailInput = document.getElementById('email');
        this.passwordInput = document.getElementById('password');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.submitButton = this.form.querySelector('.login-btn');
        this.successMessage = document.getElementById('successMessage');

        this.init();
    }

    init() {
        this.bindEvents();
        this.setupPasswordToggle();
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.emailInput.addEventListener('blur', () => this.validateEmail());
        this.passwordInput.addEventListener('blur', () => this.validatePassword());
        this.emailInput.addEventListener('input', () => this.clearError('email'));
        this.passwordInput.addEventListener('input', () => this.clearError('password'));
    }

    setupPasswordToggle() {
        this.passwordToggle.addEventListener('click', () => {
            const type = this.passwordInput.type === 'password' ? 'text' : 'password';
            this.passwordInput.type = type;

            const icon = this.passwordToggle.querySelector('.toggle-icon');
            icon.classList.toggle('show-password', type === 'text');
        });
    }

    validateEmail() {
        const email = this.emailInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!email) {
            this.showError('email', 'Email is required');
            return false;
        }

        if (!emailRegex.test(email)) {
            this.showError('email', 'Please enter a valid email address');
            return false;
        }

        this.clearError('email');
        return true;
    }

    validatePassword() {
        const password = this.passwordInput.value;

        if (!password) {
            this.showError('password', 'Password is required');
            return false;
        }

        if (password.length < 6) {
            this.showError('password', 'Password must be at least 6 characters');
            return false;
        }

        this.clearError('password');
        return true;
    }

    showError(field, message) {
        const formGroup = document.getElementById(field).closest('.form-group');
        const errorElement = document.getElementById(`${field}Error`);

        formGroup.classList.add('error');
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }

    clearError(field) {
        const formGroup = document.getElementById(field).closest('.form-group');
        const errorElement = document.getElementById(`${field}Error`);

        formGroup.classList.remove('error');
        errorElement.classList.remove('show');
        setTimeout(() => {
            errorElement.textContent = '';
        }, 200);
    }

    async handleSubmit(e) {
        e.preventDefault();

        const isEmailValid = this.validateEmail();
        const isPasswordValid = this.validatePassword();

        if (!isEmailValid || !isPasswordValid) {
            return;
        }

        this.setLoading(true);

        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Show success state
            this.showSuccess();
        } catch (error) {
            this.showError('password', 'Login failed. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(loading) {
        this.submitButton.classList.toggle('loading', loading);
        this.submitButton.disabled = loading;
    }

    showSuccess() {
        this.form.style.display = 'none';
        this.successMessage.classList.add('show');

        // Simulate redirect after 2 seconds
        setTimeout(() => {
            console.log('Redirecting to dashboard...');
            // window.location.href = '/dashboard';
        }, 2000);
    }
}

// Initialize the form when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MinimalLoginForm();
});