import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


RESULT_DIR = Path("keyword_results")

POSITIVE_FILE = RESULT_DIR / "naver_positive_summary.csv"
NEGATIVE_FILE = RESULT_DIR / "naver_negative_summary.csv"


# ==========================================
# 1. 긍정 요인 TOP 10
# ==========================================

positive = pd.read_csv(POSITIVE_FILE)

positive["언급 수"] = pd.to_numeric(
    positive["언급 수"],
    errors="coerce"
).fillna(0)

positive_top = (
    positive
    .sort_values("언급 수", ascending=False)
    .head(10)
    .sort_values("언급 수", ascending=True)
)


plt.figure(figsize=(10, 7))

plt.barh(
    positive_top["긍정 요인"],
    positive_top["언급 수"]
)

plt.title("네이버 블로그 리뷰 주요 긍정 요인 TOP 10")
plt.xlabel("언급 수")
plt.ylabel("긍정 요인")


# 막대 끝에 숫자 표시
for i, value in enumerate(positive_top["언급 수"]):
    plt.text(
        value,
        i,
        f" {int(value)}",
        va="center"
    )


plt.tight_layout()

plt.savefig(
    RESULT_DIR / "naver_positive_top10.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==========================================
# 2. 부정 요인 TOP 10
# ==========================================

negative = pd.read_csv(NEGATIVE_FILE)

negative["언급 수"] = pd.to_numeric(
    negative["언급 수"],
    errors="coerce"
).fillna(0)

negative_top = (
    negative
    .sort_values("언급 수", ascending=False)
    .head(10)
    .sort_values("언급 수", ascending=True)
)


plt.figure(figsize=(10, 7))

plt.barh(
    negative_top["불만 원인"],
    negative_top["언급 수"]
)

plt.title("네이버 블로그 리뷰 주요 부정 요인 TOP 10")
plt.xlabel("언급 수")
plt.ylabel("불만 원인")


for i, value in enumerate(negative_top["언급 수"]):
    plt.text(
        value,
        i,
        f" {int(value)}",
        va="center"
    )


plt.tight_layout()

plt.savefig(
    RESULT_DIR / "naver_negative_top10.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# ==========================================
# 3. 세부 주제별 긍정 vs 부정
# ==========================================

positive_compare = (
    positive[["긍정 요인", "언급 수"]]
    .rename(
        columns={
            "긍정 요인": "요인",
            "언급 수": "긍정"
        }
    )
)

negative_compare = (
    negative[["불만 원인", "언급 수"]]
    .rename(
        columns={
            "불만 원인": "요인",
            "언급 수": "부정"
        }
    )
)


comparison = pd.merge(
    positive_compare,
    negative_compare,
    on="요인",
    how="outer"
).fillna(0)


comparison["전체"] = (
    comparison["긍정"]
    + comparison["부정"]
)


comparison = (
    comparison
    .sort_values("전체", ascending=False)
    .head(10)
    .sort_values("전체", ascending=True)
)


plt.figure(figsize=(11, 7))


y = range(len(comparison))

bar_height = 0.35


plt.barh(
    [i - bar_height / 2 for i in y],
    comparison["긍정"],
    height=bar_height,
    label="긍정"
)

plt.barh(
    [i + bar_height / 2 for i in y],
    comparison["부정"],
    height=bar_height,
    label="부정"
)


plt.yticks(
    y,
    comparison["요인"]
)

plt.title("네이버 블로그 리뷰 세부 주제별 긍정·부정 비교")
plt.xlabel("언급 수")
plt.ylabel("세부 주제")

plt.legend()

plt.tight_layout()

plt.savefig(
    RESULT_DIR / "naver_positive_negative_compare.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()