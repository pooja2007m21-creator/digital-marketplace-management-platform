/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Product Details & Customer Verified Reviews
 */

let currentProductId = null;
let currentProduct = null;

document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  currentProductId = urlParams.get('id');

  if (!currentProductId) {
    showToast('Invalid product link', 'error');
    setTimeout(() => { window.location.href = resolvePageUrl('products.html'); }, 1000);
    return;
  }

  loadProductDetails(currentProductId);
  loadProductReviews(currentProductId);
  initReviewForm();
});

async function loadProductDetails(productId) {
  const container = document.getElementById('product-details-container');
  if (!container) return;

  try {
    currentProduct = await apiFetch(`/products/${productId}`);
    document.title = `${currentProduct.name} - Digital Marketplace`;

    // Populate UI elements
    document.getElementById('p-image').src = formatProductImage(currentProduct.image);
    document.getElementById('p-title').textContent = currentProduct.name;
    document.getElementById('p-category').textContent = currentProduct.category_name || 'Marketplace';
    document.getElementById('p-seller').textContent = currentProduct.seller_name || 'Verified Merchant';
    document.getElementById('p-brand').textContent = currentProduct.brand || 'Original Brand';
    document.getElementById('p-sku').textContent = currentProduct.sku;
    document.getElementById('p-description').textContent = currentProduct.description || 'No description provided.';
    
    // Pricing
    document.getElementById('p-price-final').textContent = formatCurrency(currentProduct.final_price);
    if (currentProduct.discount > 0) {
      document.getElementById('p-price-original').textContent = formatCurrency(currentProduct.price);
      document.getElementById('p-discount-badge').textContent = `${currentProduct.discount}% OFF`;
      document.getElementById('p-discount-badge').classList.remove('d-none');
    }

    // Rating
    document.getElementById('p-rating-stars').innerHTML = renderStars(currentProduct.rating_avg || 0);

    // Stock logic
    const stockBadge = document.getElementById('p-stock-badge');
    const lowStockWarning = document.getElementById('p-low-stock-alert');
    const addCartBtn = document.getElementById('p-btn-add-cart');
    const buyNowBtn = document.getElementById('p-btn-buy-now');

    if (currentProduct.stock_quantity <= 0 || currentProduct.status === 'OUT_OF_STOCK') {
      stockBadge.className = 'stock-tag stock-out';
      stockBadge.innerHTML = '<i class="fas fa-times-circle me-1"></i>Out of Stock';
      addCartBtn.disabled = true;
      buyNowBtn.disabled = true;
    } else if (currentProduct.stock_quantity <= 5) {
      stockBadge.className = 'stock-tag stock-low';
      stockBadge.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>In Stock (${currentProduct.stock_quantity} remaining)`;
      lowStockWarning.classList.remove('d-none');
      document.getElementById('p-low-stock-count').textContent = currentProduct.stock_quantity;
    } else {
      stockBadge.className = 'stock-tag stock-in';
      stockBadge.innerHTML = `<i class="fas fa-check-circle me-1"></i>In Stock (${currentProduct.stock_quantity} available)`;
    }

    // Specifications
    const specTable = document.getElementById('p-specifications-body');
    if (specTable && currentProduct.specifications) {
      const specsList = currentProduct.specifications.split('|');
      let specRows = '';
      specsList.forEach(spec => {
        const parts = spec.split(':');
        if (parts.length >= 2) {
          specRows += `
            <tr>
              <th>${parts[0].trim()}</th>
              <td>${parts.slice(1).join(':').trim()}</td>
            </tr>
          `;
        } else {
          specRows += `<tr><td colspan="2">${spec.trim()}</td></tr>`;
        }
      });
      specTable.innerHTML = specRows;
    }

  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger">Error loading product details: ${err.message}</div>`;
  }
}

function adjustDetailQuantity(delta) {
  const input = document.getElementById('detail-qty-input');
  if (!input || !currentProduct) return;
  let val = parseInt(input.value) + delta;
  if (val < 1) val = 1;
  if (val > currentProduct.stock_quantity) {
    showToast(`Maximum available quantity is ${currentProduct.stock_quantity}`, 'warning');
    val = currentProduct.stock_quantity;
  }
  input.value = val;
}

async function handleDetailAddToCart() {
  if (!currentProduct) return;
  const qty = parseInt(document.getElementById('detail-qty-input')?.value || 1);
  await addToCart(currentProduct.id, qty);
}

async function handleDetailBuyNow() {
  if (!currentProduct) return;
  const qty = parseInt(document.getElementById('detail-qty-input')?.value || 1);
  await addToCart(currentProduct.id, qty);
  window.location.href = resolvePageUrl('checkout.html');
}

async function loadProductReviews(productId) {
  const container = document.getElementById('reviews-list-container');
  const avgDisplay = document.getElementById('reviews-avg-rating');
  const countDisplay = document.getElementById('reviews-total-count');
  if (!container) return;

  try {
    const reviews = await apiFetch(`/products/${productId}/reviews`);
    if (countDisplay) countDisplay.textContent = `(${reviews.length} reviews)`;

    if (reviews.length === 0) {
      container.innerHTML = `
        <div class="text-center py-4 text-muted">
          <i class="far fa-comment-dots fs-2 mb-2"></i>
          <p>No reviews yet for this product. Be the first verified buyer to leave a review!</p>
        </div>
      `;
      if (avgDisplay) avgDisplay.innerHTML = renderStars(0);
      return;
    }

    const avg = (reviews.reduce((acc, r) => acc + r.rating, 0) / reviews.length).toFixed(1);
    if (avgDisplay) avgDisplay.innerHTML = renderStars(avg);

    let html = '';
    reviews.forEach(r => {
      html += `
        <div class="border-bottom py-3">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-light text-dark border"><i class="fas fa-check-circle text-success me-1"></i>Verified Buyer</span>
              <strong class="small">${r.user_name || 'Verified Customer'}</strong>
            </div>
            <span class="text-muted small">${formatDate(r.created_at)}</span>
          </div>
          <div class="mb-2">
            ${renderStars(r.rating)}
            <strong class="ms-2 small">${r.title}</strong>
          </div>
          <p class="text-muted small mb-0">${r.comment}</p>
        </div>
      `;
    });

    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger small">Error loading reviews: ${err.message}</div>`;
  }
}

function initReviewForm() {
  const form = document.getElementById('submit-review-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!isAuthenticated()) {
      showToast('Please log in to submit a review', 'info');
      return;
    }

    const rating = parseInt(document.querySelector('input[name="review_rating"]:checked')?.value || 5);
    const title = document.getElementById('review-title').value.trim();
    const comment = document.getElementById('review-comment').value.trim();

    try {
      await apiFetch(`/products/${currentProductId}/reviews`, {
        method: 'POST',
        body: JSON.stringify({ rating, title, comment })
      });

      showToast('Review submitted successfully!', 'success');
      form.reset();
      loadProductReviews(currentProductId);
    } catch (err) {
      showToast(err.message || 'Unable to submit review. Ensure you have purchased this product.', 'error');
    }
  });
}
