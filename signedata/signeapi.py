from datetime import datetime

import requests


def fetch_bibliographies(api_url, paperids=None):
    now = datetime.now().strftime("%Y-%m-%d")
    fromto = f"fromdate=1600-01-01&todate={now}"

    if paperids is None:
        # TODO: for some reason (implicit date filters?), this only lists 243 papers...
        start_url = f"{api_url}/bibliographies"
        paperids = (item['id'] for item in requests.get(start_url).json()['newspapers'])

    for paperid in paperids:
        yield requests.get(f"{api_url}/bibliographies/{paperid}?{fromto}").json()
