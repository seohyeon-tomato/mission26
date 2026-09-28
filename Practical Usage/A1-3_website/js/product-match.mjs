const normalize = value => String(value ?? '').trim().replace(/\s+/g, ' ');

export async function requestCandidate(input, { signal } = {}) {
  const response = await fetch('/api/product_match', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input), signal,
  });
  let result;
  try { result = await response.json(); }
  catch { throw new Error('AI 응답을 읽지 못했어요. 잠시 후 다시 시도해 주세요.'); }
  if (!response.ok) throw new Error(result?.error?.message || '제품 후보를 가져오지 못했어요. 다시 시도해 주세요.');
  const candidate = result.candidate;
  if (!candidate || typeof candidate.name !== 'string' || !candidate.name.trim() ||
      candidate.name.length > 120 || typeof candidate.options !== 'string' || candidate.options.length > 120 ||
      typeof candidate.searchQuery !== 'string' || !candidate.searchQuery.trim() || candidate.searchQuery.length > 240) {
    throw new Error('제품 후보 형식이 올바르지 않아요. 다시 시도해 주세요.');
  }
  return { name: candidate.name, options: candidate.options, searchQuery: candidate.searchQuery };
}

// 아이템 하나마다 인스턴스를 생성. 동일 입력 캐시와 오래된 응답 차단을 함께 처리한다.
export function createProductMatcher({ onState, request = requestCandidate, delay = 900, timeout = 25000 }) {
  let timer, controller, generation = 0, current = null, state = { status: 'empty' }, disposed = false;
  const cache = new Map();
  const emit = next => { state = next; onState({ ...next }); };
  function cancel() { clearTimeout(timer); controller?.abort(); generation++; }
  async function run(key, input, version) {
    if (version !== generation || disposed) return;
    controller = new AbortController();
    const ownController = controller;
    const stop = setTimeout(() => ownController.abort(), timeout);
    emit({ status: 'loading' });
    try {
      const candidate = await request(input, { signal: ownController.signal });
      if (version !== generation || disposed) return;
      if (ownController.signal.aborted) throw new Error('응답이 늦어지고 있어요. 다시 시도해 주세요.');
      cache.set(key, { candidate });
      emit({ status: 'candidate', candidate });
    } catch (error) {
      if (version !== generation || disposed) return;
      const message = ownController.signal.aborted ? '응답이 늦어지고 있어요. 다시 시도해 주세요.' : error.message;
      cache.set(key, { error: message });
      emit({ status: 'error', message });
    } finally { clearTimeout(stop); }
  }
  return {
    update(productName, options = '') {
      if (disposed) return;
      const input = { productName: normalize(productName), options: normalize(options) };
      const key = JSON.stringify(input);
      if (current?.key === key) return;
      cancel(); current = { key, input };
      if (!input.productName) return emit({ status: 'empty', message: '상품명을 입력해 주세요.' });
      if (input.productName.length > 120 || input.options.length > 120) return emit({ status: 'invalid', message: '상품명과 옵션은 각각 120자 이하로 입력해 주세요.' });
      const previous = cache.get(key);
      if (previous) return emit(previous.error ? { status: 'error', message: previous.error } : { status: 'candidate', candidate: previous.candidate });
      emit({ status: 'waiting' });
      const version = generation;
      timer = setTimeout(() => run(key, input, version), delay);
    },
    retry() {
      if (disposed || !current || state.status !== 'error') return;
      cancel(); cache.delete(current.key);
      return run(current.key, current.input, generation);
    },
    confirm() {
      if (state.status !== 'candidate') throw new Error('제품 후보를 먼저 확인해 주세요.');
      const item = { ...current.input, ...state.candidate, confirmed: true };
      emit({ status: 'confirmed', candidate: state.candidate, item });
      return item;
    },
    getConfirmed() { return state.status === 'confirmed' ? { ...state.item } : null; },
    dispose() { disposed = true; cancel(); cache.clear(); },
  };
}
