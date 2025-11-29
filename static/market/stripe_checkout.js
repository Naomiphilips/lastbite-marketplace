// Get Stripe publishable key and initialize
fetch('/market/config/')
  .then((result) => result.json())
  .then((data) => {
    // Initialize Stripe
    const stripe = Stripe(data.publishableKey);
    
    // Get checkout button
    const checkoutButton = document.getElementById('checkout-button');
    
    if (checkoutButton) {
      checkoutButton.addEventListener('click', function() {
        // Disable button during processing
        checkoutButton.disabled = true;
        checkoutButton.textContent = 'Processing...';
        
        // Create checkout session
        fetch('/market/create-checkout-session/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
          },
        })
        .then((result) => result.json())
        .then((data) => {
          if (data.error) {
            alert(data.error);
            checkoutButton.disabled = false;
            checkoutButton.textContent = 'Proceed to Checkout';
          } else {
            // Redirect to Stripe Checkout
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          }
        })
        .then((result) => {
          if (result && result.error) {
            alert(result.error.message);
            checkoutButton.disabled = false;
            checkoutButton.textContent = 'Proceed to Checkout';
          }
        })
        .catch((error) => {
          console.error('Error:', error);
          alert('An error occurred. Please try again.');
          checkoutButton.disabled = false;
          checkoutButton.textContent = 'Proceed to Checkout';
        });
      });
    }
  })
  .catch((error) => {
    console.error('Error loading Stripe config:', error);
  });

// Helper function to get CSRF token
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