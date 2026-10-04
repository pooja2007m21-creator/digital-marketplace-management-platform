/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Authentication Scripts (Login, Registration, Password Reset, Demo Fast-Fill)
 */

document.addEventListener('DOMContentLoaded', () => {
  initLoginForm();
  initRegisterForm();
  initForgotPasswordModal();
});

function initLoginForm() {
  const loginForm = document.getElementById('login-form');
  if (!loginForm) return;

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;

    const usernameOrEmail = document.getElementById('login-identifier').value.trim();
    const password = document.getElementById('login-password').value;
    const rememberMe = document.getElementById('remember-me')?.checked || false;

    if (!usernameOrEmail || !password) {
      showToast('Please enter both username/email and password', 'warning');
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Authenticating...';

      const response = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username_or_email: usernameOrEmail,
          password: password,
          remember_me: rememberMe
        })
      });

      setAuthSession(response.access_token, response.user);
      showToast(`Welcome back, ${response.user.full_name}!`, 'success');

      // Check redirect URL parameter
      const urlParams = new URLSearchParams(window.location.search);
      const redirectUrl = urlParams.get('redirect');

      setTimeout(() => {
        if (redirectUrl) {
          window.location.href = redirectUrl;
        } else if (response.user.role === 'ADMIN') {
          window.location.href = resolvePageUrl('admin/dashboard.html');
        } else if (response.user.role === 'SELLER') {
          window.location.href = resolvePageUrl('seller/dashboard.html');
        } else {
          window.location.href = resolvePageUrl('index.html');
        }
      }, 800);

    } catch (err) {
      showToast(err.message || 'Login failed. Please verify your credentials.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnText;
    }
  });
}

function initRegisterForm() {
  const registerForm = document.getElementById('register-form');
  if (!registerForm) return;

  // Toggle seller specific fields when switching tabs
  const roleRadios = document.querySelectorAll('input[name="user_type"]');
  const sellerFieldsBox = document.getElementById('seller-extra-fields');

  roleRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      if (sellerFieldsBox) {
        if (radio.value === 'SELLER') {
          sellerFieldsBox.classList.remove('d-none');
        } else {
          sellerFieldsBox.classList.add('d-none');
        }
      }
    });
  });

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = registerForm.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;

    const fullName = document.getElementById('reg-name').value.trim();
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const phone = document.getElementById('reg-phone')?.value.trim();
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm-password').value;
    const userType = document.querySelector('input[name="user_type"]:checked')?.value || 'CUSTOMER';

    if (password !== confirmPassword) {
      showToast('Passwords do not match. Please verify.', 'error');
      return;
    }

    if (password.length < 6) {
      showToast('Password must be at least 6 characters long.', 'warning');
      return;
    }

    const payload = {
      full_name: fullName,
      username: username,
      email: email,
      phone: phone,
      password: password,
      user_type: userType
    };

    if (userType === 'SELLER') {
      payload.business_name = document.getElementById('reg-business-name')?.value.trim() || `${fullName}'s Store`;
      payload.business_description = document.getElementById('reg-business-desc')?.value.trim();
      payload.business_address = document.getElementById('reg-business-addr')?.value.trim();
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating Account...';

      await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      showToast('Registration successful! Redirecting to login...', 'success');
      setTimeout(() => {
        window.location.href = resolvePageUrl(`login.html?registered=true&email=${encodeURIComponent(email)}`);
      }, 1200);

    } catch (err) {
      showToast(err.message || 'Registration failed.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnText;
    }
  });
}

function fillDemoCredentials(email, password) {
  const idInput = document.getElementById('login-identifier');
  const pwdInput = document.getElementById('login-password');
  if (idInput && pwdInput) {
    idInput.value = email;
    pwdInput.value = password;
    showToast(`Filled credentials for ${email}`, 'info');
  }
}

function initForgotPasswordModal() {
  const forgotForm = document.getElementById('forgot-password-form');
  if (!forgotForm) return;

  forgotForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value.trim();
    try {
      const res = await apiFetch('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email })
      });
      showToast(res.message + ` (Demo Code: ${res.demo_code})`, 'info');
      document.getElementById('reset-box')?.classList.remove('d-none');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  const resetForm = document.getElementById('reset-password-form');
  if (resetForm) {
    resetForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('forgot-email').value.trim();
      const code = document.getElementById('reset-code').value.trim();
      const newPwd = document.getElementById('reset-new-password').value;

      try {
        const res = await apiFetch('/auth/reset-password', {
          method: 'POST',
          body: JSON.stringify({ email, reset_code: code, new_password: newPwd })
        });
        showToast(res.message, 'success');
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
}
