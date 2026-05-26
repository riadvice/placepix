// Common JavaScript functions shared across pages

// Language dropdown click handler
document.addEventListener('click', function(e) {
  var sel = document.getElementById('lang-selector');
  var dd  = document.getElementById('lang-dropdown');
  if (sel && dd && !sel.contains(e.target)) {
    dd.classList.remove('lang-dd-open');
    var btn = document.getElementById('lang-trigger');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }
});

// Mobile nav toggle
document.addEventListener('DOMContentLoaded', function() {
  var toggle = document.getElementById('nav-toggle');
  var nav = document.getElementById('site-nav');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', function(e) {
    e.preventDefault();
    var open = nav.classList.toggle('nav-mobile-open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  document.addEventListener('click', function(e) {
    if (!nav.classList.contains('nav-mobile-open')) return;
    if (nav.contains(e.target)) return;
    nav.classList.remove('nav-mobile-open');
    toggle.setAttribute('aria-expanded', 'false');
  });
});

// Copy category URL to clipboard
function copyCategoryURL(category, event) {
  event.stopPropagation();
  const url = window.location.origin + '/' + category;
  navigator.clipboard.writeText(url).then(() => {
    Toastify({
      text: i18n.get('notification.copied') || "URL copied to clipboard!",
      duration: 3000,
      gravity: "top",
      position: "center",
      offset: { x: 0, y: 60 },
      style: {
        background: "linear-gradient(to right, #0284c7, #0ea5e9)",
      }
    }).showToast();
  }).catch(err => {
    console.error('Failed to copy:', err);
  });
}

// Copy code snippet to clipboard
function copyCode(button, code) {
  // If it's a Docker command, copy as-is without URL prefix
  const textToCopy = code.startsWith('docker') ? code : window.location.origin + code;
  const isDockerCommand = code.startsWith('docker');
  navigator.clipboard.writeText(textToCopy).then(() => {
    const originalIcon = button.innerHTML;
    button.innerHTML = '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
    setTimeout(() => {
      button.innerHTML = originalIcon;
    }, 1500);
    Toastify({
      text: isDockerCommand ? (i18n.get('notification.command_copied') || "Command copied to clipboard!") : (i18n.get('notification.copied') || "URL copied to clipboard!"),
      duration: 3000,
      gravity: "top",
      position: "center",
      offset: { x: 0, y: 60 },
      style: {
        background: "linear-gradient(to right, #0284c7, #0ea5e9)",
      }
    }).showToast();
  }).catch(err => {
    console.error('Failed to copy:', err);
  });
}

// Dark Mode Toggle
function toggleTheme() {
  const body = document.body;
  const currentTheme = body.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  body.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);

  // Update toggle icon
  const toggle = document.getElementById('theme-toggle');
  toggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

// Load saved theme
function loadTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.body.setAttribute('data-theme', savedTheme);
  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
  }
}

// Load theme on page load
loadTheme();
