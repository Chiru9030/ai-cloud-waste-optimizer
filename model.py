# model.py
def classify_resource(resource):
    cpu, memory, storage = resource["cpu"], resource["memory"], resource["storage"]

    if cpu < 20 and memory < 20:
        return "Idle"
    elif cpu < 50:
        return "Underutilized"
    else:
        return "Critical"
