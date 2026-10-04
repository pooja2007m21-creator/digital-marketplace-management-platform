/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Customer Orders, Receipt & Visual Timeline Tracking
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;

  const urlParams = new URLSearchParams(window.location.search);
  const orderId = urlParams.get('id');

  if (window.location.pathname.includes('order-details.html')) {
    if (orderId) loadOrderReceipt(orderId);
    else window.location.href = resolvePageUrl('orders.html');
  } else if (window.location.pathname.includes('orders.html')) {
    loadCustomerOrders();
  }
});

async function loadCustomerOrders() {
  const container = document.getElementById('customer-orders-list');
  const emptyState = document.getElementById('orders-empty-state');
  if (!container) return;

  try {
    const orders = await apiFetch('/orders');

    if (!orders || orders.length === 0) {
      if (emptyState) emptyState.classList.remove('d-none');
      container.innerHTML = '';
      return;
    }

    if (emptyState) emptyState.classList.add('d-none');

    let html = '';
    orders.forEach(ord => {
      const statusBadges = {
        PLACED: 'badge-placed',
        CONFIRMED: 'badge-confirmed',
        PROCESSING: 'badge-processing',
        SHIPPED: 'badge-shipped',
        OUT_FOR_DELIVERY: 'badge-out-for-delivery',
        DELIVERED: 'badge-delivered',
        CANCELLED: 'badge-cancelled'
      };

      const badgeClass = statusBadges[ord.order_status] || 'badge-placed';

      let itemsPreview = '';
      ord.items.forEach(i => {
        itemsPreview += `<span class="badge bg-light text-dark border me-1">${i.quantity}x ${i.product_name}</span>`;
      });

      const detailUrl = resolvePageUrl(`order-details.html?id=${ord.id}`);

      html += `
        <div class="card card-custom mb-3 p-3">
          <div class="d-flex flex-wrap justify-content-between align-items-center border-bottom pb-2 mb-3">
            <div>
              <span class="text-muted small">ORDER NUMBER:</span>
              <strong class="ms-1">${ord.order_number}</strong>
            </div>
            <div>
              <span class="status-badge ${badgeClass}">${ord.order_status}</span>
            </div>
          </div>
          <div class="row align-items-center">
            <div class="col-md-6 mb-2 mb-md-0">
              <div class="text-muted small mb-1">Placed on: ${formatDate(ord.created_at)}</div>
              <div class="mb-2">${itemsPreview}</div>
              <div class="small"><i class="fas fa-map-marker-alt text-danger me-1"></i>${ord.delivery_address}</div>
            </div>
            <div class="col-md-3 mb-2 mb-md-0 text-md-center">
              <div class="text-muted small">Total Amount</div>
              <div class="fs-5 fw-bold text-dark">${formatCurrency(ord.total_amount)}</div>
              <span class="badge bg-secondary-subtle text-secondary small">${ord.payment_method} (${ord.payment_status})</span>
            </div>
            <div class="col-md-3 text-md-end">
              <a href="${detailUrl}" class="btn btn-outline-primary btn-sm mb-1 w-100 w-md-auto">
                <i class="fas fa-eye me-1"></i>Track & View
              </a>
              ${(ord.order_status === 'PLACED' || ord.order_status === 'CONFIRMED') ? `
                <button class="btn btn-outline-danger btn-sm w-100 w-md-auto mt-1" onclick="cancelOrder(${ord.id})">
                  Cancel Order
                </button>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">Error loading orders: ${err.message}</div>`;
  }
}

async function loadOrderReceipt(orderId) {
  const receiptContainer = document.getElementById('order-receipt-content');
  if (!receiptContainer) return;

  try {
    const order = await apiFetch(`/orders/${orderId}`);

    document.getElementById('receipt-order-id').textContent = order.order_number;
    document.getElementById('receipt-order-date').textContent = formatDate(order.created_at);
    document.getElementById('receipt-cust-name').textContent = order.customer_name;
    document.getElementById('receipt-cust-email').textContent = order.customer_email;
    document.getElementById('receipt-cust-phone').textContent = order.customer_phone;
    document.getElementById('receipt-delivery-addr').textContent = order.delivery_address;

    document.getElementById('receipt-payment-method').textContent = order.payment_method;
    document.getElementById('receipt-payment-status').textContent = order.payment_status;
    document.getElementById('receipt-txn-ref').textContent = order.payment ? order.payment.transaction_reference : 'N/A';

    // Timeline Tracker
    renderVisualTimeline(order.order_status);

    // Items table
    const tableBody = document.getElementById('receipt-items-tbody');
    let itemsHtml = '';
    order.items.forEach((it, idx) => {
      itemsHtml += `
        <tr>
          <td>${idx + 1}</td>
          <td>
            <div class="fw-semibold">${it.product_name}</div>
          </td>
          <td>${formatCurrency(it.unit_price)}</td>
          <td>${it.quantity}</td>
          <td class="text-end fw-bold">${formatCurrency(it.subtotal)}</td>
        </tr>
      `;
    });
    tableBody.innerHTML = itemsHtml;

    // Totals
    document.getElementById('receipt-subtotal').textContent = formatCurrency(order.subtotal);
    document.getElementById('receipt-delivery').textContent = order.delivery_charge === 0 ? 'FREE' : formatCurrency(order.delivery_charge);
    document.getElementById('receipt-tax').textContent = formatCurrency(order.tax);
    document.getElementById('receipt-total').textContent = formatCurrency(order.total_amount);

    // Cancel button in details page if eligible
    const cancelBtn = document.getElementById('receipt-cancel-btn');
    if (cancelBtn) {
      if (order.order_status === 'PLACED' || order.order_status === 'CONFIRMED') {
        cancelBtn.classList.remove('d-none');
        cancelBtn.onclick = () => cancelOrder(order.id);
      } else {
        cancelBtn.classList.add('d-none');
      }
    }

  } catch (err) {
    receiptContainer.innerHTML = `<div class="alert alert-danger">Failed to load order receipt: ${err.message}</div>`;
  }
}

function renderVisualTimeline(currentStatus) {
  const steps = [
    { id: 'PLACED', label: 'Order Placed', icon: 'fa-clipboard-check' },
    { id: 'CONFIRMED', label: 'Confirmed', icon: 'fa-check' },
    { id: 'PROCESSING', label: 'Processing', icon: 'fa-box' },
    { id: 'SHIPPED', label: 'Shipped', icon: 'fa-shipping-fast' },
    { id: 'OUT_FOR_DELIVERY', label: 'Out for Delivery', icon: 'fa-truck' },
    { id: 'DELIVERED', label: 'Delivered', icon: 'fa-home' }
  ];

  const statusOrder = ['PLACED', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED'];
  const currentIndex = statusOrder.indexOf(currentStatus);

  const container = document.getElementById('order-timeline-tracker');
  if (!container) return;

  if (currentStatus === 'CANCELLED') {
    container.innerHTML = `
      <div class="alert alert-danger text-center p-3">
        <i class="fas fa-ban fs-3 me-2"></i>
        <strong>This order was CANCELLED</strong>. Stock was restored to marketplace inventory.
      </div>
    `;
    return;
  }

  let html = '';
  steps.forEach((step, idx) => {
    let stateClass = '';
    if (idx < currentIndex) stateClass = 'completed';
    else if (idx === currentIndex) stateClass = 'active';

    html += `
      <div class="timeline-step ${stateClass}">
        <div class="timeline-icon">
          <i class="fas ${step.icon}"></i>
        </div>
        <div class="timeline-title">${step.label}</div>
      </div>
    `;
  });

  container.innerHTML = html;
}

async function cancelOrder(orderId) {
  if (!confirm('Are you sure you want to cancel this order?')) return;

  try {
    await apiFetch(`/orders/${orderId}/cancel`, { method: 'POST' });
    showToast('Order cancelled successfully', 'info');
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  } catch (err) {
    showToast(err.message, 'error');
  }
}
