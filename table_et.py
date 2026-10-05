from pathlib import Path
import pandas as pd
import requests
import json


INPUT_FILE = Path(
    "everytime_results/everytime_sentiment.csv"
)

OUTPUT_DIR = Path("everytime_results")

POSITIVE_FILE = OUTPUT_DIR / "positive_summary.csv"
NEGATIVE_FILE = OUTPUT_DIR / "negative_summary.csv"

MODEL = "qwen2.5:7b"

OUTPUT_DIR.mkdir(exist_ok=True)


def summarize_sentiment(df, sentiment):

    subset = df[
        df["sentiment"] == sentiment
    ].copy()

    if subset.empty:
        return []

    opinions = []

    for _, row in subset.iterrows():

        opinion = str(
            row.get("opinion", "")
        ).strip()

        evidence = str(
            row.get("evidence", "")
        ).strip()

        if not opinion:
            continue

        opinions.append({
            "opinion": opinion,
            "evidence": evidence
        })

    opinion_text = "\n".join(
        [
            f"{i+1}. Opinion: {item['opinion']}\n"
            f"   Evidence: {item['evidence']}"
            for i, item in enumerate(opinions)
        ]
    )


    if sentiment == "긍정":

        task_description = """
Group the positive opinions into meaningful positive factors.

Examples of possible factors include:
- 맛
- 식감
- 양·포만감
- 속재료
- 가격·가성비
- 메뉴 다양성
- 서비스
- 위치·접근성
- 포장
- 온도
- 재구매 의향

These are examples only.
Use factors that are actually supported by the input.
"""

    else:

        task_description = """
Group the negative opinions into meaningful complaint causes.

Examples of possible causes include:
- 가격
- 맛
- 느끼함
- 짠맛
- 양·포만감
- 위생
- 서비스
- 운영
- 영업시간
- 대기시간
- 포장
- 온도
- 접근성

These are examples only.
Use causes that are actually supported by the input.
"""


    prompt = f"""
You are analyzing Korean customer opinions about a restaurant.

Sentiment being analyzed:
{sentiment}

{task_description}

Below are opinions previously extracted from customer posts and comments.

[Opinions]

{opinion_text}


[Task]

1. Group opinions that express the same underlying customer experience.
2. Give each group a short Korean label.
3. Do not create a group unless it is supported by the input.
4. Count how many individual opinion records belong to each group.
5. Each input opinion should normally contribute to only one group.
6. Do not inflate counts by counting repeated words inside one opinion.
7. Write one concise Korean summary representing the main opinion of the group.
8. Include up to three representative evidence expressions.
9. Keep positive and negative interpretations separate.
10. Do not introduce business recommendations. Only summarize what customers actually said.
11. Sort the groups from the most frequently mentioned to the least frequently mentioned.

Return JSON only.

Format:

{{
  "results": [
    {{
      "factor": "요인 또는 원인",
      "count": 0,
      "summary": "대표적인 고객 의견을 한국어 한 문장으로 요약",
      "evidence": [
        "근거 원문 1",
        "근거 원문 2"
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
        timeout=600
    )

    response.raise_for_status()

    result = json.loads(
        response.json()["response"]
    )

    return result.get("results", [])


def save_summary(results, sentiment, output_file):

    rows = []

    for item in results:

        evidence = item.get(
            "evidence",
            []
        )

        if sentiment == "긍정":

            rows.append({
                "긍정 요인": item.get(
                    "factor",
                    ""
                ),
                "언급 수": item.get(
                    "count",
                    0
                ),
                "대표 의견": item.get(
                    "summary",
                    ""
                ),
                "근거 예시": " | ".join(
                    evidence
                )
            })

        else:

            rows.append({
                "불만 원인": item.get(
                    "factor",
                    ""
                ),
                "언급 수": item.get(
                    "count",
                    0
                ),
                "대표 의견": item.get(
                    "summary",
                    ""
                ),
                "근거 예시": " | ".join(
                    evidence
                )
            })


    result_df = pd.DataFrame(rows)

    if not result_df.empty:

        result_df = result_df.sort_values(
            "언급 수",
            ascending=False
        )

    result_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return result_df


def main():

    df = pd.read_csv(INPUT_FILE)

    df["sentiment"] = (
        df["sentiment"]
        .fillna("")
        .astype(str)
        .str.strip()
    )


    # =========================
    # 긍정 분석
    # =========================

    print("긍정 의견 분석 중...")

    positive_results = summarize_sentiment(
        df,
        "긍정"
    )

    positive_df = save_summary(
        positive_results,
        "긍정",
        POSITIVE_FILE
    )


    # =========================
    # 부정 분석
    # =========================

    print("부정 의견 분석 중...")

    negative_results = summarize_sentiment(
        df,
        "부정"
    )

    negative_df = save_summary(
        negative_results,
        "부정",
        NEGATIVE_FILE
    )


    # =========================
    # 결과 출력
    # =========================

    print("\n==========================")
    print("긍정 의견")
    print("==========================")

    print(
        positive_df.to_string(
            index=False
        )
    )


    print("\n==========================")
    print("부정 의견")
    print("==========================")

    print(
        negative_df.to_string(
            index=False
        )
    )


    print("\n저장 완료")
    print(f"- {POSITIVE_FILE}")
    print(f"- {NEGATIVE_FILE}")


if __name__ == "__main__":
    main()