#!/usr/bin/env python3
"""generate_unl.py — scaffold an EVE-NG Pro .unl from a topology spec.

SCAFFOLD, DON'T CONFIGURE. This tool builds the tedious structural parts of a lab
(nodes, images, wiring, canvas layout, networks) so a lab is easier to stand up.
It NEVER invents or edits device configuration: any node `config_file` is embedded
VERBATIM (faithful to what the user gives it). Technical config changes are the
user's hands-on lab work — surface them as TODO/advisories, do not apply them here.

Format is replicated from a real EVE-NG **Pro** export. The .unl schema differs
between Community and Pro and across versions: a generated .unl is NOT proven
until it has been import-validated on the target EVE-NG server.

Usage:
  generate_unl.py spec.json > lab.unl
  generate_unl.py --example > egress-lab.json    # emit a sample spec to adapt
  generate_unl.py spec.json --catalog catalog.json   # warn on images not in catalog

Spec JSON:
  {
    "lab": {"name": "my-lab", "author": "..."},
    "networks": [{"id":1,"type":"pnet0","name":"Cloud0","icon":"Cloud-2D-Green-S.svg","left":475,"top":172}],
    "nodes": [
      {"id":1,"name":"Kali","template":"linux","image":"linux-kali","left":304,"top":506,
       "ifaces":[{"name":"e0","network":3}]},
      {"id":2,"name":"R1","template":"csr1000vng","image":"csr...","left":512,"top":356,
       "config_file":"r1.txt","ifaces":[{"name":"Gi1","network":1},{"name":"Gi2","network":4}]}
    ]
  }
network.type: pnet0..pnet9 | internal | bridge.  iface: {name, network(id), label?}
"""
import sys, json, base64, uuid, html, argparse

# Template profiles captured from a real EVE-NG Pro export. console/icon/ram are
# sensible defaults a node can override. image strings are SERVER-SPECIFIC and are
# never guessed here — they come from the spec (validate against the node catalog).
PROFILES = {
    "linux":      dict(console="vnc",  ram=4096, ethernet=1, icon="Server.png",
                       qemu_options="-machine type=pc,accel=kvm -vga std -usbdevice tablet -boot order=cd -cpu host",
                       qemu_version="5.2.0", qemu_nic="virtio-net-pci"),
    "csr1000vng": dict(console="telnet", ram=4096, ethernet=4, icon="Router_FW.png",
                       qemu_options="-machine type=pc-1.0,accel=kvm -cpu Nehalem -serial mon:stdio -nographic -no-user-config -nodefaults -rtc base=utc",
                       qemu_version="5.2.0", qemu_nic="vmxnet3", eth_format="Gi{1}"),
    "winserver":  dict(console="vnc",  ram=8192, ethernet=1, icon="Server_Win.png",
                       qemu_options="-machine type=pc,accel=kvm -cpu host,+fsgsbase -vga std -usbdevice tablet -boot order=dc",
                       qemu_version="2.12.0"),
    "docker":     dict(console="rdp",  ram=1024, ethernet=2, icon="Docker.png"),
}

def esc(s): return html.escape(str(s), quote=True)

def node_xml(n, configs):
    p = PROFILES.get(n["template"], {})
    g = lambda k, d=None: n.get(k, p.get(k, d))
    cpu = n.get("cpu", 1)
    eth = n.get("ethernet", max(len(n.get("ifaces", [])), p.get("ethernet", 1)))
    a = [f'id="{n["id"]}"', f'name="{esc(n["name"])}"', f'type="{n.get("type","qemu")}"',
         f'template="{n["template"]}"', f'image="{esc(n["image"])}"',
         f'console="{g("console","vnc")}"', f'cpu="{cpu}"', 'cpulimit="1"',
         f'ram="{g("ram",1024)}"', f'ethernet="{eth}"', f'uuid="{uuid.uuid4()}"']
    if n.get("type", "qemu") == "qemu":
        a.append(f'firstmac="50:00:00:{n["id"]:02d}:00:00"')
    if g("qemu_options"): a.append(f'qemu_options="{esc(g("qemu_options"))}"')
    if g("qemu_version"): a.append(f'qemu_version="{g("qemu_version")}"')
    if n.get("type", "qemu") == "qemu": a.append('qemu_arch="x86_64"')
    if g("qemu_nic"):     a.append(f'qemu_nic="{g("qemu_nic")}"')
    if g("eth_format"):   a.append(f'eth_format="{g("eth_format")}"')
    cfg = 0
    if n.get("config_file"):
        text = open(n["config_file"]).read()          # embedded VERBATIM — never edited
        configs.append((n["id"], base64.b64encode(text.encode()).decode()))
        cfg = 1
    a += ['delay="0"', 'sat="-1"', f'icon="{g("icon","Server.png")}"',
          f'config="{cfg}"', f'left="{n.get("left",400)}"', f'top="{n.get("top",300)}"']
    s = f'      <node {" ".join(a)}>\n'
    for i, itf in enumerate(n.get("ifaces", [])):
        lab = f' label="{esc(itf["label"])}"' if itf.get("label") else ""
        s += (f'        <interface id="{i}" name="{esc(itf["name"])}" type="ethernet" '
              f'network_id="{itf["network"]}" vid="1"{lab} labelpos="0.5" stub="0" width="1" '
              f'curviness="10" beziercurviness="150" round="0" midpoint="0.5" srcpos="0.15" dstpos="0.85"/>\n')
    return s + "      </node>\n"

def net_xml(nw):
    return (f'      <network id="{nw["id"]}" smart="0" native_vlan="1" vlan8021ad="0" '
            f'type="{nw["type"]}" name="{esc(nw["name"])}" left="{nw.get("left",0)}" '
            f'top="{nw.get("top",0)}" style="Solid" linkstyle="Straight" color="" label="" '
            f'visibility="{nw.get("visibility",1)}" icon="{nw.get("icon","lan.png")}" width="0" '
            f'hideme="0" l2filter_lldp="0" l2filter_stp="0" l2filter_cisco="0" l2filter_lacp="0"/>\n')

def generate(spec, catalog=None):
    if catalog:
        known = {n.get("image") for n in catalog.get("nodes", [])} | set(catalog.get("images", []))
        for n in spec["nodes"]:
            if n["image"] not in known:
                sys.stderr.write(f"WARN: image {n['image']!r} (node {n['name']}) not in catalog — "
                                 f"verify it is installed on the EVE-NG server before import.\n")
    lab = spec.get("lab", {})
    configs = []
    body = "".join(node_xml(n, configs) for n in spec["nodes"])
    nets = "".join(net_xml(nw) for nw in spec["networks"])
    cfgxml = ""
    if configs:
        cfgxml = "  <objects>\n    <configs>\n" + "".join(
            f'      <config id="{nid}">{b64}</config>\n' for nid, b64 in configs
        ) + "    </configs>\n  </objects>\n"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<lab name="{esc(lab.get("name","generated-lab"))}" version="0" scripttimeout="600" '
        f'countdown="0" linkwidth="1" lock="0" grid="1" author="{esc(lab.get("author",""))}" sat="-1">\n'
        '  <topology>\n    <nodes>\n' + body + '    </nodes>\n    <networks>\n' + nets +
        '    </networks>\n  </topology>\n' + cfgxml + '</lab>\n'
    )

EXAMPLE = {
    "lab": {"name": "osint-egress-lab", "author": ""},
    "networks": [
        {"id": 1, "type": "pnet0", "name": "192.168.100.0/24 (Cloud0)", "icon": "Cloud-2D-Green-S.svg", "left": 475, "top": 172},
        {"id": 2, "type": "internal", "name": "Internet", "icon": "Cloud-2D-Blue-S.svg", "left": 800, "top": 148},
        {"id": 3, "type": "bridge", "name": "LAB_LAN 10.10.70.0/24", "icon": "lan.png", "left": 300, "top": 470},
        {"id": 4, "type": "bridge", "name": "TRANSIT 192.168.1.0/24", "icon": "lan.png", "left": 430, "top": 360},
    ],
    "nodes": [
        {"id": 1, "name": "Kali", "template": "linux", "image": "linux-kali", "cpu": 2, "ram": 4096,
         "icon": "Kali.png", "left": 304, "top": 506, "ifaces": [{"name": "e0", "network": 3}]},
        {"id": 5, "name": "Ubuntu-GW", "template": "linux", "image": "linux-ubuntu-22.04.02-server", "cpu": 2,
         "ram": 4096, "icon": "local-network-gateways.svg", "left": 296, "top": 339,
         "ifaces": [{"name": "e0", "network": 3}, {"name": "e1", "network": 4}]},
        {"id": 2, "name": "CSR1000v", "template": "csr1000vng", "image": "csr1000vng-universalk9.17.03.05-serial",
         "left": 512, "top": 356, "ifaces": [{"name": "Gi1", "network": 1}, {"name": "Gi2", "network": 4}]},
        {"id": 3, "name": "Mullvad", "template": "winserver", "image": "winserver-2022R2", "icon": "Server_Win.png",
         "left": 959, "top": 250, "ifaces": [{"name": "e0", "network": 2}]},
        {"id": 4, "name": "ISP", "template": "docker", "image": "eve-gui-server:latest", "icon": "Winserver.png",
         "left": 851, "top": 465, "ifaces": [{"name": "eth0", "network": 1, "label": "WireGuard Tunnel UDP :51820"},
                                              {"name": "eth1", "network": 2}]},
    ],
}

def main():
    ap = argparse.ArgumentParser(description="Scaffold an EVE-NG Pro .unl from a topology spec.")
    ap.add_argument("spec", nargs="?", help="topology spec JSON (omit with --example)")
    ap.add_argument("--example", action="store_true", help="print a sample spec and exit")
    ap.add_argument("--catalog", help="node catalog JSON; warn on images not present")
    args = ap.parse_args()
    if args.example:
        print(json.dumps(EXAMPLE, indent=2)); return
    if not args.spec:
        ap.error("provide a spec file or --example")
    spec = json.load(open(args.spec))
    catalog = json.load(open(args.catalog)) if args.catalog else None
    sys.stdout.write(generate(spec, catalog))

if __name__ == "__main__":
    main()
