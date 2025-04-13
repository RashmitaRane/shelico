// static/js/auth.js
function checkAuthAndRedirect() {
    // Check if user is logged in (admin or regular user)
    fetch('/check-auth-status')
        .then(response => response.json())
        .then(data => {
            if (data.isAuthenticated) {
                if (data.isAdmin) {
                    window.location.href = "/admindashboard";
                } else {
                    window.location.href = "/dashboard";
                }
            } else {
                // Show login modal or redirect to login page
                alert('Please login first to explore our services.');
                window.location.href = "/login";
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.location.href = "/login";
        });
}

// For service buttons
function redirectToLogin() {
    window.location.href = "/login";
}