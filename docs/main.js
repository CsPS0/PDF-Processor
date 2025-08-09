const tabOCR = document.getElementById('tab-ocr');
const tabDiscord = document.getElementById('tab-discord');
const contentOCR = document.getElementById('content-ocr');
const contentDiscord = document.getElementById('content-discord');

tabOCR.addEventListener('click', () => {
  tabOCR.classList.add('tab-active');
  tabDiscord.classList.remove('tab-active');
  contentOCR.classList.remove('hidden');
  contentDiscord.classList.add('hidden');
});

tabDiscord.addEventListener('click', () => {
  tabDiscord.classList.add('tab-active');
  tabOCR.classList.remove('tab-active');
  contentDiscord.classList.remove('hidden');
  contentOCR.classList.add('hidden');
});
