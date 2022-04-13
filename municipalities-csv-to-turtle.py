from rdflib import Graph, URIRef, Namespace, Literal

# csv generated from https://www.scb.se/contentassets/c4b8142033a9440ca53725ca32321a74/a_regioner.xls
with open('a-regioner.csv') as f:
    all_lines = f.readlines()

g = Graph()
tmp_ns = Namespace('http://tmp/')

current_region = None
for line in all_lines:
    region_code, region_label, muni_code, muni_label = line.split(',')
    if region_code and region_label:
        current_region = URIRef(tmp_ns + 'region/' + region_code)
        triple = (current_region, URIRef(tmp_ns + 'regionCode'), Literal(region_code))
        g.add(triple)
    if current_region and muni_code and muni_label:
        triple = (current_region, URIRef(tmp_ns + 'muniCode'), Literal(muni_code))
        g.add(triple)

g.serialize(format='turtle', destination='municipality-codes.ttl')