#!/usr/bin/env python3
"""nb_reader — dựng bản đọc HTML tự chứa: bấm trích dẫn là mở đúng đoạn nguồn.

    python3 nb_reader.py draft.md --out reader.html
    python3 nb_reader.py draft.md --notebook ./notebook --title "Tổng quan"
    python3 nb_reader.py draft.md --lite      # chỉ nhúng đoạn được trích ±2

File xuất ra không gọi mạng, không cần file ngoài — mở được ngay trong khung
làm việc của Claude hoặc bất kỳ trình duyệt nào.
"""
import argparse
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nb_common as C


# --------------------------------------------------------- markdown → html

def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def _mini_md(md):
    out, i = [], 0
    lines = md.split("\n")
    while i < len(lines):
        l = lines[i]
        if l.strip().startswith("```"):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(lines[j]); j += 1
            out.append("<pre><code>%s</code></pre>"
                       % html.escape("\n".join(buf)))
            i = j + 1; continue
        if not l.strip():
            i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", l)
        if m:
            n = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (n, _inline(m.group(2)), n))
            i += 1; continue
        if re.match(r"^\s*(---+|\*\*\*+)\s*$", l):
            out.append("<hr>"); i += 1; continue
        if l.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip()); i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(" ".join(buf)))
            continue
        if l.lstrip().startswith("|") and i + 1 < len(lines) \
           and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in l.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in
                             lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join("<th>%s</th>" % _inline(c) for c in head)
            tb = "".join("<tr>%s</tr>" % "".join(
                "<td>%s</td>" % _inline(c) for c in r) for r in rows)
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                       % (th, tb))
            continue
        m = re.match(r"^\s*([-*+]|\d+[.)])\s+", l)
        if m:
            ordered = not m.group(1) in "-*+"
            items = []
            while i < len(lines) and re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join(
                "<li>%s</li>" % _inline(x) for x in items), tag))
            continue
        buf = []
        while i < len(lines) and lines[i].strip() \
                and not re.match(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```)",
                                 lines[i]):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>%s</p>" % _inline(" ".join(buf)))
    return "\n".join(out)


def md_to_html(md):
    try:
        import markdown as _m
        return _m.markdown(md, extensions=["tables", "fenced_code",
                                           "sane_lists"])
    except Exception:
        return _mini_md(md)


def chipify(htm, known):
    def rep(m):
        cids = [x.strip() for x in m.group(1).split(";")]
        chips = []
        for cid in cids:
            ok = cid in known
            chips.append(
                '<a class="cite%s" data-cid="%s" href="#" title="%s">%s</a>'
                % ("" if ok else " bad", html.escape(cid),
                   "Mở đoạn nguồn" if ok else "Mã không tồn tại trong sổ tay",
                   html.escape(cid)))
        return '<span class="cg">' + "".join(chips) + "</span>"
    return C.MARKER_RE.sub(rep, htm)


# ------------------------------------------------------------------ shell

CSS = """
*{box-sizing:border-box}
:root{
 --bg:#faf9f7; --fg:#1f1d1a; --mut:#6b665e; --line:#e2ded6;
 --card:#fff; --acc:#8a5a2b; --accbg:#f3e9dd; --mark:#ffe9a8; --bad:#b3261e;
 --sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
 --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
}
@media (prefers-color-scheme:dark){:root{
 --bg:#171614; --fg:#eae7e1; --mut:#a29c92; --line:#33302b; --card:#1f1e1b;
 --acc:#d8a76a; --accbg:#33291d; --mark:#5c4a1e; --bad:#ff8a80;}}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);
 font-size:15px;line-height:1.62}
#top{display:flex;gap:10px;align-items:center;padding:10px 16px;
 border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);
 z-index:9;flex-wrap:wrap}
#top h1{font:600 15px/1.3 var(--sans);margin:0;flex:1;min-width:120px}
button{font:inherit;font-size:13px;padding:5px 11px;border:1px solid var(--line);
 background:var(--card);color:var(--fg);border-radius:7px;cursor:pointer}
button:hover{border-color:var(--acc);color:var(--acc)}
#wrap{display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:0;
 align-items:start}
#doc{padding:26px 34px 120px;max-width:820px;font-family:var(--serif);
 font-size:17px}
#doc h1,#doc h2,#doc h3,#doc h4{font-family:var(--sans);line-height:1.3;
 margin:1.7em 0 .5em}
#doc h1{font-size:1.5em}#doc h2{font-size:1.22em}#doc h3{font-size:1.06em}
#doc p{margin:0 0 1em}
#doc blockquote{margin:1em 0;padding:.5em 1em;border-left:3px solid var(--acc);
 background:var(--accbg);border-radius:0 6px 6px 0}
#doc table{border-collapse:collapse;width:100%;font-size:.9em;margin:1em 0}
#doc th,#doc td{border:1px solid var(--line);padding:6px 9px;text-align:left}
#doc code{background:var(--accbg);padding:1px 5px;border-radius:4px;
 font-size:.85em;font-family:ui-monospace,monospace}
#doc pre{background:var(--card);border:1px solid var(--line);padding:12px;
 border-radius:8px;overflow:auto}
.cg{white-space:nowrap}
a.cite{display:inline-block;font-family:var(--sans);font-size:11px;
 font-weight:600;line-height:1.5;padding:1px 6px;margin:0 1px;border-radius:5px;
 background:var(--accbg);color:var(--acc);text-decoration:none;
 vertical-align:.12em;border:1px solid transparent;cursor:pointer}
a.cite:hover{border-color:var(--acc)}
a.cite.on{background:var(--acc);color:var(--bg)}
a.cite.bad{background:transparent;color:var(--bad);
 border:1px dashed var(--bad)}
#side{position:sticky;top:47px;height:calc(100vh - 47px);
 border-left:1px solid var(--line);background:var(--card);display:flex;
 flex-direction:column}
#sh{display:flex;gap:6px;align-items:center;padding:9px 12px;
 border-bottom:1px solid var(--line)}
#sh b{font-size:12px;font-weight:600;flex:1;overflow:hidden;
 text-overflow:ellipsis;white-space:nowrap}
#sb{flex:1;overflow:auto;padding:14px 16px 40px}
#q{width:100%;font:inherit;font-size:13px;padding:6px 9px;border-radius:7px;
 border:1px solid var(--line);background:var(--bg);color:var(--fg)}
.loc{font-size:11px;color:var(--mut);margin:0 0 8px;font-weight:600;
 letter-spacing:.02em;text-transform:uppercase}
.quote{font-family:var(--serif);font-size:15.5px;background:var(--accbg);
 border-left:3px solid var(--acc);padding:10px 13px;border-radius:0 7px 7px 0;
 white-space:pre-wrap}
.ctx{font-family:var(--serif);color:var(--mut);font-size:14px;margin:9px 0;
 white-space:pre-wrap}
.row{display:flex;gap:6px;margin:12px 0;flex-wrap:wrap}
.src{display:block;width:100%;text-align:left;margin:0 0 7px;padding:9px 11px;
 border-radius:8px;line-height:1.4}
.src small{display:block;color:var(--mut);font-size:11px;margin-top:2px}
#full{white-space:pre-wrap;font-family:var(--serif);font-size:14.5px;
 line-height:1.7}
#full mark,.hit mark{background:var(--mark);color:inherit;border-radius:3px;
 padding:1px 0}
.hit{display:block;width:100%;text-align:left;margin:0 0 6px;font-size:13px;
 line-height:1.45;padding:8px 10px}
.mut{color:var(--mut);font-size:12.5px}
#toggle{display:none}
@media(max-width:900px){
 #wrap{grid-template-columns:1fr}
 #doc{padding:18px 18px 90px;font-size:16px}
 #side{position:fixed;inset:auto 0 0 0;height:74vh;border-left:0;
  border-top:1px solid var(--line);border-radius:14px 14px 0 0;
  box-shadow:0 -8px 30px rgba(0,0,0,.18);transform:translateY(101%);
  transition:transform .22s ease;z-index:20}
 #side.open{transform:none}
 #toggle{display:inline-block}
}
"""

JS = r"""
const D=JSON.parse(document.getElementById('nbdata').textContent);
const bySid={};D.sources.forEach(s=>bySid[s.sid]=s);
const byCid={};D.chunks.forEach(c=>byCid[c.cid]=c);
const perSid={};D.chunks.forEach(c=>{(perSid[c.sid]=perSid[c.sid]||[]).push(c)});
const sb=document.getElementById('sb'),sh=document.getElementById('sh'),
      side=document.getElementById('side'),title=document.getElementById('st');
const esc=s=>s.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const txt=(sid,a,b)=>(D.docs[sid]||'').slice(a,b);
const open=()=>{if(innerWidth<=900)side.classList.add('open')};
function loc(c){const s=bySid[c.sid];
 return s.title+' · '+(c.page?('tr. '+c.page):('đoạn '+(c.order+1)))
  +(c.heading?(' · '+c.heading):'')}

function viewSources(){
 title.textContent='Nguồn ('+D.sources.length+')';
 const used={};D.used.forEach(c=>{const s=byCid[c];if(s)used[s.sid]=(used[s.sid]||0)+1});
 sb.innerHTML='<input id="q" placeholder="Tìm trong toàn bộ nguồn…">'
  +'<div style="height:12px"></div>'
  +D.sources.map(s=>`<button class="src" data-full="${s.sid}">${esc(s.title)}
   <small>${s.kind.toUpperCase()} · ${s.n_chunks} đoạn${s.pages?' · '+s.pages+' trang':''}
   · được trích ${used[s.sid]||0} lần</small></button>`).join('')
  +(D.lite?'<p class="mut">Bản nhẹ: chỉ nhúng đoạn được trích và lân cận.</p>':'');
 const q=document.getElementById('q');
 q.oninput=()=>{clearTimeout(q._t);q._t=setTimeout(()=>search(q.value),220)};
}
function search(v){
 const old=document.getElementById('res');
 if(!v||v.length<2){if(old)old.remove();return}
 const rx=new RegExp(v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'ig');
 let out=[],n=0;
 for(const sid in D.docs){const t=D.docs[sid];let m;rx.lastIndex=0;
  while((m=rx.exec(t))&&n<60){n++;
   const a=Math.max(0,m.index-70),b=Math.min(t.length,m.index+m[0].length+90);
   out.push(`<button class="hit" data-jump="${sid}" data-a="${m.index}"
    data-b="${m.index+m[0].length}"><span class="mut">${sid}</span> …${
    esc(t.slice(a,m.index))}<mark>${esc(m[0])}</mark>${esc(t.slice(m.index+m[0].length,b))}…</button>`)}}
 const box=document.getElementById('res')||(()=>{const d=document.createElement('div');
  d.id='res';sb.appendChild(d);return d})();
 box.innerHTML='<p class="loc">'+n+' kết quả</p>'+out.join('');
}
function viewCite(cid){
 const c=byCid[cid];if(!c)return;
 document.querySelectorAll('a.cite.on').forEach(e=>e.classList.remove('on'));
 document.querySelectorAll('a.cite[data-cid="'+cid+'"]')
  .forEach(e=>e.classList.add('on'));
 const sib=perSid[c.sid],i=sib.indexOf(c);
 const pv=i>0?sib[i-1]:null,nx=i<sib.length-1?sib[i+1]:null;
 title.textContent=cid;
 sb.innerHTML=`<p class="loc">${esc(loc(c))}</p>
  ${pv?`<div class="ctx">…${esc(txt(c.sid,pv.start,pv.end).trim())}</div>`:''}
  <div class="quote">${esc(txt(c.sid,c.start,c.end).trim())}</div>
  ${nx?`<div class="ctx">${esc(txt(c.sid,nx.start,nx.end).trim())}…</div>`:''}
  <div class="row">
   <button data-full="${c.sid}" data-a="${c.start}" data-b="${c.end}">Mở toàn văn tại đoạn này</button>
   <button data-copy="${cid}">Chép nguyên văn</button>
  </div>
  <p class="mut">Tệp gốc: ${esc(bySid[c.sid].file)}</p>`;
 sb.scrollTop=0;open();
}
function viewFull(sid,a,b){
 const t=D.docs[sid]||'';title.textContent=bySid[sid].title;
 let h;
 if(a!=null){h=esc(t.slice(0,a))+'<mark id="mk">'+esc(t.slice(a,b))+'</mark>'+esc(t.slice(b))}
 else h=esc(t);
 sb.innerHTML='<p class="loc">Toàn văn đã chuyển sang Markdown</p><div id="full">'+h+'</div>';
 const mk=document.getElementById('mk');
 if(mk)mk.scrollIntoView({block:'center'});else sb.scrollTop=0;
 open();
}
document.addEventListener('click',e=>{
 const c=e.target.closest('a.cite');
 if(c){e.preventDefault();if(!c.classList.contains('bad'))viewCite(c.dataset.cid);return}
 const f=e.target.closest('[data-full]');
 if(f){viewFull(f.dataset.full,f.dataset.a?+f.dataset.a:null,+f.dataset.b);return}
 const j=e.target.closest('[data-jump]');
 if(j){viewFull(j.dataset.jump,+j.dataset.a,+j.dataset.b);return}
 const cp=e.target.closest('[data-copy]');
 if(cp){const k=byCid[cp.dataset.copy];
  navigator.clipboard.writeText(txt(k.sid,k.start,k.end).trim()+' ['+k.cid+']')
   .then(()=>{cp.textContent='Đã chép';setTimeout(()=>cp.textContent='Chép nguyên văn',1200)});
  return}
});
document.getElementById('back').onclick=()=>{
 document.querySelectorAll('a.cite.on').forEach(e=>e.classList.remove('on'));
 viewSources()};
document.getElementById('toggle').onclick=()=>side.classList.toggle('open');
addEventListener('keydown',e=>{if(e.key==='Escape')viewSources()});
viewSources();
"""

SHELL = """<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{css}</style>
<div id="top"><h1>{title}</h1>
 <span class="mut">{stat}</span>
 <button id="toggle">Nguồn</button></div>
<div id="wrap">
 <article id="doc">{doc}</article>
 <aside id="side"><div id="sh"><b id="st">Nguồn</b>
   <button id="back">Danh sách</button></div>
  <div id="sb"></div></aside>
</div>
<script type="application/json" id="nbdata">{data}</script>
<script>{js}</script>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--notebook", default="notebook")
    ap.add_argument("--out", default="reader.html")
    ap.add_argument("--title")
    ap.add_argument("--lite", action="store_true",
                    help="chỉ nhúng đoạn được trích ± 2 đoạn kề")
    args = ap.parse_args()

    idx_path = os.path.join(args.notebook, "index.json")
    idx = C.load_index(idx_path)
    srcs = {s["sid"]: s for s in idx["sources"]}
    by_cid = {c["cid"]: c for c in idx["chunks"]}

    raw = open(args.draft, encoding="utf-8").read()
    used = []
    for m in C.MARKER_RE.finditer(raw):
        for cid in [x.strip() for x in m.group(1).split(";")]:
            if cid in by_cid and cid not in used:
                used.append(cid)

    docs = {}
    for s in idx["sources"]:
        docs[s["sid"]] = C.read_doc(idx_path, s)

    chunks = idx["chunks"]
    if args.lite:
        keep = set()
        per = {}
        for c in chunks:
            per.setdefault(c["sid"], []).append(c)
        for cid in used:
            c = by_cid[cid]
            sib = per[c["sid"]]
            i = sib.index(c)
            for j in range(max(0, i - 2), min(len(sib), i + 3)):
                keep.add(sib[j]["cid"])
        chunks = [c for c in chunks if c["cid"] in keep]
        kept_sids = {c["sid"] for c in chunks}
        for sid in list(docs):
            if sid not in kept_sids:
                docs[sid] = ""
            else:
                span = [c for c in chunks if c["sid"] == sid]
                lo = min(c["start"] for c in span)
                hi = max(c["end"] for c in span)
                docs[sid] = docs[sid][:hi]

    data = {
        "sources": [{k: s[k] for k in
                     ("sid", "title", "kind", "pages", "n_chunks", "file")}
                    for s in idx["sources"]],
        "chunks": [{k: c[k] for k in
                    ("cid", "sid", "page", "heading", "start", "end", "order")}
                   for c in chunks],
        "docs": docs,
        "used": used,
        "lite": bool(args.lite),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    body = chipify(md_to_html(raw), set(by_cid))
    title = args.title or os.path.splitext(os.path.basename(args.draft))[0]
    stat = "%d trích dẫn · %d nguồn" % (len(used), len(idx["sources"]))

    out = SHELL.format(title=html.escape(title), css=CSS, js=JS,
                       doc=body, data=payload, stat=stat)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    kb = os.path.getsize(args.out) / 1024
    print("→ %s (%.0f KB, %d trích dẫn, %d nguồn)"
          % (args.out, kb, len(used), len(idx["sources"])))
    if kb > 4000:
        print("  ! file khá nặng, cân nhắc --lite")
    return 0


if __name__ == "__main__":
    sys.exit(main())
