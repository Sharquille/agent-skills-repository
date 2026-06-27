#!/usr/bin/env python3
"""unl_to_topology.py — parse an EVE-NG .unl lab (XML) into structured
topology.json, or emit a Mermaid / Graphviz DOT diagram from it.

EVE-NG .unl is XML with a <lab> root containing <topology> with <nodes>,
<networks>, and per-node <interface> elements. An interface links to a network
via its `network_id`; nodes on the same network are adjacent. Validated against a
real EVE-NG Pro export. The schema varies between Community and Pro, so the
parser is defensive: unmapped elements are reported under "_unmapped".

Enrichments (presentation-grade):
- interface/link labels are preserved on edges (e.g. "WireGuard Tunnel UDP :51820")
- node icon/type is mapped to a role (router/server/docker/kali/linux/cloud)
- nodes with no <interface> are flagged isolated (rendered dashed, never given a
  fabricated edge)
- <textobjects> are decoded into a "zones" list (annotations like "Research Zone")

Device <config> blocks are intentionally NOT included — they leak certs/IPs and
must be redacted by the publication layer, not auto-embedded.

Usage:
  unl_to_topology.py lab.unl                 # -> topology.json (stdout)
  unl_to_topology.py lab.unl --emit mermaid  # -> Mermaid graph
  unl_to_topology.py lab.unl --emit dot      # -> Graphviz DOT

Exit: 0 ok, 2 usage/parse error.
"""
import base64
import json
import re
import sys
import xml.etree.ElementTree as ET

_TAG = re.compile(r"<[^>]+>")


def _role(template, ntype, icon):
    blob = " ".join(x for x in (template, ntype, icon) if x).lower()
    if "kali" in blob:
        return "kali"
    if "router" in blob or "csr" in blob or "ios" in blob or "_fw" in blob or "firewall" in blob:
        return "router"
    if "docker" in blob:
        return "docker"
    if "winserver" in blob or "server" in blob or "win" in blob:
        return "server"
    if "cloud" in blob or "pnet" in blob:
        return "cloud"
    if "linux" in blob:
        return "linux"
    return "generic"


def parse_unl(path):
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        sys.stderr.write(f"error: cannot parse .unl XML: {e}\n")
        sys.exit(2)
    root = tree.getroot()

    nodes, networks, zones, unmapped = {}, {}, [], []

    for net in root.iter("network"):
        nid = net.get("id")
        if nid is None:
            unmapped.append("network without id")
            continue
        networks[nid] = {"id": nid, "name": net.get("name") or f"net{nid}",
                         "type": net.get("type") or "bridge"}

    for node in root.iter("node"):
        nid = node.get("id")
        if nid is None:
            unmapped.append("node without id")
            continue
        ifaces = [{"id": i.get("id"), "name": i.get("name"),
                   "network_id": i.get("network_id"), "label": i.get("label")}
                  for i in node.iter("interface")]
        nodes[nid] = {
            "id": nid, "name": node.get("name") or f"node{nid}",
            "template": node.get("template") or node.get("type") or "generic",
            "type": node.get("type"), "icon": node.get("icon"),
            "role": _role(node.get("template"), node.get("type"), node.get("icon")),
            "x": node.get("left"), "y": node.get("top"),
            "interfaces": ifaces, "isolated": len(ifaces) == 0,
        }

    # zone annotations: decode base64 HTML in <textobject type="text">
    for tobj in root.iter("textobject"):
        if tobj.get("type") != "text":
            continue
        data = tobj.findtext("data")
        if not data:
            continue
        try:
            html = base64.b64decode(data).decode("utf-8", "ignore")
        except Exception:
            continue
        text = _TAG.sub("", html).strip()
        if text:
            zones.append({"id": tobj.get("id"), "text": text})

    # links: nodes sharing a network are connected; carry interface labels
    by_net = {}
    for n in nodes.values():
        for itf in n["interfaces"]:
            net = itf.get("network_id")
            if net:
                by_net.setdefault(net, []).append((n["id"], itf.get("name"), itf.get("label")))
    links = []
    for net, members in by_net.items():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                labels = [m for m in (members[i][2], members[j][2]) if m]
                links.append({
                    "a": members[i][0], "a_if": members[i][1],
                    "b": members[j][0], "b_if": members[j][1],
                    "via_network": net,
                    "network_name": networks.get(net, {}).get("name", net),
                    "labels": labels,
                })

    return {
        "source": path,
        "nodes": list(nodes.values()),
        "networks": list(networks.values()),
        "links": links,
        "zones": zones,
        "_unmapped": unmapped,
        "_counts": {"nodes": len(nodes), "networks": len(networks),
                    "links": len(links), "zones": len(zones),
                    "isolated": sum(1 for n in nodes.values() if n["isolated"])},
    }


def _edge_label(l):
    parts = [l["network_name"]] + l.get("labels", [])
    return " · ".join(p for p in parts if p)


def to_mermaid(topo):
    out = ["graph LR",
           "  classDef kali fill:#2b2b2b,color:#fff,stroke:#7a3;",
           "  classDef router fill:#1f3a5f,color:#fff,stroke:#4a90d9;",
           "  classDef server fill:#3a2f1f,color:#fff,stroke:#d99a4a;",
           "  classDef docker fill:#13344f,color:#fff,stroke:#2496ed;",
           "  classDef cloud fill:#2a2a2a,color:#fff,stroke:#888;",
           "  classDef isolated stroke-dasharray:5 5,stroke:#c55,color:#c55;"]
    for n in topo["nodes"]:
        nid = f"n{n['id']}"
        note = " ⚠ unwired in .unl" if n["isolated"] else ""
        out.append(f'  {nid}["{n["name"]}<br/><small>{n["role"]}{note}</small>"]')
        cls = "isolated" if n["isolated"] else n["role"]
        if cls in ("kali", "router", "server", "docker", "cloud", "isolated"):
            out.append(f"  class {nid} {cls};")
    seen = set()
    for l in topo["links"]:
        key = tuple(sorted((l["a"], l["b"]))) + (l["via_network"],)
        if key in seen:
            continue
        seen.add(key)
        out.append(f'  n{l["a"]} -- "{_edge_label(l)}" --- n{l["b"]}')
    if topo["zones"]:
        out.append("  %% zones (annotations from .unl textobjects):")
        for z in topo["zones"]:
            out.append(f'  %%   - {z["text"]}')
    return "\n".join(out)


def to_dot(topo):
    out = ["graph topology {", '  rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica"];']
    style = {"kali": '#2b2b2b", fontcolor="white',
             "router": '#1f3a5f", fontcolor="white',
             "server": '#3a2f1f", fontcolor="white',
             "docker": '#13344f", fontcolor="white',
             "cloud": '#2a2a2a", fontcolor="white',
             "linux": '#333333", fontcolor="white',
             "generic": '#444444", fontcolor="white'}
    for n in topo["nodes"]:
        fill = style.get(n["role"], style["generic"])
        extra = ', style="rounded,filled,dashed", color="#cc5555"' if n["isolated"] else ""
        label = n["name"] + ("\\n(unwired in .unl)" if n["isolated"] else f"\\n{n['role']}")
        out.append(f'  n{n["id"]} [label="{label}", fillcolor="{fill}"{extra}];')
    seen = set()
    for l in topo["links"]:
        key = tuple(sorted((l["a"], l["b"]))) + (l["via_network"],)
        if key in seen:
            continue
        seen.add(key)
        out.append(f'  n{l["a"]} -- n{l["b"]} [label="{_edge_label(l)}"];')
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
    if topo["_counts"]["isolated"]:
        sys.stderr.write(f"note: {topo['_counts']['isolated']} isolated node(s) "
                         f"(present in .unl but no <interface>); rendered dashed, not wired\n")
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
