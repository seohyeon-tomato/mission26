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


def get_non_empty_input(message):
    """빈 문자열이 아닌 값이 입력될 때까지 다시 요청한다."""
    while True:
        value = input(message).strip()
        if value:
            return value
        print("입력값은 비워둘 수 없습니다. 다시 입력해 주세요.")


def add_prompt(prompts):
    """사용자에게 정보를 입력받아 새 프롬프트를 추가한다."""
    print("\n--- 프롬프트 추가 ---")
    title = get_non_empty_input("제목: ")
    content = get_non_empty_input("내용: ")
    category = get_non_empty_input("카테고리: ")

    prompts.append(
        {
            "title": title,
            "content": content,
            "category": category,
            "favorite": False,
        }
    )
    print("프롬프트가 추가되었습니다!")


def show_prompt_list(prompts):
    """저장된 프롬프트의 제목과 카테고리를 목록으로 출력한다."""
    print("\n--- 프롬프트 목록 ---")
    if not prompts:
        print("저장된 프롬프트가 없습니다.")
        return

    for index, prompt in enumerate(prompts, start=1):
        star = "★" if prompt["favorite"] else "☆"
        print(f'{index}. {star} [{prompt["category"]}] {prompt["title"]}')


def show_by_category(prompts):
    """선택한 카테고리에 속한 프롬프트만 출력한다."""
    categories = sorted({prompt["category"] for prompt in prompts})
    if not categories:
        print("등록된 카테고리가 없습니다.")
        return

    print("\n--- 카테고리 선택 ---")
    for index, category in enumerate(categories, start=1):
        print(f"{index}. {category}")

    selected = input("카테고리 번호: ").strip()
    if not selected.isdigit() or not 1 <= int(selected) <= len(categories):
        print("올바른 카테고리 번호를 입력해 주세요.")
        return

    category = categories[int(selected) - 1]
    filtered = [prompt for prompt in prompts if prompt["category"] == category]
    print(f"\n[{category}] 카테고리 프롬프트")
    show_prompt_list(filtered)


def main():
    """프로그램의 시작점."""
    prompts = create_default_prompts()
    print("=== 나만의 프롬프트 관리 ===")
    print(f"기본 프롬프트 {len(prompts)}개를 불러왔습니다.")

    while True:
        show_menu()
        choice = input("선택: ").strip()

        if choice == "1":
            add_prompt(prompts)
        elif choice == "2":
            show_prompt_list(prompts)
        elif choice == "3":
            show_by_category(prompts)
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("아직 준비 중인 기능입니다.")


if __name__ == "__main__":
    main()
