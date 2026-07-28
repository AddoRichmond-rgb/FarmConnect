/* FarmConnect — vanilla JS interactions.
   1. page loader   2. mobile nav   3. sticky navbar   4. scroll reveal
   5. flash dismiss 6. form validation 7. search suggestions 8. accordion
   9. register role switcher  10. product gallery */
(function () {
  'use strict';

  // 1. Page loader ---------------------------------------------------------
  window.addEventListener('load', function () {
    var loader = document.getElementById('pageLoader');
    if (loader) { loader.classList.add('hidden'); }
  });

  // 2. Mobile navigation ---------------------------------------------------
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.classList.toggle('active', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // 3. Sticky navbar shadow on scroll -------------------------------------
  var navbar = document.getElementById('navbar');
  if (navbar) {
    var onScroll = function () {
      navbar.classList.toggle('scrolled', window.scrollY > 12);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // 4. Reveal-on-scroll animations ----------------------------------------
  var revealables = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealables.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add('visible'); });
  }

  // 5. Dismissable flash messages -----------------------------------------
  document.querySelectorAll('.flash-close').forEach(function (btn) {
    btn.addEventListener('click', function () { btn.parentElement.remove(); });
  });
  setTimeout(function () {
    document.querySelectorAll('.flash').forEach(function (f) { f.classList.add('fade'); });
  }, 6000);

  // 6. Client-side form validation ----------------------------------------
  document.querySelectorAll('form[data-validate]').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      var valid = true;
      form.querySelectorAll('input, textarea, select').forEach(function (field) {
        clearError(field);
        if (field.hasAttribute('required') && !field.value.trim()) {
          showError(field, 'This field is required.'); valid = false; return;
        }
        var min = parseInt(field.getAttribute('minlength'), 10);
        if (min && field.value.trim().length && field.value.trim().length < min) {
          showError(field, 'Must be at least ' + min + ' characters.'); valid = false; return;
        }
        if (field.type === 'email' && field.value &&
            !/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(field.value)) {
          showError(field, 'Enter a valid email address.'); valid = false;
        }
      });
      var pwd = form.querySelector('#password, #new_password');
      var confirmPwd = form.querySelector('#confirm_password');
      if (pwd && confirmPwd && pwd.value !== confirmPwd.value) {
        showError(confirmPwd, 'Passwords do not match.'); valid = false;
      }
      if (!valid) { event.preventDefault(); }
    });
  });

  function showError(field, message) {
    field.classList.add('invalid');
    var note = document.createElement('small');
    note.className = 'error-note';
    note.textContent = message;
    field.parentElement.appendChild(note);
  }
  function clearError(field) {
    field.classList.remove('invalid');
    var note = field.parentElement.querySelector('.error-note');
    if (note) { note.remove(); }
  }

  // 7. Live search suggestions --------------------------------------------
  var search = document.getElementById('navSearch');
  var box = document.getElementById('suggestions');
  if (search && box) {
    var timer = null;
    search.addEventListener('input', function () {
      clearTimeout(timer);
      var term = search.value.trim();
      if (term.length < 2) { box.innerHTML = ''; box.classList.remove('open'); return; }
      timer = setTimeout(function () {
        fetch('/api/search-suggestions?q=' + encodeURIComponent(term))
          .then(function (r) { return r.json(); })
          .then(function (payload) {
            box.innerHTML = '';
            payload.results.forEach(function (item) {
              var li = document.createElement('li');
              var a = document.createElement('a');
              a.href = '/products/' + item.id;
              a.textContent = item.name;
              li.appendChild(a);
              box.appendChild(li);
            });
            box.classList.toggle('open', payload.results.length > 0);
          })
          .catch(function () { box.classList.remove('open'); });
      }, 220);
    });
    document.addEventListener('click', function (e) {
      if (!box.contains(e.target) && e.target !== search) { box.classList.remove('open'); }
    });
  }

  // 8. FAQ accordion -------------------------------------------------------
  document.querySelectorAll('.accordion-trigger').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      var item = trigger.parentElement;
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.accordion-item').forEach(function (i) {
        i.classList.remove('open');
      });
      if (!isOpen) { item.classList.add('open'); }
    });
  });

  // 9. Register page: swap customer/farmer fields --------------------------
  var roleInputs = document.querySelectorAll('input[name="role"]');
  var farmerFields = document.getElementById('farmerFields');
  var customerFields = document.getElementById('customerFields');
  if (roleInputs.length && farmerFields && customerFields) {
    roleInputs.forEach(function (input) {
      input.addEventListener('change', function () {
        var isFarmer = input.value === 'farmer' && input.checked;
        farmerFields.hidden = !isFarmer;
        customerFields.hidden = isFarmer;
      });
    });
  }

  // 10. Product gallery thumbnails ----------------------------------------
  var mainImage = document.getElementById('mainImage');
  document.querySelectorAll('.thumb').forEach(function (thumb) {
    thumb.addEventListener('click', function () {
      if (mainImage) { mainImage.src = thumb.src; }
    });
  });
})();
