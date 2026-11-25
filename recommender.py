# recommender.py
def get_recommendation(status):
    if status == "Idle":
        return "Delete or stop instance"
    elif status == "Underutilized":
        return "Resize to smaller tier"
    else:
        return "Retain as is"
