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
import sys, os, json, argparse, base64, random, math
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
    gid = f"grad{i}"; top_a = round(a * 0.45, 3)   # subtle top-lighter vertical gradient
    return (f'<div id="customShape{i}" class="customShape context-menu resizable-content" '
            f'style="display:inline; z-index:998; width:{w}px; height:{h}px; visibility:visible; '
            f'position:absolute; left:{left}px; top:{top}px;" data-jtk-managed="customShape{i}">\n'
            f'  <svg width="{w}px" height="{h}px">\n'
            f'    <defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="rgba({r}, {g}, {b}, {top_a})"/>'
            f'<stop offset="100%" stop-color="rgba({r}, {g}, {b}, {a})"/></linearGradient></defs>\n'
            f'    <rect x="2" y="2" width="{w-2}px" height="{h-2}px" rx="18" ry="18" '
            f'fill="url(#{gid})" stroke="rgba({sr}, {sg}, {sb}, {sa})" '
            f'stroke-width="1.5" stroke-dasharray="{dash}"></rect>\n  </svg>\n</div>')

def _label_html(i, left, top, text, bold=False, mono=False):
    inner = f"<strong>{text}</strong>" if bold else text
    font = "font-family:'Menlo','Consolas',monospace; " if mono else ""   # scannable IPs/subnets
    return (f'<div id="customText{i}" class="customText customShape context-menu ck ck-content '
            f'resizable-content" data-jtk-managed="customText{i}" style="z-index:1000; cursor:move; '
            f'display:inline; width:auto; height:auto; visibility:visible; position:absolute; '
            f'{font}left:{left}px; top:{top}px;"><p>{inner}</p></div>')

def _link_style(dist):
    """Pick an EVE-NG link style by endpoint distance: short = straight, longer = bezier
    flow with curvature scaled by distance."""
    if dist < 140:
        return ("Straight", 10, 150)
    return ("Bezier", min(12 + int(dist / 6), 120), min(120 + int(dist / 2), 480))

def design(spec, catalog=None):
    tiers = spec["tiers"]
    netdefs = spec.get("networks", {})
    # rows-per-tier and the global (aligned) zone height
    rows = [len(t["items"]) for t in tiers]
    max_rows = max(rows) if rows else 1
    zone_h = HEADER + max_rows * ROW_H + PAD_BOTTOM

    nodes, networks, shapes, labels = [], [], [], []
    # node-id and network-id are separate EVE-NG namespaces; number each from 1.
    netkey_to_id = {key: i + 1 for i, key in enumerate(netdefs)}
    net_endpoints, link_refs = {}, []     # net key -> [(x,y)]; (iface, node_center, net_key)
    node_id = 0
    for ti, tier in enumerate(tiers):
        cx = X0 + ti * COL_W
        zleft = cx - ZW // 2
        fill, stroke = COLORS.get(tier.get("color", "slate"), COLORS["slate"])
        shapes.append((zleft, ZONE_TOP, ZW, zone_h, fill, stroke))
        labels.append((zleft + 14, ZONE_TOP + 10, tier["title"], True, False))
        if tier.get("subnet"):
            labels.append((zleft + 14, ZONE_TOP + 40, tier["subnet"], False, True))
        y = ZONE_TOP + HEADER
        for item in tier["items"]:
            if "network" in item:
                key = item["network"]; nd = netdefs[key]
                networks.append(dict(id=netkey_to_id[key], type=nd.get("type", "bridge"),
                                     name=nd.get("name", key), icon=nd.get("icon", "lan.png"),
                                     left=cx - 30, top=y, visibility=1))
                net_endpoints.setdefault(key, []).append((cx, y + 20))
            else:
                n = item["node"]; node_id += 1
                center = (cx, y + 28)
                ifaces = []
                for i in n.get("ifaces", []):
                    if i["net"] not in netkey_to_id:
                        raise SystemExit(f"node {n['name']!r} iface {i['name']!r} references "
                                         f"unknown network {i['net']!r}")
                    itf = dict(name=i["name"], network=netkey_to_id[i["net"]])
                    if i.get("label"): itf["label"] = i["label"]
                    ifaces.append(itf)
                    net_endpoints.setdefault(i["net"], []).append(center)
                    link_refs.append((itf, center, i["net"]))
                node = dict(id=node_id, name=n["name"], template=n["template"], image=n["image"],
                            icon=n.get("icon"), left=cx - 30, top=y, ifaces=ifaces)
                for k in ("cpu", "ram", "console", "type"):
                    if k in n: node[k] = n[k]
                if n.get("config"): node["config_file"] = n["config"]
                nodes.append(node)
                if n.get("ip"):
                    ip = str(n["ip"])
                    # centre under the icon, clamped inside the zone so it never bleeds out
                    lx = max(cx - ZW // 2 + 10, cx - min(len(ip) * 4, ZW // 2 - 12))
                    labels.append((lx, y + 66, ip, False, True))
            y += ROW_H

    # distance-based link styling: short hops stay straight, longer ones flow as beziers
    for itf, center, key in link_refs:
        peers = [c for c in net_endpoints.get(key, []) if c != center]
        if not peers: continue
        px = sum(p[0] for p in peers) / len(peers); py = sum(p[1] for p in peers) / len(peers)
        ls, curv, bcurv = _link_style(math.hypot(px - center[0], py - center[1]))
        itf["linkstyle"], itf["curviness"], itf["beziercurviness"] = ls, curv, bcurv

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
    for (l, t, text, bold, mono) in labels:
        to = ET.SubElement(tos, "textobject", id=str(tid), name=text[:32], type="text")
        ET.SubElement(to, "data").text = _b64(_label_html(tid, l, t, text, bold, mono)); tid += 1

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

# --- Excalidraw export (presentation diagram from the SAME design spec) --------
# Recommended by the consult panel over cramming a hand-drawn look into EVE-NG
# textobjects: the .unl stays the lab source of truth; the .excalidraw is the
# shareable, version-drift-proof picture (opens at excalidraw.com, embeds in docs).
EXCALI_PALETTE = {  # stroke, light fill
    "green": ("#2f9e44", "#ebfbee"), "purple": ("#7048e8", "#f3f0ff"),
    "blue":  ("#1971c2", "#e7f5ff"), "red":    ("#e03131", "#fff5f5"),
    "amber": ("#f08c00", "#fff9db"), "slate":  ("#495057", "#f1f3f5"),
}

def to_excalidraw(spec):
    rng = random.Random(spec.get("lab", {}).get("name", "lab"))  # deterministic per lab
    def _id(): return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(10))
    def el(**kw):
        e = dict(id=_id(), x=0, y=0, width=0, height=0, angle=0, strokeColor="#1e1e1e",
                 backgroundColor="transparent", fillStyle="solid", strokeWidth=2,
                 strokeStyle="solid", roughness=1, opacity=100, groupIds=[], frameId=None,
                 roundness=None, seed=rng.randint(1, 2**31 - 1), version=1,
                 versionNonce=rng.randint(1, 2**31 - 1), isDeleted=False, boundElements=None,
                 updated=1, link=None, locked=False)
        e.update(kw); return e
    def text(x, y, s, size=16, color="#1e1e1e", gid=None):
        return el(type="text", x=x, y=y, width=max(20, int(len(s) * size * 0.55)),
                  height=int(size * 1.25), text=s, fontSize=size, fontFamily=1,
                  textAlign="left", verticalAlign="top", containerId=None, originalText=s,
                  lineHeight=1.25, strokeColor=color, groupIds=[gid] if gid else [])

    tiers, netdefs = spec["tiers"], spec.get("networks", {})
    max_rows = max((len(t["items"]) for t in tiers), default=1)
    zone_h = HEADER + max_rows * ROW_H + PAD_BOTTOM
    elements, net_centers = [], {}
    elements.append(text(X0 - ZW // 2, ZONE_TOP - 48,
                         spec.get("lab", {}).get("name", "topology"), 26, "#1e1e1e"))
    for ti, tier in enumerate(tiers):
        cx = X0 + ti * COL_W; zleft = cx - ZW // 2; gid = _id()
        stroke, bg = EXCALI_PALETTE.get(tier.get("color", "slate"), EXCALI_PALETTE["slate"])
        elements.append(el(type="rectangle", x=zleft, y=ZONE_TOP, width=ZW, height=zone_h,
                           strokeColor=stroke, backgroundColor=bg, fillStyle="solid",
                           strokeStyle="dashed", roundness={"type": 3}, groupIds=[gid]))
        elements.append(text(zleft + 14, ZONE_TOP + 10, tier["title"], 18, stroke, gid))
        if tier.get("subnet"):
            elements.append(text(zleft + 14, ZONE_TOP + 38, tier["subnet"], 13, "#495057", gid))
        y = ZONE_TOP + HEADER
        for item in tier["items"]:
            if "network" in item:
                key = item["network"]; nd = netdefs.get(key, {})
                elements.append(el(type="diamond", x=cx - 34, y=y + 4, width=68, height=44,
                                   strokeColor="#1971c2", backgroundColor="#e7f5ff",
                                   fillStyle="solid", groupIds=[gid]))
                elements.append(text(cx - 44, y + 50, nd.get("name", key), 11, "#495057", gid))
                net_centers.setdefault(key, []).append((cx, y + 26))
            else:
                n = item["node"]
                elements.append(el(type="rectangle", x=cx - 48, y=y, width=96, height=56,
                                   strokeColor="#343a40", backgroundColor="#ffffff",
                                   fillStyle="solid", roundness={"type": 3}, groupIds=[gid]))
                elements.append(text(cx - 44, y + 9, n["name"], 14, "#212529", gid))
                if n.get("ip"):
                    elements.append(text(cx - 44, y + 34, str(n["ip"]), 10, "#868e96", gid))
                for i in n.get("ifaces", []):
                    net_centers.setdefault(i["net"], []).append((cx, y + 28))
            y += ROW_H
    # links: connect, left-to-right, the elements sharing each network; longer hops bow
    for centers in net_centers.values():
        pts = sorted(set(centers))
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy)
            if dist > 170:                       # curved "flow" for longer links
                nx, ny = -dy / dist, dx / dist
                off = min(dist * 0.13, 44)
                pts2 = [[0, 0], [dx / 2 + nx * off, dy / 2 + ny * off], [dx, dy]]
                rnd = {"type": 2}
            else:
                pts2, rnd = [[0, 0], [dx, dy]], None
            elements.append(el(type="line", x=x1, y=y1, width=dx, height=dy, points=pts2,
                               roundness=rnd, lastCommittedPoint=None, startBinding=None,
                               endBinding=None, startArrowhead=None, endArrowhead=None,
                               strokeColor="#868e96", strokeWidth=1.5))
    # legend: color swatch + tier name, below the zones
    ly = ZONE_TOP + zone_h + 28; lx = X0 - ZW // 2
    for tier in tiers:
        stroke, bg = EXCALI_PALETTE.get(tier.get("color", "slate"), EXCALI_PALETTE["slate"])
        elements.append(el(type="rectangle", x=lx, y=ly, width=18, height=18, strokeColor=stroke,
                           backgroundColor=bg, fillStyle="solid", roundness={"type": 3}))
        elements.append(text(lx + 24, ly + 1, tier["title"], 12, "#495057"))
        lx += 24 + 14 + len(tier["title"]) * 8 + 20
    return json.dumps({"type": "excalidraw", "version": 2,
                       "source": "eve-ng-topology/design_unl.py", "elements": elements,
                       "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
                       "files": {}}, indent=2)

def main():
    ap = argparse.ArgumentParser(description="Context-driven, presentable EVE-NG Pro .unl designer.")
    ap.add_argument("design", nargs="?", help="design spec JSON (omit with --example)")
    ap.add_argument("--example", action="store_true", help="print a sample design and exit")
    ap.add_argument("--catalog", help="node catalog JSON; warn on images not present")
    ap.add_argument("--format", choices=["unl", "excalidraw"], default="unl",
                    help="unl = importable EVE-NG lab; excalidraw = shareable diagram")
    args = ap.parse_args()
    if args.example:
        print(json.dumps(EXAMPLE, indent=2)); return
    if not args.design:
        ap.error("provide a design file or --example")
    spec = json.load(open(args.design, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(args.design))
    for t in spec.get("tiers", []):          # resolve config paths relative to the spec file
        for it in t.get("items", []):
            nd = it.get("node")
            if nd and nd.get("config") and not os.path.isabs(nd["config"]):
                nd["config"] = os.path.join(base, nd["config"])
    if args.format == "excalidraw":
        sys.stdout.write(to_excalidraw(spec)); return
    catalog = json.load(open(args.catalog, encoding="utf-8")) if args.catalog else None
    sys.stdout.write(design(spec, catalog))

if __name__ == "__main__":
    main()
