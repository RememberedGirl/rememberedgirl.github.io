'use strict';
const search = document.getElementById('player-search');
search?.addEventListener('input', () => {
  const query = search.value.trim().toLocaleLowerCase('ru');
  let visible = 0;
  for (const card of document.querySelectorAll('#player-grid [data-name]')) {
    card.hidden = !card.dataset.name.toLocaleLowerCase('ru').includes(query);
    if (!card.hidden) visible++;
  }
  document.getElementById('no-players').hidden = visible > 0;
});
