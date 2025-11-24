// Urban Platter JavaScript Functionality

// Global variables
let cart = JSON.parse(localStorage.getItem('urbanPlatterCart') || '[]');
let menuItems = {};

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize Application
function initializeApp() {
    // Load menu items if on menu page
    if (window.location.pathname.includes('/menu')) {
        loadMenuItems();
    }
    
    // Initialize cart UI
    updateCartUI();
    
    // Add smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize fade-in animations
    initializeFadeInAnimations();
    
    // Initialize tooltips
    initializeTooltips();
}

// Load menu items data
function loadMenuItems() {
    fetch('/api/menu_items')
        .then(response => response.json())
        .then(items => {
            items.forEach(item => {
                menuItems[item.id] = item;
            });
            updateCartUI();
        })
        .catch(error => {
            console.error('Error loading menu items:', error);
            showToast('Failed to load menu items', 'danger');
        });
}

// Cart Management Functions
function addToCart(itemId, quantity = 1) {
    const item = menuItems[itemId];
    if (!item) {
        showToast('Item not found', 'danger');
        return;
    }
    
    const existingItemIndex = cart.findIndex(cartItem => cartItem.id === itemId);
    
    if (existingItemIndex > -1) {
        cart[existingItemIndex].quantity += quantity;
    } else {
        cart.push({
            id: itemId,
            name: item.name,
            price: item.price,
            quantity: quantity,
            image_url: item.image_url
        });
    }
    
    localStorage.setItem('urbanPlatterCart', JSON.stringify(cart));
    updateCartUI();
    showToast(`${item.name} added to cart!`, 'success');
}

function removeFromCart(itemId) {
    const itemName = cart.find(item => item.id === itemId)?.name;
    cart = cart.filter(item => item.id !== itemId);
    localStorage.setItem('urbanPlatterCart', JSON.stringify(cart));
    updateCartUI();
    if (itemName) {
        showToast(`${itemName} removed from cart`, 'info');
    }
}

function updateCartQuantity(itemId, newQuantity) {
    if (newQuantity <= 0) {
        removeFromCart(itemId);
        return;
    }
    
    const itemIndex = cart.findIndex(item => item.id === itemId);
    if (itemIndex > -1) {
        cart[itemIndex].quantity = newQuantity;
        localStorage.setItem('urbanPlatterCart', JSON.stringify(cart));
        updateCartUI();
    }
}

function clearCart() {
    cart = [];
    localStorage.setItem('urbanPlatterCart', JSON.stringify(cart));
    updateCartUI();
    showToast('Cart cleared', 'info');
}

// Update Cart UI
function updateCartUI() {
    const cartItems = document.getElementById('cartItems');
    const cartFooter = document.getElementById('cartFooter');
    const cartCounter = document.getElementById('cartCounter');
    const cartToggle = document.getElementById('cartToggle');
    const cartTotal = document.getElementById('cartTotal');
    
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    // Update cart counter
    if (cartCounter) {
        cartCounter.textContent = totalItems;
        cartCounter.style.display = totalItems > 0 ? 'inline' : 'none';
    }
    
    // Show/hide cart toggle
    if (cartToggle) {
        cartToggle.style.display = totalItems > 0 ? 'block' : 'none';
    }
    
    // Update cart total
    if (cartTotal) {
        cartTotal.textContent = `₹${totalPrice.toFixed(2)}`;
    }
    
    if (!cartItems) return;
    
    if (cart.length === 0) {
        cartItems.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-shopping-cart fa-2x mb-2"></i>
                <p>Your cart is empty</p>
                <a href="/menu" class="btn btn-primary btn-sm">
                    <i class="fas fa-utensils me-1"></i>Browse Menu
                </a>
            </div>
        `;
        if (cartFooter) cartFooter.style.display = 'none';
    } else {
        cartItems.innerHTML = cart.map(item => `
            <div class="cart-item">
                <div class="d-flex align-items-center">
                    <img src="${item.image_url}" alt="${item.name}" class="rounded" style="width: 50px; height: 50px; object-fit: cover;">
                    <div class="flex-grow-1 ms-3">
                        <h6 class="mb-1">${item.name}</h6>
                        <small class="text-muted">₹${item.price.toFixed(2)} each</small>
                    </div>
                </div>
                <div class="d-flex align-items-center justify-content-between mt-2">
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-outline-secondary btn-sm" onclick="updateCartQuantity(${item.id}, ${item.quantity - 1})">
                            <i class="fas fa-minus"></i>
                        </button>
                        <span class="mx-2 fw-bold">${item.quantity}</span>
                        <button class="btn btn-outline-secondary btn-sm" onclick="updateCartQuantity(${item.id}, ${item.quantity + 1})">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <strong>₹${(item.price * item.quantity).toFixed(2)}</strong>
                        <button class="btn btn-outline-danger btn-sm" onclick="removeFromCart(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        if (cartFooter) cartFooter.style.display = 'block';
    }
}

// Cart Sidebar Functions
function toggleCart() {
    const cartSidebar = document.getElementById('cartSidebar');
    if (cartSidebar) {
        cartSidebar.classList.toggle('open');
    }
}

// Checkout Process
function checkout() {
    if (cart.length === 0) {
        showToast('Your cart is empty!', 'warning');
        return;
    }
    
    const orderData = {
        cart_items: cart.map(item => ({
            menu_item_id: item.id,
            quantity: item.quantity
        })),
        special_instructions: document.getElementById('specialInstructions')?.value || ''
    };
    
    // Show loading state
    const checkoutBtn = document.querySelector('[onclick="checkout()"]');
    if (checkoutBtn) {
        checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        checkoutBtn.disabled = true;
    }
    
    fetch('/order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.order_id) {
            clearCart();
            toggleCart();
            showToast('Order placed successfully!', 'success');
            setTimeout(() => {
                window.location.href = `/payment/${data.order_id}`;
            }, 1500);
        } else {
            throw new Error(data.error || 'Failed to place order');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast(error.message || 'Failed to place order. Please try again.', 'danger');
    })
    .finally(() => {
        // Reset checkout button
        if (checkoutBtn) {
            checkoutBtn.innerHTML = '<i class="fas fa-check me-2"></i>Proceed to Checkout';
            checkoutBtn.disabled = false;
        }
    });
}

// Quantity Input Functions
function incrementQuantity(itemId) {
    const input = document.getElementById(`qty-${itemId}`);
    if (input) {
        const currentValue = parseInt(input.value);
        if (currentValue < 10) {
            input.value = currentValue + 1;
        }
    }
}

function decrementQuantity(itemId) {
    const input = document.getElementById(`qty-${itemId}`);
    if (input) {
        const currentValue = parseInt(input.value);
        if (currentValue > 1) {
            input.value = currentValue - 1;
        }
    }
}

// Toast Notification System
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getToastIcon(type)} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1100';
    document.body.appendChild(container);
    return container;
}

// Smooth Scrolling
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Fade-in Animations
function initializeFadeInAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card, .menu-item-card').forEach(el => {
        observer.observe(el);
    });
}

// Initialize Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Order Status Updates (for order tracking pages)
function updateOrderStatus(orderId, newStatus) {
    fetch(`/orders/${orderId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Order status updated successfully!', 'success');
            // Refresh the page or update the UI
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            throw new Error(data.error || 'Failed to update status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast(error.message || 'Failed to update order status', 'danger');
    });
}

// Form Validation Helpers
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

// Currency Formatting
function formatCurrency(amount) {
    return `₹${parseFloat(amount).toFixed(2)}`;
}

// Image Error Handling
function handleImageError(img) {
    img.onerror = null; // Prevent infinite loop
    img.src = '/static/images/placeholder-food.jpg'; // Fallback image
    img.alt = 'Image not available';
}

// Event Listeners for Global Actions
document.addEventListener('click', function(event) {
    // Close cart when clicking outside
    const cartSidebar = document.getElementById('cartSidebar');
    const cartToggle = document.getElementById('cartToggle');
    
    if (cartSidebar && cartSidebar.classList.contains('open')) {
        if (!cartSidebar.contains(event.target) && 
            !cartToggle?.contains(event.target) &&
            !event.target.closest('.cart-item')) {
            toggleCart();
        }
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // ESC to close cart
    if (event.key === 'Escape') {
        const cartSidebar = document.getElementById('cartSidebar');
        if (cartSidebar && cartSidebar.classList.contains('open')) {
            toggleCart();
        }
    }
});

// Export functions for use in HTML templates
window.UrbanPlatter = {
    addToCart,
    removeFromCart,
    updateCartQuantity,
    clearCart,
    toggleCart,
    checkout,
    incrementQuantity,
    decrementQuantity,
    showToast,
    updateOrderStatus,
    formatCurrency,
    handleImageError
};