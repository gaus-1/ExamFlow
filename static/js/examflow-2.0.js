// ExamFlow 2.0 runtime helpers
// Минимальный модуль, чтобы избежать 404 и проблем с Manifest
// Инициализация навигации и мелких интерактивов страницы
(function () {
  try {
    const scrollToId = (id) => {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    document.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href') || '';
        const id = href.replace('#', '');
        if (id) {
          e.preventDefault();
          scrollToId(id);
        }
      });
    });
  } catch (e) {
    // no-op
  }
})();


