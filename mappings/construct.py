#!/usr/bin/env python3
from rdflib import Graph
from sys import argv, stdout

infile, queryfile = argv[1:3]

g = Graph().parse(infile)
with open(queryfile) as f:
    res = g.query(f.read())

res.serialize(stdout.buffer, format='turtle')
