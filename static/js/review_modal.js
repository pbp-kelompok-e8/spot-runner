// Review Modal Handler
console.log('Review modal script loading...');

document.addEventListener('DOMContentLoaded', function () {
  console.log('DOM loaded, initializing review modal...');

  const reviewModal = document.getElementById('reviewModal');
  const cancelModal = document.getElementById('cancelModal');
  const errorMessage = document.getElementById('errorMessage');
  const form = document.getElementById('reviewForm');
  const modalEventId = document.getElementById('modal_event_id');
  const modalEventName = document.getElementById('modal_event_name');

  console.log('Modal element:', reviewModal);

  if (!reviewModal) {
    console.error('Review modal not found in DOM!');
    return;
  }

  // Cari semua tombol rate
  const rateButtons = document.querySelectorAll('.rate-event-btn');
  console.log('Found rate buttons:', rateButtons.length);
  
  if (rateButtons.length === 0) {
    console.warn('No rate buttons found! Check if buttons have class "rate-event-btn"');
  }

  rateButtons.forEach((button, index) => {
    console.log(`Attaching listener to button ${index + 1}`);
    button.addEventListener('click', function (e) {
      e.preventDefault();
      console.log('✅ Button clicked!');
      
      const eventId = this.getAttribute('data-event-id');
      const eventName = this.getAttribute('data-event-name');
      
      console.log('Event ID:', eventId, 'Event Name:', eventName);
      
      // Set nilai ke modal
      modalEventId.value = eventId;
      modalEventName.value = eventName;
      
      // Buka modal
      reviewModal.style.display = 'flex';
      reviewModal.classList.remove('hidden');
      
      console.log('✅ Modal opened');
    });
  });

  // Tutup modal - Cancel button
  if (cancelModal) {
    cancelModal.addEventListener('click', function () {
      console.log('Closing modal...');
      reviewModal.style.display = 'none';
      reviewModal.classList.add('hidden');
      errorMessage.classList.add('hidden');
      form.reset();
    });
  }

  // Tutup modal - Click outside
  reviewModal.addEventListener('click', function(e) {
    if (e.target === reviewModal) {
      console.log('Closing modal (clicked outside)...');
      reviewModal.style.display = 'none';
      reviewModal.classList.add('hidden');
      errorMessage.classList.add('hidden');
      form.reset();
    }
  });

  // Submit form
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorMessage.classList.add('hidden');

    const formData = new FormData(form);
    const eventId = modalEventId.value;

    console.log('Submitting review for event:', eventId);

    fetch(`/review/create/${eventId}/`, {
      method: 'POST',
      headers: { 
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
      },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      console.log('Response:', data);
      if (data.success) {
        alert('Review posted successfully!');
        reviewModal.style.display = 'none';
        reviewModal.classList.add('hidden');
        form.reset();
        setTimeout(() => location.reload(), 500);
      } else {
        errorMessage.textContent = data.error || 'Failed to submit review';
        errorMessage.classList.remove('hidden');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      errorMessage.textContent = 'An error occurred. Please try again.';
      errorMessage.classList.remove('hidden');
    });
  });
});