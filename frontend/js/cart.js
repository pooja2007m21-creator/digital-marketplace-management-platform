/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Shopping Cart Management & Live Cost Calculation
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadCartData();
});

async function loadCartData() {
  const container = document.getElementById('cart-items-container');
  const emptyState = document.getElementById('cart-empty-state');
  const cartContent = document.getElementById('cart-content-wrapper');
  if (!container) return;

  try {
    const cart = await apiFetch('/cart');

    if (!cart.items || cart.items.length === 0) {
      if (cartContent) cartContent.classList.add('d-none');
      if (emptyState) emptyState.classList.remove('d-none');
      updateNavbar();
      return;
    }

    if (cartContent) cartContent.classList.remove('d-none');
    if (emptyState) emptyState.classList.add('d-none');

    let itemsHtml = '';
    cart.items.forEach(item => {
      const p = item.product;
      const unitPrice = p ? p.final_price : 0;
      const lineTotal = item.subtotal || (unitPrice * item.quantity);
      const detailUrl = resolvePageUrl(`product-details.html?id=${p.id}`);
      const imageUrl = formatProductImage(p.image);

      itemsHtml += `
        <div class="card card-custom mb-3 p-3">
          <div class="row align-items-center">
            <div class="col-md-2 col-4">
              <img src="${imageUrl}" class="img-fluid rounded border" alt="${p.name}">
            </div>
            <div class="col-md-4 col-8">
              <span class="badge bg-light text-primary border mb-1">${p.category_name || 'Marketplace'}</span>
              <h6 class="mb-1"><a href="${detailUrl}" class="text-dark">${p.name}</a></h6>
              <div class="small text-muted"><i class="fas fa-store me-1"></i>${p.seller_name || 'Seller'}</div>
              <div class="fw-bold mt-1 text-primary">${formatCurrency(unitPrice)}</div>
            </div>
            <div class="col-md-3 col-6 mt-3 mt-md-0">
              <div class="input-group input-group-sm" style="max-width: 130px;">
                <button class="btn btn-outline-secondary" type="button" onclick="updateItemQuantity(${item.id}, ${item.quantity - 1})">-</button>
                <input type="text" class="form-control text-center fw-bold" value="${item.quantity}" readonly>
                <button class="btn btn-outline-secondary" type="button" onclick="updateItemQuantity(${item.id}, ${item.quantity + 1})">+</button>
              </div>
            </div>
            <div class="col-md-2 col-4 text-end mt-3 mt-md-0">
              <div class="fw-bold fs-6">${formatCurrency(lineTotal)}</div>
            </div>
            <div class="col-md-1 col-2 text-end mt-3 mt-md-0">
              <button class="btn btn-outline-danger btn-sm rounded-circle" onclick="removeCartItem(${item.id})" title="Remove item">
                <i class="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = itemsHtml;

    // Summary calculations
    document.getElementById('summary-subtotal').textContent = formatCurrency(cart.subtotal);
    document.getElementById('summary-delivery').textContent = cart.delivery_charge === 0 ? 'FREE' : formatCurrency(cart.delivery_charge);
    document.getElementById('summary-tax').textContent = formatCurrency(cart.tax);
    document.getElementById('summary-total').textContent = formatCurrency(cart.grand_total);
    document.getElementById('summary-count').textContent = cart.item_count;

    const checkoutBtn = document.getElementById('btn-proceed-checkout');
    if (checkoutBtn) {
      checkoutBtn.href = resolvePageUrl('checkout.html');
    }

    updateNavbar();

  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">Failed to load cart: ${err.message}</div>`;
  }
}

async function updateItemQuantity(itemId, newQty) {
  if (newQty <= 0) {
    removeCartItem(itemId);
    return;
  }

  try {
    await apiFetch(`/cart/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity: newQty })
    });
    loadCartData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function removeCartItem(itemId) {
  try {
    await apiFetch(`/cart/${itemId}`, { method: 'DELETE' });
    showToast('Item removed from cart', 'info');
    loadCartData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function clearCartAll() {
  if (!confirm('Are you sure you want to clear your entire cart?')) return;
  try {
    await apiFetch('/cart', { method: 'DELETE' });
    showToast('Shopping cart cleared', 'info');
    loadCartData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
