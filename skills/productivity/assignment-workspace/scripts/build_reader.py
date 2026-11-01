#!/usr/bin/env python3
"""Build a self-contained reading viewer for a graded assignment.

Input is a JSON spec (see references/reader-spec.md). Every highlight phrase must
appear verbatim in one of its question's spotlight blocks; the build fails
otherwise, so a highlight never points at text that is not there.

Usage: build_reader.py SPEC.json OUT.html
"""
import json
import sys
from pathlib import Path

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>__TITLE__</title>
<style>
:root{--bg:#f2f4f8;--surface:#fff;--ink:#18202c;--muted:#505d70;--line:#cbd3df;--accent:#235db4;--soft:#eaf1fb;--hl:#ffe27a;--spot:#fff8d6;--warn:#855400}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#10151d;--surface:#19212d;--ink:#edf1f7;--muted:#b3bfd1;--line:#455267;--accent:#9cc1ff;--soft:#202f47;--hl:#6b5a12;--spot:#2a2614;--warn:#f3c36e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 "Avenir Next","Segoe UI",system-ui,sans-serif}
.top{position:sticky;top:0;z-index:3;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.tab{font:600 .9rem/1 inherit;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:8px 14px;cursor:pointer}
.tab[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
select{font:inherit;font-size:.9rem;padding:7px 10px;border-radius:8px;border:1px solid var(--line);background:var(--surface);color:var(--ink);max-width:100%}
.wrap{max-width:820px;margin:0 auto;padding:16px 16px 80px}
.guide{background:var(--soft);border-radius:10px;padding:12px 16px;margin:12px 0}
.guide h2{margin:0 0 4px;font-size:1.05rem}.guide p{margin:4px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{font-size:.85rem;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:4px 10px;cursor:pointer;text-align:left}
.src{font-size:.85rem;color:var(--muted)}.src a{color:var(--accent)}
.blk{display:grid;grid-template-columns:3.2em 1fr;gap:8px;padding:8px 10px;border-radius:8px;margin:2px 0;scroll-margin-top:120px}
.blk .n{font:700 .8rem/1.9 ui-monospace,Menlo,monospace;color:var(--muted);text-align:right}
.blk p{margin:0;font:18px/1.7 Georgia,"Times New Roman",serif}
.blk.spot{background:var(--spot);outline:1px solid var(--line)}
.blk.dim{opacity:.55}
.pg{font:700 .72rem/1 ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:18px 0 6px;border-top:1px dashed var(--line);padding-top:8px}
mark{background:var(--hl);color:inherit;border-radius:3px;padding:0 2px;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px}
mark.flash{outline:3px solid var(--accent)}
.cite{font:600 .75rem ui-monospace,Menlo,monospace;color:var(--accent);margin-left:6px;cursor:pointer;border:0;background:none;padding:0}
.note{font-size:.85rem;color:var(--warn)}
.toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:8px 14px;border-radius:999px;font-size:.9rem;opacity:0;transition:opacity .2s}
.toast.on{opacity:1}
</style>
</head>
<body>
<div class="top">
  <span id="tabs"></span>
  <label class="src" for="qsel">Question:</label>
  <select id="qsel" aria-label="Choose a question"><option value="">— read freely, no highlights —</option></select>
  <label class="src"><input type="checkbox" id="dim"> fade other paragraphs</label>
</div>
<main class="wrap">
  <div class="guide" id="guide" hidden></div>
  <p class="src" id="srcline"></p>
  <p class="note">Transcribed from your course files for study. Before quoting, check the wording against the original page using the “PDF p.” links.</p>
  <div id="text"></div>
</main>
<div class="toast" id="toast" role="status"></div>
<script>
const D=__DATA__;
const S=Object.fromEntries(D.sources.map(s=>[s.key,s]));
let cur=D.sources[0].key,q="";
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
$("tabs").innerHTML=D.sources.map(s=>`<button class="tab" type="button" data-t="${esc(s.key)}">${esc(s.label)}</button> `).join("");
function render(){
  document.querySelectorAll(".tab").forEach(b=>b.setAttribute("aria-pressed",b.dataset.t===cur));
  const src=S[cur],Qd=q?D.questions[q]:null,spot=new Set(Qd?Qd.blocks:[]),phr=Qd?Qd.phrases:[];
  $("srcline").innerHTML=esc(src.source_line)+(src.pdf?` · <a href="${esc(src.pdf)}" target="_blank" rel="noopener">open original PDF</a>`:"");
  let h="",last=null;
  for(const b of src.blocks){
    if(String(b.page)!==String(last)){h+=`<div class="pg">Page ${esc(b.page)}`+(src.pdf&&b.pdf_page?` · <a href="${esc(src.pdf)}#page=${b.pdf_page}" target="_blank" rel="noopener">PDF p.${b.pdf_page}</a>`:"")+`</div>`;last=b.page}
    let t=esc(b.text);
    if(spot.has(b.id))for(const p of phr){const e=esc(p);if(t.includes(e))t=t.split(e).join(`<mark data-p="${encodeURIComponent(p)}">${e}</mark>`)}
    const cls=spot.has(b.id)?"spot":(Qd&&$("dim").checked?"dim":"");
    const c=`(${src.cite_author} ${String(b.page).split(/[–-]/)[0]})`;
    h+=`<div class="blk ${cls}" id="${esc(b.id)}"><span class="n">${esc(b.label)}</span><p>${t}<button class="cite" type="button" data-c="${esc(c)}" title="Copy citation">${esc(c)}</button></p></div>`;
  }
  $("text").innerHTML=h;
  const g=$("guide");
  if(Qd){g.hidden=false;g.innerHTML=`<h2>${esc(Qd.title)}</h2><p>${esc(Qd.tip)}</p><p class="src">Highlighted phrases (click to jump):</p><div class="chips">${phr.map(p=>`<button class="chip" type="button" data-j="${encodeURIComponent(p)}">“${esc(p.length>60?p.slice(0,57)+"…":p)}”</button>`).join("")}</div>`;
    const f=document.querySelector(".blk.spot");if(f)f.scrollIntoView({block:"start"});}
  else g.hidden=true;
}
function setQ(id){q=id&&D.questions[id]?id:"";if(q)cur=D.questions[q].source;$("qsel").value=q;try{history.replaceState(null,"",q?"#"+q:location.pathname+location.search)}catch(_){}render();}
function toast(m){const t=$("toast");t.textContent=m;t.classList.add("on");setTimeout(()=>t.classList.remove("on"),1600)}
for(const [k,v] of Object.entries(D.questions)){const o=document.createElement("option");o.value=k;o.textContent=S[v.source].short+" · "+v.title;$("qsel").appendChild(o)}
$("qsel").onchange=e=>setQ(e.target.value);
$("dim").onchange=render;
document.addEventListener("click",async e=>{
  const tb=e.target.closest(".tab");if(tb){cur=tb.dataset.t;if(q&&D.questions[q].source!==cur)q="";$("qsel").value=q;render();window.scrollTo(0,0)}
  const j=e.target.closest("[data-j]");if(j){const m=document.querySelector(`mark[data-p="${j.dataset.j}"]`);if(m){m.scrollIntoView({block:"center",behavior:"smooth"});m.classList.add("flash");setTimeout(()=>m.classList.remove("flash"),1500)}}
  const c=e.target.closest(".cite");if(c){try{await navigator.clipboard.writeText(c.dataset.c);toast("Copied "+c.dataset.c)}catch(_){toast(c.dataset.c)}}
});
window.addEventListener("hashchange",()=>setQ(location.hash.slice(1)));
setQ(location.hash.slice(1));
</script>
</body>
</html>"""

REQUIRED_SOURCE = ("key", "label", "short", "cite_author", "source_line", "blocks")


def validate(spec: dict) -> list[str]:
    errors = []
    sources = spec.get("sources") or []
    if not sources:
        errors.append("spec.sources is empty")
    blocks = {}
    for s in sources:
        for k in REQUIRED_SOURCE:
            if k not in s:
                errors.append(f"source {s.get('key', '?')}: missing {k}")
        for b in s.get("blocks", []):
            if b["id"] in blocks:
                errors.append(f"duplicate block id {b['id']}")
            blocks[b["id"]] = (s["key"], b)
    for qid, q in (spec.get("questions") or {}).items():
        if q.get("source") not in {s["key"] for s in sources}:
            errors.append(f"{qid}: unknown source {q.get('source')}")
            continue
        for bid in q.get("blocks", []):
            if bid not in blocks:
                errors.append(f"{qid}: unknown block {bid}")
            elif blocks[bid][0] != q["source"]:
                errors.append(f"{qid}: block {bid} is in another source")
        texts = [blocks[b][1]["text"] for b in q.get("blocks", []) if b in blocks]
        for p in q.get("phrases", []):
            if not any(p in t for t in texts):
                errors.append(f"{qid}: phrase not found verbatim in its blocks: {p!r}")
    return errors


def build(spec: dict) -> str:
    errors = validate(spec)
    if errors:
        raise ValueError("\n".join(errors))
    data = json.dumps(spec, ensure_ascii=False).replace("</", "<\\/")
    title = spec.get("title", "Reader").replace("<", "&lt;")
    return PAGE.replace("__TITLE__", title).replace("__DATA__", data)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text())
    try:
        html = build(spec)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    Path(sys.argv[2]).write_text(html)
    n = sum(len(s["blocks"]) for s in spec["sources"])
    print(f"ok: {len(spec['sources'])} sources, {n} blocks, {len(spec.get('questions', {}))} questions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
