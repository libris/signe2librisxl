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

bibdocs = compiler.jsonlines(
    cache_dir / 'bib.jsonl', lambda: signeapi.fetch_bibliographies(api_url)
)
bibrows = compiler.pytuples(
    cache_dir / 'bib.pydbtuples', lambda: signesql.dump(sql_connection, 'Bibliografi')
)

editionrows = filter(lambda row: row[2] == 8, bibrows)

desc_cfg = cfg['description']

compiler.build(desc_cfg, (build_dir / 'bibs.jsonld.lines'), bibdocmapper.convert, bibdocs)
compiler.build(desc_cfg, (build_dir / 'editions.jsonld.lines'), bibrowmapper.convert, editionrows)
