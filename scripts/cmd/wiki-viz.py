#!/usr/bin/env python3
"""wiki-viz.py — the static visualizer export (#177 S5).

`wf export viz --out <dir>` produces a self-contained static directory
(index.html + graph.json) renderable by any static host (GitHub Pages,
MkDocs, Netlify). Zero-dependency client: reads the sibling graph file,
renders a filterable node graph + clickable page list. No live reload (the
export is a build artifact — the corpus's next export refreshes it).

OpenWiki's visualize --export shape; the graph source is the SAME data the
citation-graph step already builds (registry/wiki-graph.json).
"""

import argparse
import json
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))  # wiki_lib is a package under scripts/
from pathlib import Path


_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Wiki — graph</title>
<style>
 body { font: 14px system-ui; margin: 0; display: flex; height: 100vh; }
 #list { width: 320px; overflow-y: auto; border-right: 1px solid #ddd; padding: 8px; }
 #read { flex: 1; overflow-y: auto; padding: 20px 28px; }
 .row { padding: 3px 6px; cursor: pointer; border-radius: 4px; }
 .row:hover { background: #f0f4ff; }
 .row.topic { color: #1a4fa5; font-weight: 600; }
 .row.project { color: #7a2ea5; font-weight: 600; }
 .row.claim { color: #444; font-size: 13px; padding-left: 14px; }
 #q { width: 100%; box-sizing: border-box; padding: 6px; margin-bottom: 8px; }
 h1 { margin-top: 0; }
 pre { white-space: pre-wrap; }
</style></head>
<body>
<div id="list"><input id="q" placeholder="filter…"><div id="rows"></div></div>
<div id="read"><em>Select a page from the list.</em></div>
<script>
let graph = null;
fetch('./graph.json').then(r => r.json()).then(g => {
  graph = g; render('');
});
document.getElementById('q').addEventListener('input', e => render(e.target.value));
function render(q) {
  const el = document.getElementById('rows');
  el.innerHTML = '';
  const frag = document.createDocumentFragment();
  for (const n of (graph.nodes || [])) {
    if (n.type !== 'topic' && n.type !== 'project') continue;
    const label = (n.label || n.id).replace(/["]/g, '');
    if (q && !label.toLowerCase().includes(q.toLowerCase())) continue;
    const d = document.createElement('div');
    d.className = 'row ' + n.type;
    d.textContent = label + (n.claims ? ' (' + n.claims + ')' : '');
    d.onclick = () => read(n);
    frag.appendChild(d);
  }
  el.appendChild(frag);
}
function read(n) {
  const el = document.getElementById('read');
  const claims = (graph.edges || [])
    .filter(e => e.source === n.id && e.target && e.target.startsWith('claim:'))
    .map(e => e.target);
  const labels = claims.map(c => {
    const cn = (graph.nodes || []).find(x => x.id === c);
    return '<li>' + ((cn && cn.label) || c || '').replace(/["]/g, '') + '</li>';
  }).join('');
  el.innerHTML = '<h1>' + (n.label || n.id).replace(/["]/g, '') + '</h1>' +
    '<em>' + n.type + ' — ' + claims.length + ' claims linked</em><ul>' + labels + '</ul>' +
    '<p>Citations: the claim stems link into the corpus (evidence/claims/&lt;stem&gt;.md).</p>';
}
</script>
</body></html>
"""


def main():
    parser = argparse.ArgumentParser(description="Export the wiki graph viewer (static)")
    parser.add_argument("--out", default=None, help="Output dir (default: <wiki>/viz)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from fabric_config import CORPUS_ROOT
    import layout
    wiki = _wiki_root_safe()
    if wiki is None:
        print("no wiki root (run: wf export wiki)", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else (wiki / "viz")
    src = layout.registry(CORPUS_ROOT) / "wiki-graph.json"
    if not src.exists():
        print(f"no graph source: {src} (run: wf export wiki)", file=sys.stderr)
        return 2
    graph = json.loads(src.read_text())
    if args.dry_run:
        print(f"[DRY] would export viz: {out} ({len(graph.get('nodes', []))} nodes)")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(_TEMPLATE, encoding="utf-8")
    (out / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    print(f"Visualizer export: {out}/ (self-contained; static host ready)")
    return 0


def _wiki_root_safe():
    try:
        import wiki_lib.generators as _g
        return _g._wiki_root()
    except Exception:
        return None


if __name__ == "__main__":
    sys.exit(main())