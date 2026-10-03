from pathlib import Path
import csv
import json
import re
import requests


INPUT_DIR = Path("naver_results_2024-12-01_2026-09-15")
OUTPUT_DIR = Path("categorize_keyword_results")

MODEL = "qwen2.5:7b"

OUTPUT_DIR.mkdir(exist_ok=True)


def split_reviews(text):
    reviews = re.split(r"\n\s*\n+", text)

    return [
        review.strip()
        for review in reviews
        if review.strip()
    ]

def analyze_review(review):
    prompt = f"""
You are an assistant for analyzing topics and keywords in restaurant customer reviews.

Read the review below and extract topics and keywords using ONLY the predefined categories listed below.

[Category Guidelines]

1. 맛·제품
- 맛
- 식감
- 속 재료
- 양·포만감
- 온도
- 메뉴별 평가

2. 가격·구성
- 가격 부담
- 가성비
- 세트
- 사이드
- 최소주문
- 배달비

3. 서비스
- 응대
- 메뉴 설명
- 주문 처리
- 누락 대응

4. 공간·접근성
- 좌석
- 청결
- 분위기
- 위치
- 매장 찾기

5. 운영
- 영업시간
- 임시휴무
- 품절
- 대기시간

6. 배달·포장
- 도착 상태
- 눅눅함
- 파손
- 포장
- 누락
- 배송 지연

7. 이용 상황·구매동기
- 공강
- 점심
- 간식
- 식사대용
- 첫 방문
- 재구매

8. 기타·판단 불가
- Content that does not fit the categories above
- Content that is too ambiguous to interpret reliably


[Analysis Rules]

- Select one of the predefined major categories for each extracted item.
- Do not create new major categories.
- A single review may contain multiple topics.
- If a review contains multiple distinct topics, extract them as separate items.
- Use the provided subtopic labels whenever possible.
- "original_expression" must preserve the exact wording found in the original review.
- Do not paraphrase, summarize, or rewrite the original expression.
- "integrated_keyword" should normalize expressions with the same meaning into one representative keyword.
- The integrated keyword should be written in Korean.
- The category and topic labels should also be written exactly in Korean as defined above.
- Do not infer information that is not supported by the review.
- Do not create keywords based on assumptions.
- If the meaning is unclear or does not fit the predefined categories, classify it as "기타·판단 불가".
- Use integrated keywords at a level that allows similar expressions from multiple reviews to be grouped together.

[Normalization Examples]

"바삭해요"
"겉이 바삭함"
"바삭바삭해요"
→ "바삭한 식감"

"양이 적어요"
"한 개로는 부족해요"
"배가 안 차요"
→ "양 부족"

"또 먹고 싶어요"
"다음에 또 올게요"
"재방문하고 싶어요"
→ "재구매 의향"


[Review]

{review}


Return JSON only.

Use the following format:

{{
  "results": [
    {{
      "category": "대분류",
      "topic": "세부 주제",
      "original_expression": "Exact expression from the review",
      "integrated_keyword": "통합 키워드"
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

    result_text = response.json()["response"]

    return json.loads(result_text)


def analyze_file(file_path):

    print(f"\n분석 시작: {file_path.name}")

    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    reviews = split_reviews(text)

    print(f"리뷰 수: {len(reviews)}")

    rows = []

    for review_index, review in enumerate(reviews, start=1):

        print(f"[{review_index}/{len(reviews)}] 분석 중...")

        try:
            result = analyze_review(review)

            for item in result.get("results", []):

                rows.append({
                    "source_file": file_path.name,
                    "category": item.get("category", ""),
                    "topic": item.get("topic", ""),
                    "original_expression": item.get(
                        "original_expression",
                        ""
                    ),
                    "integrated_keyword": item.get(
                        "integrated_keyword",
                        ""
                    )
                })

        except Exception as e:

            print(f"분석 실패: {e}")

            rows.append({
                "source_file": file_path.name,
                "category": "기타·판단 불가",
                "topic": "분석 실패",
                "original_expression": "",
                "integrated_keyword": ""
            })

    return rows


def save_csv(rows, output_path):

    fieldnames = [
        "source_file",
        "category",
        "topic",
        "original_expression",
        "integrated_keyword"
    ]

    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)


def main():

    txt_files = sorted(
        INPUT_DIR.glob("*.txt")
    )

    if not txt_files:
        print("분석할 txt 파일이 없습니다.")
        return

    all_rows = []

    for file_path in txt_files:

        rows = analyze_file(file_path)

        all_rows.extend(rows)

        output_path = (
            OUTPUT_DIR
            / f"{file_path.stem}_keywords.csv"
        )

        save_csv(
            rows,
            output_path
        )

        print(f"저장 완료: {output_path}")

    save_csv(
        all_rows,
        OUTPUT_DIR / "all_reviews_keywords.csv"
    )

    print("\n전체 키워드 분석 완료")


if __name__ == "__main__":
    main()