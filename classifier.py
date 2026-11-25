# ai_classifier.py
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

df = pd.read_csv("cloud_usage.csv")
df['cpu_avg']=np.random.uniform(1,100,len(df))
df['mem_avg']=np.random.uniform(1,100,len(df))

kmeans=KMeans(n_clusters=3,random_state=42).fit(df[['cpu_avg','mem_avg']])
df['cluster']=kmeans.labels_

# Map cluster to human-readable tags
centers=pd.DataFrame(kmeans.cluster_centers_,columns=['cpu','mem']).sort_values('cpu')
mapping={centers.index[0]:'IDLE_DELETE',centers.index[1]:'UNDERUSED_RESIZE',centers.index[2]:'CRITICAL'}
df['classification_tag']=df['cluster'].map(mapping)

print(df[['resource_id','cpu_avg','mem_avg','classification_tag']])
