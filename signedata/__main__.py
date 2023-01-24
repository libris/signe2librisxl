import sys
from configparser import ConfigParser
from pathlib import Path

from . import bibdocmapper, bibrowmapper, compiler, signeapi, signesql

cfg = ConfigParser()
args = sys.argv[1:]
cfg.read(args.pop(0) if args else 'signe.ini')

api_url = cfg['signe']['api_url']
sql_connection = cfg['signe']['sql_connection']
cache_dir = Path(cfg['compiler'].get('cache', 'cache')).expanduser()
build_dir = Path(cfg['compiler'].get('build', 'build')).expanduser()

desc_cfg = cfg['description']

bibrows = compiler.pytuples(
    cache_dir / 'bib.pydbtuples', lambda: signesql.dump(sql_connection, 'Bibliografi')
)

paperids = set()
def siphon_paperid(row): paperids.add(row[1]); return row

editionrows = (siphon_paperid(row) for row in bibrows if row[2] == 8)

compiler.build(desc_cfg, (build_dir / 'editions.jsonld.lines'), bibrowmapper.convert, editionrows)

bibdocs = compiler.jsonlines(
    cache_dir / 'bib.jsonl', lambda: signeapi.fetch_bibliographies(api_url, paperids)
)

compiler.build(desc_cfg, (build_dir / 'bibs.jsonld.lines'), bibdocmapper.convert, bibdocs)
