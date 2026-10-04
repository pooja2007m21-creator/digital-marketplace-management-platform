/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Centralized API & Client Utilities
 */

const API_CONFIG = {
  // Use port 8000 when running locally (FastAPI backend)
  BASE_URL: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? `${window.location.protocol}//${window.location.hostname}:8000/api`
    : `${window.location.origin}/api`,
  BACKEND_HOST: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : window.location.origin,
  STORAGE_TOKEN_KEY: 'dmmp_auth_token',
  STORAGE_USER_KEY: 'dmmp_auth_user'
};

// ==========================================
// DYNAMIC URL RESOLUTION HELPER
// ==========================================

function resolvePageUrl(relativePath) {
  if (!relativePath) return '#';
  if (relativePath.startsWith('http') || relativePath.startsWith('javascript:')) return relativePath;

  const cleanPath = relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
  const currentPath = window.location.pathname;

  if (currentPath.includes('/frontend/')) {
    const base = currentPath.substring(0, currentPath.indexOf('/frontend/') + 10);
    return base + cleanPath;
  } else if (currentPath.includes('/app/')) {
    const base = currentPath.substring(0, currentPath.indexOf('/app/') + 5);
    return base + cleanPath;
  } else {
    // Normal root or subfolder
    if (currentPath.includes('/seller/') || currentPath.includes('/admin/')) {
      if (cleanPath.startsWith('seller/') || cleanPath.startsWith('admin/')) {
        return '../' + cleanPath;
      }
      return '../' + cleanPath;
    }
    return '/' + cleanPath;
  }
}

function formatProductImage(url) {
  if (!url) return resolvePageUrl('assets/images/placeholder.svg');
  if (url.startsWith('http')) return url;
  if (url.startsWith('/uploads')) {
    return `${API_CONFIG.BACKEND_HOST}${url}`;
  }
  if (url.startsWith('/assets') || url.startsWith('assets')) {
    return resolvePageUrl(url);
  }
  return url;
}

// ==========================================
// AUTH STATE MANAGEMENT
// ==========================================

function getToken() {
  return localStorage.getItem(API_CONFIG.STORAGE_TOKEN_KEY);
}

function getUser() {
  const u = localStorage.getItem(API_CONFIG.STORAGE_USER_KEY);
  try {
    return u ? JSON.parse(u) : null;
  } catch (e) {
    return null;
  }
}

function setAuthSession(token, user) {
  localStorage.setItem(API_CONFIG.STORAGE_TOKEN_KEY, token);
  localStorage.setItem(API_CONFIG.STORAGE_USER_KEY, JSON.stringify(user));
}

function clearAuthSession() {
  localStorage.removeItem(API_CONFIG.STORAGE_TOKEN_KEY);
  localStorage.removeItem(API_CONFIG.STORAGE_USER_KEY);
}

function isAuthenticated() {
  return !!getToken();
}

function requireAuth(allowedRoles = null) {
  const user = getUser();
  const token = getToken();

  if (!token || !user) {
    window.location.href = resolvePageUrl('login.html?redirect=' + encodeURIComponent(window.location.pathname + window.location.search));
    return false;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    showToast('Unauthorized access to this section', 'error');
    setTimeout(() => {
      if (user.role === 'ADMIN') window.location.href = resolvePageUrl('admin/dashboard.html');
      else if (user.role === 'SELLER') window.location.href = resolvePageUrl('seller/dashboard.html');
      else window.location.href = resolvePageUrl('index.html');
    }, 1000);
    return false;
  }

  return true;
}

// ==========================================
// CENTRALIZED FETCH WRAPPER
// ==========================================

async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.BASE_URL}${endpoint}`;
  const token = getToken();

  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {})
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers
    });

    // Handle 401 Unauthorized
    if (response.status === 401 && !endpoint.includes('/auth/login')) {
      clearAuthSession();
      showToast('Session expired. Please log in again.', 'warning');
      setTimeout(() => {
        window.location.href = resolvePageUrl('login.html');
      }, 1200);
      throw new Error('Authentication expired');
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

// ==========================================
// UI & FORMATTING HELPERS
// ==========================================

function formatCurrency(amount) {
  const num = Number(amount) || 0;
  return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function renderStars(rating = 0) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  
  let html = '';
  for (let i = 0; i < full; i++) html += '<i class="fas fa-star"></i>';
  if (half) html += '<i class="fas fa-star-half-alt"></i>';
  for (let i = 0; i < empty; i++) html += '<i class="far fa-star"></i>';
  return `<span class="rating-stars">${html} <span class="ms-1 text-muted small">(${Number(rating).toFixed(1)})</span></span>`;
}

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: 'fa-check-circle text-success',
    error: 'fa-exclamation-circle text-danger',
    warning: 'fa-exclamation-triangle text-warning',
    info: 'fa-info-circle text-info'
  };

  const toast = document.createElement('div');
  toast.className = `custom-toast ${type}`;
  toast.innerHTML = `
    <i class="fas ${icons[type] || icons.info} fs-5"></i>
    <div class="flex-grow-1 text-dark small fw-semibold">${message}</div>
    <button type="button" class="btn-close btn-close-sm" onclick="this.parentElement.remove()"></button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, 4000);
}

// ==========================================
// NAVBAR & CART BADGE SYNCHRONIZATION
// ==========================================

async function updateNavbar() {
  const user = getUser();
  const token = getToken();

  // Auth area
  const authContainer = document.getElementById('nav-auth-container');
  if (authContainer) {
    if (user && token) {
      let roleBadge = '';
      let dashboardLink = resolvePageUrl('profile.html');
      
      if (user.role === 'ADMIN') {
        roleBadge = '<span class="badge bg-danger ms-1">Admin</span>';
        dashboardLink = resolvePageUrl('admin/dashboard.html');
      } else if (user.role === 'SELLER') {
        roleBadge = '<span class="badge bg-primary ms-1">Seller</span>';
        dashboardLink = resolvePageUrl('seller/dashboard.html');
      }

      authContainer.innerHTML = `
        <div class="dropdown">
          <button class="btn btn-outline-light text-dark dropdown-toggle d-flex align-items-center gap-2 border bg-white shadow-sm" type="button" data-bs-toggle="dropdown">
            <i class="fas fa-user-circle fs-5 text-primary"></i>
            <span class="fw-semibold small">${user.full_name.split(' ')[0]} ${roleBadge}</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-end shadow border-0 mt-2">
            <li><h6 class="dropdown-header">${user.email}</h6></li>
            <li><a class="dropdown-item" href="${dashboardLink}"><i class="fas fa-chart-line me-2 text-primary"></i>Dashboard</a></li>
            <li><a class="dropdown-item" href="${resolvePageUrl('profile.html')}"><i class="fas fa-user-cog me-2 text-secondary"></i>My Profile</a></li>
            <li><a class="dropdown-item" href="${resolvePageUrl('orders.html')}"><i class="fas fa-box-open me-2 text-success"></i>My Orders</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item text-danger" href="javascript:void(0)" onclick="logout()"><i class="fas fa-sign-out-alt me-2"></i>Sign Out</a></li>
          </ul>
        </div>
      `;
    } else {
      authContainer.innerHTML = `
        <a href="${resolvePageUrl('login.html')}" class="btn btn-outline-primary btn-sm me-2">Login</a>
        <a href="${resolvePageUrl('register.html')}" class="btn btn-primary btn-sm">Register</a>
      `;
    }
  }

  // Synchronize Cart and Wishlist counters if logged in
  if (user && token) {
    try {
      const cart = await apiFetch('/cart');
      const cartBadges = document.querySelectorAll('.cart-count-badge');
      cartBadges.forEach(b => {
        b.textContent = cart.item_count || 0;
        b.style.display = cart.item_count > 0 ? 'inline-block' : 'none';
      });

      const wishlist = await apiFetch('/wishlist');
      const wishBadges = document.querySelectorAll('.wishlist-count-badge');
      wishBadges.forEach(b => {
        b.textContent = wishlist.item_count || 0;
        b.style.display = wishlist.item_count > 0 ? 'inline-block' : 'none';
      });
    } catch (e) {
      // Ignore count fetch errors on initial load
    }
  }
}

function logout() {
  clearAuthSession();
  showToast('Logged out successfully', 'info');
  setTimeout(() => {
    window.location.href = resolvePageUrl('index.html');
  }, 500);
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
  // Update static nav links with dynamic resolution if needed
  document.querySelectorAll('a[data-resolve-url]').forEach(a => {
    const raw = a.getAttribute('data-resolve-url');
    a.href = resolvePageUrl(raw);
  });
  updateNavbar();
});
