/* File location: dashboard/static/dashboard/js/dashboard.js */

// Map variables
let map;
let markers = [];
let userMarker;

// Constants
const KM_TO_MILES = 0.621371;
const MILES_TO_KM = 1.60934;

document.addEventListener('DOMContentLoaded', function() {
    
    // Debug: Check if Django URLs are loaded
    console.log('Geocode URL:', typeof GEOCODE_URL !== 'undefined' ? GEOCODE_URL : 'undefined');
    console.log('Nearby Businesses URL:', typeof NEARBY_BUSINESSES_URL !== 'undefined' ? NEARBY_BUSINESSES_URL : 'undefined');
    
    // Initialize map functionality
    initMapEventListeners();
    
    // Auto-detect location on page load
    detectLocation();
    
    // Mobile sidebar toggle
    const createSidebarToggle = () => {
        if (window.innerWidth <= 991) {
            const navbar = document.querySelector('.navbar .container-fluid');
            const sidebar = document.querySelector('.sidebar');
            
            // Create toggle button if it doesn't exist
            if (!document.getElementById('sidebarToggle')) {
                const toggleBtn = document.createElement('button');
                toggleBtn.id = 'sidebarToggle';
                toggleBtn.className = 'btn btn-outline-light me-2';
                toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
                toggleBtn.style.order = '-1';
                
                toggleBtn.addEventListener('click', function() {
                    sidebar.classList.toggle('show');
                });
                
                navbar.insertBefore(toggleBtn, navbar.firstChild);
            }
        }
    };

    createSidebarToggle();
    window.addEventListener('resize', createSidebarToggle);

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        const sidebar = document.querySelector('.sidebar');
        const toggleBtn = document.getElementById('sidebarToggle');
        
        if (window.innerWidth <= 991 && sidebar && sidebar.classList.contains('show')) {
            if (!sidebar.contains(e.target) && e.target !== toggleBtn && (!toggleBtn || !toggleBtn.contains(e.target))) {
                sidebar.classList.remove('show');
            }
        }
    });

    // Sidebar link active state
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't prevent default if it has a real URL
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
            }
            
            // Remove active class from all links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
            
            // Close sidebar on mobile after clicking
            if (window.innerWidth <= 991) {
                const sidebar = document.querySelector('.sidebar');
                if (sidebar) {
                    sidebar.classList.remove('show');
                }
            }
        });
    });

    // Animate stat cards on load
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Placeholder for future functionality
    console.log('Dashboard loaded successfully!');
    
    // Button click handlers (placeholders)
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        if (btn.id !== 'sidebarToggle' && 
            btn.id !== 'detectLocationBtn' &&
            btn.id !== 'searchZipBtn' &&
            !btn.classList.contains('dropdown-toggle') && 
            !btn.classList.contains('navbar-toggler')) {
            btn.addEventListener('click', function(e) {
                if (this.getAttribute('href') === '#' || !this.getAttribute('href')) {
                    e.preventDefault();
                    const btnText = this.textContent.trim();
                    console.log('Button clicked:', btnText);
                }
            });
        }
    });

    // Smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Add active state to navigation based on current page
    const currentPath = window.location.pathname;
    sidebarLinks.forEach(link => {
        const linkPath = new URL(link.href, window.location.origin).pathname;
        if (linkPath === currentPath) {
            link.classList.add('active');
        }
    });

    // Optional: Add animation to empty state
    const emptyState = document.querySelector('.empty-state');
    if (emptyState) {
        setTimeout(() => {
            emptyState.style.opacity = '0';
            emptyState.style.transform = 'translateY(20px)';
            emptyState.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            
            setTimeout(() => {
                emptyState.style.opacity = '1';
                emptyState.style.transform = 'translateY(0)';
            }, 100);
        }, 300);
    }
});

// ============ MAP FUNCTIONALITY ============

// Initialize map event listeners
function initMapEventListeners() {
    // Detect location button
    const detectBtn = document.getElementById('detectLocationBtn');
    if (detectBtn) {
        detectBtn.addEventListener('click', detectLocation);
    }
    
    // Search by ZIP button
    const searchBtn = document.getElementById('searchZipBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchByZipCode);
    }
    
    // Update businesses when radius changes
    const radiusSelect = document.getElementById('radiusSelect');
    if (radiusSelect) {
        radiusSelect.addEventListener('change', function() {
            if (map && userMarker) {
                const center = map.getCenter();
                loadNearbyBusinesses(center.lat, center.lng);
            }
        });
    }
    
    // Allow Enter key to trigger ZIP search
    const zipInput = document.getElementById('zipCodeInput');
    if (zipInput) {
        zipInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchByZipCode();
            }
        });
    }
}

// Initialize map
function initMap(lat, lng) {
    // Clear existing map if any
    if (map) {
        map.remove();
    }
    
    // Create map centered on user location
    map = L.map('map').setView([lat, lng], 13);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add user location marker
    userMarker = L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'user-marker',
            html: '<i class="fas fa-user-circle fa-2x text-primary"></i>',
            iconSize: [30, 30]
        })
    }).addTo(map);
    
    userMarker.bindPopup('<b>You are here</b>').openPopup();
    
    // Load nearby businesses
    loadNearbyBusinesses(lat, lng);
}

// Detect user location
function detectLocation() {
    if (!navigator.geolocation) {
        showError('Geolocation is not supported by your browser. Please enter a ZIP code.');
        return;
    }
    
    showLoading(true);
    hideError();
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            showLoading(false);
            initMap(position.coords.latitude, position.coords.longitude);
        },
        function(error) {
            showLoading(false);
            let errorMsg = 'Unable to detect location. ';
            if (error.code === error.PERMISSION_DENIED) {
                errorMsg += 'Please enable location access or enter a ZIP code.';
            } else {
                errorMsg += 'Please enter a ZIP code to search.';
            }
            showError(errorMsg);
        }
    );
}

// Search by ZIP code
function searchByZipCode() {
    const zipCode = document.getElementById('zipCodeInput').value.trim();
    
    if (!zipCode) {
        showError('Please enter a ZIP code');
        return;
    }
    
    showLoading(true);
    hideError();
    
    console.log('Searching for ZIP code:', zipCode);
    
    // Get CSRF token
    const csrftoken = getCookie('csrftoken');
    
    // Check if URL is defined
    if (typeof GEOCODE_URL === 'undefined') {
        showLoading(false);
        showError('Configuration error: Geocode URL not found');
        console.error('GEOCODE_URL not defined');
        return;
    }
    
    console.log('Fetching from URL:', GEOCODE_URL);
    
    fetch(GEOCODE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `zip_code=${zipCode}`
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        showLoading(false);
        if (data.success) {
            console.log('Initializing map with coordinates:', data.latitude, data.longitude);
            initMap(data.latitude, data.longitude);
        } else {
            showError(data.error || 'ZIP code not found');
        }
    })
    .catch(error => {
        showLoading(false);
        showError('Failed to search ZIP code. Please try again.');
        console.error('ZIP code search error:', error);
    });
}

// Load nearby businesses
function loadNearbyBusinesses(lat, lng) {
    const radiusMiles = document.getElementById('radiusSelect').value;
    const radiusKm = radiusMiles * MILES_TO_KM; // Convert miles to km for backend
    
    console.log('Loading businesses for:', { lat, lng, radiusMiles, radiusKm });
    
    // Check if URL is defined
    if (typeof NEARBY_BUSINESSES_URL === 'undefined') {
        showError('Configuration error: Nearby businesses URL not found');
        console.error('NEARBY_BUSINESSES_URL not defined');
        return;
    }
    
    showLoading(true);
    
    fetch(`${NEARBY_BUSINESSES_URL}?lat=${lat}&lng=${lng}&radius=${radiusKm}`)
    .then(response => {
        console.log('Businesses response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Businesses data:', data);
        showLoading(false);
        if (data.success) {
            displayBusinesses(data.businesses);
            const countEl = document.getElementById('listingCount');
            if (countEl) {
                countEl.textContent = `${data.count} store${data.count !== 1 ? 's' : ''}`;
            }
        } else {
            showError('Failed to load businesses');
        }
    })
    .catch(error => {
        showLoading(false);
        showError('Failed to load nearby businesses');
        console.error('Load businesses error:', error);
    });
}

// Display businesses on map
function displayBusinesses(businesses) {
    // Clear existing markers
    markers.forEach(marker => marker.remove());
    markers = [];
    
    if (businesses.length === 0) {
        showError('No stores found in this area. Try increasing the search radius.');
        return;
    }
    
    hideError();
    
    // Add markers for each business
    businesses.forEach(business => {
        const marker = L.marker([business.latitude, business.longitude], {
            icon: L.divIcon({
                className: 'business-marker',
                html: '<i class="fas fa-store fa-2x text-success"></i>',
                iconSize: [30, 30]
            })
        }).addTo(map);
        
        // Convert distance from km to miles
        const distanceMi = (business.distance * KM_TO_MILES).toFixed(2);
        
        // Format address
        const addressParts = [];
        if (business.address) addressParts.push(business.address);
        if (business.city) addressParts.push(business.city);
        if (business.state) addressParts.push(business.state);
        if (business.zip_code) addressParts.push(business.zip_code);
        const fullAddress = addressParts.join(', ');
        
        // Get first listing image if available
        const firstProduct = business.products && business.products.length > 0 ? business.products[0] : null;
        const businessImage = firstProduct && firstProduct.image ? firstProduct.image : null;
        
        // Create popup content with link to business public page
        // CHANGED: Use business_id instead of owner_id
        const popupContent = `
            <div class="business-popup" style="min-width: 240px; max-width: 300px;">
                ${businessImage ? `
                    <img src="${businessImage}" 
                         alt="${business.owner_name}" 
                         style="width: 100%; height: 140px; object-fit: cover; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                ` : ''}
                
                <h6 style="margin: 8px 0 12px 0; font-weight: bold; color: #2c3e50; font-size: 1.15em;">
                    <i class="fas fa-store" style="color: #28a745; margin-right: 6px;"></i>
                    ${business.owner_name}
                </h6>
                
                <div style="margin: 12px 0; padding: 10px 0; border-top: 1px solid #e9ecef; border-bottom: 1px solid #e9ecef;">
                    ${fullAddress ? `
                        <p style="margin: 6px 0; font-size: 0.85em; color: #666; line-height: 1.4;">
                            <i class="fas fa-map-marker-alt" style="color: #dc3545; width: 18px;"></i> 
                            ${fullAddress}
                        </p>
                    ` : ''}
                    
                    <p style="margin: 6px 0; font-size: 0.9em; color: #555; font-weight: 500;">
                        <i class="fas fa-location-arrow" style="color: #007bff; width: 18px;"></i> 
                        ${distanceMi} miles away
                    </p>
                    
                    <p style="margin: 6px 0; font-size: 0.9em; color: ${business.product_count > 0 ? '#28a745' : '#999'}; font-weight: 500;">
                        <i class="fas fa-box" style="width: 18px;"></i> 
                        ${business.product_count || 0} item${(business.product_count || 0) !== 1 ? 's' : ''} available
                    </p>
                </div>
                
                ${business.products && business.products.length > 0 ? `
                    <div style="margin: 12px 0;">
                        <p style="font-size: 0.8em; color: #666; margin-bottom: 6px; font-weight: 600;">Featured Items:</p>
                        ${business.products.slice(0, 2).map(product => `
                            <div style="font-size: 0.8em; color: #555; margin: 4px 0; padding: 4px; background: #f8f9fa; border-radius: 4px;">
                                • ${product.title} - <strong style="color: #28a745;">$${product.price}</strong>
                            </div>
                        `).join('')}
                        ${business.products.length > 2 ? `
                            <p style="font-size: 0.75em; color: #999; margin: 4px 0;">
                                +${business.products.length - 2} more item${business.products.length - 2 !== 1 ? 's' : ''}
                            </p>
                        ` : ''}
                    </div>
                ` : ''}
                
                <a href="/biz/public/${business.business_id}/" 
                   class="btn btn-sm btn-success w-100" 
                   style="text-decoration: none; margin-top: 10px; padding: 10px; font-weight: 600; border-radius: 6px; box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2); transition: all 0.3s ease;">
                    <i class="fas fa-shopping-bag"></i> Visit Store
                </a>
            </div>
        `;
        
        marker.bindPopup(popupContent, {
            maxWidth: 320,
            className: 'custom-business-popup'
        });
        
        markers.push(marker);
    });
    
    // Fit map to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup([userMarker, ...markers]);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Helper functions
function showLoading(show) {
    const loadingEl = document.getElementById('mapLoading');
    const mapEl = document.getElementById('map');
    
    if (loadingEl && mapEl) {
        loadingEl.style.display = show ? 'block' : 'none';
        mapEl.style.display = show ? 'none' : 'block';
    }
}

function showError(message) {
    const errorEl = document.getElementById('mapError');
    const messageEl = document.getElementById('errorMessage');
    
    if (errorEl && messageEl) {
        messageEl.textContent = message;
        errorEl.style.display = 'block';
    }
}

function hideError() {
    const errorEl = document.getElementById('mapError');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}