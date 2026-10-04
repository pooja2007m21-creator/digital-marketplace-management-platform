/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Seller Portal Scripts (Dashboard, Products CRUD, Inventory, Orders)
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth(['SELLER', 'ADMIN'])) return;

  if (window.location.pathname.includes('seller/dashboard.html')) {
    loadSellerDashboard();
  } else if (window.location.pathname.includes('seller/products.html')) {
    loadSellerProductsTable();
  } else if (window.location.pathname.includes('seller/add-product.html')) {
    initProductForm();
  } else if (window.location.pathname.includes('seller/inventory.html')) {
    loadSellerInventoryTable();
  } else if (window.location.pathname.includes('seller/orders.html')) {
    loadSellerOrdersTable();
  }
});

// ==========================================
// 1. SELLER DASHBOARD
// ==========================================
async function loadSellerDashboard() {
  try {
    const data = await apiFetch('/seller/dashboard');

    document.getElementById('stat-total-products').textContent = data.total_products || 0;
    document.getElementById('stat-active-products').textContent = data.active_products || 0;
    document.getElementById('stat-low-stock').textContent = data.low_stock_products || 0;
    document.getElementById('stat-total-orders').textContent = data.total_orders || 0;
    document.getElementById('stat-pending-orders').textContent = data.pending_orders || 0;
    document.getElementById('stat-total-sales').textContent = formatCurrency(data.total_sales || 0);

    // Render Recent Orders table
    const ordersTbody = document.getElementById('seller-recent-orders-tbody');
    if (ordersTbody) {
      if (!data.recent_orders || data.recent_orders.length === 0) {
        ordersTbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No recent orders found</td></tr>';
      } else {
        let html = '';
        data.recent_orders.forEach(o => {
          html += `
            <tr>
              <td><strong>${o.order_number}</strong></td>
              <td>${o.customer_name}</td>
              <td>${o.items_count} items</td>
              <td>${formatCurrency(o.seller_total)}</td>
              <td><span class="status-badge badge-${o.order_status.toLowerCase().replace(/_/g, '-')}">${o.order_status}</span></td>
              <td>${o.created_at}</td>
            </tr>
          `;
        });
        ordersTbody.innerHTML = html;
      }
    }

    // Render Low Stock Alert list
    const lowStockContainer = document.getElementById('seller-low-stock-list');
    if (lowStockContainer) {
      if (!data.low_stock_items || data.low_stock_items.length === 0) {
        lowStockContainer.innerHTML = '<div class="text-muted p-3 text-center">All inventory levels healthy!</div>';
      } else {
        let html = '';
        data.low_stock_items.forEach(p => {
          html += `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
              <div>
                <strong>${p.name}</strong>
                <div class="small text-muted">SKU: ${p.sku}</div>
              </div>
              <div>
                <span class="badge bg-danger">${p.stock_quantity} left</span>
                <a href="${resolvePageUrl('seller/inventory.html')}" class="btn btn-sm btn-outline-primary ms-2">Restock</a>
              </div>
            </div>
          `;
        });
        lowStockContainer.innerHTML = html;
      }
    }

    // Chart.js Monthly Sales
    initSellerSalesChart(data.monthly_sales);

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function initSellerSalesChart(salesData) {
  const ctx = document.getElementById('sellerSalesChart');
  if (!ctx || typeof Chart === 'undefined') return;

  const labels = (salesData || []).map(d => d.month);
  const values = (salesData || []).map(d => d.sales);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
      datasets: [{
        label: 'Monthly Revenue (₹)',
        data: values.length ? values : [1500, 4200, 7800, 11500, 18200],
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        fill: true,
        tension: 0.35,
        borderWidth: 3
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

// ==========================================
// 2. SELLER PRODUCTS MANAGEMENT
// ==========================================
async function loadSellerProductsTable() {
  const tbody = document.getElementById('seller-products-tbody');
  if (!tbody) return;

  try {
    const products = await apiFetch('/seller/products');
    if (!products || products.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No products created yet. Click "Add New Product" to start selling!</td></tr>';
      return;
    }

    let html = '';
    products.forEach(p => {
      const isOut = p.stock_quantity <= 0;
      const imageUrl = formatProductImage(p.image);
      const editUrl = resolvePageUrl(`seller/add-product.html?id=${p.id}`);

      html += `
        <tr>
          <td>
            <img src="${imageUrl}" width="48" height="48" class="rounded border me-2" alt="${p.name}">
            <strong>${p.name}</strong>
          </td>
          <td>${p.category_name || 'N/A'}</td>
          <td>${p.sku}</td>
          <td>${formatCurrency(p.price)} ${p.discount > 0 ? `<span class="badge bg-danger ms-1">-${p.discount}%</span>` : ''}</td>
          <td>
            <span class="badge ${isOut ? 'bg-danger' : (p.stock_quantity <= 5 ? 'bg-warning text-dark' : 'bg-success')}">
              ${p.stock_quantity}
            </span>
          </td>
          <td>
            <span class="status-badge ${p.status === 'ACTIVE' ? 'badge-delivered' : 'badge-cancelled'}">${p.status}</span>
          </td>
          <td>
            <a href="${editUrl}" class="btn btn-sm btn-outline-secondary me-1" title="Edit Product">
              <i class="fas fa-edit"></i>
            </a>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteSellerProduct(${p.id})" title="Delete Product">
              <i class="fas fa-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-danger p-3">Error: ${err.message}</td></tr>`;
  }
}

async function deleteSellerProduct(productId) {
  if (!confirm('Are you sure you want to delete this product?')) return;
  try {
    await apiFetch(`/products/${productId}`, { method: 'DELETE' });
    showToast('Product deleted successfully', 'info');
    loadSellerProductsTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 3. ADD / EDIT PRODUCT FORM
// ==========================================
async function initProductForm() {
  const form = document.getElementById('product-form');
  if (!form) return;

  // Load categories into select
  const catSelect = document.getElementById('prod-category');
  try {
    const categories = await apiFetch('/categories');
    catSelect.innerHTML = categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  } catch (e) {}

  // Image Upload handler
  const imageFileInput = document.getElementById('prod-image-file');
  const imageHiddenInput = document.getElementById('prod-image-url');
  const imagePreview = document.getElementById('prod-image-preview');

  if (imageFileInput) {
    imageFileInput.addEventListener('change', async () => {
      const file = imageFileInput.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        showToast('Uploading image...', 'info');
        const res = await apiFetch('/products/upload-image', {
          method: 'POST',
          body: formData
        });
        imageHiddenInput.value = res.image_url;
        imagePreview.src = formatProductImage(res.image_url);
        imagePreview.classList.remove('d-none');
        showToast('Image uploaded successfully!', 'success');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Check if Editing existing product
  const urlParams = new URLSearchParams(window.location.search);
  const editId = urlParams.get('id');
  if (editId) {
    document.getElementById('form-heading').textContent = 'Edit Product';
    try {
      const p = await apiFetch(`/products/${editId}`);
      document.getElementById('prod-name').value = p.name;
      document.getElementById('prod-category').value = p.category_id;
      document.getElementById('prod-brand').value = p.brand || '';
      document.getElementById('prod-sku').value = p.sku;
      document.getElementById('prod-price').value = p.price;
      document.getElementById('prod-discount').value = p.discount || 0;
      document.getElementById('prod-stock').value = p.stock_quantity;
      document.getElementById('prod-status').value = p.status;
      document.getElementById('prod-desc').value = p.description || '';
      document.getElementById('prod-specs').value = p.specifications || '';
      if (p.image) {
        imageHiddenInput.value = p.image;
        imagePreview.src = formatProductImage(p.image);
        imagePreview.classList.remove('d-none');
      }
    } catch (e) {
      showToast('Error loading product details', 'error');
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('prod-name').value.trim(),
      category_id: parseInt(document.getElementById('prod-category').value),
      brand: document.getElementById('prod-brand').value.trim(),
      sku: document.getElementById('prod-sku').value.trim() || undefined,
      price: parseFloat(document.getElementById('prod-price').value),
      discount: parseFloat(document.getElementById('prod-discount').value) || 0,
      stock_quantity: parseInt(document.getElementById('prod-stock').value) || 0,
      status: document.getElementById('prod-status').value,
      description: document.getElementById('prod-desc').value.trim(),
      specifications: document.getElementById('prod-specs').value.trim(),
      image: imageHiddenInput.value || '/assets/images/placeholder.svg'
    };

    try {
      if (editId) {
        await apiFetch(`/products/${editId}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
        showToast('Product updated successfully!', 'success');
      } else {
        await apiFetch('/products', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        showToast('Product created successfully!', 'success');
      }
      setTimeout(() => { window.location.href = resolvePageUrl('seller/products.html'); }, 1000);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// ==========================================
// 4. SELLER INVENTORY MANAGEMENT
// ==========================================
async function loadSellerInventoryTable() {
  const tbody = document.getElementById('seller-inventory-tbody');
  if (!tbody) return;

  try {
    const products = await apiFetch('/seller/products');
    let html = '';
    products.forEach(p => {
      let statusBadge = '<span class="stock-tag stock-in">In Stock</span>';
      if (p.stock_quantity <= 0) statusBadge = '<span class="stock-tag stock-out">Out of Stock</span>';
      else if (p.stock_quantity <= 5) statusBadge = '<span class="stock-tag stock-low">Low Stock</span>';

      html += `
        <tr>
          <td><strong>${p.name}</strong></td>
          <td>${p.sku}</td>
          <td>
            <input type="number" min="0" class="form-control form-control-sm inventory-stock-input" id="inv-stock-${p.id}" value="${p.stock_quantity}">
          </td>
          <td>
            <input type="number" step="0.01" min="1" class="form-control form-control-sm" style="max-width: 110px;" id="inv-price-${p.id}" value="${p.price}">
          </td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="saveInventoryRow(${p.id})">
              <i class="fas fa-save me-1"></i>Save
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger p-3">Error: ${err.message}</td></tr>`;
  }
}

async function saveInventoryRow(productId) {
  const stock = document.getElementById(`inv-stock-${productId}`).value;
  const price = document.getElementById(`inv-price-${productId}`).value;

  try {
    await apiFetch(`/seller/inventory/${productId}`, {
      method: 'PUT',
      body: JSON.stringify({ stock_quantity: stock, price: price })
    });
    showToast('Inventory updated!', 'success');
    loadSellerInventoryTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// 5. SELLER ORDERS MANAGEMENT
// ==========================================
async function loadSellerOrdersTable() {
  const container = document.getElementById('seller-orders-container');
  if (!container) return;

  try {
    const orders = await apiFetch('/seller/orders');
    if (!orders || orders.length === 0) {
      container.innerHTML = '<div class="alert alert-info text-center p-4">No customer orders received yet.</div>';
      return;
    }

    let html = '';
    orders.forEach(ord => {
      let itemsList = '';
      ord.items.forEach(it => {
        itemsList += `<li><strong>${it.quantity}x</strong> ${it.product_name} - ${formatCurrency(it.subtotal)}</li>`;
      });

      html += `
        <div class="card card-custom mb-3 p-3">
          <div class="d-flex flex-wrap justify-content-between align-items-center border-bottom pb-2 mb-3">
            <div>
              <strong>${ord.order_number}</strong>
              <span class="text-muted small ms-2">${ord.created_at}</span>
            </div>
            <div>
              <span class="status-badge badge-${ord.order_status.toLowerCase().replace(/_/g, '-')}">${ord.order_status}</span>
            </div>
          </div>
          <div class="row">
            <div class="col-md-5">
              <div class="small text-muted mb-1">Customer & Shipping:</div>
              <div><strong>${ord.customer_name}</strong> (${ord.customer_phone})</div>
              <div class="small text-muted">${ord.delivery_address}</div>
            </div>
            <div class="col-md-4">
              <div class="small text-muted mb-1">Ordered Items:</div>
              <ul class="small mb-0 ps-3">${itemsList}</ul>
              <div class="fw-bold text-primary mt-1">Seller Subtotal: ${formatCurrency(ord.seller_subtotal)}</div>
            </div>
            <div class="col-md-3">
              <div class="small text-muted mb-1">Update Status:</div>
              <select class="form-select form-select-sm mb-2" id="order-status-select-${ord.id}">
                <option value="CONFIRMED" ${ord.order_status === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED</option>
                <option value="PROCESSING" ${ord.order_status === 'PROCESSING' ? 'selected' : ''}>PROCESSING</option>
                <option value="SHIPPED" ${ord.order_status === 'SHIPPED' ? 'selected' : ''}>SHIPPED</option>
                <option value="OUT_FOR_DELIVERY" ${ord.order_status === 'OUT_FOR_DELIVERY' ? 'selected' : ''}>OUT_FOR_DELIVERY</option>
                <option value="DELIVERED" ${ord.order_status === 'DELIVERED' ? 'selected' : ''}>DELIVERED</option>
                <option value="CANCELLED" ${ord.order_status === 'CANCELLED' ? 'selected' : ''}>CANCELLED</option>
              </select>
              <button class="btn btn-sm btn-outline-primary w-100" onclick="updateOrderStatusSeller(${ord.id})">Update Status</button>
            </div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
  }
}

async function updateOrderStatusSeller(orderId) {
  const newStatus = document.getElementById(`order-status-select-${orderId}`).value;
  try {
    await apiFetch(`/orders/${orderId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ order_status: newStatus })
    });
    showToast(`Order status updated to ${newStatus}`, 'success');
    loadSellerOrdersTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
