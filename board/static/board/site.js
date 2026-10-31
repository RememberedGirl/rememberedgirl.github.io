
'use strict';
const search = document.getElementById('player-search');
search?.addEventListener('input', () => {
  const query = search.value.trim().toLocaleLowerCase('ru');
  const matches = [];
  for (const card of document.querySelectorAll('#player-grid [data-name]')) {
    card.hidden = !card.dataset.name.toLocaleLowerCase('ru').includes(query);
    if (!card.hidden) matches.push(card);
  }
  document.getElementById('no-players').hidden = matches.length > 0;
  const results = document.getElementById('player-search-results');
  if (!results) return;
  results.replaceChildren();
  results.hidden = !query;
  if (!query) return;
  for (const card of matches.slice(0, 8)) {
    const source = card.matches('a[href]') ? card : card.querySelector('a[href]');
    if (!source) continue;
    const link = document.createElement('a');
    link.href = source.getAttribute('href');
    const name = document.createElement('strong');
    name.textContent = card.querySelector('strong,h3')?.textContent || source.textContent;
    const meta = document.createElement('span');
    const th = card.querySelector('.th-badge')?.textContent.trim();
    meta.textContent = (th ? 'ТХ ' + th + ' · ' : '') + 'Профиль ↗';
    link.append(name, meta); results.append(link);
  }
  if (!matches.length) results.textContent = 'Игрок с таким ником не найден.';
});
