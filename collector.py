# collector.py
import random

def collect_data():
    resources = []
    for i in range(5):
        resource = {
            "id": f"vm-{i+1}",
            "cpu": random.randint(1, 100),
            "memory": random.randint(1, 100),
            "storage": random.randint(1, 100)
        }
        resources.append(resource)
    return resources
