import requests
import json

token = ""

def get_token():
    # Read from local storage if available or hardcode
    import os
    pass

try:
    with open('/Users/mac/Desktop/phhh/frontend/.env.local', 'r') as f:
        pass
except:
    pass

# Direct test on VPS
# ssh -i ~/.ssh/lightsail_key -o StrictHostKeyChecking=no ubuntu@15.237.208.231 "ps aux | grep uvicorn"
