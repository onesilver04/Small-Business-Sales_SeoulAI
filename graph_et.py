import pandas as pd
import matplotlib.pyplot as plt


plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


df = pd.read_csv(
    "everytime_results/everytime_sentiment.csv"
)


# 중립 제외
sentiment_df = df[
    df["sentiment"].isin(
        ["긍정", "부정"]
    )
]


counts = (
    sentiment_df["sentiment"]
    .value_counts()
    .reindex(
        ["긍정", "부정"],
        fill_value=0
    )
)


plt.figure(figsize=(7, 5))

plt.bar(
    counts.index,
    counts.values
)

plt.title("에브리타임 리뷰 긍정·부정 의견")
plt.ylabel("의견 수")

for i, value in enumerate(counts.values):
    plt.text(
        i,
        value,
        str(value),
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "everytime_results/sentiment_count.png",
    dpi=300
)

plt.show()