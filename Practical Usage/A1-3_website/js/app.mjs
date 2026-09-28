import { createStore, shoppingUrl } from './storage.mjs';
import { createProductMatcher } from './product-match.mjs';

const $ = selector => document.querySelector(selector);
const node = (tag, text, className) => {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
};
const store = () => createStore(window.localStorage);
const demos = [
  ['demo-1', 'Sunday picnic bag', '햇빛 좋은 날 들고 나간 작은 것들.', '리본 파우치', '분홍'],
  ['demo-2', 'My weekday pouch', '출근할 때 꼭 챙기는 현실 파우치.', '무선 이어폰', '화이트'],
  ['demo-3', 'tiny travel things', '1박 2일이면 이 정도면 충분해.', '여행용 수첩', '크림'],
].map(([id, title, description, name, options]) => ({ id, title, description, demo: true, items: [{name, options, searchQuery: `${name} ${options}`}] }));

function photo(post, className = 'photo') {
  const wrapper = node('div', undefined, className);
  if (post.photo) {
    wrapper.classList.add('has-image');
    const image = node('img'); image.src = post.photo; image.alt = post.title; image.loading = 'lazy';
    wrapper.append(image);
  } else {
    wrapper.setAttribute('role', 'img'); wrapper.setAttribute('aria-label', '예시 가방 일러스트');
    if (post.id === 'demo-2') wrapper.style.background = '#e8f8c9';
    if (post.id === 'demo-3') wrapper.style.background = '#f8dfc7';
  }
  return wrapper;
}
function card(post) {
  const article = node('article', undefined, 'bag-card');
  const a = node('a', undefined, 'card-link'); a.href = `detail.html?id=${encodeURIComponent(post.id)}`;
  a.append(photo(post), node('h3', post.title), node('p', post.description));
  article.append(node('span', `${post.items.length} ITEMS`, 'card-sticker'), a,
    node('div', post.demo ? '예시 기록 · 실제 사용자 게시물 아님' : '나의 기록 · 이 브라우저에 저장됨', 'meta'));
  return article;
}
function feed() {
  const list = $('#feed-list');
  try {
    const posts = store().list();
    list.replaceChildren(...posts.map(card), ...demos.map(card));
    $('#page-status').textContent = posts.length ? `내 기록 ${posts.length}개와 예시 기록이에요.` : '아직 내 기록이 없어요. 예시를 구경하고 첫 가방을 올려보세요.';
  } catch (error) { $('#page-status').textContent = error.message; }
}
function detail() {
  const area = $('#detail-content');
  try {
    const id = new URLSearchParams(location.search).get('id');
    const post = demos.find(value => value.id === id) || store().find(id);
    if (!post) throw new Error('기록을 찾을 수 없어요. 이 브라우저에 저장된 기록인지 확인해 주세요.');
    const visual = node('section', undefined, 'panel');
    visual.append(node('span', post.demo ? 'SAMPLE BAG' : 'MY LITTLE THINGS', 'eyebrow'), node('h1', post.title), photo(post, 'photo detail-photo'), node('p', post.description));
    const items = node('section', undefined, 'panel'); items.append(node('h2', 'little things inside ♡'));
    for (const [index, item] of post.items.entries()) {
      const box = node('div', undefined, 'item-box');
      const a = node('a', '제품 찾아보기 ↗', 'btn secondary'); a.href = shoppingUrl(item.searchQuery); a.target = '_blank'; a.rel = 'noopener noreferrer';
      box.append(node('span', `ITEM ${index + 1}`, 'item-tag'), node('h3', item.name), node('p', item.options || '옵션 없음'), a);
      items.append(box);
    }
    items.append(node('p', post.demo ? '서비스 이용 흐름을 보여주는 예시예요. 검색어도 예시입니다.' : '확인해 둔 검색어로 네이버 쇼핑을 열어요. 검색 결과는 실제 제품과 다를 수 있어요.', 'scrap-note'));
    area.classList.add('detail-layout');
    area.replaceChildren(visual, items);
  } catch (error) {
    const panel = node('section', undefined, 'panel'); const a = node('a', 'FEED로 돌아가기', 'btn'); a.href = 'index.html';
    panel.append(node('h1', '기록을 찾을 수 없어요'), node('p', error.message), a); area.replaceChildren(panel);
  } finally { area.setAttribute('aria-busy', 'false'); }
}

async function compressPhoto(file) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) throw new Error('JPG, PNG, WebP 사진을 선택해 주세요.');
  if (file.size > 12 * 1024 * 1024) throw new Error('사진은 12MB 이하로 선택해 주세요.');
  const url = URL.createObjectURL(file);
  try {
    const image = new Image(); image.src = url; await image.decode();
    if (image.width * image.height > 50000000) throw new Error('사진 해상도가 너무 커요. 크기를 줄여 주세요.');
    const scale = Math.min(1, 1200 / Math.max(image.width, image.height));
    const canvas = document.createElement('canvas'); canvas.width = Math.round(image.width * scale); canvas.height = Math.round(image.height * scale);
    const context = canvas.getContext('2d'); context.fillStyle = '#fff'; context.fillRect(0, 0, canvas.width, canvas.height); context.drawImage(image, 0, 0, canvas.width, canvas.height);
    for (const quality of [0.82, 0.65, 0.45]) {
      const data = canvas.toDataURL('image/jpeg', quality);
      if (data.length <= 700000) return data;
    }
    throw new Error('사진 용량이 커요. 더 작은 사진을 선택해 주세요.');
  } finally { URL.revokeObjectURL(url); }
}
function upload() {
  const rows = []; let sequence = 0, photoData = '', imageVersion = 0, processing = false;
  function preview() {
    $('#preview-title').textContent = $('#post-title').value || '나의 작은 취향';
    $('#preview-description').textContent = $('#post-description').value || '어떤 물건을 챙겼나요?';
    $('#preview-items').replaceChildren(...rows.map(row => {
      const confirmed = row.matcher.getConfirmed();
      return node('div', confirmed ? `${confirmed.name} · ${confirmed.options} ✓` : `${row.name.value || '새 아이템'} · 확인 전`, 'mock-item');
    }));
    $('#add-item').disabled = rows.length >= 10;
    for (const row of rows) row.element.querySelector('[data-remove]').disabled = rows.length <= 1;
  }
  function addItem() {
    if (rows.length >= 10) return;
    const element = $('#item-template').content.firstElementChild.cloneNode(true);
    const name = element.querySelector('[data-name]'), options = element.querySelector('[data-options]');
    const rowId = ++sequence;
    name.id = `name-${rowId}`; options.id = `options-${rowId}`;
    element.querySelector('[data-name-label]').htmlFor = name.id;
    element.querySelector('[data-options-label]').htmlFor = options.id;
    element.querySelector('.item-tag').textContent = `ITEM ${String(rowId).padStart(2, '0')}`;
    const row = { element, name, options };
    row.matcher = createProductMatcher({ onState(state) {
      const messages = { empty: '상품명을 입력하면 AI가 검색 후보를 정리해요.', waiting: '입력이 끝나면 확인할게요…', loading: '제품 후보를 정리하고 있어요…', candidate: '이 제품 맞아요? 확인한 후 저장해 주세요.', confirmed: '확인했어요 ♡' };
      element.querySelector('[data-state]').textContent = state.message || messages[state.status] || '';
      const candidateBox = element.querySelector('[data-candidate]'); candidateBox.hidden = !state.candidate;
      candidateBox.replaceChildren();
      if (state.candidate) candidateBox.append(node('strong', state.candidate.name), node('div', state.candidate.options), node('div', `검색어: ${state.candidate.searchQuery}`));
      element.querySelector('[data-confirm]').hidden = state.status !== 'candidate';
      element.querySelector('[data-edit]').hidden = !['candidate', 'confirmed'].includes(state.status);
      element.querySelector('[data-retry]').hidden = state.status !== 'error';
      preview();
    }});
    rows.push(row); $('#items').append(element);
    for (const input of [name, options]) input.addEventListener('input', () => { row.matcher.update(name.value, options.value); preview(); });
    element.querySelector('[data-confirm]').addEventListener('click', () => row.matcher.confirm());
    element.querySelector('[data-edit]').addEventListener('click', () => { name.focus(); name.select(); });
    element.querySelector('[data-retry]').addEventListener('click', () => row.matcher.retry());
    element.querySelector('[data-remove]').addEventListener('click', () => {
      if (rows.length <= 1) return;
      row.matcher.dispose(); rows.splice(rows.indexOf(row), 1); element.remove(); preview();
    });
    row.matcher.update('', ''); preview();
    if (rows.length > 1) name.focus();
  }
  $('#add-item').addEventListener('click', addItem);
  $('#post-title').addEventListener('input', preview); $('#post-description').addEventListener('input', preview);
  $('#photo-input').addEventListener('change', async event => {
    const version = ++imageVersion; photoData = ''; processing = true; $('#save-post').disabled = true;
    $('#preview-photo').replaceChildren(); $('#preview-photo').classList.remove('has-image');
    try {
      const file = event.target.files[0];
      if (!file) { $('#photo-status').textContent = '사진을 선택해 주세요.'; return; }
      $('#photo-status').textContent = '사진 크기를 정리하고 있어요…';
      const data = await compressPhoto(file);
      if (version !== imageVersion) return;
      photoData = data;
      const image = node('img'); image.src = data; image.alt = '선택한 사진 미리보기';
      $('#preview-photo').classList.add('has-image'); $('#preview-photo').append(image);
      $('#photo-status').textContent = '사진을 준비했어요.';
    } catch (error) { if (version === imageVersion) $('#photo-status').textContent = error.name === 'EncodingError' ? '사진을 읽지 못했어요. 다른 JPG 또는 PNG 사진을 선택해 주세요.' : error.message; }
    finally { if (version === imageVersion) { processing = false; $('#save-post').disabled = false; } }
  });
  $('#upload-form').addEventListener('submit', event => {
    event.preventDefault(); const status = $('#form-status');
    try {
      if (!$('#post-title').value.trim()) { $('#post-title').focus(); throw new Error('게시물 제목을 입력해 주세요.'); }
      if (processing || !photoData) throw new Error('사진을 먼저 선택해 주세요.');
      const items = rows.map(row => row.matcher.getConfirmed());
      if (items.some(item => !item)) throw new Error('모든 아이템의 AI 후보를 확인해 주세요.');
      const post = { id: crypto.randomUUID(), title: $('#post-title').value.trim(), description: $('#post-description').value.trim(), photo: photoData, items, createdAt: new Date().toISOString() };
      $('#save-post').disabled = true; store().add(post);
      window.location.href = `detail.html?id=${encodeURIComponent(post.id)}`;
    } catch (error) { status.textContent = error.message; $('#save-post').disabled = false; }
  });
  window.addEventListener('pagehide', event => { if (!event.persisted) rows.forEach(row => row.matcher.dispose()); });
  addItem(); preview();
}
({ feed, detail, upload }[document.body.dataset.page] || (() => {}))();
