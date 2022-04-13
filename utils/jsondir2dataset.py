#!/usr/bin/env python3
import pathlib, sys, json

dirpath = sys.argv[1]

print('{"@graph": [')

for i, fp in enumerate(pathlib.Path(dirpath).glob("*.json")):
    with fp.open() as f:
        data = json.load(f)
        data["@id"] = fp.name
        comma = ',' if i > 0 else ''
        print(comma, json.dumps(data))

print(']}')
