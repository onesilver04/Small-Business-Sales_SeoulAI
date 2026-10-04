import pandas as pd
import requests
import json
from pathlib import Path


INPUT_FILE = Path("keyword_results/all_reviews_keywords.csv")
OUTPUT_FILE = Path("keyword_results/opinion_summary.csv")

MODEL = "qwen3:4b"


# 분석할 표준 세부 주제
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


def analyze_opinions(category, topic, expressions):

    # 너무 많은 경우 모델 context가 길어지는 것을 방지
    expressions = expressions[:150]

    review_text = "\n".join(
        f"- {text}"
        for text in expressions
        if isinstance(text, str) and text.strip()
    )

    prompt = f"""
You are analyzing customer opinions from restaurant reviews.

The following review expressions all belong to:

Major category: {category}
Subtopic: {topic}

[Review expressions]

{review_text}


Your task is to identify the recurring customer opinions expressed in these texts.

Follow these rules carefully:

1. Group expressions that communicate the same or very similar opinion.
2. Do NOT simply list individual review sentences.
3. Summarize each recurring opinion in Korean.
4. Classify each opinion into exactly one of:
   - 긍정
   - 불만
   - 요구
   - 중립
5. Do not invent opinions that are not supported by the review expressions.
6. Separate conflicting opinions.
   For example:
   - "The portion is large enough for a meal."
   - "One pie is not enough."
   These must be treated as two separate opinions.
7. Count approximately how many review expressions support each opinion.
8. Include up to 3 representative expressions exactly as they appear in the input.
9. Focus on meaningful customer experiences rather than factual metadata.
   For example, an address or opening-hour listing alone should not be treated
   as a customer opinion unless it contains an evaluation.
10. If there is no meaningful opinion for this subtopic, return an empty list.

Return JSON only.

Format:

{{
  "opinions": [
    {{
      "opinion_type": "긍정 | 불만 | 요구 | 중립",
      "opinion": "한국어로 요약한 주요 고객 의견",
      "count": 0,
      "evidence": [
        "원문 표현 1",
        "원문 표현 2"
      ]
    }}
  ]
}}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        },
        timeout=300
    )

    response.raise_for_status()

    result = response.json()["response"]

    return json.loads(result)


def main():

    df = pd.read_csv(INPUT_FILE)

    df["category"] = (
        df["category"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["topic"] = (
        df["topic"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["original_expression"] = (
        df["original_expression"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    rows = []

    for category, topics in CATEGORY_TOPICS.items():

        for topic in topics:

            subset = df[
                (df["category"] == category)
                & (df["topic"] == topic)
                & (df["original_expression"] != "")
            ]

            if subset.empty:
                continue

            expressions = (
                subset["original_expression"]
                .drop_duplicates()
                .tolist()
            )

            print(
                f"\n분석 중: {category} > {topic}"
                f" ({len(expressions)}개 표현)"
            )

            try:

                result = analyze_opinions(
                    category,
                    topic,
                    expressions
                )

                for opinion in result.get("opinions", []):

                    evidence = opinion.get(
                        "evidence",
                        []
                    )

                    rows.append({
                        "대분류": category,
                        "세부 주제": topic,
                        "의견 유형": opinion.get(
                            "opinion_type",
                            ""
                        ),
                        "주요 의견": opinion.get(
                            "opinion",
                            ""
                        ),
                        "언급 수": opinion.get(
                            "count",
                            0
                        ),
                        "근거 예시": " | ".join(evidence)
                    })

            except Exception as e:

                print(
                    f"분석 실패: {category} > {topic}"
                )

                print(e)

    result_df = pd.DataFrame(rows)

    if not result_df.empty:

        result_df = result_df.sort_values(
            ["대분류", "세부 주제", "언급 수"],
            ascending=[True, True, False]
        )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n분석 완료")
    print(f"저장 위치: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()