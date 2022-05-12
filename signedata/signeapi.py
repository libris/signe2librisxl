from datetime import datetime

import requests


def fetch_bibliographies(api_url):
    now = datetime.now().strftime("%Y-%m-%d")
    fromto = f"fromdate=1600-01-01&todate={now}"

    for item in requests.get(f"{api_url}/bibliographies").json()['newspapers']:
        yield requests.get(f"{api_url}/bibliographies/{item['id']}?{fromto}").json()
