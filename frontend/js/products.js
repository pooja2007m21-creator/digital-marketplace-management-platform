/**
 * DIGITAL MARKETPLACE MANAGEMENT PLATFORM
 * Products Catalog, Dynamic Filtering, Instant Search, Sorting & Pagination
 */

let currentFilters = {
  search: '',
  category_id: null,
  min_price: null,
  max_price: null,
  min_rating: null,
  availability: null,
  has_discount: false,
  sort_by: 'newest',
  page: 1,
  page_size: 12
};

document.addEventListener('DOMContentLoaded', () => {
  // Read query params from URL
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('search')) currentFilters.search = urlParams.get('search');
  if (urlParams.get('category_id')) currentFilters.category_id = parseInt(urlParams.get('category_id'));
  if (urlParams.get('sort_by')) currentFilters.sort_by = urlParams.get('sort_by');
  if (urlParams.get('has_discount')) currentFilters.has_discount = true;

  loadCategoriesFilter();
  loadProducts();
  initFilterListeners();
});

async function loadCategoriesFilter() {
  const container = document.getElementById('filter-categories-list');
  if (!container) return;

  try {
    const categories = await apiFetch('/categories');
    let html = `
      <div class="form-check mb-2">
        <input class="form-check-input category-filter-radio" type="radio" name="category_filter" id="cat-all" value="" ${!currentFilters.category_id ? 'checked' : ''}>
        <label class="form-check-label small fw-semibold" for="cat-all">All Categories</label>
      </div>
    `;

    categories.forEach(cat => {
      const isChecked = currentFilters.category_id === cat.id ? 'checked' : '';
      html += `
        <div class="form-check mb-2">
          <input class="form-check-input category-filter-radio" type="radio" name="category_filter" id="cat-${cat.id}" value="${cat.id}" ${isChecked}>
          <label class="form-check-label small" for="cat-${cat.id}">
            ${cat.name} <span class="text-muted">(${cat.product_count || 0})</span>
          </label>
        </div>
      `;
    });

    container.innerHTML = html;

    // Attach category change listener
    document.querySelectorAll('.category-filter-radio').forEach(r => {
      r.addEventListener('change', (e) => {
        currentFilters.category_id = e.target.value ? parseInt(e.target.value) : null;
        currentFilters.page = 1;
        loadProducts();
      });
    });
  } catch (err) {
    console.error('Failed to load categories', err);
  }
}

async function loadProducts() {
  const grid = document.getElementById('products-grid');
  const countDisplay = document.getElementById('products-count-display');
  const paginationContainer = document.getElementById('pagination-container');
  if (!grid) return;

  grid.innerHTML = `
    <div class="col-12 text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="text-muted mt-2">Loading marketplace products...</p>
    </div>
  `;

  try {
    const queryParams = new URLSearchParams();
    if (currentFilters.search) queryParams.set('search', currentFilters.search);
    if (currentFilters.category_id) queryParams.set('category_id', currentFilters.category_id);
    if (currentFilters.min_price !== null && currentFilters.min_price !== '') queryParams.set('min_price', currentFilters.min_price);
    if (currentFilters.max_price !== null && currentFilters.max_price !== '') queryParams.set('max_price', currentFilters.max_price);
    if (currentFilters.min_rating) queryParams.set('min_rating', currentFilters.min_rating);
    if (currentFilters.availability) queryParams.set('availability', currentFilters.availability);
    if (currentFilters.has_discount) queryParams.set('has_discount', 'true');
    if (currentFilters.sort_by) queryParams.set('sort_by', currentFilters.sort_by);
    queryParams.set('page', currentFilters.page);
    queryParams.set('page_size', currentFilters.page_size);

    const response = await apiFetch(`/products?${queryParams.toString()}`);

    if (countDisplay) {
      countDisplay.textContent = `Showing ${response.items.length} of ${response.total} products`;
    }

    if (response.items.length === 0) {
      grid.innerHTML = `
        <div class="col-12 text-center py-5 bg-white rounded-3 border p-5">
          <i class="fas fa-search fs-1 text-muted mb-3"></i>
          <h4>No products found</h4>
          <p class="text-muted">Try adjusting your search terms or filter criteria.</p>
          <button class="btn btn-outline-primary btn-sm" onclick="clearAllFilters()">Clear All Filters</button>
        </div>
      `;
      if (paginationContainer) paginationContainer.innerHTML = '';
      return;
    }

    let html = '';
    response.items.forEach(p => {
      const discountBadge = p.discount > 0 ? `<div class="discount-badge">-${p.discount}% OFF</div>` : '';
      const originalPrice = p.discount > 0 ? `<span class="price-original">${formatCurrency(p.price)}</span>` : '';
      
      let stockBadge = '<span class="stock-tag stock-in"><i class="fas fa-check-circle me-1"></i>In Stock</span>';
      if (p.stock_quantity <= 0 || p.status === 'OUT_OF_STOCK') {
        stockBadge = '<span class="stock-tag stock-out"><i class="fas fa-times-circle me-1"></i>Out of Stock</span>';
      } else if (p.stock_quantity <= 5) {
        stockBadge = `<span class="stock-tag stock-low"><i class="fas fa-exclamation-circle me-1"></i>Only ${p.stock_quantity} Left</span>`;
      }

      const detailUrl = resolvePageUrl(`product-details.html?id=${p.id}`);
      const imageUrl = formatProductImage(p.image);

      html += `
        <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
          <div class="product-card">
            ${discountBadge}
            <button class="wishlist-btn-corner" onclick="addToWishlist(${p.id})" title="Save to Wishlist">
              <i class="fas fa-heart"></i>
            </button>
            <div class="product-image-wrap">
              <a href="${detailUrl}">
                <img src="${imageUrl}" alt="${p.name}" loading="lazy">
              </a>
            </div>
            <div class="product-body">
              <div class="d-flex justify-content-between align-items-center">
                <span class="product-category-tag">${p.category_name || 'Marketplace'}</span>
                ${stockBadge}
              </div>
              <a href="${detailUrl}" class="product-title" title="${p.name}">
                ${p.name}
              </a>
              <div class="product-seller-name">
                <i class="fas fa-store me-1"></i>${p.seller_name || 'Verified Seller'}
              </div>
              <div class="mb-2">
                ${renderStars(p.rating_avg || 0)}
              </div>
              <div class="product-price-row">
                <span class="price-current">${formatCurrency(p.final_price)}</span>
                ${originalPrice}
              </div>
              <div class="d-grid gap-2 mt-3">
                <button class="btn btn-primary btn-sm" onclick="addToCart(${p.id})" ${p.stock_quantity <= 0 ? 'disabled' : ''}>
                  <i class="fas fa-cart-plus me-1"></i>Add to Cart
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
    renderPagination(response.page, response.pages);

  } catch (err) {
    grid.innerHTML = `<div class="col-12 alert alert-danger">Error loading products: ${err.message}</div>`;
  }
}

function renderPagination(currentPage, totalPages) {
  const container = document.getElementById('pagination-container');
  if (!container || totalPages <= 1) {
    if (container) container.innerHTML = '';
    return;
  }

  let html = '<ul class="pagination justify-content-center">';
  
  // Previous button
  html += `
    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
      <a class="page-link" href="javascript:void(0)" onclick="goToPage(${currentPage - 1})">Previous</a>
    </li>
  `;

  for (let i = 1; i <= totalPages; i++) {
    html += `
      <li class="page-item ${i === currentPage ? 'active' : ''}">
        <a class="page-link" href="javascript:void(0)" onclick="goToPage(${i})">${i}</a>
      </li>
    `;
  }

  // Next button
  html += `
    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
      <a class="page-link" href="javascript:void(0)" onclick="goToPage(${currentPage + 1})">Next</a>
    </li>
  `;

  html += '</ul>';
  container.innerHTML = html;
}

function goToPage(page) {
  currentFilters.page = page;
  loadProducts();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initFilterListeners() {
  // Search bar
  const searchInput = document.getElementById('catalog-search-input');
  if (searchInput) {
    if (currentFilters.search) searchInput.value = currentFilters.search;
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentFilters.search = e.target.value.trim();
        currentFilters.page = 1;
        loadProducts();
      }, 400);
    });
  }

  // Sort dropdown
  const sortSelect = document.getElementById('catalog-sort-select');
  if (sortSelect) {
    if (currentFilters.sort_by) sortSelect.value = currentFilters.sort_by;
    sortSelect.addEventListener('change', (e) => {
      currentFilters.sort_by = e.target.value;
      currentFilters.page = 1;
      loadProducts();
    });
  }

  // Price range apply
  const priceApplyBtn = document.getElementById('price-filter-apply-btn');
  if (priceApplyBtn) {
    priceApplyBtn.addEventListener('click', () => {
      currentFilters.min_price = document.getElementById('filter-min-price').value;
      currentFilters.max_price = document.getElementById('filter-max-price').value;
      currentFilters.page = 1;
      loadProducts();
    });
  }

  // Availability filter
  document.querySelectorAll('input[name="availability_filter"]').forEach(r => {
    r.addEventListener('change', (e) => {
      currentFilters.availability = e.target.value || null;
      currentFilters.page = 1;
      loadProducts();
    });
  });

  // Rating filter
  document.querySelectorAll('input[name="rating_filter"]').forEach(r => {
    r.addEventListener('change', (e) => {
      currentFilters.min_rating = e.target.value ? parseFloat(e.target.value) : null;
      currentFilters.page = 1;
      loadProducts();
    });
  });

  // Discount only filter
  const discountCheckbox = document.getElementById('filter-discount-only');
  if (discountCheckbox) {
    if (currentFilters.has_discount) discountCheckbox.checked = true;
    discountCheckbox.addEventListener('change', (e) => {
      currentFilters.has_discount = e.target.checked;
      currentFilters.page = 1;
      loadProducts();
    });
  }
}

function clearAllFilters() {
  currentFilters = {
    search: '',
    category_id: null,
    min_price: null,
    max_price: null,
    min_rating: null,
    availability: null,
    has_discount: false,
    sort_by: 'newest',
    page: 1,
    page_size: 12
  };

  const searchInput = document.getElementById('catalog-search-input');
  if (searchInput) searchInput.value = '';

  const minP = document.getElementById('filter-min-price');
  const maxP = document.getElementById('filter-max-price');
  if (minP) minP.value = '';
  if (maxP) maxP.value = '';

  const disc = document.getElementById('filter-discount-only');
  if (disc) disc.checked = false;

  const catAll = document.getElementById('cat-all');
  if (catAll) catAll.checked = true;

  const availAll = document.getElementById('avail-all');
  if (availAll) availAll.checked = true;

  const rateAll = document.getElementById('rate-all');
  if (rateAll) rateAll.checked = true;

  loadProducts();
}

// Add to Cart
async function addToCart(productId, quantity = 1) {
  if (!isAuthenticated()) {
    showToast('Please log in to add items to your cart', 'info');
    setTimeout(() => {
      window.location.href = resolvePageUrl('login.html?redirect=' + encodeURIComponent(window.location.pathname + window.location.search));
    }, 1000);
    return;
  }

  try {
    const res = await apiFetch('/cart', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity: quantity })
    });
    showToast('Product added to shopping cart!', 'success');
    updateNavbar();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Add to Wishlist
async function addToWishlist(productId) {
  if (!isAuthenticated()) {
    showToast('Please log in to save items to wishlist', 'info');
    setTimeout(() => {
      window.location.href = resolvePageUrl('login.html?redirect=' + encodeURIComponent(window.location.pathname + window.location.search));
    }, 1000);
    return;
  }

  try {
    await apiFetch('/wishlist', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId })
    });
    showToast('Saved to wishlist!', 'success');
    updateNavbar();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
