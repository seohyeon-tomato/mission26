import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore, shoppingUrl, STORAGE_KEY } from '../js/storage.mjs';
import { createProductMatcher, requestCandidate } from '../js/product-match.mjs';

const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const candidate = { name: '리본 파우치', options: '분홍', searchQuery: '리본 파우치 분홍' };
const post = () => ({ id: 'test-id', title: '오늘의 가방', description: '', createdAt: '2026-09-28T00:00:00Z', photo: 'data:image/jpeg;base64,YQ==', items: [{ productName: '파우치', ...candidate, confirmed: true }] });
function memory() {
  const values = new Map();
  return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
}

test('저장 후 새 인스턴스로 읽어도 기록 유지; 잘못된 ID는 null', () => {
  const storage = memory(); createStore(storage).add(post());
  assert.deepEqual(createStore(storage).find('test-id'), post());
  assert.equal(createStore(storage).find('missing'), null);
});
test('손상된 데이터는 덮어쓰지 않는다', () => {
  const storage = memory(); storage.setItem(STORAGE_KEY, '{bad');
  assert.throws(() => createStore(storage).add(post()), /보존/);
  assert.equal(storage.getItem(STORAGE_KEY), '{bad');
});
test('용량 초과 시 저장 실패 전달', () => {
  const storage = { getItem: () => null, setItem: () => { throw new Error('quota'); } };
  assert.throws(() => createStore(storage).add(post()), /저장 공간/);
});
test('확인되지 않은 아이템은 저장 불가', () => {
  const value = post(); value.items[0].confirmed = false;
  assert.throws(() => createStore(memory()).add(value), /확인/);
});
test('쇼핑 링크는 한글과 특수문자를 정확히 인코딩', () => {
  const query = '가방 & 리본 #분홍';
  const url = new URL(shoppingUrl(query));
  assert.equal(url.origin, 'https://search.shopping.naver.com');
  assert.equal(url.searchParams.get('query'), query);
});
test('연속 입력은 최종 입력 1회 호출, 동일 값 재입력 캐시, 변경 시 확인 해제', async () => {
  const calls = [];
  const matcher = createProductMatcher({ delay: 5, onState() {}, request: async input => { calls.push(input); return candidate; } });
  matcher.update('리'); matcher.update('리본'); matcher.update('리본 파우치', '분홍');
  await pause(25); assert.equal(calls.length, 1);
  assert.equal(matcher.confirm().confirmed, true);
  matcher.update(' 리본   파우치 ', '분홍');
  assert.ok(matcher.getConfirmed());
  matcher.update('다른 파우치'); assert.equal(matcher.getConfirmed(), null);
  matcher.update('리본 파우치', '분홍'); await pause(25);
  assert.equal(calls.length, 1); assert.equal(matcher.getConfirmed(), null);
  matcher.dispose();
});
test('변경 전 요청의 늦은 응답은 무시', async () => {
  const pending = []; let latest;
  const matcher = createProductMatcher({ delay: 1, onState: value => { latest = value; }, request: () => new Promise(resolve => pending.push(resolve)) });
  matcher.update('처음'); await pause(10);
  matcher.update('최종'); await pause(10);
  pending[1]({ ...candidate, name: '최종' }); await pause(1);
  pending[0]({ ...candidate, name: '처음' }); await pause(1);
  assert.equal(latest.candidate.name, '최종'); matcher.dispose();
});
test('빈 입력은 호출하지 않음; 오류 후 자동 재시도 없음, 명시적 재시도만 허용', async () => {
  let calls = 0; let latest;
  const matcher = createProductMatcher({ delay: 1, onState: value => { latest = value; }, request: async () => { calls++; throw new Error('API 오류'); } });
  matcher.update(' '); await pause(10); assert.equal(calls, 0);
  matcher.update('파우치'); await pause(10); assert.equal(latest.status, 'error');
  matcher.update('파우치'); await pause(10); assert.equal(calls, 1);
  await matcher.retry(); assert.equal(calls, 2); matcher.dispose();
});
test('시간 초과 안내', async () => {
  let latest;
  const matcher = createProductMatcher({ delay: 1, timeout: 5, onState: value => { latest = value; }, request: (_, { signal }) => new Promise((resolve, reject) => signal.addEventListener('abort', () => reject(new Error('aborted')))) });
  matcher.update('파우치'); await pause(25);
  assert.equal(latest.status, 'error'); assert.match(latest.message, /늦어/); matcher.dispose();
});
test('fetch는 서버 엔드포인트만 호출하고 후보 계약을 검증', async t => {
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    assert.equal(url, '/api/product_match');
    assert.equal(init.headers.Authorization, undefined);
    assert.equal(JSON.parse(init.body).productName, '파우치');
    return { ok: true, json: async () => ({ candidate }) };
  });
  assert.deepEqual(await requestCandidate({ productName: '파우치', options: '' }), candidate);
});
