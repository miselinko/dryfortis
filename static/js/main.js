// ─────────────────────────────────────────
// AOS – Animate On Scroll init
// ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  if (typeof AOS !== 'undefined') {
    AOS.init({
      duration: 700,
      easing: 'ease-out-cubic',
      once: true,
      offset: 60,
    });
  }
});

// ─────────────────────────────────────────
// Counter Animation
// ─────────────────────────────────────────
(function () {
  const counters = document.querySelectorAll('.counter');
  if (!counters.length) return;

  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    const duration = 1800;
    const step = 16;
    const increment = target / (duration / step);
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        el.textContent = target.toLocaleString('sr-RS');
        clearInterval(timer);
      } else {
        el.textContent = Math.floor(current).toLocaleString('sr-RS');
      }
    }, step);
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => observer.observe(el));
})();

// ─────────────────────────────────────────
// FAQ Accordion
// ─────────────────────────────────────────
(function () {
  document.querySelectorAll('.faq-trigger').forEach(trigger => {
    trigger.addEventListener('click', function () {
      const item = this.closest('.faq-item');
      const answer = item.querySelector('.faq-answer');
      const icon = item.querySelector('.faq-icon');
      const isOpen = answer.classList.contains('open');

      // Close all others
      document.querySelectorAll('.faq-item').forEach(other => {
        other.querySelector('.faq-answer').classList.remove('open', 'hidden');
        other.querySelector('.faq-answer').classList.add('hidden');
        other.querySelector('.faq-icon').classList.remove('rotated');
      });

      // Toggle current
      if (!isOpen) {
        answer.classList.remove('hidden');
        answer.classList.add('open');
        icon.classList.add('rotated');
      }
    });
  });
})();

// ─────────────────────────────────────────
// Mobile Menu Toggle
// ─────────────────────────────────────────
(function () {
  const btn = document.getElementById('mobile-menu-btn');
  const menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;

  btn.addEventListener('click', () => {
    menu.classList.toggle('open');
    const spans = btn.querySelectorAll('span');
    btn.classList.toggle('menu-open');
    if (btn.classList.contains('menu-open')) {
      spans[0] && (spans[0].style.transform = 'rotate(45deg) translate(5px,5px)');
      spans[1] && (spans[1].style.opacity = '0');
      spans[2] && (spans[2].style.transform = 'rotate(-45deg) translate(5px,-5px)');
    } else {
      spans.forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    }
  });

  menu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menu.classList.remove('open');
      btn.classList.remove('menu-open');
      btn.querySelectorAll('span').forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    });
  });
})();

// ─────────────────────────────────────────
// Gallery Tab Filtering
// ─────────────────────────────────────────
(function () {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const galleryCards = document.querySelectorAll('.gallery-card');
  if (!tabBtns.length) return;

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      galleryCards.forEach(card => {
        card.classList.toggle('hidden', filter !== 'all' && card.dataset.category !== filter);
      });
    });
  });
})();

// ─────────────────────────────────────────
// Lightbox
// ─────────────────────────────────────────
(function () {
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCaption = document.getElementById('lightbox-caption');
  const closeBtn = document.getElementById('lightbox-close');
  if (!lightbox) return;

  document.addEventListener('click', function (e) {
    const item = e.target.closest('[data-lightbox]');
    if (item) {
      lightboxImg.src = item.dataset.lightbox;
      lightboxCaption.textContent = item.dataset.caption || '';
      lightbox.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  });

  closeBtn && closeBtn.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

  function closeLightbox() {
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
    lightboxImg.src = '';
  }
})();

// ─────────────────────────────────────────
// Smooth Scroll
// ─────────────────────────────────────────
(function () {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
})();

// ─────────────────────────────────────────
// Contact Form Validation
// ─────────────────────────────────────────
(function () {
  const form = document.getElementById('contact-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    let valid = true;
    ['name', 'phone', 'message'].forEach(name => {
      const field = form.querySelector(`[name="${name}"]`);
      if (!field) return;
      if (!field.value.trim()) {
        field.style.borderColor = '#ef4444';
        valid = false;
      } else {
        field.style.borderColor = '';
      }
    });

    if (!valid) {
      e.preventDefault();
      let err = document.getElementById('form-error');
      if (!err) {
        err = document.createElement('div');
        err.id = 'form-error';
        err.style.cssText = 'color:#ef4444;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px 14px;margin-top:8px;font-size:14px;';
        form.insertBefore(err, form.querySelector('button[type="submit"]'));
      }
      err.textContent = 'Molimo popunite sva polja.';
    }
  });
})();

// ─────────────────────────────────────────
// Upload Spinner
// ─────────────────────────────────────────
(function () {
  const uploadForm = document.getElementById('upload-form');
  if (!uploadForm) return;
  uploadForm.addEventListener('submit', function () {
    const spinner = document.getElementById('upload-spinner');
    const btnText = document.getElementById('upload-btn-text');
    if (spinner) spinner.classList.add('active');
    if (btnText) btnText.textContent = 'Otpremanje...';
  });
})();

// ─────────────────────────────────────────
// Admin Delete Confirmation
// ─────────────────────────────────────────
(function () {
  document.querySelectorAll('.delete-confirm').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm('Da li ste sigurni da želite da obrišete ovaj element?')) {
        e.preventDefault();
      }
    });
  });
})();

// ─────────────────────────────────────────
// Image Preview Before Upload
// ─────────────────────────────────────────
(function () {
  const fileInput = document.getElementById('upload-file');
  const preview = document.getElementById('upload-preview');
  if (!fileInput || !preview) return;

  fileInput.addEventListener('change', function () {
    const file = this.files[0];
    if (!file) { preview.style.display = 'none'; return; }
    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  });
})();
