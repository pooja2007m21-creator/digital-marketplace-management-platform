/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Customer Profile, Address & Security Management
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadUserProfile();
  initProfileForms();
});

async function loadUserProfile() {
  try {
    const user = await apiFetch('/users/me');
    setAuthSession(getToken(), user); // sync fresh data

    document.getElementById('prof-display-name').textContent = user.full_name;
    document.getElementById('prof-display-email').textContent = user.email;
    document.getElementById('prof-display-role').textContent = user.role;

    // Prefill edit inputs
    document.getElementById('edit-fullname').value = user.full_name || '';
    document.getElementById('edit-phone').value = user.phone || '';
    document.getElementById('edit-address').value = user.address || '';
    document.getElementById('edit-city').value = user.city || '';
    document.getElementById('edit-state').value = user.state || '';
    document.getElementById('edit-zip').value = user.postal_code || '';

    // Load customer dashboard stats if on profile
    loadCustomerDashboardStats();

  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadCustomerDashboardStats() {
  try {
    const stats = await apiFetch('/users/dashboard');
    document.getElementById('stat-total-orders').textContent = stats.total_orders || 0;
    document.getElementById('stat-pending-orders').textContent = stats.pending_orders || 0;
    document.getElementById('stat-wishlist-count').textContent = stats.wishlist_count || 0;
    document.getElementById('stat-cart-count').textContent = stats.cart_count || 0;
  } catch (e) {
    // optional widget
  }
}

function initProfileForms() {
  // Update Profile Form
  const profileForm = document.getElementById('profile-edit-form');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        full_name: document.getElementById('edit-fullname').value.trim(),
        phone: document.getElementById('edit-phone').value.trim(),
        address: document.getElementById('edit-address').value.trim(),
        city: document.getElementById('edit-city').value.trim(),
        state: document.getElementById('edit-state').value.trim(),
        postal_code: document.getElementById('edit-zip').value.trim()
      };

      try {
        const updated = await apiFetch('/users/me', {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
        setAuthSession(getToken(), updated);
        showToast('Profile updated successfully!', 'success');
        loadUserProfile();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Change Password Form
  const pwdForm = document.getElementById('password-change-form');
  if (pwdForm) {
    pwdForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const curPwd = document.getElementById('pwd-current').value;
      const newPwd = document.getElementById('pwd-new').value;
      const confirmPwd = document.getElementById('pwd-confirm').value;

      if (newPwd !== confirmPwd) {
        showToast('New passwords do not match.', 'warning');
        return;
      }

      if (newPwd.length < 6) {
        showToast('Password must be at least 6 characters.', 'warning');
        return;
      }

      try {
        await apiFetch('/auth/change-password', {
          method: 'POST',
          body: JSON.stringify({ current_password: curPwd, new_password: newPwd })
        });
        showToast('Password changed successfully!', 'success');
        pwdForm.reset();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
}

async function handleDeleteAccount() {
  if (!confirm('Are you ABSOLUTELY sure you want to delete your account? This action cannot be undone.')) return;
  try {
    await apiFetch('/users/me', { method: 'DELETE' });
    clearAuthSession();
    showToast('Account deleted. Goodbye!', 'info');
    setTimeout(() => { window.location.href = resolvePageUrl('index.html'); }, 1000);
  } catch (err) {
    showToast(err.message, 'error');
  }
}
