document.addEventListener('DOMContentLoaded', () => {
  const tabDesktop = document.getElementById('tab-desktop');
  const tabDiscord = document.getElementById('tab-discord');
  const contentDesktop = document.getElementById('content-desktop');
  const contentDiscord = document.getElementById('content-discord');

  function switchTab(activeTab, inactiveTab, activeContent, inactiveContent) {
    inactiveTab.classList.remove('tab-active');
    activeTab.classList.add('tab-active');

    inactiveContent.classList.remove('tab-content-active');

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        activeContent.classList.add('tab-content-active');
      });
    });
  }

  tabDesktop.addEventListener('click', () => {
    switchTab(tabDesktop, tabDiscord, contentDesktop, contentDiscord);
  });

  tabDiscord.addEventListener('click', () => {
    switchTab(tabDiscord, tabDesktop, contentDiscord, contentDesktop);
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );

  document.querySelectorAll('#features .feature-card, #platforms .glass-card, #platforms .tab-content-wrapper').forEach((el) => {
    el.classList.add('scroll-fade-in');
    observer.observe(el);
  });
});
