import datetime


def convert(bibrow):
    bibrowid, paperid, catid, fromdate, todate, text1, text2, comment = bibrow

    libris_uri = (
        f'signe:bib/{paperid}'
        #f'http://libris.kb.se/resource/bib/{printid}'
        #if isinstance(printid, int)
        #else f'https://libris.kb.se/{printid}#it'
    )

    if catid == 8:  # Editionsbeteckningar = 8
        return {
            '@id': f'signe:edition/{bibrowid}',
            '@type': 'SerialEdition',
            'isEditionOf': {'@id': libris_uri},
            'editionStatement': text1,
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

    return None


def reprdate(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%d")


if __name__ == '__main__':
    import json
    import sys

    for l in sys.stdin:
        if data := convert(eval(l)):
            print(json.dumps(data, ensure_ascii=False))
