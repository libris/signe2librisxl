#!/bin/bash
python3 -m trld -e context.jsonld - -c context-xl.jsonld | python3 fixups.py | python3 -m trld -i jsonld -o trig
