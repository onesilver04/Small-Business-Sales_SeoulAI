import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("keyword_results/opinion_summary.csv")

# 의견 유형별 언급 수 합계
sentiment = (
    df.groupby(["세부 주제", "의견 유형"])["언급 수"]
    .sum()
    .unstack(fill_value=0)
)

# 전체 언급이 많은 주제 순
sentiment["total"] = sentiment.sum(axis=1)

sentiment = (
    sentiment
    .sort_values("total", ascending=False)
    .head(15)
    .drop(columns="total")
)

sentiment.plot(
    kind="barh",
    stacked=True,
    figsize=(11, 8)
)

plt.gca().invert_yaxis()

plt.title("주요 세부 주제별 고객 의견 유형")
plt.xlabel("언급 수")
plt.ylabel("세부 주제")

plt.legend(title="의견 유형")

plt.tight_layout()
plt.show()