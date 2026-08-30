"""나만의 프롬프트 관리 프로그램."""


def create_default_prompts():
    """프로그램 시작 시 사용할 기본 프롬프트 3개를 반환한다."""
    return [
        {
            "title": "블로그 글 작성 도우미",
            "content": "주어진 주제로 읽기 쉬운 블로그 글 초안을 작성해 주세요.",
            "category": "텍스트 생성",
            "favorite": False,
        },
        {
            "title": "제품 이미지 생성",
            "content": "제품이 돋보이는 깔끔한 광고 이미지를 생성해 주세요.",
            "category": "이미지 생성",
            "favorite": False,
        },
        {
            "title": "친절한 학습 튜터",
            "content": "비전공자도 이해할 수 있도록 예시와 함께 설명해 주세요.",
            "category": "페르소나",
            "favorite": True,
        },
    ]


def show_menu():
    """사용자가 선택할 수 있는 전체 메뉴를 출력한다."""
    print("\n=== 메뉴 ===")
    print("1. 프롬프트 추가")
    print("2. 프롬프트 목록")
    print("3. 카테고리별 조회")
    print("4. 프롬프트 검색")
    print("5. 프롬프트 상세 보기")
    print("6. 즐겨찾기 추가/해제")
    print("7. 즐겨찾기 목록")
    print("0. 종료")


def main():
    """프로그램의 시작점."""
    prompts = create_default_prompts()
    print("=== 나만의 프롬프트 관리 ===")
    print(f"기본 프롬프트 {len(prompts)}개를 불러왔습니다.")

    while True:
        show_menu()
        choice = input("선택: ").strip()

        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        print("아직 준비 중인 기능입니다.")


if __name__ == "__main__":
    main()
