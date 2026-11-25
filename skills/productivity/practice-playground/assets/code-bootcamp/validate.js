/* node validate.js <draft.js> [...more]: loads content.js + drafts in a sandbox and checks module structure. */
const fs = require("fs"), vm = require("vm"), path = require("path");
const H = __dirname;
const ctx = { console };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(H, "content.js"), "utf8") + "\nthis.__ = { MODULES, EX, LABS, ARENA, COMPS, REG };", ctx);
const baseEx = new Set(Object.keys(ctx.__.EX)), baseArena = new Set(ctx.__.ARENA.map(a => a.id));
let bad = 0; const err = (f, m) => { bad++; console.log(`  ✗ ${f}: ${m}`); };
for (const file of process.argv.slice(2)) {
  console.log(file);
  const before = new Set(Object.keys(ctx.__.EX)); const arenaBefore = ctx.__.ARENA.length;
  try { vm.runInContext(fs.readFileSync(file, "utf8"), ctx, { filename: file }); } catch (e) { err(file, "does not run: " + e.message); continue; }
  const { MODULES, EX, LABS, ARENA, COMPS } = ctx.__;
  const n = +(/mod(\d+)/.exec(file) || [])[1]; const m = MODULES.find(x => x.id === n);
  if (!m || m.planned) { err(file, "REG did not replace the planned module"); continue; }
  const L = m.lessons || []; if (L.length < 2) err(file, `only ${L.length} lessons`);
  const all = Object.assign({}, EX); ARENA.forEach(a => all[a.id] = a);
  L.forEach(l => {
    const where = `lesson ${l.id}`;
    for (const k of ["id", "title", "tier", "contracts", "comp", "mins", "concept", "model", "syntax", "vba", "example", "micro", "failure", "deeper", "check"]) if (l[k] == null) err(where, "missing " + k);
    if (![1, 2].includes(l.tier)) err(where, "tier must be 1 or 2");
    if (!COMPS[l.comp]) err(where, "unknown comp " + l.comp);
    if (l.example && (!l.example.steps || !l.example.steps.every(([, t]) => t && t.rows.every(r => r.length === t.cols.length)))) err(where, "example steps not rectangular");
    [l.micro, ...(l.check || [])].forEach(id => { if (!all[id]) err(where, "missing exercise " + id); });
  });
  for (const [id, x] of Object.entries(EX)) { if (before.has(id)) continue;
    if (!COMPS[x.comp]) err("ex " + id, "unknown comp " + x.comp);
    if (x.type === "mc" && (x.opts.length !== 4 || x.opts.filter(o => o[1]).length !== 1)) err("ex " + id, "mc needs 4 options, exactly one correct");
    if (x.type === "multi" && !(x.opts.filter(o => o[1]).length >= 2 && x.opts.some(o => !o[1]))) err("ex " + id, "multi needs 2+ correct and a distractor");
    if (x.type === "fill" && (!x.answers || !x.answers.length || !/▢/.test(x.code || ""))) err("ex " + id, "fill needs answers and ▢ in code");
    if (x.type === "mc" || x.type === "multi") x.opts.forEach(o => { if (!o[2]) err("ex " + id, "option without a reason: " + o[0]); });
  }
  ARENA.slice(arenaBefore).forEach(a => { if (baseArena.has(a.id)) err("arena " + a.id, "duplicate id"); if (!a.kind) err("arena " + a.id, "no kind");
    if (a.type === "mc" && (a.opts.length !== 4 || a.opts.filter(o => o[1]).length !== 1)) err("arena " + a.id, "mc needs 4 options, exactly one correct"); });
  const lab = LABS[m.lab]; if (!lab) err(file, "no lab");
  else { for (const k of ["title", "comps", "scenario", "objectives", "requirements", "constraints", "edges", "starter", "expected", "tests", "hints", "solution", "alternatives", "review", "goals"]) if (lab[k] == null) err("lab", "missing " + k);
    if (lab.expected && !lab.expected.rows.every(r => r.length === lab.expected.cols.length)) err("lab", "expected not rectangular");
    (lab.predict || []).forEach(id => { if (!EX[id]) err("lab", "missing predict " + id); }); }
}
console.log(bad ? `${bad} problem(s)` : "all checks passed");
process.exit(bad ? 1 : 0);
