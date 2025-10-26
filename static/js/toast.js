function showToast(id, message) {
  const toast = document.getElementById(id);
  if (!toast) return;

  // Ubah pesan di dalam toast
  const msg = toast.querySelector('div.ms-3');
  if (msg) msg.textContent = message;

  toast.classList.remove('hidden');
  toast.classList.add('flex');

  // Otomatis hilang setelah 3 detik
  setTimeout(() => hideToast(id), 3000);
}

function hideToast(id) {
  const toast = document.getElementById(id);
  if (!toast) return;

  toast.classList.add('hidden');
  toast.classList.remove('flex');
}

