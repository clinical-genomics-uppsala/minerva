import argparse
import re
import networkx as nx

parser = argparse.ArgumentParser(
    description="Remove back edges from a Snakemake rulegraph .dot file so that it becomes acyclic (e.g. for snakevision)."
)
parser.add_argument("input", help="rulegraph .dot file produced by snakemake --rulegraph")
parser.add_argument("output", help="acyclic .dot file to write")
args = parser.parse_args()
src, dst = args.input, args.output
lines = open(src).read().splitlines()
label = {m.group(1): m.group(2) for line in lines if (m := re.match(r'\s*(\d+)\[label = "([^"]+)"', line))}
edge_re = re.compile(r'\s*(\d+)\s*->\s*(\d+)')
G = nx.DiGraph((m.group(1), m.group(2)) for line in lines if (m := edge_re.match(line)))
drop = set()
while True:
    try:
        u, v = nx.find_cycle(G)[-1][:2]
    except nx.NetworkXNoCycle:
        break
    print(f"dropping {label[u]} -> {label[v]}")
    G.remove_edge(u, v)
    drop.add((u, v))
out = [line for line in lines if not ((m := edge_re.match(line)) and (m.group(1), m.group(2)) in drop)]
open(dst, "w").write("\n".join(out) + "\n")
