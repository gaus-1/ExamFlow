// Автоматическое переключение темы по времени суток (МСК)
(function () {
  try {
    var now = new Date();
    var mskString = now.toLocaleString('en-US', { timeZone: 'Europe/Moscow' });
    var msk = new Date(mskString);
    var hour = msk.getHours();
    var preferred = (hour >= 9 && hour < 21) ? 'light' : 'dark';

    // Если пользователь уже вручную переключал, не трогаем
    var userChoice = localStorage.getItem('user-theme');
    var themeToApply = userChoice || preferred;

    document.documentElement.setAttribute('data-theme', themeToApply);
    document.documentElement.dataset.theme = themeToApply;
    // Кешируем авто-выбор отдельно
    localStorage.setItem('preferred-theme', preferred);
  } catch (e) {
    // fail silently
  }
})();
