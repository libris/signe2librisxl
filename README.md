# Signe Newspaper Data 2 Libris XL

## Fetch and Convert

Declare some useful environment variables:
```sh
$ USERPASS=abc:123 # NOTE: ask for correct credentials!
$ SIGNEAPI=http://$USERPASS@signetest.utv.kb.se/signe/rest
$ FROMTO="fromdate=1900-01-01&todate=$(date +%Y-%m-%d)"
$ TMPDATA=~/tmp/kb-signe # or any other location you prefer
```
Fetch one "bibliographic record" from the API:
```sh
$ curl -s "$SIGNEAPI/bibliographies/1?$FROMTO"
```
Fetch them all:
```sh
$ mkdir -p $TMPDATA
$ curl -s "$SIGNEAPI/bibliographies" |
  jq '.newspapers[] |.id' |
  xargs -IX curl -s "$SIGNEAPI/bibliographies/X?$FROMTO" -o $TMPDATA/X.json
```
## Convert

(This uses [TRLD](https://github.com/niklasl/trld) for JSON-LD processing and
TriG serialization. Clone or `pip install` that first into your `venv`.)

(In the calls below, you can remove the `-s` flag if you want to get *lots* of
entities, e.g. componentparts and newsbills.)

Convert one:
```sh
$ cat test/bibliographies-1-aftonbladet.json | ./convert.sh -s
```
Convert all:
```sh
$ python utils/jsondir2dataset.py $TMPDATA | ./convert.sh -s
```
## Auxiliary Data

## Geographic

The files `regions.ttl` and `context-regions.jsonld` were originally generated
from data in the VDD app
(<https://git.kb.se/vdd/VDD/-/blob/master/src/js/vdd/regions.js>), using
`utils/makeregiondata.js`. They have subsequently been somewhat edited.

Alas, we do not know the origin of the data in VDD. SCB have published various
data dumps (e.g. Excel files) about the A-regions, which we've been scavenging
so far. One goal here is to find or at worst establish a linked data source for
these.

The file `matching-places.ttl` was generated by running:
```sh
$ utils/construct.py regions.ttl match-places.rq
```

## Frequencies

The file `frequencies.ttl` was extracted from an original conversion run where
these were all local bnodes. The frequencies are few enough to warrant
definining "enums" for them, to facilitate both a consistent notation and I18N
of their labels. See also <https://id.loc.gov/vocabulary/frequencies>.

## Temporality

This data uses a qualification model of time, meaning that we use specific
qualified relations to capture relations restricted to a certain date range.

This has a precursor in the existing use of `provisionActivity` and structured
values, as well as following the rationale in the accepted BF 2.1 [Proposal:
pubFrequency/PubFrequency for recording complex frequency
information](https://github.com/lcnetdev/bibframe-ontology/issues/76).

Furthermore, as these qualifications relate to the instances of the serial that
were issued during a given period, we use the specific `firstIssue` and
`lastIssue` properties throughout to clearly reflect that.

Particularly, this can be used, e.g. in an application consuming this data, as
an indication that the qualified data applies to any issue (any entity linking
to a serial using `isIssueOf`) which has a `date` (of `publication`) that falls
within the qualified date range.
