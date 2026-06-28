#!/usr/bin/env python3
"""design_unl.py — context-driven, presentable EVE-NG Pro .unl designer.

You describe the lab by TRUST TIERS (what lives in each zone); the tool computes
an elegant, aligned layout: tiers become evenly-spaced columns, nodes stack
inside them, each tier gets a NON-OVERLAPPING zone rectangle with a title +
subnet header, and every node gets an IP label under its icon. The result is a
valid .unl that imports into EVE-NG Pro.

SCAFFOLD, DON'T CONFIGURE (inherited from generate_unl.py): device `config` is
embedded VERBATIM; the tool never edits, fixes, or invents config. IPs in the
spec are display labels only — generic placeholders are fine.

The design is computed from CONTEXT, not a fixed template: change the tiers/nodes
and the layout, zones, and labels recompute. Coordinates are never hand-placed.

Usage:
  design_unl.py design.json > lab.unl
  design_unl.py --example > design.json     # sample design to adapt
  design_unl.py design.json --catalog catalog.json

Design JSON:
  {
    "lab": {"name": "...", "author": ""},
    "networks": {"lab_lan": {"type":"bridge","name":"LAB_LAN 10.10.70.0/24","icon":"lan.png"}, ...},
    "tiers": [
      {"title":"LAB / SUBJECT", "color":"green", "subnet":"10.10.70.0/24",
       "items":[{"node":{"name":"Kali","template":"linux","image":"linux-kali","icon":"Kali.png",
                         "ip":"10.10.70.10/24","ifaces":[{"name":"e0","net":"lab_lan"}]}}]},
      ...
    ]
  }
An item is either {"node": {...}} or {"network": "<network-key>"} (to place a
cloud/bridge icon inside a tier). iface: {name, net(key), label?}.
"""
import sys, os, json, argparse, base64
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_unl  # reuse node/network/config emission + template profiles

# --- layout constants (pixels on the EVE-NG canvas) ----------------------------
X0, COL_W = 230, 250          # first tier centre, spacing between tiers
ZW = 200                      # zone width (< COL_W -> guaranteed no overlap)
ZONE_TOP, HEADER, ROW_H = 110, 74, 132   # zone top, header height, row pitch
PAD_BOTTOM = 22

COLORS = {  # fill [r,g,b,a], stroke [r,g,b,a]  (alpha 0-1)
    "green":  ([113, 167, 153, 0.41], [0, 100, 0, 1]),
    "purple": ([128, 0, 255, 0.27],   [70, 0, 130, 1]),
    "blue":   ([0, 128, 255, 0.17],   [0, 70, 130, 1]),
    "red":    ([255, 99, 71, 0.20],   [128, 0, 0, 1]),
    "amber":  ([255, 176, 32, 0.20],  [150, 90, 0, 1]),
    "slate":  ([100, 116, 139, 0.20], [51, 65, 85, 1]),
}

def _b64(html): return base64.b64encode(html.encode()).decode()

def _shape_html(i, left, top, w, h, fill, stroke, dash="10,10"):
    r, g, b, a = fill; sr, sg, sb, sa = stroke
    return (f'<div id="customShape{i}" class="customShape context-menu resizable-content" '
            f'style="display:inline; z-index:998; width:{w}px; height:{h}px; visibility:visible; '
            f'position:absolute; left:{left}px; top:{top}px;" data-jtk-managed="customShape{i}">\n'
            f'  <svg width="{w}px" height="{h}px">\n'
            f'    <rect x="2" y="2" width="{w-2}px" height="{h-2}px" rx="18" ry="18" '
            f'fill="rgba({r}, {g}, {b}, {a})" stroke="rgba({sr}, {sg}, {sb}, {sa})" '
            f'stroke-width="1.5" stroke-dasharray="{dash}"></rect>\n  </svg>\n</div>')

def _label_html(i, left, top, text, bold=False):
    inner = f"<strong>{text}</strong>" if bold else text
    return (f'<div id="customText{i}" class="customText customShape context-menu ck ck-content '
            f'resizable-content" data-jtk-managed="customText{i}" style="z-index:1000; cursor:move; '
            f'display:inline; width:auto; height:auto; visibility:visible; position:absolute; '
            f'left:{left}px; top:{top}px;"><p>{inner}</p></div>')

def design(spec, catalog=None):
    tiers = spec["tiers"]
    netdefs = spec.get("networks", {})
    # rows-per-tier and the global (aligned) zone height
    rows = [len(t["items"]) for t in tiers]
    max_rows = max(rows) if rows else 1
    zone_h = HEADER + max_rows * ROW_H + PAD_BOTTOM

    nodes, networks, shapes, labels = [], [], [], []
    netkey_to_id, used = {}, set()
    nid_counter = [0]
    def new_net_id():
        nid_counter[0] += 1
        while nid_counter[0] in used: nid_counter[0] += 1
        used.add(nid_counter[0]); return nid_counter[0]

    # pre-assign network ids referenced by interfaces
    for key in netdefs: netkey_to_id[key] = new_net_id()

    node_id = 0
    for ti, tier in enumerate(tiers):
        cx = X0 + ti * COL_W
        zleft = cx - ZW // 2
        fill, stroke = COLORS.get(tier.get("color", "slate"), COLORS["slate"])
        shapes.append((zleft, ZONE_TOP, ZW, zone_h, fill, stroke))
        labels.append((zleft + 14, ZONE_TOP + 10, tier["title"], True))
        if tier.get("subnet"):
            labels.append((zleft + 14, ZONE_TOP + 40, tier["subnet"], False))
        y = ZONE_TOP + HEADER
        for item in tier["items"]:
            if "network" in item:
                key = item["network"]; nd = netdefs[key]
                networks.append(dict(id=netkey_to_id[key], type=nd.get("type", "bridge"),
                                     name=nd.get("name", key), icon=nd.get("icon", "lan.png"),
                                     left=cx - 30, top=y, visibility=1))
            else:
                n = item["node"]; node_id += 1; used.add(node_id)
                ifaces = [dict(name=i["name"], network=netkey_to_id[i["net"]],
                               **({"label": i["label"]} if i.get("label") else {}))
                          for i in n.get("ifaces", [])]
                node = dict(id=node_id, name=n["name"], template=n["template"], image=n["image"],
                            icon=n.get("icon"), left=cx - 30, top= y, ifaces=ifaces)
                for k in ("cpu", "ram", "console", "type"):
                    if k in n: node[k] = n[k]
                if n.get("config"): node["config_file"] = n["config"]
                nodes.append(node)
                if n.get("ip"):
                    labels.append((cx - 56, y + 64, n["ip"], False))
            y += ROW_H

    # place any networks not visually pinned into a tier (referenced but not listed)
    placed = {nw["id"] for nw in networks}
    for key, nid in netkey_to_id.items():
        if nid not in placed:
            nd = netdefs[key]
            networks.append(dict(id=nid, type=nd.get("type", "bridge"), name=nd.get("name", key),
                                 icon=nd.get("icon", "lan.png"), left=0, top=0, visibility=0))

    gen_spec = {"lab": spec.get("lab", {}), "nodes": nodes, "networks": networks}
    base = generate_unl.generate(gen_spec, catalog)

    # inject textobjects (zones first so labels render on top)
    root = ET.fromstring(base)
    objects = root.find("objects")
    if objects is None:
        objects = ET.Element("objects"); root.append(objects)
    tos = ET.Element("textobjects")
    objects.insert(0, tos)
    tid = 1000
    for (l, t, w, h, fill, stroke) in shapes:
        to = ET.SubElement(tos, "textobject", id=str(tid), name="", type="square")
        ET.SubElement(to, "data").text = _b64(_shape_html(tid, l, t, w, h, fill, stroke)); tid += 1
    for (l, t, text, bold) in labels:
        to = ET.SubElement(tos, "textobject", id=str(tid), name=text[:32], type="text")
        ET.SubElement(to, "data").text = _b64(_label_html(tid, l, t, text, bold)); tid += 1

    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + \
           ET.tostring(root, encoding="unicode")

EXAMPLE = {
    "lab": {"name": "osint-egress-lab", "author": ""},
    "networks": {
        "lab_lan":  {"type": "bridge",   "name": "LAB_LAN 10.10.70.0/24",   "icon": "lan.png"},
        "transit":  {"type": "bridge",   "name": "TRANSIT 192.168.1.0/24",  "icon": "lan.png"},
        "cloud0":   {"type": "pnet0",    "name": "Cloud0 192.168.100.0/24", "icon": "Cloud-2D-Green-S.svg"},
        "internet": {"type": "internal", "name": "Internet",                "icon": "Cloud-2D-Blue-S.svg"},
    },
    "tiers": [
        {"title": "LAB / SUBJECT", "color": "green", "subnet": "10.10.70.0/24", "items": [
            {"node": {"name": "Kali", "template": "linux", "image": "linux-kali", "icon": "Kali.png",
                      "ip": "10.10.70.10/24", "ifaces": [{"name": "e0", "net": "lab_lan"}]}}]},
        {"title": "GATEWAY DMZ", "color": "purple", "subnet": "transit 192.168.1.0/24", "items": [
            {"node": {"name": "Ubuntu-GW", "template": "linux", "image": "linux-ubuntu-22.04.02-server",
                      "icon": "local-network-gateways.svg", "ip": "lan .1 / wan .2",
                      "ifaces": [{"name": "e0", "net": "lab_lan"}, {"name": "e1", "net": "transit"}]}}]},
        {"title": "EDGE / WAN", "color": "blue", "subnet": "Cloud0 192.168.100.0/24", "items": [
            {"node": {"name": "CSR1000v", "template": "csr1000vng", "image": "csr1000vng-universalk9.17.03.05-serial",
                      "icon": "Router_FW.png", "ip": "Gi1 .254 / Gi2 .1",
                      "ifaces": [{"name": "Gi1", "net": "cloud0"}, {"name": "Gi2", "net": "transit"}]}},
            {"network": "cloud0"},
            {"node": {"name": "ISP", "template": "docker", "image": "eve-gui-server:latest", "icon": "Winserver.png",
                      "ifaces": [{"name": "eth0", "net": "cloud0", "label": "WireGuard UDP :51820"},
                                 {"name": "eth1", "net": "internet"}]}}]},
        {"title": "INTERNET / VPN", "color": "red", "subnet": "VPN egress", "items": [
            {"network": "internet"},
            {"node": {"name": "Mullvad", "template": "winserver", "image": "winserver-2022R2",
                      "icon": "Server_Win.png", "ifaces": [{"name": "e0", "net": "internet"}]}}]},
    ],
}

def main():
    ap = argparse.ArgumentParser(description="Context-driven, presentable EVE-NG Pro .unl designer.")
    ap.add_argument("design", nargs="?", help="design spec JSON (omit with --example)")
    ap.add_argument("--example", action="store_true", help="print a sample design and exit")
    ap.add_argument("--catalog", help="node catalog JSON; warn on images not present")
    args = ap.parse_args()
    if args.example:
        print(json.dumps(EXAMPLE, indent=2)); return
    if not args.design:
        ap.error("provide a design file or --example")
    spec = json.load(open(args.design))
    catalog = json.load(open(args.catalog)) if args.catalog else None
    sys.stdout.write(design(spec, catalog))

if __name__ == "__main__":
    main()
