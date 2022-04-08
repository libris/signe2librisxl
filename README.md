# Signe Newspaper Data 2 Libris XL

## Fetch and Convert

Fetch one "bibliographic record" from the API:
```sh
$ USERPASS=abc:123 # NOTE: ask for correct credentials!

$ curl -su "$USERPASS" "http://signetest.utv.kb.se/signe/rest/bibliographies/1?fromdate=1900-01-01&todate=$(date +%Y-%m-%d)"
```
Fetch them all:
```sh
$ time curl -su "$USERPASS" 'http://signetest.utv.kb.se/signe/rest/bibliographies' | jq '.newspapers[] |.id' | xargs -IX curl -su "$USERPASS" "http://signetest.utv.kb.se/signe/rest/bibliographies/X?fromdate=1900-01-01&todate=$(date +%Y-%m-%d)" -o ~/tmp/kb-signe/X.json
```
## Convert

(This uses [TRLD](https://github.com/niklasl/trld) for JSON-LD processing and
TriG serialization. Clone or `pip install` that first into your `venv`.)

Convert one (remove `-s` to get *lots of entities*, e.g. componentparts and newsbills):
```sh
$ cat test/bibliographies-1-aftonbladet.json | ./convert.sh -s
```
Convert all:
```sh
$ python jsondir2lines.py ~/tmp/kb-signe | awk -F$'\n' 'BEGIN { print "{\"@graph\": [" } { if (NR > 1) printf ", "; print $0 } END { print "]}" }' | ./convert.sh -s
```
