#!/bin/bash
getopts 's' OPT
if [[ $OPT == 's' ]]; then
    CONTEXT=context-short.jsonld
else
    CONTEXT=context.jsonld
fi

python3 -m trld -e $CONTEXT - -c context-xl.jsonld | python3 fixups.py | python3 -m trld -i jsonld -o trig
