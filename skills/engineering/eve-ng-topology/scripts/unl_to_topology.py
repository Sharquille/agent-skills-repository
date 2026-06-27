#!/usr/bin/env python3
"""unl_to_topology.py — parse an EVE-NG .unl lab (XML) into structured
topology.json, or emit a Mermaid / Graphviz DOT diagram from it.

EVE-NG .unl is XML with a <lab> root containing <topology> with <nodes>,
<networks>, and per-node <interface> elements. An interface links to a network
via its `network_id`; nodes connected to the same network are adjacent. The
schema varies between Community and Pro, so this parser is defensive: unknown or
missing fields are reported under "_unmapped" rather than guessed.

Usage:
  unl_to_topology.py lab.unl                 # -> topology.json (stdout)
  unl_to_topology.py lab.unl --emit mermaid  # -> Mermaid graph
  unl_to_topology.py lab.unl --emit dot      # -> Graphviz DOT

Exit: 0 ok, 2 usage/parse error.
"""
import json
import sys
import xml.etree.ElementTree as ET


def parse_unl(path):
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        sys.stderr.write(f"error: cannot parse .unl XML: {e}\n")
        sys.exit(2)
    root = tree.getroot()

    nodes, networks, unmapped = {}, {}, []

    for net in root.iter("network"):
        nid = net.get("id")
        if nid is None:
            unmapped.append("network without id")
            continue
        networks[nid] = {
            "id": nid,
            "name": net.get("name") or f"net{nid}",
            "type": net.get("type") or "bridge",
        }

    for node in root.iter("node"):
        nid = node.get("id")
        if nid is None:
            unmapped.append("node without id")
            continue
        ifaces = []
        for itf in node.iter("interface"):
            ifaces.append({
                "id": itf.get("id"),
                "name": itf.get("name"),
                "network_id": itf.get("network_id"),
            })
        nodes[nid] = {
            "id": nid,
            "name": node.get("name") or f"node{nid}",
            "template": node.get("template") or node.get("type") or "generic",
            "x": node.get("left"), "y": node.get("top"),
            "interfaces": ifaces,
        }

    # links: nodes sharing a network are connected (skip cloud/NAT singletons)
    by_net = {}
    for n in nodes.values():
        for itf in n["interfaces"]:
            net = itf.get("network_id")
            if net:
                by_net.setdefault(net, []).append((n["id"], itf.get("name")))
    links = []
    for net, members in by_net.items():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                links.append({
                    "a": members[i][0], "a_if": members[i][1],
                    "b": members[j][0], "b_if": members[j][1],
                    "via_network": net,
                    "network_name": networks.get(net, {}).get("name", net),
                })

    return {
        "source": path,
        "nodes": list(nodes.values()),
        "networks": list(networks.values()),
        "links": links,
        "_unmapped": unmapped,
        "_counts": {"nodes": len(nodes), "networks": len(networks), "links": len(links)},
    }


def to_mermaid(topo):
    out = ["graph LR"]
    for n in topo["nodes"]:
        nid = f"n{n['id']}"
        out.append(f'  {nid}["{n["name"]}<br/><small>{n["template"]}</small>"]')
    seen = set()
    for l in topo["links"]:
        key = tuple(sorted((l["a"], l["b"]))) + (l["via_network"],)
        if key in seen:
            continue
        seen.add(key)
        out.append(f'  n{l["a"]} -- "{l["network_name"]}" --- n{l["b"]}')
    return "\n".join(out)


def to_dot(topo):
    out = ["graph topology {", '  rankdir=LR; node [shape=box, style=rounded];']
    for n in topo["nodes"]:
        out.append(f'  n{n["id"]} [label="{n["name"]}\\n{n["template"]}"];')
    seen = set()
    for l in topo["links"]:
        key = tuple(sorted((l["a"], l["b"]))) + (l["via_network"],)
        if key in seen:
            continue
        seen.add(key)
        out.append(f'  n{l["a"]} -- n{l["b"]} [label="{l["network_name"]}"];')
    out.append("}")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        sys.stderr.write(__doc__)
        return 2
    path = argv[1]
    emit = None
    if "--emit" in argv:
        try:
            emit = argv[argv.index("--emit") + 1]
        except IndexError:
            sys.stderr.write("error: --emit needs a value (json|mermaid|dot)\n")
            return 2
    topo = parse_unl(path)
    if topo["_unmapped"]:
        sys.stderr.write(f"warning: {len(topo['_unmapped'])} unmapped element(s); "
                         f"validate against the EVE-NG UI\n")
    if emit in (None, "json"):
        print(json.dumps(topo, indent=2))
    elif emit == "mermaid":
        print(to_mermaid(topo))
    elif emit == "dot":
        print(to_dot(topo))
    else:
        sys.stderr.write(f"error: unknown --emit {emit}\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
