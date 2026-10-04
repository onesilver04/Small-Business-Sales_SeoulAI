import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("keyword_results/topic_frequency.csv")


# 1. 대분류별 총 추출 건수
category_sum = (
    df.groupby("대분류")["추출 건수"]
    .sum()
    .sort_values(ascending=True)
)

plt.figure(figsize=(10, 6))
category_sum.plot(kind="barh")

plt.title("대분류별 리뷰 언급량")
plt.xlabel("추출 건수")
plt.ylabel("대분류")

plt.tight_layout()
plt.show()


# 2. 세부 주제 TOP 15
top_topics = (
    df.sort_values("추출 건수", ascending=False)
    .head(15)
)

plt.figure(figsize=(10, 8))

plt.barh(
    top_topics["세부 주제"],
    top_topics["추출 건수"]
)

plt.gca().invert_yaxis()

plt.title("리뷰에서 많이 언급된 세부 주제 TOP 15")
plt.xlabel("추출 건수")
plt.ylabel("세부 주제")

plt.tight_layout()
plt.show()


# 3. 추출 건수 vs 등장 문서 수
plt.figure(figsize=(10, 7))

plt.scatter(
    df["등장 문서 수"],
    df["추출 건수"]
)

for _, row in df.iterrows():
    if row["추출 건수"] >= 15:
        plt.text(
            row["등장 문서 수"],
            row["추출 건수"],
            row["세부 주제"],
            fontsize=8
        )

plt.title("세부 주제별 언급량과 등장 문서 수")
plt.xlabel("등장 문서 수")
plt.ylabel("추출 건수")

plt.tight_layout()
plt.show()