#!/usr/bin/env python3
from rdflib import Graph
from sys import argv, stdout

g = Graph()

queryfile = argv[1]

if len(argv) > 2:
    for infile in argv[2:]:
        g.parse(infile)

with open(queryfile) as f:
    res = g.query(f.read())

res.serialize(stdout.buffer, format='turtle')
