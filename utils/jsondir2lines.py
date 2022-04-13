#!/usr/bin/env python3
import pathlib, sys, json

dirpath = sys.argv[1]

for fp in pathlib.Path(dirpath).glob("*.json"):
    with fp.open() as f:
        data = json.load(f)
        data["@id"] = fp.name
        print(json.dumps(data))
