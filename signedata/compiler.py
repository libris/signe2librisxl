import datetime
import json
import sys
from pathlib import Path


def jsonlines(fpath: Path, func):
    yield from lines(
        fpath,
        func,
        ser=lambda data: json.dumps(data, ensure_ascii=False),
        deser=json.loads,
    )


def pytuples(fpath: Path, func):
    yield from lines(
        fpath, func, ser=repr, deser=lambda s: eval(s, {'datetime': datetime})
    )


def lines(fpath: Path, func, *, ser, deser):
    fpath.parent.mkdir(parents=True, exist_ok=True)
    if fpath.exists() and fpath.stat().st_size > 0:
        print("Using cached:", fpath, file=sys.stderr)
        with fpath.open() as f:
            for l in f:
                yield deser(l)
    else:
        with fpath.open('w') as f:
            for data in func():
                print(ser(data), file=f)
                yield data


def build(desc_cfg, fpath: Path, convert, items):
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with fpath.open('w') as f:
        for item in items:
            if data := convert(item, desc_cfg):
                print(json.dumps(data, ensure_ascii=False), file=f)
