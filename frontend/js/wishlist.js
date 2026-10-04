/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Wishlist Management & Move-to-Cart Script
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  loadWishlistData();
});

async function loadWishlistData() {
  const container = document.getElementById('wishlist-grid');
  const emptyState = document.getElementById('wishlist-empty-state');
  if (!container) return;

  try {
    const wishlist = await apiFetch('/wishlist');

    if (!wishlist.items || wishlist.items.length === 0) {
      container.innerHTML = '';
      if (emptyState) emptyState.classList.remove('d-none');
      updateNavbar();
      return;
    }

    if (emptyState) emptyState.classList.add('d-none');

    let html = '';
    wishlist.items.forEach(item => {
      const p = item.product;
      if (!p) return;

      const discountBadge = p.discount > 0 ? `<div class="discount-badge">-${p.discount}% OFF</div>` : '';
      let stockBadge = '<span class="stock-tag stock-in">In Stock</span>';
      if (p.stock_quantity <= 0) stockBadge = '<span class="stock-tag stock-out">Out of Stock</span>';
      const detailUrl = resolvePageUrl(`product-details.html?id=${p.id}`);
      const imageUrl = formatProductImage(p.image);

      html += `
        <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
          <div class="product-card">
            ${discountBadge}
            <div class="product-image-wrap">
              <a href="${detailUrl}">
                <img src="${imageUrl}" alt="${p.name}">
              </a>
            </div>
            <div class="product-body">
              <div class="d-flex justify-content-between align-items-center">
                <span class="product-category-tag">${p.category_name || 'Marketplace'}</span>
                ${stockBadge}
              </div>
              <a href="${detailUrl}" class="product-title">${p.name}</a>
              <div class="product-price-row">
                <span class="price-current">${formatCurrency(p.final_price)}</span>
                ${p.discount > 0 ? `<span class="price-original">${formatCurrency(p.price)}</span>` : ''}
              </div>
              <div class="d-grid gap-2 mt-3">
                <button class="btn btn-primary btn-sm" onclick="moveItemToCart(${p.id})" ${p.stock_quantity <= 0 ? 'disabled' : ''}>
                  <i class="fas fa-cart-plus me-1"></i>Move to Cart
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="removeWishlistItem(${p.id})">
                  <i class="fas fa-trash-alt me-1"></i>Remove
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
    updateNavbar();

  } catch (err) {
    container.innerHTML = `<div class="col-12 alert alert-danger">Error loading wishlist: ${err.message}</div>`;
  }
}

async function moveItemToCart(productId) {
  try {
    await apiFetch(`/wishlist/${productId}/move-to-cart`, { method: 'POST' });
    showToast('Product moved to cart!', 'success');
    loadWishlistData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function removeWishlistItem(productId) {
  try {
    await apiFetch(`/wishlist/${productId}`, { method: 'DELETE' });
    showToast('Removed from wishlist', 'info');
    loadWishlistData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
