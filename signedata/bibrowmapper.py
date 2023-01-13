from __future__ import annotations
import datetime
from urllib.parse import quote


def convert(bibrow: tuple, cfg={}):
    bibrowid: int
    paperid: int
    catid: int
    fromdate: datetime.datetime
    todate: datetime.datetime
    text1: str | None
    text2: str | None
    comment: str | None

    bibrowid, paperid, catid, fromdate, todate, text1, text2, comment = bibrow

    libris_uri = (
        cfg['bib_base_uri'] + str(paperid)
        #f'http://libris.kb.se/resource/bib/{printid}'
        #if isinstance(printid, int)
        #else f'https://libris.kb.se/{printid}#it'
    )

    item = None

    if catid == 8:  # Editionsbeteckningar
        item = {
            '@id': cfg['edition_base_uri'] + str(bibrowid),
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
        if text1 is None or not text1.strip():
            return None

        item = {
            '@id': cfg['political_base_uri'] + quote(text1),
            '@type': 'Concept',
            #'label': text1,
        }
        if text1 and '"' in text1:
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
