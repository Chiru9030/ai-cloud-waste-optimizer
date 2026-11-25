# actions.py
import pandas as pd

df = pd.read_csv("cloud_usage.csv")  # or from ai_classifier output
df['classification_tag']=pd.read_csv("ai_classifier_output.csv")['classification_tag']  # simplified

actions=[]
for _,r in df.iterrows():
    if r['classification_tag']=='IDLE_DELETE': actions.append({'resource_id':r['resource_id'],'action':'DELETE'})
    elif r['classification_tag']=='UNDERUSED_RESIZE': actions.append({'resource_id':r['resource_id'],'action':'RESIZE'})

print("Recommended Actions:", actions[:5])
