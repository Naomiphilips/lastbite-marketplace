/* File location: dashboard/static/dashboard/js/dashboard-stats.js */


// Function to update dashboard statistics
function updateDashboardStats() {
    fetch('/dashboard/api/stats/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.stats;
                
                // Update Items in Cart (CHANGED: was Total Orders)
                const cartItemsEl = document.querySelector('.stat-card:nth-child(1) h3');
                if (cartItemsEl && stats.total_cart_items !== undefined) {
                    cartItemsEl.textContent = stats.total_cart_items;
                }
                
                // Update Cart Subtotal
                const subtotalEl = document.querySelector('.stat-card:nth-child(2) h3');
                if (subtotalEl && stats.cart_subtotal !== undefined) {
                    subtotalEl.textContent = `$${stats.cart_subtotal.toFixed(2)}`;
                }
                
                // Update Favorites
                const favoritesEl = document.querySelector('.stat-card:nth-child(3) h3');
                if (favoritesEl && stats.favorites_count !== undefined) {
                    favoritesEl.textContent = stats.favorites_count;
                }
                
                // Update Total Spent (if you have a 4th card)
                const spentEl = document.querySelector('.stat-card:nth-child(4) h3');
                if (spentEl && stats.total_spent !== undefined) {
                    spentEl.textContent = `$${stats.total_spent.toFixed(2)}`;
                }
                
                console.log('Dashboard stats updated:', stats);
            }
        })
        .catch(error => {
            console.error('Error updating dashboard stats:', error);
        });
}

// Update stats when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initial update
    updateDashboardStats();
    
    // Optional: Auto-refresh every 30 seconds
    // setInterval(updateDashboardStats, 30000);
});

// Update stats when user returns to the tab
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        updateDashboardStats();
    }
});