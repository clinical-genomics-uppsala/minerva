import argparse
import re
import networkx as nx

parser = argparse.ArgumentParser(
    description="Remove back edges from a Snakemake rulegraph .dot file so that it becomes acyclic (e.g. for snakevision)."
)
parser.add_argument("input", help="rulegraph .dot file produced by snakemake --rulegraph")
parser.add_argument("output", help="acyclic .dot file to write")
parser.add_argument(
    "--skip",
    nargs="*",
    default=[r"^_copy_"],
    metavar="REGEX",
    help="regexes matched (re.search) against rule names; matching rules are removed from the graph (default: ^_copy_)",
)
args = parser.parse_args()
src, dst = args.input, args.output
lines = open(src).read().splitlines()
label = {m.group(1): m.group(2) for line in lines if (m := re.match(r'\s*(\d+)\[label = "([^"]+)"', line))}
edge_re = re.compile(r'\s*(\d+)\s*->\s*(\d+)')
skip_res = [re.compile(r) for r in args.skip]
skipped = {n for n, name in label.items() if any(r.search(name) for r in skip_res)}
for n in sorted(skipped, key=int):
    print(f"skipping rule {label[n]}")
node_re = re.compile(r'\s*(\d+)\[label')
G = nx.DiGraph(
    (m.group(1), m.group(2))
    for line in lines
    if (m := edge_re.match(line)) and m.group(1) not in skipped and m.group(2) not in skipped
)
drop = set()
while True:
    try:
        u, v = nx.find_cycle(G)[-1][:2]
    except nx.NetworkXNoCycle:
        break
    print(f"dropping {label[u]} -> {label[v]}")
    G.remove_edge(u, v)
    drop.add((u, v))
out = []
for line in lines:
    if (m := edge_re.match(line)) and (m.group(1) in skipped or m.group(2) in skipped or (m.group(1), m.group(2)) in drop):
        continue
    if (m := node_re.match(line)) and m.group(1) in skipped:
        continue
    out.append(line)
open(dst, "w").write("\n".join(out) + "\n")
