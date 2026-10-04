/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Checkout, Address Autofill & Simulated Payment System
 */

let currentCart = null;

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadCheckoutOverview();
  initPaymentMethodToggle();
  initCheckoutForm();
});

async function loadCheckoutOverview() {
  try {
    currentCart = await apiFetch('/cart');
    if (!currentCart.items || currentCart.items.length === 0) {
      showToast('Your cart is empty. Add products before checkout.', 'warning');
      setTimeout(() => { window.location.href = resolvePageUrl('products.html'); }, 1000);
      return;
    }

    // Prefill user profile info
    const user = getUser();
    if (user) {
      document.getElementById('co-name').value = user.full_name || '';
      document.getElementById('co-email').value = user.email || '';
      document.getElementById('co-phone').value = user.phone || '';
      document.getElementById('co-address').value = user.address || '';
      document.getElementById('co-city').value = user.city || '';
      document.getElementById('co-state').value = user.state || '';
      document.getElementById('co-zip').value = user.postal_code || '';
    }

    // Render Order summary items
    const itemsContainer = document.getElementById('checkout-items-list');
    if (itemsContainer) {
      let html = '';
      currentCart.items.forEach(item => {
        html += `
          <div class="d-flex justify-content-between align-items-center mb-2 small">
            <div>
              <strong>${item.product.name}</strong>
              <div class="text-muted">${item.quantity} x ${formatCurrency(item.product.final_price)}</div>
            </div>
            <span class="fw-semibold">${formatCurrency(item.subtotal)}</span>
          </div>
        `;
      });
      itemsContainer.innerHTML = html;
    }

    document.getElementById('co-subtotal').textContent = formatCurrency(currentCart.subtotal);
    document.getElementById('co-delivery').textContent = currentCart.delivery_charge === 0 ? 'FREE' : formatCurrency(currentCart.delivery_charge);
    document.getElementById('co-tax').textContent = formatCurrency(currentCart.tax);
    document.getElementById('co-total').textContent = formatCurrency(currentCart.grand_total);

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function initPaymentMethodToggle() {
  const methodRadios = document.querySelectorAll('input[name="payment_method"]');
  const onlineDetails = document.getElementById('online-payment-details');

  methodRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.value === 'SIMULATED_ONLINE') {
        onlineDetails?.classList.remove('d-none');
      } else {
        onlineDetails?.classList.add('d-none');
      }
    });
  });
}

function initCheckoutForm() {
  const form = document.getElementById('checkout-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('btn-place-order');
    const originalText = submitBtn.innerHTML;

    const payload = {
      customer_name: document.getElementById('co-name').value.trim(),
      customer_email: document.getElementById('co-email').value.trim(),
      customer_phone: document.getElementById('co-phone').value.trim(),
      delivery_address: document.getElementById('co-address').value.trim(),
      city: document.getElementById('co-city').value.trim(),
      state: document.getElementById('co-state').value.trim(),
      postal_code: document.getElementById('co-zip').value.trim(),
      payment_method: document.querySelector('input[name="payment_method"]:checked')?.value || 'COD'
    };

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing Order & Payment...';

      // Place order via API
      const order = await apiFetch('/orders', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      // Show success modal with simulated payment info
      const txnModal = document.getElementById('order-success-modal');
      if (txnModal) {
        document.getElementById('modal-order-id').textContent = order.order_number;
        document.getElementById('modal-order-total').textContent = formatCurrency(order.total_amount);
        document.getElementById('modal-txn-ref').textContent = order.payment ? order.payment.transaction_reference : 'N/A';
        document.getElementById('modal-pay-status').textContent = order.payment_status;
        
        const modal = new bootstrap.Modal(txnModal);
        modal.show();

        document.getElementById('btn-view-order-receipt').onclick = () => {
          window.location.href = resolvePageUrl(`order-details.html?id=${order.id}`);
        };
      } else {
        showToast('Order placed successfully!', 'success');
        setTimeout(() => {
          window.location.href = resolvePageUrl(`order-details.html?id=${order.id}`);
        }, 1200);
      }

    } catch (err) {
      showToast(err.message || 'Order placement failed.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });
}
