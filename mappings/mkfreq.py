import json

DAYS: dict = {
    "varierande": (0, "var", "varierande"),
    "oregelbunden": (0, "ore", "oregelbunden dag"),
    "må": (1, "ma", "måndagar"),
    "ti": (2, "ti", "tisdagar"),
    "on": (3, "on", "onsdagar"),
    "to": (4, "to", "torsdagar"),
    "fre": (5, "fr", "fredagar"),
    "lö": (6, "lo", "lördagar"),
    "sö": (7, "so", "söndagar"),
}

FREQ_UNIT = {
    "v": ("v", "vecka"),
    "m": ("m", "månaden"),
    "år": ("ar", "år"),
}

TIMEOFDAY = {
    'em': "på eftermiddagen",
    'fm': "på förmiddagen",
    'kv': "på kvällen",
    'mid': "på mitt på dagen",
    'morg': "på morgonen",
}

def mk_frequency(freqs, freq, days, timeofday=None):
    num, unitcode = freq.split('/')
    unit = FREQ_UNIT[unitcode]

    mdays = []
    gap = False
    for day in days.split(','):
        mday = DAYS.get(day.strip())
        if mdays and mday[0] - mdays[-1][0] > 1:
            gap = True

        if mday:
            mdays.append(mday)

    code = f'{freq} - {days}'
    if not mdays:
        mdays.append((0, days, days))

    segment = ','.join(mday[1] for mday in mdays)

    if gap and len(mdays) > 2:
        label = ', '.join(mday[2] for mday in mdays)
    elif len(mdays) > 1:
        #segment = f'{mdays[0][1]}-{mdays[-1][1]}'
        to = "och" if len(mdays) == 2 else "till"
        label = f'{mdays[0][2]} {to} {mdays[-1][2]}'
    else:
        #segment = mdays[0][1]
        label = mdays[0][2]

    id = f'/freq/{unit[0]}/{num}/{segment}'
    per = f"{'gång' if num == '1' else 'gånger'} {'i' if unitcode == 'm' else 'per'}"
    label = f"{num} {per} {unit[1]}, {label}"

    basebaseid = f'/freq/{unit[0]}/{num}'
    if basebaseid not in freqs:
        basebasecode = f'{freq}'
        basebaselabel = f"{num} {per} {unit[1]}"
        freqs[basebaseid] = {
            '@id': basebaseid,
            '@type': 'Frequency',
            'code': basebasecode,
            'labelByLang': {'sv': basebaselabel},
            'category': {'@id': '/vocab/pending'},
        }

    baseid = None
    if timeofday:
        baseid = id
        if baseid not in freqs:
            freqs[baseid] = {
                '@id': baseid,
                '@type': 'Frequency',
                'code': code,
                'labelByLang': {'sv': label[0].upper() + label[1:]},
                'category': {'@id': '/vocab/pending'},
            }
        freqs[baseid].setdefault('broader', set()).add(basebaseid)

        for mday in mdays:
            dayid = f'/freq/{mday[1]}'
            if dayid not in freqs:
                freqs[dayid] = {
                    '@id': dayid,
                    '@type': 'Frequency',
                    'code': mday[1],
                    'labelByLang': {'sv': mday[2].title()},
                    'category': {'@id': '/vocab/pending'},
                }
                if mday[0] > 0:
                    freqs[dayid]['ordinal'] = mday[0]

            freqs[baseid].setdefault('broader', set()).add(dayid)

        id += f'/{timeofday}'
        code += f' {timeofday}'
        label += f', {TIMEOFDAY[timeofday]}'

    else:
        baseid = basebaseid

    if id not in freqs:
        freqs[id] = {
            '@id': id,
            '@type': 'Frequency',
            'code': code,
            'labelByLang': {'sv': label[0].upper() + label[1:]}
        }
        if baseid:
            freqs[id].setdefault('broader', set()).add(baseid)


def process(linestream):
    freqs = {}
    for l in linestream:
        l = l.strip()
        if not l:
            continue

        freq, *rest = l.split('\t')
        days = rest.pop(0) if rest else None
        timeofday = rest.pop(0) if rest else None

        if days:
            mk_frequency(freqs, freq, days, timeofday)
        else:
            # TODO: this is captured by a baseid, but that is marked as
            # pending!
            pass

    items = list(freqs.values())
    for item in items:
        if 'broader' in item:
            item['broader'] = [{'@id': ref} for ref in item['broader']]

    return {
        "@context": {
          "@vocab": "https://id.kb.se/vocab/",
          "@base": "https://id.kb.se/",
          "labelByLang": {"@id": "label", "@container": "@language"},
        },
        "@graph": items,
    }


def main(cmd, *args):
    fpath = args[0]
    with open(fpath) as f:
        data = process(f)

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    import sys

    main(*sys.argv[:])
