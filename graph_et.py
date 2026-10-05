import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 긍정 의견 시각화
# =========================

positive = pd.read_csv(
    "everytime_results/positive_summary.csv"
)

positive = positive.sort_values(
    "언급 수",
    ascending=True
)

plt.figure(figsize=(10, 6))

plt.barh(
    positive["긍정 요인"],
    positive["언급 수"]
)

plt.title("에브리타임 리뷰의 주요 긍정 요인")
plt.xlabel("언급 수")
plt.ylabel("긍정 요인")

for i, value in enumerate(positive["언급 수"]):
    plt.text(
        value,
        i,
        f" {value}",
        va="center"
    )

plt.tight_layout()

plt.savefig(
    "everytime_results/positive_factors.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# =========================
# 부정 의견 시각화
# =========================

negative = pd.read_csv(
    "everytime_results/negative_summary.csv"
)

negative = negative.sort_values(
    "언급 수",
    ascending=True
)

plt.figure(figsize=(10, 6))

plt.barh(
    negative["불만 원인"],
    negative["언급 수"]
)

plt.title("에브리타임 리뷰의 주요 부정 요인")
plt.xlabel("언급 수")
plt.ylabel("불만 원인")

for i, value in enumerate(negative["언급 수"]):
    plt.text(
        value,
        i,
        f" {value}",
        va="center"
    )

plt.tight_layout()

plt.savefig(
    "everytime_results/negative_factors.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()