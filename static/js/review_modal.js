// static/js/review_modal.js
// Review Modal Handler - Updated for Create & Edit
console.log('Review modal script loading...');

document.addEventListener('DOMContentLoaded', function () {
  console.log('DOM loaded, initializing review modal...');

  const reviewModal = document.getElementById('reviewModal');
  const cancelModal = document.getElementById('cancelModal');
  const errorMessage = document.getElementById('errorMessage');
  const form = document.getElementById('reviewForm');
  const modalEventId = document.getElementById('modal_event_id');
  const modalEventName = document.getElementById('modal_event_name');
  const modalReviewId = document.getElementById('modal_review_id');
  const modalMode = document.getElementById('modal_mode');
  const modalTitle = document.getElementById('modalTitle');
  const submitBtn = document.getElementById('submitBtn');

  console.log('Modal element:', reviewModal);

  if (!reviewModal) {
    console.error('Review modal not found in DOM!');
    return;
  }

  // Cari semua tombol rate (untuk CREATE review)
  const rateButtons = document.querySelectorAll('.rate-event-btn');
  console.log('Found rate buttons:', rateButtons.length);
  
  if (rateButtons.length === 0) {
    console.warn('No rate buttons found! Check if buttons have class "rate-event-btn"');
  }

  rateButtons.forEach((button, index) => {
    console.log(`Attaching listener to button ${index + 1}`);
    button.addEventListener('click', function (e) {
      e.preventDefault();
      console.log('✅ Rate button clicked!');
      
      const eventId = this.getAttribute('data-event-id');
      const eventName = this.getAttribute('data-event-name');
      
      console.log('Event ID:', eventId, 'Event Name:', eventName);
      
      // Set mode to CREATE
      openReviewModal(eventId, eventName);
    });
  });

  // Tutup modal - Cancel button
  if (cancelModal) {
    cancelModal.addEventListener('click', function () {
      closeReviewModal();
    });
  }

  // Tutup modal - Click outside
  reviewModal.addEventListener('click', function(e) {
    if (e.target === reviewModal) {
      closeReviewModal();
    }
  });

  // Submit form (handle both CREATE and EDIT)
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    errorMessage.classList.add('hidden');

    const mode = modalMode.value;
    const reviewId = modalReviewId.value;
    const eventId = modalEventId.value;
    const rating = document.getElementById('rating').value;
    const reviewText = document.getElementById('review_text').value;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Validate
    if (!rating || rating < 1 || rating > 5) {
      showError('Please enter a valid rating (1-5)');
      return;
    }

    console.log(`Submitting ${mode} for ${mode === 'edit' ? 'review' : 'event'}:`, mode === 'edit' ? reviewId : eventId);

    try {
      let url, body;
      
      if (mode === 'edit') {
        // EDIT review
        url = `/review/${reviewId}/edit/`;
        body = JSON.stringify({
          rating: parseInt(rating),
          review_text: reviewText
        });
      } else {
        // CREATE review
        url = `/review/create/${eventId}/`;
        body = JSON.stringify({
          rating: parseInt(rating),
          review_text: reviewText
        });
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: body
      });

      const data = await response.json();
      console.log('Response:', data);

      if (data.success) {
        alert(mode === 'edit' ? 'Review updated successfully!' : 'Review posted successfully!');
        closeReviewModal();
        setTimeout(() => location.reload(), 500);
      } else {
        showError(data.message || 'Failed to save review');
      }
    } catch (error) {
      console.error('Error:', error);
      showError('An error occurred. Please try again.');
    }
  });

  // Show error message
  function showError(message) {
    if (errorMessage) {
      errorMessage.textContent = message;
      errorMessage.classList.remove('hidden');
      
      setTimeout(() => {
        errorMessage.classList.add('hidden');
      }, 5000);
    }
  }
});

// Global functions for opening modal (accessible from HTML onclick)
window.openReviewModal = function(eventId, eventName) {
  console.log('Opening CREATE modal for event:', eventId, eventName);
  
  document.getElementById('modal_review_id').value = '';
  document.getElementById('modal_event_id').value = eventId;
  document.getElementById('modal_event_name').value = eventName;
  document.getElementById('rating').value = '';
  document.getElementById('review_text').value = '';
  document.getElementById('modal_mode').value = 'create';
  
  // Update modal title and button
  document.getElementById('modalTitle').textContent = 'Rate & Review';
  document.getElementById('submitBtn').textContent = 'Post';
  
  // Show modal
  const modal = document.getElementById('reviewModal');
  modal.style.display = 'flex';
  modal.classList.remove('hidden');
  
  console.log('✅ CREATE modal opened');
};

window.openEditReview = function(reviewId, eventId, eventName, rating, reviewText) {
  console.log('Opening EDIT modal for review:', reviewId);
  
  document.getElementById('modal_review_id').value = reviewId;
  document.getElementById('modal_event_id').value = eventId;
  document.getElementById('modal_event_name').value = eventName;
  document.getElementById('rating').value = rating;
  document.getElementById('review_text').value = reviewText;
  document.getElementById('modal_mode').value = 'edit';
  
  // Update modal title and button
  document.getElementById('modalTitle').textContent = 'Edit Review';
  document.getElementById('submitBtn').textContent = 'Update';
  
  // Show modal
  const modal = document.getElementById('reviewModal');
  modal.style.display = 'flex';
  modal.classList.remove('hidden');
  
  console.log('✅ EDIT modal opened');
};

window.closeReviewModal = function() {
  console.log('Closing modal...');
  const modal = document.getElementById('reviewModal');
  const errorMessage = document.getElementById('errorMessage');
  const form = document.getElementById('reviewForm');
  
  modal.style.display = 'none';
  modal.classList.add('hidden');
  if (errorMessage) errorMessage.classList.add('hidden');
  if (form) form.reset();
  
  console.log('✅ Modal closed');
};

// Toggle review menu dropdown
window.toggleReviewMenu = function(menuId) {
  console.log('Toggling menu:', menuId);
  
  // Close all other menus first
  document.querySelectorAll('[id^="menu-"]').forEach(menu => {
    if (menu.id !== menuId) {
      menu.classList.add('hidden');
    }
  });
  
  const menu = document.getElementById(menuId);
  if (!menu) {
    console.error('Menu not found:', menuId);
    return;
  }
  
  menu.classList.toggle('hidden');
  
  // Close menu when clicking outside
  if (!menu.classList.contains('hidden')) {
    setTimeout(() => {
      document.addEventListener('click', function closeMenu(e) {
        if (!e.target.closest(`#${menuId}`) && !e.target.closest('button[onclick*="toggleReviewMenu"]')) {
          menu.classList.add('hidden');
          document.removeEventListener('click', closeMenu);
        }
      });
    }, 100);
  }
};

// Delete review
window.deleteReview = async function(reviewId) {
  if (!confirm('Are you sure you want to delete this review?')) {
    return;
  }
  
  console.log('Deleting review:', reviewId);
  
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  try {
    const response = await fetch(`/review/${reviewId}/delete/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    const data = await response.json();
    console.log('Delete response:', data);
    
    if (data.success) {
      alert('Review deleted successfully!');
      setTimeout(() => location.reload(), 500);
    } else {
      alert('Failed to delete review: ' + data.message);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('An error occurred while deleting the review');
  }
};

console.log('✅ Review modal script loaded successfully');