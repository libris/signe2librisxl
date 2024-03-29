import json
from urllib.parse import quote, unquote
from trld.jsonld.compaction import compact
from trld.jsonld.expansion import expand

from .util import asiter, get_etc_path


ANNOTATION = '@annotation'
BASE = '@base'
CONTEXT = '@context'
GRAPH = '@graph'
ID = '@id'
INCLUDED = '@included'
REVERSE = '@reverse'
TYPE = '@type'
VALUE = '@value'
VOCAB = '@vocab'

ID_BASE = 'https://id.kb.se/'
KBV = 'https://id.kb.se/vocab/'

REVERSE_INSTANCE_RELATION = False

CONTEXT_DATA = {
    VOCAB: KBV,
    BASE: 'https://signe.kb.se/',
}

ID_RULES = {
    None: ('bib_base_uri', 'id'),
    GRAPH: ('bib_base_uri', 'id'),
    'hasInstance': ('instance_base_uri', 'id'),
    'hasPart': ('part_base_uri', 'id'),
    'generatedEdition': ('edition_base_uri', 'id'),
    'associatedNewsBill': ('newsbill_base_uri', 'id'),
    'hasSupplement': ('supplement_base_uri', 'id'),
    'politicalTendency': ('politicalTendency', 'political_base_uri', 'label'),
}

top_type_rule = ('Text', 'Serial', 'https://id.kb.se/term/saogf/Dagstidningar')
TYPE_RULES = {
    None: top_type_rule,
    GRAPH: top_type_rule,
    'hasTitle': ('VariantTitle', None, None),
    'manufacture': ('Manufacture', None, None),
    'geographicCoverage': ('GeographicCoverage', None, None),
    'frequencyPeriod': ('FrequencyPeriod', None, None),
    'politicalTendencyPeriod': ('PoliticalTendencyPeriod', None, None),
    'politicalTendency': ('PoliticalTendency', None, None),
    'languagePeriod': ('LanguagePeriod', None, None),
    'hasPart': ('Text', 'SerialComponentPart', 'https://id.kb.se/term/repr/Tidningsdel'),
    'generatedEdition': ('SerialEdition', None, None),
    'associatedNewsBill': ('Text', 'SerialComponentPart', 'https://id.kb.se/term/repr/L%F6psedel'),
    'hasSupplement': ('Text', 'SerialComponentPart', 'https://id.kb.se/term/repr/Tidningsbilaga'),
}

LANGUAGE_MAP = {
    'svenska': 'https://id.kb.se/language/swe',
    'finska': 'https://id.kb.se/language/fin',
    'engelska': 'https://id.kb.se/language/eng',
    'arabiska': 'https://id.kb.se/language/ara',
    'bosniska': 'https://id.kb.se/language/bos',
    'estniska': 'https://id.kb.se/language/est',
    'spanska': 'https://id.kb.se/language/spa',
}


def lang_desc(l):
    if l not in LANGUAGE_MAP:
        return {TYPE: 'Language', 'labelByLang': {'sv': l}}
    return {ID: LANGUAGE_MAP[l]}


def convert(bibdoc, cfg={}):
    context = cfg['context']
    base_iri = None
    data = expand(bibdoc, base_iri, get_etc_path(context).as_uri())
    data = compact(get_etc_path('context-xl.jsonld').as_uri(), data)

    walk(cfg, data)
    del data[CONTEXT]

    return data


def walk(cfg, data, via=None, owner=None):
    at_dataset_root = via in {None, GRAPH}

    if isinstance(data, list):
        for li in data:
            walk(cfg, li, via, owner)
        while {} in data:
            data.remove({})
        if via == GRAPH:
            for li in iter(data):
                data.extend(li.pop(INCLUDED, []))
        return

    if not isinstance(data, dict):
        id_rule = ID_RULES.get(via)
        if id_rule:
            link, base_id_key, *parts = id_rule
            del owner[via]
            base_id = cfg.get(base_id_key)
            if base_id:
                owner[link] = {ID: base_id + squote(data)}
            else:
                key = parts[0]
                rtype = TYPE_RULES[link][0]
                owner[link] = {"@type": rtype, key: data}
        return

    # Pre-Walk
    new_id = None

    id_rule = ID_RULES.get(via)
    if id_rule:
        base_id_key, key = id_rule
        base_id = cfg.get(base_id_key)

        if key in data:
            value = squote(str(data.pop(key)).encode('utf8'))
        if base_id:
            new_id = base_id + value

    _normalize_frequency(data)

    if at_dataset_root:
        data['@context'] = CONTEXT_DATA

    # Drop and re-add "at the top" below
    hastitle = list(asiter(data.pop('hasTitle', None)))

    # Set top title to Title
    if at_dataset_root and 'title' in data:
        data['hasTitle'] = [
            {
                TYPE: 'Title',
                'mainTitle': data.pop('title')
            }
        ] + hastitle

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
            data['issuanceType'] = itype
        if gform:
            data['genreForm'] = {ID: gform}

    if hastitle:
        data['hasTitle'] = hastitle
        walk(cfg, hastitle, 'hasTitle', data)


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
            assert False, (via, 'id', k)
            #data['exactMatch'] = {ID: f'signe:{via}/{v}'}

        if k == 'placeLabel':
            data['place'] = {'label': v}

        elif k == 'sameAs':
            data[ID] = v[ID]

        elif k == 'language':
            data['language'] = [
                lang_desc(l.strip()) for l in v.split(',')
            ]

        elif k == 'periodOfPublication':
            v = data['temporalCoverage'] = {
                TYPE: 'TemporalCoverage',
                'issuePeriod': v
            }

        elif k == 'regionCode':
            assert via == 'geographicCoverage'
            aregion_base_uri = cfg.get('aregion_base_uri')
            data['place'] = [
                (
                    {ID: aregion_base_uri +code}
                    if aregion_base_uri
                    else {TYPE: 'GeographicCoverage', 'code': code}
                )
                for code in v.split(', ')
            ]

        elif k == 'issuePeriod':
            startdate, enddate = _parse_date_range(v)
            if startdate:
                data['firstIssueDate'] = startdate
            if enddate:
                data['lastIssueDate'] = enddate

        else:
            data[k] = v

        walk(cfg, v, via=k, owner=data)


    # Post-Walk

    # Set specific title types
    for title in hastitle:
        if 'lastIssueDate' in title:
            title[TYPE] = 'FormerTitle'

    workref = {ID: data[ID]} if ID in data else None
    included = []
    reverses = {}

    if workref and 'hasInstance' in data:
        instances = list(asiter(data['hasInstance']))

        if REVERSE_INSTANCE_RELATION:
            del data['hasInstance']

        iprint = None
        for inst in instances:
            #inst['instanceOf'] = workref
            if iprint is None and inst[TYPE] == 'Print':
                iprint = inst

        if 'production' in data:
            microform = {
                ID: f'{data[ID]}/microform',
                TYPE: 'Microform',
                'issuanceType': 'Serial',
                #'instanceOf': workref,
            }
            microform['production'] = [
                dict({TYPE: 'Production'}, **prod)
                for prod in asiter(data.pop('production'))
            ]
            instances.append(microform)

        if REVERSE_INSTANCE_RELATION:
            reverses.setdefault('instanceOf', []).extend(instances)

        # De-duplicates on place name and generated...
        _process_manufacture_data(data, iprint, included)

    _process_supplements(data, workref, included)

    if reverses:
        data.setdefault(REVERSE, {}).update(reverses)

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
            # TODO: map segments to linked frequency form
            #code = ifreq.pop('code')
            #if code.split('/', 1)[0].isdigit() and 'daysOfWeek' in ifreq:
            #    weekdays = ifreq.pop('daysOfWeek').replace(' ', '')
            #    if weekdays:
            #        timeofday = ifreq.get('timeOfDay')
            #        todcode = timeofday.replace(' ', '') if timeofday else None
            #        if todcode and todcode.isalpha():
            #            ifreq_id = f'{ID_BASE}freq/{code}-{weekdays}@{todcode}'
            #            del ifreq['timeOfDay']
            #        elif not timeofday:
            #            ifreq_id = f'{ID_BASE}freq/{code}-{weekdays}'
            #else:
            #    ifreq_id = f"{ID_BASE}freq/{code.replace(' ', '_')}"

            if ifreq_id:
                ifreq[ID] = ifreq_id
            else:
                ifreq[TYPE] = 'Frequency'
                #ifreq['label'] = code


def _process_manufacture_data(data, iprint, included):
    manufacture = list({
        (
            repr(printing.get('place', {})),
            '|'.join(sorted(x[ID] for x in asiter(printing.get('generatedEdition'))))
        ): printing
        for printing in asiter(data.pop('manufacture', None))
        if len(printing) > 1 or TYPE not in printing
    }.values())

    if manufacture:
        toinclude = []
        for printing in manufacture:
            editions = printing.pop('generatedEdition', None)
            for edition in asiter(editions):
                if len(printing) > 1 or TYPE not in printing:
                    edition.setdefault('manufacture', []).append(printing)
                edition['isEditionOf'] = {ID: iprint[ID]}
                toinclude.append(edition)

        included.extend(toinclude)


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


def squote(s: str):
    return quote(s, safe='/,@')


def _parse_date_range(v):
    startdate, sep, enddate = v.partition('--')
    return startdate.strip() or None, enddate.strip() or None


if __name__ == '__main__':
    import sys

    data = json.load(sys.stdin)
    data = convert(data)
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
