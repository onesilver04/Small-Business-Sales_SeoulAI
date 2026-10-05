from pathlib import Path
import pandas as pd
import requests
import json
import time


INPUT_FILE = Path("everytime_crawling.csv")
OUTPUT_DIR = Path("everytime_results")
OUTPUT_FILE = OUTPUT_DIR / "everytime_sentiment.csv"

MODEL = "qwen2.5:7b"

OUTPUT_DIR.mkdir(exist_ok=True)


def analyze_text(text):

    prompt = f"""
You are analyzing Korean customer opinions about a restaurant.

Extract each meaningful opinion from the text below and classify its sentiment.

[Sentiment labels]

- 긍정:
  The writer expresses satisfaction, preference, recommendation,
  enjoyment, convenience, or another favorable evaluation.

- 부정:
  The writer expresses dissatisfaction, inconvenience, disappointment,
  concern, criticism, or another unfavorable evaluation.

- 중립:
  The text only provides factual information, asks a question,
  or does not clearly express a positive or negative evaluation.

[Rules]

1. A single text may contain multiple opinions.
2. Separate conflicting opinions into different items.
3. Do not classify the entire text with only one sentiment when it contains
   multiple distinct opinions.
4. Preserve the exact Korean expression supporting each opinion.
5. Summarize the opinion briefly in Korean.
6. Do not invent information that is not explicitly supported by the text.
7. Questions such as "얼마야?" or "하나 먹어도 배 차?" are neutral.
8. Simple factual information such as "가격은 6500원" is neutral unless
   the writer evaluates the price.
9. Recommendation or repurchase intention is positive.
10. Expressions such as "비싸다", "느끼하다", "짜다", "더럽다",
    "늦다", or "문이 닫혀 있었다" should be negative only when
    they are actually expressed as dissatisfaction or concern.
11. Informal Korean expressions such as "존맛", "개맛있다", "굿",
    "추천", "행복하다" should be interpreted as positive.
12. Internet slang and abbreviated Korean should be interpreted from context.

[Text]

{text}

Return JSON only.

Format:

{{
  "opinions": [
    {{
      "sentiment": "긍정 | 부정 | 중립",
      "opinion": "Brief Korean summary of the opinion",
      "evidence": "Exact expression from the text"
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

    return json.loads(
        response.json()["response"]
    )


def split_comments(review_text):

    if pd.isna(review_text):
        return []

    review_text = str(review_text).strip()

    if not review_text:
        return []

    return [
        comment.strip()
        for comment in review_text.split("\\n")
        if comment.strip()
    ]


def add_analysis(
    rows,
    post_id,
    title,
    date,
    source_type,
    source_index,
    text
):

    if not text or not str(text).strip():
        return

    try:

        result = analyze_text(str(text))

        for item in result.get("opinions", []):

            rows.append({
                "post_id": post_id,
                "title": title,
                "date": date,
                "source_type": source_type,
                "source_index": source_index,
                "sentiment": item.get(
                    "sentiment",
                    ""
                ),
                "opinion": item.get(
                    "opinion",
                    ""
                ),
                "evidence": item.get(
                    "evidence",
                    ""
                )
            })

    except Exception as e:

        print(f"분석 실패: {post_id} / {source_type}")
        print(e)


def main():

    df = pd.read_csv(INPUT_FILE)

    rows = []

    total = len(df)

    for index, row in df.iterrows():

        post_id = index + 1

        title = (
            str(row["title"])
            if not pd.isna(row["title"])
            else ""
        )

        body = (
            str(row["body"])
            if not pd.isna(row["body"])
            else ""
        )

        date = (
            str(row["date"])
            if not pd.isna(row["date"])
            else ""
        )

        print(
            f"[{post_id}/{total}] "
            f"{title[:30]}"
        )

        # -----------------------------
        # 게시글 본문 분석
        # -----------------------------

        add_analysis(
            rows=rows,
            post_id=post_id,
            title=title,
            date=date,
            source_type="본문",
            source_index=0,
            text=body
        )

        # -----------------------------
        # 댓글 분석
        # -----------------------------

        comments = split_comments(
            row.get("review", "")
        )

        for comment_index, comment in enumerate(
            comments,
            start=1
        ):

            add_analysis(
                rows=rows,
                post_id=post_id,
                title=title,
                date=date,
                source_type="댓글",
                source_index=comment_index,
                text=comment
            )

        # 너무 빠른 연속 요청 방지
        time.sleep(0.05)


    result_df = pd.DataFrame(rows)

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n분석 완료")
    print(f"저장 위치: {OUTPUT_FILE}")

    print("\n감성 분포")

    print(
        result_df["sentiment"]
        .value_counts()
    )


if __name__ == "__main__":
    main()