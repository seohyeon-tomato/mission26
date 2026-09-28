// UI와 독립된 저장 계층. 화면에서는 반환값을 textContent로 표시한다.
export const STORAGE_KEY = 'slig.posts.v1';
const text = (value, max) => typeof value === 'string' && value.trim().length > 0 && value.length <= max;

export function validatePost(post) {
  if (!post || !text(post.id, 80) || !text(post.title, 100) ||
      typeof post.description !== 'string' || post.description.length > 2000 ||
      !text(post.createdAt, 40) || !Number.isFinite(Date.parse(post.createdAt)) ||
      typeof post.photo !== 'string' || post.photo.length > 700000 ||
      !/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+=*$/.test(post.photo) ||
      !Array.isArray(post.items) || post.items.length < 1 || post.items.length > 10) {
    throw new Error('기록 형식이 올바르지 않아요. 입력 내용을 확인해 주세요.');
  }
  for (const item of post.items) {
    if (!item || !text(item.productName, 120) || typeof item.options !== 'string' ||
        item.options.length > 120 || !text(item.name, 120) ||
        !text(item.searchQuery, 240) || item.confirmed !== true) {
      throw new Error('각 아이템의 제품 후보를 확인해 주세요.');
    }
  }
  return post;
}

export function createStore(storage) {
  function list() {
    let raw;
    try { raw = storage.getItem(STORAGE_KEY); }
    catch { throw new Error('브라우저 저장소에 접근할 수 없어요. 저장 허용 설정을 확인해 주세요.'); }
    if (raw === null) return [];
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || parsed.length > 100) throw new Error();
      parsed.forEach(validatePost);
      if (new Set(parsed.map(post => post.id)).size !== parsed.length) throw new Error();
      return parsed;
    } catch {
      throw new Error('저장된 기록을 읽지 못했어요. 기존 데이터는 보존했어요.');
    }
  }
  return {
    list,
    find: id => list().find(post => post.id === id) ?? null,
    add(post) {
      validatePost(post);
      const posts = list();
      if (posts.some(saved => saved.id === post.id)) throw new Error('이미 저장된 기록이에요.');
      if (posts.length >= 100) throw new Error('이 브라우저의 기록 개수 제한에 도달했어요.');
      try { storage.setItem(STORAGE_KEY, JSON.stringify([post, ...posts])); }
      catch { throw new Error('저장 공간이 부족하거나 저장이 차단됐어요. 사진 크기를 줄여 다시 시도해 주세요.'); }
      return post.id;
    },
  };
}

export function shoppingUrl(searchQuery) {
  if (!text(searchQuery, 240)) throw new Error('저장된 검색어가 없어요.');
  return `https://search.shopping.naver.com/search/all?query=${encodeURIComponent(searchQuery.trim())}`;
}
