from pathlib import Path
import csv
import json
import re
import requests


INPUT_DIR = Path("naver_results_2024-12-01_2026-09-15")
OUTPUT_DIR = Path("categorize_needs_results")

MODEL = "qwen3.5:27b"

OUTPUT_DIR.mkdir(exist_ok=True)


def split_reviews(text):
    """
    빈 줄을 기준으로 리뷰를 분리.
    실제 크롤링 txt 구조에 맞게 추후 수정 가능.
    """
    reviews = re.split(r"\n\s*\n+", text)

    return [
        review.strip()
        for review in reviews
        if review.strip()
    ]


def analyze_review(review):

    prompt = f"""
너는 음식점 고객 리뷰를 분석하는 연구 보조자다.

다음 리뷰를 분석하라.

[리뷰]
{review}

다음 기준을 반드시 따른다.

1. 긍정
고객이 좋았다고 평가한 요소.

2. 불만
고객이 불편하거나 아쉽다고 평가한 요소.

3. 중립·판단 불가
사실 설명만 있거나 평가 방향을 판단할 수 없는 내용.

4. 니즈
고객이 원하는 것 또는 리뷰 내용으로부터 합리적으로 추론할 수 있는 기대.

니즈는 반드시 다음 중 하나로 구분한다.

- 명시적 요구
- 추론한 가설
- 없음


[중요]

- 한 리뷰에서 여러 주제를 찾을 수 있다.
- 긍정과 불만은 동시에 존재할 수 있다.
- 서로 다른 평가 요소는 각각 별도의 항목으로 분리한다.
- 고객이 말하지 않은 구체적인 해결책을 임의로 만들지 않는다.
- 추론은 리뷰에서 직접 근거를 찾을 수 있을 때만 한다.
- 근거 원문은 반드시 원래 리뷰의 문장을 그대로 가져온다.
- 근거 원문을 요약하거나 수정하지 않는다.
- 정보가 부족하면 억지로 니즈를 만들지 않는다.

예시:

리뷰:
"겉은 바삭하고 맛있는데, 한 개로 점심을 먹기에는 조금 부족했어요."

결과:

{{
  "results": [
    {{
      "topic": "식감",
      "evaluation": "긍정",
      "evidence": "겉은 바삭하고",
      "need_type": "없음",
      "need": ""
    }},
    {{
      "topic": "맛",
      "evaluation": "긍정",
      "evidence": "맛있는데",
      "need_type": "없음",
      "need": ""
    }},
    {{
      "topic": "양·포만감",
      "evaluation": "불만",
      "evidence": "한 개로 점심을 먹기에는 조금 부족했어요",
      "need_type": "추론한 가설",
      "need": "한 끼 식사로 충분한 포만감을 기대할 가능성"
    }}
  ]
}}

반드시 JSON만 출력한다.

형식:

{{
  "results": [
    {{
      "topic": "",
      "evaluation": "긍정 | 불만 | 중립·판단 불가",
      "evidence": "",
      "need_type": "명시적 요구 | 추론한 가설 | 없음",
      "need": ""
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

        print(
            f"[{review_index}/{len(reviews)}] 분석 중..."
        )

        try:

            result = analyze_review(review)

            for item in result.get("results", []):

                rows.append({
                    "source_file": file_path.name,
                    "review_id": review_index,
                    "original_review": review,
                    "topic": item.get("topic", ""),
                    "evaluation": item.get(
                        "evaluation",
                        ""
                    ),
                    "evidence": item.get(
                        "evidence",
                        ""
                    ),
                    "need_type": item.get(
                        "need_type",
                        ""
                    ),
                    "need": item.get(
                        "need",
                        ""
                    )
                })

        except Exception as e:

            print(f"분석 실패: {e}")

            rows.append({
                "source_file": file_path.name,
                "review_id": review_index,
                "original_review": review,
                "topic": "분석 실패",
                "evaluation": "",
                "evidence": "",
                "need_type": "",
                "need": str(e)
            })

    return rows


def save_csv(rows, output_path):

    fieldnames = [
        "source_file",
        "review_id",
        "original_review",
        "topic",
        "evaluation",
        "evidence",
        "need_type",
        "need"
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
            / f"{file_path.stem}_analysis.csv"
        )

        save_csv(
            rows,
            output_path
        )

        print(
            f"저장 완료: {output_path}"
        )

    save_csv(
        all_rows,
        OUTPUT_DIR / "all_reviews_analysis.csv"
    )

    print("\n전체 분석 완료")


if __name__ == "__main__":
    main()