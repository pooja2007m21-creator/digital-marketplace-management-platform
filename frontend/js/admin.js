/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Administrator Portal Scripts (Analytics, Users, Sellers, Products, Categories, Orders, Reviews, Reports)
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth(['ADMIN'])) return;

  if (window.location.pathname.includes('admin/dashboard.html')) {
    loadAdminDashboard();
  } else if (window.location.pathname.includes('admin/users.html')) {
    loadAdminUsersTable();
  } else if (window.location.pathname.includes('admin/sellers.html')) {
    loadAdminSellersTable();
  } else if (window.location.pathname.includes('admin/products.html')) {
    loadAdminProductsTable();
  } else if (window.location.pathname.includes('admin/categories.html')) {
    loadAdminCategoriesTable();
    initCategoryModalForm();
  } else if (window.location.pathname.includes('admin/orders.html')) {
    loadAdminOrdersTable();
  } else if (window.location.pathname.includes('admin/reviews.html')) {
    loadAdminReviewsTable();
  } else if (window.location.pathname.includes('admin/reports.html')) {
    loadAdminReports();
  }
});

// ==========================================
// 1. ADMIN DASHBOARD
// ==========================================
async function loadAdminDashboard() {
  try {
    const data = await apiFetch('/admin/dashboard');

    document.getElementById('adm-total-customers').textContent = data.total_customers || 0;
    document.getElementById('adm-total-sellers').textContent = data.total_sellers || 0;
    document.getElementById('adm-total-products').textContent = data.total_products || 0;
    document.getElementById('adm-total-orders').textContent = data.total_orders || 0;
    document.getElementById('adm-total-revenue').textContent = formatCurrency(data.total_revenue || 0);
    document.getElementById('adm-pending-sellers').textContent = data.pending_seller_approvals || 0;

    // Recent Orders
    const ordersTbody = document.getElementById('adm-recent-orders-tbody');
    if (ordersTbody) {
      let html = '';
      (data.recent_orders || []).forEach(o => {
        html += `
          <tr>
            <td><strong>${o.order_number}</strong></td>
            <td>${o.customer_name}</td>
            <td>${formatCurrency(o.total_amount)}</td>
            <td><span class="status-badge badge-${o.order_status.toLowerCase().replace(/_/g, '-')}">${o.order_status}</span></td>
            <td>${formatDate(o.created_at)}</td>
          </tr>
        `;
      });
      ordersTbody.innerHTML = html || '<tr><td colspan="5" class="text-center py-3">No orders yet</td></tr>';
    }

    // Initialize Charts
    initAdminSalesChart(data.sales_overview);
    initAdminOrderPieChart(data.order_status_counts);

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function initAdminSalesChart(salesData) {
  const ctx = document.getElementById('adminSalesChart');
  if (!ctx || typeof Chart === 'undefined') return;

  const labels = (salesData || []).map(d => d.period);
  const revenue = (salesData || []).map(d => d.sales);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [{
        label: 'Platform Revenue (₹)',
        data: revenue.length ? revenue : [12000, 18500, 24000, 31000],
        backgroundColor: '#4f46e5',
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } }
    }
  });
}

function initAdminOrderPieChart(statusCounts) {
  const ctx = document.getElementById('adminOrderPieChart');
  if (!ctx || typeof Chart === 'undefined') return;

  const labels = Object.keys(statusCounts || {});
  const data = Object.values(statusCounts || {});

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels.length ? labels : ['PLACED', 'CONFIRMED', 'DELIVERED'],
      datasets: [{
        data: data.length ? data : [5, 3, 12],
        backgroundColor: ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

// ==========================================
// 2. USER MANAGEMENT
// ==========================================
async function loadAdminUsersTable() {
  const tbody = document.getElementById('adm-users-tbody');
  if (!tbody) return;

  const roleFilter = document.getElementById('filter-user-role')?.value;
  const search = document.getElementById('search-user-input')?.value;

  const params = new URLSearchParams();
  if (roleFilter) params.set('role', roleFilter);
  if (search) params.set('search', search);

  try {
    const users = await apiFetch(`/admin/users?${params.toString()}`);
    let html = '';
    users.forEach(u => {
      const isCurrentAdmin = u.email === getUser().email;
      html += `
        <tr>
          <td>#${u.id}</td>
          <td><strong>${u.full_name}</strong><br><small class="text-muted">@${u.username}</small></td>
          <td>${u.email}</td>
          <td>${u.phone || 'N/A'}</td>
          <td><span class="admin-badge-role role-${u.role.toLowerCase()}">${u.role}</span></td>
          <td>
            <span class="status-badge ${u.status === 'ACTIVE' ? 'badge-approved' : 'badge-rejected'}">${u.status}</span>
          </td>
          <td>${formatDate(u.created_at)}</td>
          <td>
            ${!isCurrentAdmin ? `
              <button class="btn btn-sm ${u.status === 'ACTIVE' ? 'btn-outline-warning' : 'btn-outline-success'} me-1" onclick="toggleUserStatus(${u.id}, '${u.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'}')">
                ${u.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
              </button>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteUserAdmin(${u.id})">
                <i class="fas fa-trash"></i>
              </button>
            ` : '<span class="badge bg-secondary">Current Admin</span>'}
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html || '<tr><td colspan="8" class="text-center py-4">No users found</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-danger p-3">${err.message}</td></tr>`;
  }
}

async function toggleUserStatus(userId, newStatus) {
  try {
    await apiFetch(`/admin/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus })
    });
    showToast(`User status updated to ${newStatus}`, 'success');
    loadAdminUsersTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteUserAdmin(userId) {
  if (!confirm('Are you sure you want to permanently delete this user?')) return;
  try {
    await apiFetch(`/admin/users/${userId}`, { method: 'DELETE' });
    showToast('User deleted successfully', 'info');
    loadAdminUsersTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 3. SELLER APPROVALS & MANAGEMENT
// ==========================================
async function loadAdminSellersTable() {
  const tbody = document.getElementById('adm-sellers-tbody');
  if (!tbody) return;

  try {
    const sellers = await apiFetch('/admin/sellers');
    let html = '';
    sellers.forEach(s => {
      const statusClass = s.approval_status === 'APPROVED' ? 'badge-approved' : (s.approval_status === 'PENDING' ? 'badge-pending' : 'badge-rejected');
      html += `
        <tr>
          <td>#${s.id}</td>
          <td><strong>${s.business_name}</strong><br><small class="text-muted">${s.business_address || ''}</small></td>
          <td>${s.user ? s.user.full_name : 'N/A'}</td>
          <td>${s.user ? s.user.email : 'N/A'}</td>
          <td>${s.user ? s.user.phone || 'N/A' : 'N/A'}</td>
          <td><span class="status-badge ${statusClass}">${s.approval_status}</span></td>
          <td>${formatDate(s.created_at)}</td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-success" onclick="updateSellerApproval(${s.id}, 'APPROVED')" title="Approve">
                <i class="fas fa-check"></i>
              </button>
              <button class="btn btn-outline-danger" onclick="updateSellerApproval(${s.id}, 'REJECTED')" title="Reject">
                <i class="fas fa-times"></i>
              </button>
              <button class="btn btn-outline-secondary" onclick="updateSellerApproval(${s.id}, 'SUSPENDED')" title="Suspend">
                <i class="fas fa-pause"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html || '<tr><td colspan="8" class="text-center py-4">No seller profiles found</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-danger p-3">${err.message}</td></tr>`;
  }
}

async function updateSellerApproval(sellerId, status) {
  try {
    await apiFetch(`/admin/sellers/${sellerId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ approval_status: status })
    });
    showToast(`Seller status updated to ${status}`, 'success');
    loadAdminSellersTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 4. PRODUCT MODERATION
// ==========================================
async function loadAdminProductsTable() {
  const tbody = document.getElementById('adm-products-tbody');
  if (!tbody) return;

  try {
    const products = await apiFetch('/admin/products');
    let html = '';
    products.forEach(p => {
      const imageUrl = formatProductImage(p.image);
      html += `
        <tr>
          <td><img src="${imageUrl}" width="40" height="40" class="rounded border me-2"><strong>${p.name}</strong></td>
          <td>${p.seller_name || 'N/A'}</td>
          <td>${p.category_name || 'N/A'}</td>
          <td>${formatCurrency(p.price)}</td>
          <td>${p.stock_quantity}</td>
          <td><span class="status-badge ${p.status === 'ACTIVE' ? 'badge-approved' : 'badge-rejected'}">${p.status}</span></td>
          <td>
            <button class="btn btn-sm ${p.status === 'ACTIVE' ? 'btn-outline-warning' : 'btn-outline-success'} me-1" onclick="toggleAdminProductStatus(${p.id}, '${p.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'}')">
              ${p.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteAdminProduct(${p.id})">
              <i class="fas fa-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html || '<tr><td colspan="7" class="text-center py-4">No products found</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-danger p-3">${err.message}</td></tr>`;
  }
}

async function toggleAdminProductStatus(productId, status) {
  try {
    await apiFetch(`/admin/products/${productId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
    showToast(`Product status changed to ${status}`, 'success');
    loadAdminProductsTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteAdminProduct(productId) {
  if (!confirm('Are you sure you want to delete this product?')) return;
  try {
    await apiFetch(`/products/${productId}`, { method: 'DELETE' });
    showToast('Product deleted', 'info');
    loadAdminProductsTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 5. CATEGORY MANAGEMENT
// ==========================================
async function loadAdminCategoriesTable() {
  const tbody = document.getElementById('adm-categories-tbody');
  if (!tbody) return;

  try {
    const categories = await apiFetch('/categories');
    let html = '';
    categories.forEach(c => {
      html += `
        <tr>
          <td>#${c.id}</td>
          <td><i class="fas ${c.icon || 'fa-box'} text-primary me-2"></i><strong>${c.name}</strong></td>
          <td>${c.description || 'N/A'}</td>
          <td><span class="badge bg-primary rounded-pill">${c.product_count || 0} Products</span></td>
          <td><span class="badge bg-success">${c.status}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-secondary me-1" onclick="editCategoryModal(${c.id}, '${c.name}', '${c.description || ''}', '${c.icon || 'fa-box'}')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteAdminCategory(${c.id})">
              <i class="fas fa-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html || '<tr><td colspan="6" class="text-center py-4">No categories created yet</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger p-3">${err.message}</td></tr>`;
  }
}

let currentEditCatId = null;
function initCategoryModalForm() {
  const form = document.getElementById('category-modal-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('cat-modal-name').value.trim(),
      description: document.getElementById('cat-modal-desc').value.trim(),
      icon: document.getElementById('cat-modal-icon').value.trim() || 'fa-box',
      status: 'ACTIVE'
    };

    try {
      if (currentEditCatId) {
        await apiFetch(`/categories/${currentEditCatId}`, { method: 'PUT', body: JSON.stringify(payload) });
        showToast('Category updated!', 'success');
      } else {
        await apiFetch('/categories', { method: 'POST', body: JSON.stringify(payload) });
        showToast('Category created!', 'success');
      }
      bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
      loadAdminCategoriesTable();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

function openAddCategoryModal() {
  currentEditCatId = null;
  document.getElementById('cat-modal-title').textContent = 'Add New Category';
  document.getElementById('category-modal-form').reset();
  new bootstrap.Modal(document.getElementById('categoryModal')).show();
}

function editCategoryModal(id, name, desc, icon) {
  currentEditCatId = id;
  document.getElementById('cat-modal-title').textContent = 'Edit Category';
  document.getElementById('cat-modal-name').value = name;
  document.getElementById('cat-modal-desc').value = desc;
  document.getElementById('cat-modal-icon').value = icon;
  new bootstrap.Modal(document.getElementById('categoryModal')).show();
}

async function deleteAdminCategory(catId) {
  if (!confirm('Are you sure you want to delete this category? (Only empty categories can be deleted)')) return;
  try {
    await apiFetch(`/categories/${catId}`, { method: 'DELETE' });
    showToast('Category deleted successfully', 'info');
    loadAdminCategoriesTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 6. ALL ORDERS MANAGEMENT
// ==========================================
async function loadAdminOrdersTable() {
  const tbody = document.getElementById('adm-orders-tbody');
  if (!tbody) return;

  try {
    const orders = await apiFetch('/admin/orders');
    let html = '';
    orders.forEach(o => {
      html += `
        <tr>
          <td><strong>${o.order_number}</strong></td>
          <td>${o.customer_name}<br><small class="text-muted">${o.customer_email}</small></td>
          <td>${formatCurrency(o.total_amount)}</td>
          <td>${o.payment_method} (${o.payment_status})</td>
          <td><span class="status-badge badge-${o.order_status.toLowerCase().replace(/_/g, '-')}">${o.order_status}</span></td>
          <td>${formatDate(o.created_at)}</td>
          <td>
            <select class="form-select form-select-sm d-inline-block w-auto" onchange="updateAdminOrderStatus(${o.id}, this.value)">
              <option value="PLACED" ${o.order_status === 'PLACED' ? 'selected' : ''}>PLACED</option>
              <option value="CONFIRMED" ${o.order_status === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED</option>
              <option value="PROCESSING" ${o.order_status === 'PROCESSING' ? 'selected' : ''}>PROCESSING</option>
              <option value="SHIPPED" ${o.order_status === 'SHIPPED' ? 'selected' : ''}>SHIPPED</option>
              <option value="OUT_FOR_DELIVERY" ${o.order_status === 'OUT_FOR_DELIVERY' ? 'selected' : ''}>OUT_FOR_DELIVERY</option>
              <option value="DELIVERED" ${o.order_status === 'DELIVERED' ? 'selected' : ''}>DELIVERED</option>
              <option value="CANCELLED" ${o.order_status === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
            </select>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html || '<tr><td colspan="7" class="text-center py-4">No marketplace orders</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-danger p-3">${err.message}</td></tr>`;
  }
}

async function updateAdminOrderStatus(orderId, newStatus) {
  try {
    await apiFetch(`/orders/${orderId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ order_status: newStatus })
    });
    showToast(`Order status set to ${newStatus}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
    loadAdminOrdersTable();
  }
}

// ==========================================
// 7. REVIEW MODERATION
// ==========================================
async function loadAdminReviewsTable() {
  const tbody = document.getElementById('adm-reviews-tbody');
  if (!tbody) return;

  try {
    const reviews = await apiFetch('/admin/reviews');
    let html = '';
    reviews.forEach(r => {
      html += `
        <tr>
          <td>#${r.id}</td>
          <td><strong>${r.product_name}</strong></td>
          <td>${r.user_name}</td>
          <td>${renderStars(r.rating)}</td>
          <td><strong>${r.title}</strong><br><small class="text-muted">${r.comment}</small></td>
          <td>${formatDate(r.created_at)}</td>
          <td>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteAdminReview(${r.id})" title="Delete Review">
              <i class="fas fa-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html || '<tr><td colspan="7" class="text-center py-4">No reviews to moderate</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-danger p-3">${err.message}</td></tr>`;
  }
}

async function deleteAdminReview(reviewId) {
  if (!confirm('Are you sure you want to remove this review?')) return;
  try {
    await apiFetch(`/reviews/${reviewId}`, { method: 'DELETE' });
    showToast('Review removed successfully', 'info');
    loadAdminReviewsTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 8. REPORTS & ANALYTICS
// ==========================================
async function loadAdminReports() {
  try {
    const reports = await apiFetch('/admin/reports');

    document.getElementById('rep-sales').textContent = formatCurrency(reports.summary.total_sales);
    document.getElementById('rep-orders').textContent = reports.summary.total_orders;
    document.getElementById('rep-cust').textContent = reports.summary.total_customers;
    document.getElementById('rep-sellers').textContent = reports.summary.total_sellers;
    document.getElementById('rep-prod').textContent = reports.summary.total_products;

    // Top selling
    const topTbody = document.getElementById('rep-top-products-tbody');
    if (topTbody) {
      let html = '';
      reports.top_selling_products.forEach((p, idx) => {
        html += `
          <tr>
            <td>#${idx + 1}</td>
            <td><strong>${p.name}</strong></td>
            <td>${p.units} units</td>
            <td class="fw-bold">${formatCurrency(p.revenue)}</td>
          </tr>
        `;
      });
      topTbody.innerHTML = html || '<tr><td colspan="4" class="text-center py-3">No sales records yet</td></tr>';
    }

  } catch (err) {
    showToast(err.message, 'error');
  }
}
