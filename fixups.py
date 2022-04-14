import json
import sys
from pathlib import Path
from urllib.parse import quote, unquote


ANNOTATION = '@annotation'
BASE = '@base'
CONTEXT = '@context'
GRAPH = '@graph'
ID = '@id'
INCLUDED = '@included'
TYPE = '@type'
VALUE = '@value'
VOCAB = '@vocab'

KBV = 'https://id.kb.se/vocab/'

CONTEXT_DATA = {
    VOCAB: KBV,
    BASE: 'https://signe.kb.se/',
}

ID_RULES = {
    None: ('/signe/bib/{}', ['id']),
    GRAPH: ('/signe/bib/{}', ['id']),
    'hasInstance': ('/signe/instance/{}', ['id']),
    'hasPart': ('/signe/part/{}', ['id']),
    'generatedEdition': ('/signe/edition/{}', ['id']),
    'associatedNewsBill': ('/signe/newsbill/{}', ['id']),
    'hasSupplement': ('/signe/supplement/{}', ['id']),
    'politicalLabel': ('object', '/term/signe/politik/{}'),
}

top_type_rule = ('Text', 'https://id.kb.se/vocab/Serial', 'https://id.kb.se/term/saogf/Dagstidningar')
TYPE_RULES = {
    None: top_type_rule,
    GRAPH: top_type_rule,
    'hasTitle': ('Title', None, None),
    'manufacture': ('Manufacture', None, None),
    'hasPart': ('Text', 'https://id.kb.se/vocab/SerialComponentPart', 'https://id.kb.se/term/komp/Tidningsdel'),
    'generatedEdition': ('Print', 'https://id.kb.se/vocab/Serial', 'https://id.kb.se/term/komp/Upplaga'), # TODO: subseriesOf (or hasSubseries, and put manufacture within these editions?)?
    'associatedNewsBill': ('Text', 'https://id.kb.se/vocab/SerialComponentPart', 'https://id.kb.se/term/komp/L%F6psedel'),
    'hasSupplement': ('Text', 'https://id.kb.se/vocab/SerialComponentPart', 'https://id.kb.se/term/komp/Tidningsbilaga'),
}

LANGUAGE_MAP = {
    'svenska': 'https://id.kb.se/language/swe',
    'finska': 'https://id.kb.se/language/fin',
    'engelska': 'https://id.kb.se/language/eng',
    'arabiska': 'https://id.kb.se/language/ara',
    'bosniska': 'https://id.kb.se/language/bos',
}

# TODO:
# - Replace all "/signe/"-URI:s with real ones; including <frequencies.ttl>
with open(Path(__file__).parent / 'context-regions.jsonld') as f:
    region = json.load(f)[CONTEXT]


def asiter(o):
    if o is None:
        return
    if isinstance(o, list):
        yield from o
    else:
        yield o


def squote(s: str):
    return quote(s, safe='/,@')


def drop_encoded(data, keys):
    return [squote(str(data.pop(key)).encode('utf8'))
            for key in keys if key in data]


def parse_date_range(v):
    startdate, sep, enddate = v.partition('--')
    return startdate.strip() or None, enddate.strip() or None


def walk(data, via=None, owner=None):
    if isinstance(data, list):
        for li in data:
            walk(li, via, owner)
        while {} in data:
            data.remove({})
        if via == GRAPH:
            for li in iter(data):
                data.extend(li.pop(INCLUDED, []))
        return

    if not isinstance(data, dict):
        id_rule = ID_RULES.get(via)
        if id_rule:
            link, base_id = id_rule
            del owner[via]
            owner[link] = {ID: base_id.format(squote(data))}
        return

    # Pre-Walk
    new_id = None

    if ID in data:
        did = data[ID]
        if '%' not in did and ':' not in did \
                and (not did.isalnum() or not did.isascii()):
            new_id = squote(data.pop(ID))

    id_rule = ID_RULES.get(via)
    if id_rule:
        base_id, keys = id_rule
        values = drop_encoded(data, keys)
        if values:
            new_id = base_id.format(*values)

    _normalize_frequency(data)

    if via in {None, GRAPH}:
        data['@context'] = CONTEXT_DATA

    if via in {None, GRAPH} and 'title' in data:
        data['hasTitle'] = [ { 
            TYPE: 'KeyTitle',
            'mainTitle': data.pop('title')
        } ] + list(asiter(data['hasTitle']))

    hastitle = data.pop('hasTitle', None)

    entries = list(data.items())
    entries.sort(key=lambda kv: -int(kv[0].startswith('@')))
    data.clear()

    if new_id:
        data[ID] = new_id

    type_rule = TYPE_RULES.get(via)

    if type_rule:
        rtype, itype, gform = type_rule
        data[TYPE] = rtype
        if itype:
            data['issuanceType'] = {ID: itype}
        if gform:
            data['genreForm'] = {ID: gform}

    if hastitle:
        data['hasTitle'] = hastitle
        walk(hastitle, 'hasTitle', data)


    # Walk
    for k, v in entries:
        if isinstance(v, str) and '\n' not in v:
            v = v.strip()

        if v == "" or v == []:
            continue

        if v == {ID: "stdin"}:
            continue

        if v == {ID: KBV}:
            continue

        if k == 'id':
            data['exactMatch'] = {ID: f'/signe/{via}/{v}'}

        elif k.startswith('_about'):
            prop = k[1:]
            data[ANNOTATION] = {prop: v}

        elif k == 'sameAs':
            data[ID] = v[ID]

        elif via == 'language' and k == 'label' and v in LANGUAGE_MAP:
            data[ID] = LANGUAGE_MAP[v]

        #elif k == 'placeName':
        #    data['place'] = {TYPE:'Place', 'name': v}

        elif k == 'generatedEdition':
            data['generated'] = v

        elif k == 'regionCode':
            assert via == 'publication'
            data['place'] = [{ID: region[code]} for code in v.split(', ')]

        elif k == 'dateRange':
            startdate, enddate = parse_date_range(v)
            if startdate:
                data['startDate'] = startdate
            if enddate:
                data['endDate'] = enddate

        elif k == 'publicationPeriod':
            startdate, enddate = parse_date_range(v)
            publ = data['publication'] = {TYPE: 'Publication'}
            if startdate:
                publ['startDate'] = startdate
            if enddate:
                publ['endDate'] = enddate

        else:
            data[k] = v

        walk(v, via=k, owner=data)


    # Post-Walk
    workref = {ID: data[ID]} if ID in data else None
    included = []

    _process_supplements(data, workref, included)

    if workref and 'hasInstance' in data:
        instances = list(asiter(data.pop('hasInstance')))
        iprint = None
        for inst in instances:
            inst['instanceOf'] = workref
            if iprint is None and inst[TYPE] == 'Print':
                iprint = inst

        move_to_print = ['publication', 'pubFrequency']
        for key in move_to_print:
            if key in data:
                iprint[key] = data.pop(key)

        if 'production' in data:
            microform = {
                ID: f'{data[ID]}/microform',
                TYPE: 'Microform',
                'issuanceType': 'Serial',
                'instanceOf': workref,
            }
            microform['production'] = [
                dict({TYPE: 'Production'}, **prod)
                for prod in asiter(data.pop('production'))
            ]
            instances.append(microform)

        included.extend(instances)

        # De-duplicates on place name and generated...
        manufacture = list({
            (
                printing.get('place', {}).get(ID, ""),
                '|'.join(sorted(x[ID] for x in asiter(printing.get('generated'))))
            ): printing
            for printing in asiter(data.pop('manufacture', None))
            if len(printing) > 1 or TYPE not in printing
        }.values())

        if manufacture:
            if iprint:
                toinclude = []
                for printing in manufacture:
                    editions = printing.pop('generated', iprint)
                    for edition in asiter(editions):
                        if len(printing) > 1 or TYPE not in printing:
                            edition.setdefault('manufacture', []).append(printing)
                        if edition is not iprint:
                            #edition['specializationOf'] = {ID: iprint[ID]}
                            toinclude.append(edition)
                        #edition['instanceOf'] = workref

                subslice_link = 'hasEdition' # 'generalizationOf' # 'hasSubseries'
                iprint[subslice_link] = [{ID: sub[ID]} for sub in toinclude]
                included.extend(toinclude)

    if included:
        data.setdefault(INCLUDED, []).extend(included)


def _normalize_frequency(data):
    freq = data.get('frequency')
    if isinstance(freq, str):
        freq = data['frequency'] = {
            'code': data.pop('frequency'),
        }
        move_into = ['daysOfWeek', 'timeOfDay']
        for key in move_into:
            if key in data:
                freq[key] = data.pop(key)
    if freq:
        for ifreq in asiter(freq):
            ifreq_id = None
            code = ifreq.pop('code')
            if code.split('/', 1)[0].isdigit() and 'daysOfWeek' in ifreq:
                weekdays = ifreq.pop('daysOfWeek').replace(' ', '')
                if weekdays:
                    timeofday = ifreq.get('timeOfDay')
                    todcode = timeofday.replace(' ', '') if timeofday else None
                    if todcode and todcode.isalpha():
                        ifreq_id = f'/signe/freq/{code}-{weekdays}@{todcode}'
                        del ifreq['timeOfDay']
                    elif not timeofday:
                        ifreq_id = f'/signe/freq/{code}-{weekdays}'
                #else:
                #    ifreq_id = f'/signe/freq/{code}'

            if ifreq_id:
                ifreq[ID] = ifreq_id
            else:
                ifreq[TYPE] = 'Frequency'
                ifreq['label'] = code


def _process_supplements(data, workref, included):
    if not workref or not 'hasSupplement' in data:
        return

    supplements = list(asiter(data.pop('hasSupplement')))

    mergedsupplements = {}
    for supplement in supplements:
        suppkey = supplement.get('title') or supplement[ID]
        mergedsupp = mergedsupplements.setdefault(suppkey, supplement)
        suppref = {ID: supplement[ID]}
        supplement['supplementTo'] = workref
        for key in ['publication', 'subject', 'frequency']:
            value = supplement.pop(key, None)
            if supplement is mergedsupp:
                mergedsupp[key] = []

            if value:
                given = mergedsupp[key]
                same = None

                if isinstance(value, str):
                    value = {VALUE: value}
                else:
                    for same in given:
                        if ID in same and same[ID] == value.get(ID):
                            break
                    else:
                        same = None

                if same:
                    same[ANNOTATION]['source'].append(suppref)
                else:
                    value[ANNOTATION] = {'source': [suppref]}

                if same is None:
                    given.append(value)

        if suppkey != supplement[ID]:
            mergedsupp[ID] = f'{workref[ID]}/{squote(suppkey)}'

    included.extend(mergedsupplements.values())


if __name__ == '__main__':
    data = json.load(sys.stdin)
    if GRAPH not in data:
        data = {GRAPH: [data]}
    walk(data)
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
