# analyzer.py
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("cloud_usage.csv")

summary = df.groupby('type')['waste_flag'].apply(lambda x: (x=="YES").sum())
print("Waste Count by Type:\n", summary)

# Simple bar chart
summary.plot(kind='bar', title="Waste by Resource Type", color='orange')
plt.ylabel("Count of Wasted Resources")
plt.show()
