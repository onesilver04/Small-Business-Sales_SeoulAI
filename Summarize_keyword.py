import pandas as pd
from pathlib import Path


INPUT_FILE = Path("categorize_keyword_results/all_keywords_by_category.csv")

CATEGORY_SUMMARY_FILE = Path(
    "keyword_results/category_summary.csv"
)

TOPIC_FREQUENCY_FILE = Path(
    "keyword_results/topic_frequency.csv"
)


# =========================================================
# 기준 분류표
# =========================================================

CATEGORY_TOPICS = {
    "맛·제품": [
        "맛",
        "식감",
        "속 재료",
        "양·포만감",
        "온도",
        "메뉴별 평가",
    ],

    "가격·구성": [
        "가격 부담",
        "가성비",
        "세트",
        "사이드",
        "최소주문",
        "배달비",
    ],

    "서비스": [
        "응대",
        "메뉴 설명",
        "주문 처리",
        "누락 대응",
    ],

    "공간·접근성": [
        "좌석",
        "청결",
        "분위기",
        "위치",
        "매장 찾기",
    ],

    "운영": [
        "영업시간",
        "임시휴무",
        "품절",
        "대기시간",
    ],

    "배달·포장": [
        "도착 상태",
        "눅눅함",
        "파손",
        "포장",
        "누락",
        "배송 지연",
    ],

    "이용 상황·구매동기": [
        "공강",
        "점심",
        "간식",
        "식사대용",
        "첫 방문",
        "재구매",
    ],

    "기타·판단 불가": [
        "기타·판단 불가",
    ],
}


# =========================================================
# topic 정규화 규칙
# =========================================================

TOPIC_MAPPING = {

    # 맛·제품
    "비프파이 맛": "메뉴별 평가",
    "비프칠리파이": "메뉴별 평가",
    "비프칠리파이 맛": "메뉴별 평가",
    "비프파이": "메뉴별 평가",
    "양송이파이": "메뉴별 평가",
    "양송이파이 맛": "메뉴별 평가",
    "시금치파이": "메뉴별 평가",
    "미트파이": "메뉴별 평가",
    "음료": "메뉴별 평가",
    "청포도에이드": "메뉴별 평가",

    "비프파이 식감": "식감",
    "비프칠리 식감": "식감",
    "바삭한 식감": "식감",

    "비프파이 내용물": "속 재료",

    "비프파이 포만감": "양·포만감",
    "양 부족": "양·포만감",

    # 가격·구성
    "배송비": "배달비",
    "비프파이 가격": "가격 부담",
    "쿠폰 할인": "가성비",
    "네이버 주문 할인": "가성비",
    "세트 구매 이벤트": "세트",
    "포장 음료 무료 제공": "세트",

    # 공간·접근성
    "매장 내부": "좌석",
    "공강": "공간·접근성",

    # 운영
    "운영 시간": "영업시간",
    "웨이팅 상황": "대기시간",

    # 배달·포장
    "패키징": "포장",
    "포장을 통한 편의성": "포장",

    # 이용 상황·구매동기
    "재구매 의향": "재구매",
}


# =========================================================
# topic 정규화 함수
# =========================================================

def normalize_topic(category, topic):

    category = str(category).strip()
    topic = str(topic).strip()

    # 정확한 mapping이 있으면 사용
    if topic in TOPIC_MAPPING:
        normalized = TOPIC_MAPPING[topic]

        # 잘못된 category 이동 방지
        if normalized == "공간·접근성":
            return "기타·판단 불가"

        return normalized

    # 이미 허용된 topic이면 그대로 사용
    valid_topics = CATEGORY_TOPICS.get(category, [])

    if topic in valid_topics:
        return topic

    # 문자열 패턴 기반 보정
    if category == "맛·제품":

        if "맛" in topic:
            return "맛"

        if "식감" in topic:
            return "식감"

        if (
            "재료" in topic
            or "내용물" in topic
            or "필링" in topic
        ):
            return "속 재료"

        if (
            "양" in topic
            or "포만" in topic
            or "사이즈" in topic
        ):
            return "양·포만감"

        if "온도" in topic:
            return "온도"

        if any(
            word in topic
            for word in [
                "파이",
                "에이드",
                "메뉴"
            ]
        ):
            return "메뉴별 평가"

    elif category == "가격·구성":

        if "가격" in topic:
            return "가격 부담"

        if (
            "할인" in topic
            or "쿠폰" in topic
            or "이벤트" in topic
        ):
            return "가성비"

        if "세트" in topic:
            return "세트"

        if "배달비" in topic or "배송비" in topic:
            return "배달비"

        if "최소주문" in topic:
            return "최소주문"

    elif category == "서비스":

        if "설명" in topic:
            return "메뉴 설명"

        if "주문" in topic:
            return "주문 처리"

        if "누락" in topic:
            return "누락 대응"

        if "응대" in topic or "친절" in topic:
            return "응대"

    elif category == "공간·접근성":

        if "좌석" in topic or "내부" in topic:
            return "좌석"

        if "청결" in topic:
            return "청결"

        if "분위기" in topic:
            return "분위기"

        if "찾기" in topic:
            return "매장 찾기"

        if "위치" in topic:
            return "위치"

    elif category == "운영":

        if "영업" in topic or "운영 시간" in topic:
            return "영업시간"

        if "휴무" in topic:
            return "임시휴무"

        if "품절" in topic:
            return "품절"

        if (
            "대기" in topic
            or "웨이팅" in topic
        ):
            return "대기시간"

    elif category == "배달·포장":

        if "도착" in topic:
            return "도착 상태"

        if "눅눅" in topic:
            return "눅눅함"

        if "파손" in topic:
            return "파손"

        if (
            "포장" in topic
            or "패키징" in topic
        ):
            return "포장"

        if "누락" in topic:
            return "누락"

        if (
            "배송" in topic
            or "지연" in topic
        ):
            return "배송 지연"

    elif category == "이용 상황·구매동기":

        if "공강" in topic:
            return "공강"

        if "점심" in topic:
            return "점심"

        if "간식" in topic:
            return "간식"

        if "식사" in topic:
            return "식사대용"

        if "첫" in topic:
            return "첫 방문"

        if (
            "재구매" in topic
            or "재방문" in topic
        ):
            return "재구매"

    return "기타·판단 불가"


# =========================================================
# category 요약
# =========================================================

def create_category_summary(df):

    rows = []

    for category, topics in CATEGORY_TOPICS.items():

        category_df = df[
            df["category"] == category
        ]

        rows.append({
            "대분류": category,
            "세부 주제": ", ".join(topics),
            "추출 건수": len(category_df),
            "등장 문서 수": (
                category_df["source_file"]
                .dropna()
                .nunique()
            ),
        })

    return pd.DataFrame(rows)


# =========================================================
# 세부 주제별 빈도
# =========================================================

def create_topic_frequency(df):

    rows = []

    for category, topics in CATEGORY_TOPICS.items():

        for topic in topics:

            topic_df = df[
                (df["category"] == category)
                & (df["normalized_topic"] == topic)
            ]

            rows.append({
                "대분류": category,
                "세부 주제": topic,
                "추출 건수": len(topic_df),
                "등장 문서 수": (
                    topic_df["source_file"]
                    .dropna()
                    .nunique()
                ),
            })

    result = pd.DataFrame(rows)

    return result


# =========================================================
# 실행
# =========================================================

def main():

    df = pd.read_csv(INPUT_FILE)

    # 앞뒤 공백 제거
    df["category"] = (
        df["category"]
        .astype(str)
        .str.strip()
    )

    df["topic"] = (
        df["topic"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # topic 정규화
    df["normalized_topic"] = df.apply(
        lambda row: normalize_topic(
            row["category"],
            row["topic"]
        ),
        axis=1
    )


    # -----------------------------------------
    # 1. 대분류 요약
    # -----------------------------------------

    category_summary = create_category_summary(df)

    category_summary.to_csv(
        CATEGORY_SUMMARY_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # -----------------------------------------
    # 2. 세부 주제별 빈도
    # -----------------------------------------

    topic_frequency = create_topic_frequency(df)

    topic_frequency.to_csv(
        TOPIC_FREQUENCY_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # -----------------------------------------
    # 터미널 출력
    # -----------------------------------------

    print("\n==============================")
    print("대분류 요약")
    print("==============================\n")

    print(
        category_summary.to_string(
            index=False
        )
    )


    print("\n\n==============================")
    print("세부 주제별 빈도")
    print("==============================\n")

    print(
        topic_frequency.to_string(
            index=False
        )
    )


    print("\n저장 완료:")
    print(f"- {CATEGORY_SUMMARY_FILE}")
    print(f"- {TOPIC_FREQUENCY_FILE}")


if __name__ == "__main__":
    main()