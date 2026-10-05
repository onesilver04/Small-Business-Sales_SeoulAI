import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("keyword_results/opinion_summary.csv")

# # 의견 유형별 언급 수 합계
# sentiment = (
#     df.groupby(["세부 주제", "의견 유형"])["언급 수"]
#     .sum()
#     .unstack(fill_value=0)
# )

# # 전체 언급이 많은 주제 순
# sentiment["total"] = sentiment.sum(axis=1)

# sentiment = (
#     sentiment
#     .sort_values("total", ascending=False)
#     .head(15)
#     .drop(columns="total")
# )

# sentiment.plot(
#     kind="barh",
#     stacked=True,
#     figsize=(11, 8)
# )

# plt.gca().invert_yaxis()

# plt.title("주요 세부 주제별 고객 의견 유형")
# plt.xlabel("언급 수")
# plt.ylabel("세부 주제")

# plt.legend(title="의견 유형")

# plt.tight_layout()
# plt.show()

# # 주요 의견별 언급 수
# opinion_rank = (
#     df.groupby(
#         ["주요 의견", "의견 유형"],
#         as_index=False
#     )["언급 수"]
#     .sum()
#     .sort_values("언급 수", ascending=False)
#     .head(15)
# )

# plt.figure(figsize=(12, 8))

# plt.barh(
#     opinion_rank["주요 의견"],
#     opinion_rank["언급 수"]
# )

# plt.gca().invert_yaxis()

# plt.title("고객 리뷰 주요 의견 TOP 15")
# plt.xlabel("언급 수")
# plt.ylabel("주요 의견")

# plt.tight_layout()
# plt.show()

category_sentiment = (
    df.groupby(["대분류", "의견 유형"])["언급 수"]
    .sum()
    .unstack(fill_value=0)
)

# 긍정/불만만 사용
wanted = [
    col for col in ["긍정", "불만"]
    if col in category_sentiment.columns
]

category_sentiment = category_sentiment[wanted]

# 비율로 변환
category_ratio = (
    category_sentiment
    .div(category_sentiment.sum(axis=1), axis=0)
    * 100
)

category_ratio.plot(
    kind="barh",
    stacked=True,
    figsize=(10, 6)
)

plt.title("대분류별 긍정·불만 의견 비율")
plt.xlabel("비율 (%)")
plt.ylabel("대분류")

plt.legend(title="의견 유형")

plt.tight_layout()
plt.show()