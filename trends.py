# trends.py
import matplotlib.pyplot as plt
from datetime import date, timedelta
import numpy as np

months=[date.today()-timedelta(days=30*i) for i in range(3,0,-1)]
savings=[150000*(0.9+0.2*np.random.rand()) for _ in months]
waste_count=[200*(0.8+0.2*np.random.rand()) for _ in months]

plt.plot(months,savings,label='Savings',marker='o',color='green')
plt.plot(months,waste_count,label='Waste Count',marker='o',color='red')
plt.title("Waste & Savings Trend")
plt.legend()
plt.show()
