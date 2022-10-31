import datetime
from urllib.parse import quote

from . import SIGNE_BASE


def convert(bibrow):
    bibrowid, paperid, catid, fromdate, todate, text1, text2, comment = bibrow

    libris_uri = (
        f'{SIGNE_BASE}bib/{paperid}'
        #f'http://libris.kb.se/resource/bib/{printid}'
        #if isinstance(printid, int)
        #else f'https://libris.kb.se/{printid}#it'
    )

    item = None

    if catid == 8:  # Editionsbeteckningar
        item = {
            '@id': f'{SIGNE_BASE}edition/{bibrowid}',
            '@type': 'SerialEdition',
            'isEditionOf': {'@id': libris_uri},
            'label': text1,
            'firstIssueDate': reprdate(fromdate),
        }
        if todate:
            item['lastIssueDate'] = reprdate(todate)
        if text2:
            item['manufacture'] = {
                '@type': 'Manufacture',
                'place': {'@type': 'Place', 'label': text2}
            }
        if comment:
            item['comment'] = comment

    if catid == 24:  # Politisk_inriktning
        if not text1.strip():
            return None

        item = {
            '@id': f'{SIGNE_BASE}politik/{quote(text1)}',
            '@type': 'Concept',
            #'label': text1,
        }
        if '"' in text1:
            item['comment'] = text1
        else:
            item['label'] = text1[0].upper() + text1[1:]

    return item


def reprdate(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%d")


if __name__ == '__main__':
    import json
    import sys

    for l in sys.stdin:
        if data := convert(eval(l)):
            print(json.dumps(data, ensure_ascii=False))
