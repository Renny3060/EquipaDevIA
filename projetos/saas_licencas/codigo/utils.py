import uuid
from datetime import timedelta

def generate_license_key():
    return "-".join([uuid.uuid4().hex[:4] for _ in range(4)])
