"""실제 API 호출 없이 모의 응답으로 예시 결과를 재현한다."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import travel_planner as planner


def main():
    recommendation = {
        'recommended_city': '강릉',
        'weather': '모의 데이터: 가을에는 서늘할 수 있으며 실제 예보를 확인해야 합니다.',
        'events': ['모의 가을 지역 행사 후보 (개최 여부·일정 확인 필요)'],
        'reason': '가을 바다와 도심 산책을 함께 계획할 수 있습니다. 음식점과 관광지를 하루 동선으로 연결하기 좋습니다.',
    }
    report = '''# 2026-10-15 국내 여행 추천 리포트

> 모의 API 응답으로 만든 예시입니다. 실제 API 호출·검색 결과가 아닙니다.

## 추천 지역
강릉

## 추천 이유
가을 바다와 도심 산책을 함께 계획할 수 있습니다. 음식점과 관광지를 하루 동선으로 연결하기 좋습니다.

## 날씨 요약
일반적인 가을의 서늘한 날씨를 가정했습니다. 실제 예보는 별도로 확인하세요.

## 행사/축제
- 모의 가을 지역 행사 후보: 개최 여부·일정 확인 필요

## 맛집 추천
데이터 없음

## 1일 일정 제안
- 오전: 해변 산책
- 오후: 도심 관광과 지역 행사 개최 여부 확인
- 저녁: 현장에서 영업 중인 음식점 확인 후 식사
'''
    replies = [
        {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(recommendation, ensure_ascii=False)}]}}]},
        {'documents': []},
        {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': report}]}}]},
    ]
    errors = []
    with patch.object(planner, 'request_json', side_effect=replies) as transport:
        result = planner.recommend('2026-10-15', 'unused-mock-key', 'gemini-2.5-flash', errors)
        places = planner.search_places(result['recommended_city'], 'unused-mock-key', errors)
        data = {'travel_date': '2026-10-15', 'source': 'mock_api', 'note': '실제 API 호출 없음. 검색 0건 시 리포트 계속 생성하는 예시.', 'recommendation': result, 'places': places, 'errors': errors}
        markdown = planner.create_report(data, 'unused-mock-key', 'gemini-2.5-flash')
        assert transport.call_count == 3
    output = planner.BASE / 'results'
    output.mkdir(exist_ok=True)
    planner.save_data(output / 'sample_mock_raw.json', data, [])
    (output / 'sample_mock_travel_plan.md').write_text(markdown, encoding='utf-8')
    print('MOCK: 외부 API 호출 없이 추천 → 검색 0건 → 최종 리포트 생성 검증 완료')
    print('results/sample_mock_raw.json 및 sample_mock_travel_plan.md 저장')


if __name__ == '__main__':
    main()
