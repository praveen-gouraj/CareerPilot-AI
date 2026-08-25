document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const storedTheme = localStorage.getItem('theme') || 'dark';
  body.setAttribute('data-theme', storedTheme);

  if (themeToggle) {
    themeToggle.innerHTML = storedTheme === 'light' ? '<i class="bi bi-moon-stars"></i>' : '<i class="bi bi-brightness-high"></i>';
    themeToggle.addEventListener('click', () => {
      const nextTheme = body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      body.setAttribute('data-theme', nextTheme);
      localStorage.setItem('theme', nextTheme);
      themeToggle.innerHTML = nextTheme === 'light' ? '<i class="bi bi-moon-stars"></i>' : '<i class="bi bi-brightness-high"></i>';
    });
  }

  const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
  const mobileSidebar = document.getElementById('mobileSidebar');
  const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
  const mobileCloseButtons = document.querySelectorAll('[data-mobile-menu-close]');

  const closeMobileMenu = () => {
    if (!mobileSidebar) return;
    mobileSidebar.classList.remove('open');
    mobileMenuOverlay?.classList.remove('show');
    body.classList.remove('mobile-menu-open');
    if (mobileMenuToggle) {
      mobileMenuToggle.setAttribute('aria-expanded', 'false');
    }
  };

  const openMobileMenu = () => {
    if (!mobileSidebar) return;
    mobileSidebar.classList.add('open');
    mobileMenuOverlay?.classList.add('show');
    body.classList.add('mobile-menu-open');
    if (mobileMenuToggle) {
      mobileMenuToggle.setAttribute('aria-expanded', 'true');
    }
  };

  if (mobileMenuToggle && mobileSidebar) {
    mobileMenuToggle.addEventListener('click', () => {
      const isOpen = mobileSidebar.classList.contains('open');
      if (isOpen) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });
  }

  mobileCloseButtons.forEach((button) => {
    button.addEventListener('click', closeMobileMenu);
  });

  if (mobileMenuOverlay) {
    mobileMenuOverlay.addEventListener('click', closeMobileMenu);
  }

  document.querySelectorAll('.mobile-sidebar .sidebar-link').forEach((link) => {
    link.addEventListener('click', closeMobileMenu);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeMobileMenu();
    }
  });

  document.querySelectorAll('.toast').forEach((toastElement) => {
    const toast = bootstrap.Toast.getOrCreateInstance(toastElement, { delay: 4200 });
    toast.show();
  });

  document.querySelectorAll('form[data-loading-form]').forEach((form) => {
    form.addEventListener('submit', () => {
      const overlay = document.getElementById('loadingOverlay');
      if (overlay) {
        overlay.classList.remove('d-none');
      }
    });
  });

  const assistantForm = document.getElementById('assistantForm');
  if (assistantForm) {
    assistantForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const input = assistantForm.querySelector('input[name="message"]');
      const message = input.value.trim();
      if (!message) return;

      const chatBody = document.getElementById('assistantMessages');
      const userBubble = document.createElement('div');
      userBubble.className = 'text-end mb-2';
      userBubble.innerHTML = `<span class="badge rounded-pill text-bg-primary">${message}</span>`;
      chatBody.appendChild(userBubble);

      const response = await fetch('/student/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      }).then((res) => res.json());

      const botBubble = document.createElement('div');
      botBubble.className = 'mb-2';
      botBubble.innerHTML = `<span class="badge rounded-pill text-bg-dark">${response.reply}</span>`;
      chatBody.appendChild(botBubble);
      input.value = '';
      chatBody.scrollTop = chatBody.scrollHeight;
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const assistantLink = document.getElementById("careerAssistantLink");
  const assistantWidget = document.getElementById("assistantWidget");

  if (!assistantLink || !assistantWidget) return;

  assistantLink.addEventListener("click", function (event) {
    event.preventDefault();

    assistantWidget.classList.toggle("assistant-open");
  });
});
