import pandas as pd
from pathlib import Path


INPUT_FILE = Path("keyword_results/opinion_summary.csv")

OUTPUT_DIR = Path("keyword_results")

POSITIVE_FILE = OUTPUT_DIR / "naver_positive_summary.csv"
NEGATIVE_FILE = OUTPUT_DIR / "naver_negative_summary.csv"

OUTPUT_DIR.mkdir(exist_ok=True)


def collect_evidence(group, max_examples=4):
    """
    한 그룹 안의 근거 예시를 모아서
    중복을 제거하고 최대 max_examples개만 반환
    """

    examples = []

    # 언급 수가 높은 의견부터 근거 수집
    group = group.sort_values(
        "언급 수",
        ascending=False
    )

    for evidence in group["근거 예시"].dropna():

        for item in str(evidence).split("|"):

            item = item.strip()

            # 앞의 '- ' 제거
            if item.startswith("- "):
                item = item[2:].strip()

            if not item:
                continue

            if item not in examples:
                examples.append(item)

            if len(examples) >= max_examples:
                return " / ".join(examples)

    return " / ".join(examples)


def make_summary(df, sentiment):

    subset = df[
        df["의견 유형"] == sentiment
    ].copy()

    rows = []

    for (category, topic), group in subset.groupby(
        ["대분류", "세부 주제"]
    ):

        # 해당 세부 주제 전체 언급 수
        total_count = group["언급 수"].sum()

        # 언급 수가 가장 높은 의견을 대표 의견으로 선택
        representative_row = (
            group.sort_values(
                "언급 수",
                ascending=False
            )
            .iloc[0]
        )

        representative_opinion = representative_row[
            "주요 의견"
        ]

        evidence = collect_evidence(
            group,
            max_examples=4
        )

        rows.append({
            "대분류": category,
            "요인": topic,
            "언급 수": total_count,
            "대표 의견": representative_opinion,
            "근거 예시": evidence
        })

    result = pd.DataFrame(rows)

    result = result.sort_values(
        "언급 수",
        ascending=False
    )

    return result


def main():

    df = pd.read_csv(INPUT_FILE)

    df["대분류"] = (
        df["대분류"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["세부 주제"] = (
        df["세부 주제"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["의견 유형"] = (
        df["의견 유형"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["언급 수"] = pd.to_numeric(
        df["언급 수"],
        errors="coerce"
    ).fillna(0)


    # ==========================
    # 긍정
    # ==========================

    positive = make_summary(
        df,
        "긍정"
    )

    positive = positive.rename(
        columns={
            "요인": "긍정 요인"
        }
    )

    positive.to_csv(
        POSITIVE_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    # ==========================
    # 부정
    # ==========================

    negative = make_summary(
        df,
        "불만"
    )

    negative = negative.rename(
        columns={
            "요인": "불만 원인"
        }
    )

    negative.to_csv(
        NEGATIVE_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    print("\n==========================")
    print("긍정 의견")
    print("==========================\n")

    print(
        positive.to_string(
            index=False
        )
    )


    print("\n==========================")
    print("부정 의견")
    print("==========================\n")

    print(
        negative.to_string(
            index=False
        )
    )


    print("\n저장 완료")
    print(f"- {POSITIVE_FILE}")
    print(f"- {NEGATIVE_FILE}")


if __name__ == "__main__":
    main()