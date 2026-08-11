#!/usr/bin/env python3
"""nb_annot — dựng bàn làm việc HTML: mở tài liệu, bôi đen, ghi chú, xuất .md

    python3 nb_annot.py --notebook ./notebook --out study.html
    python3 nb_annot.py --title "Bàn đọc luận án"

Đọc sổ tay do nb_ingest.py tạo ra, dựng một file HTML tự chứa:

  · mở toàn văn từng nguồn (bản đã chuyển sang Markdown, giữ nguyên offset)
  · bôi đen đoạn bất kỳ → gắn nhãn (trích dẫn / phương pháp / kết quả /
    khoảng trống / lý thuyết), viết ghi chú, gắn chủ đề
  · mỗi vệt bôi tự bắt về mã đoạn [S#:c#] của sổ tay
  · ghi chú lưu trong localStorage của trình duyệt, không cần mạng
  · xuất: notes.json (nạp lại được), notes.md (danh sách), synthesis.md
    (tổng hợp theo chủ đề — khung viết lit review)

File .md xuất ra dùng đúng cú pháp mã [S#:c#] nên chạy thẳng được:

    python3 nb_verify.py synthesis.md
    python3 nb_reader.py synthesis.md --out reader.html
"""
import argparse
import json
import os
import sys


# ------------------------------------------------------------------- data

def load_notebook(nb):
    idx_path = os.path.join(nb, "index.json")
    if not os.path.exists(idx_path):
        sys.exit("Không thấy %s — chạy nb_ingest.py trước." % idx_path)
    idx = json.load(open(idx_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(idx_path))
    docs = {}
    for s in idx["sources"]:
        p = s.get("markdown")
        p = p if p and os.path.isabs(p) else os.path.join(base, p or "")
        if not os.path.exists(p):
            sys.exit("Thiếu bản Markdown của %s: %s" % (s["sid"], p))
        docs[s["sid"]] = open(p, encoding="utf-8").read()
    return idx, docs


# -------------------------------------------------------------------- css

CSS = r"""
*{box-sizing:border-box}
:root{
 --bg:#faf9f7; --fg:#1f1d1a; --mut:#6b665e; --line:#e2ded6;
 --card:#fff; --acc:#8a5a2b; --accbg:#f3e9dd; --bad:#b3261e;
 --q:#ffe9a8; --qb:#c9a227;   /* trích dẫn */
 --m:#cfe3ff; --mb:#3f76c4;   /* phương pháp */
 --f:#c9edd2; --fb:#2f8a4d;   /* kết quả */
 --g:#ffd3d0; --gb:#c1453c;   /* khoảng trống */
 --t:#e2d5f7; --tb:#7a52b8;   /* lý thuyết */
 --sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
 --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
}
@media (prefers-color-scheme:dark){:root{
 --bg:#171614; --fg:#eae7e1; --mut:#a29c92; --line:#33302b; --card:#1f1e1b;
 --acc:#d8a76a; --accbg:#33291d; --bad:#ff8a80;
 --q:#5c4a1e; --qb:#e0b84f; --m:#1e3452; --mb:#7fb0f0; --f:#1d3d2a;
 --fb:#6cc98c; --g:#4a2320; --gb:#f08d84; --t:#33254a; --tb:#b795ef;}}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);
 font-size:15px;line-height:1.62;overflow:hidden}
#top{display:flex;gap:8px;align-items:center;padding:8px 14px;
 border-bottom:1px solid var(--line);background:var(--bg);flex-wrap:wrap}
#top h1{font:600 14px/1.3 var(--sans);margin:0;margin-right:4px}
select,input,textarea{font:inherit;font-size:13px;padding:5px 8px;
 border:1px solid var(--line);border-radius:7px;background:var(--card);
 color:var(--fg);max-width:100%}
textarea{width:100%;font-size:13.5px;line-height:1.5;resize:vertical}
button{font:inherit;font-size:13px;padding:5px 10px;border:1px solid var(--line);
 background:var(--card);color:var(--fg);border-radius:7px;cursor:pointer}
button:hover{border-color:var(--acc);color:var(--acc)}
button.pri{background:var(--acc);color:var(--bg);border-color:var(--acc)}
button.pri:hover{opacity:.88;color:var(--bg)}
.sp{flex:1}
#wrap{display:grid;grid-template-columns:minmax(0,1fr) 420px;
 height:calc(100% - 45px)}
#docpane{overflow:auto;padding:22px 30px 140px}
#doc{max-width:820px;white-space:pre-wrap;font-family:var(--serif);
 font-size:16.5px;line-height:1.75}
#doc .hl{border-radius:3px;padding:1px 0;cursor:pointer;
 box-shadow:inset 0 -2px 0 rgba(0,0,0,.18)}
#doc .hl.sel{outline:2px solid var(--acc);outline-offset:1px}
.c-quote{background:var(--q)}.c-method{background:var(--m)}
.c-finding{background:var(--f)}.c-gap{background:var(--g)}
.c-theory{background:var(--t)}
#doc mark.find{background:var(--acc);color:var(--bg);border-radius:3px}
#side{border-left:1px solid var(--line);background:var(--card);
 display:flex;flex-direction:column;min-height:0}
#sh{display:flex;gap:6px;align-items:center;padding:8px 11px;
 border-bottom:1px solid var(--line);flex-wrap:wrap}
#sh b{font-size:12.5px;flex:1}
#sb{flex:1;overflow:auto;padding:12px 14px 60px}
.note{border:1px solid var(--line);border-radius:9px;padding:9px 11px;
 margin:0 0 9px;background:var(--bg)}
.note.orphan{border-color:var(--bad);border-style:dashed}
.nh{display:flex;gap:6px;align-items:center;margin-bottom:5px;flex-wrap:wrap}
.chip{font-size:10.5px;font-weight:700;letter-spacing:.03em;padding:1px 6px;
 border-radius:5px;text-transform:uppercase;color:#1f1d1a}
.chip.quote{background:var(--q)}.chip.method{background:var(--m)}
.chip.finding{background:var(--f)}.chip.gap{background:var(--g)}
.chip.theory{background:var(--t)}
@media (prefers-color-scheme:dark){.chip{color:#eae7e1}}
.cid{font:600 11px/1.5 var(--sans);background:var(--accbg);color:var(--acc);
 padding:1px 6px;border-radius:5px;cursor:pointer}
.nq{font-family:var(--serif);font-size:14px;color:var(--mut);
 border-left:3px solid var(--line);padding-left:9px;margin:4px 0;
 max-height:5.6em;overflow:hidden}
.nt{font-size:13.5px;margin:5px 0 3px;white-space:pre-wrap}
.tags{font-size:11.5px;color:var(--acc)}
.na{display:flex;gap:5px;margin-top:6px}
.na button{font-size:11.5px;padding:3px 8px}
.loc{font-size:11px;color:var(--mut);margin:14px 0 7px;font-weight:600;
 letter-spacing:.03em;text-transform:uppercase}
.mut{color:var(--mut);font-size:12.5px}
.hit{display:block;width:100%;text-align:left;margin:0 0 6px;font-size:12.5px;
 line-height:1.45;padding:7px 9px;font-family:var(--serif)}
.hit mark{background:var(--q);color:inherit}
#pop{position:absolute;z-index:40;display:none;gap:4px;padding:5px;
 background:var(--card);border:1px solid var(--line);border-radius:9px;
 box-shadow:0 6px 24px rgba(0,0,0,.22)}
#pop button{font-size:11.5px;padding:4px 7px;border-radius:6px}
#ed{position:fixed;inset:0;background:rgba(0,0,0,.42);display:none;
 align-items:center;justify-content:center;z-index:60;padding:16px}
#edbox{background:var(--card);border-radius:14px;padding:16px;width:560px;
 max-width:100%;max-height:88vh;overflow:auto;
 box-shadow:0 20px 60px rgba(0,0,0,.35)}
#edbox h3{margin:0 0 10px;font-size:14px}
#edq{font-family:var(--serif);font-size:14.5px;background:var(--accbg);
 border-left:3px solid var(--acc);padding:9px 11px;border-radius:0 7px 7px 0;
 max-height:8em;overflow:auto;white-space:pre-wrap;margin-bottom:11px}
.fl{display:flex;gap:8px;align-items:center;margin:9px 0;flex-wrap:wrap}
.fl label{font-size:12px;color:var(--mut);min-width:66px}
#out{position:fixed;inset:0;background:rgba(0,0,0,.42);display:none;
 align-items:center;justify-content:center;z-index:70;padding:16px}
#outbox{background:var(--card);border-radius:14px;padding:16px;width:820px;
 max-width:100%;height:82vh;display:flex;flex-direction:column}
#outbox textarea{flex:1;font-family:ui-monospace,monospace;font-size:12px}
@media(max-width:960px){
 #wrap{grid-template-columns:1fr;grid-template-rows:1fr 46vh}
 #side{border-left:0;border-top:1px solid var(--line)}
 #docpane{padding:16px 16px 60px}
}
"""

# --------------------------------------------------------------------- js

JS = r"""
const D=JSON.parse(document.getElementById('nbdata').textContent);
const KEY='nbnotes:'+D.key;
const CATS={quote:'Trích dẫn',method:'Phương pháp',finding:'Kết quả',
            gap:'Khoảng trống',theory:'Lý thuyết'};
const bySid={};D.sources.forEach(s=>bySid[s.sid]=s);
const perSid={};D.chunks.forEach(c=>{(perSid[c.sid]=perSid[c.sid]||[]).push(c)});
const $=s=>document.querySelector(s);
const esc=s=>s.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
const docEl=$('#doc'),pane=$('#docpane'),sb=$('#sb'),pop=$('#pop');
let cur=D.sources[0].sid, notes=[], sel=null, editing=null, filter={};

/* ---------------------------------------------------------- lưu / nạp */
function load(){
 try{notes=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){notes=[]}
 notes.forEach(heal);
}
function save(){
 try{localStorage.setItem(KEY,JSON.stringify(notes))}
 catch(e){alert('Không lưu được vào trình duyệt: '+e.message)}
 stat();
}
function heal(n){           /* neo lại nếu offset lệch so với nguyên văn */
 const t=D.docs[n.sid]||'';
 if(t.slice(n.start,n.end)===n.quote){n.orphan=false;return}
 const i=t.indexOf(n.quote);
 if(i>=0){n.start=i;n.end=i+n.quote.length;n.orphan=false;n.cid=cidAt(n.sid,i)}
 else n.orphan=true;
}
function cidAt(sid,pos){
 const cs=perSid[sid]||[];let best=null,bd=1e18;
 for(const c of cs){
  if(pos>=c.start&&pos<c.end)return c.cid;
  const d=Math.min(Math.abs(pos-c.start),Math.abs(pos-c.end));
  if(d<bd){bd=d;best=c.cid}}
 return best;
}
function uid(){return 'n'+Date.now().toString(36)+Math.random().toString(36).slice(2,6)}

/* ------------------------------------------------------------ tài liệu */
function renderDoc(){
 const t=D.docs[cur]||'';
 const ns=notes.filter(n=>n.sid===cur&&!n.orphan).sort((a,b)=>a.start-b.start);
 let h='',pos=0,skipped=0;
 for(const n of ns){
  if(n.start<pos){skipped++;continue}
  h+=esc(t.slice(pos,n.start));
  h+='<span class="hl c-'+n.cat+'" data-id="'+n.id+'">'
     +esc(t.slice(n.start,n.end))+'</span>';
  pos=n.end;
 }
 h+=esc(t.slice(pos));
 docEl.innerHTML=h;
 $('#ovl').textContent=skipped?(' · '+skipped+' vệt chồng lấn không tô'):'';
}
function jump(sid,start,end){
 if(sid!==cur){cur=sid;$('#src').value=sid;renderDoc()}
 const el=[...docEl.querySelectorAll('.hl')]
   .find(e=>{const n=notes.find(x=>x.id===e.dataset.id);return n&&n.start===start});
 if(el){el.scrollIntoView({block:'center'});flash(el);return}
 /* không phải vệt bôi: tô tạm để định vị */
 const t=D.docs[sid]||'';
 docEl.innerHTML=esc(t.slice(0,start))+'<mark class="find" id="fx">'
   +esc(t.slice(start,end))+'</mark>'+esc(t.slice(end));
 const fx=$('#fx');if(fx)fx.scrollIntoView({block:'center'});
 setTimeout(renderDoc,2600);
}
function flash(el){el.classList.add('sel');setTimeout(()=>el.classList.remove('sel'),1400)}

/* ------------------------------------------------------- chọn văn bản */
function offsets(){
 const s=getSelection();
 if(!s.rangeCount||s.isCollapsed)return null;
 const r=s.getRangeAt(0);
 if(!docEl.contains(r.commonAncestorContainer))return null;
 const pre=r.cloneRange();pre.selectNodeContents(docEl);
 pre.setEnd(r.startContainer,r.startOffset);
 const start=pre.toString().length, text=r.toString();
 if(!text.trim())return null;
 return {start:start,end:start+text.length,text:text,rect:r.getBoundingClientRect()};
}
document.addEventListener('mouseup',()=>{
 setTimeout(()=>{
  const o=offsets();
  if(!o){pop.style.display='none';sel=null;return}
  sel=o;
  pop.style.display='flex';
  const y=o.rect.top+scrollY-pop.offsetHeight-8;
  pop.style.top=Math.max(scrollY+6,y)+'px';
  pop.style.left=Math.max(6,Math.min(innerWidth-pop.offsetWidth-6,
    o.rect.left+o.rect.width/2-pop.offsetWidth/2))+'px';
 },10);
});
docEl.addEventListener('click',e=>{
 const h=e.target.closest('.hl');
 if(h&&getSelection().isCollapsed){
  const n=notes.find(x=>x.id===h.dataset.id);if(n)openEd(n)}
});
pop.addEventListener('click',e=>{
 const b=e.target.closest('[data-cat]');if(!b||!sel)return;
 const t=(D.docs[cur]||'').slice(sel.start,sel.end);
 const n={id:uid(),sid:cur,start:sel.start,end:sel.end,quote:t,
   cid:cidAt(cur,sel.start),cat:b.dataset.cat,note:'',tags:'',
   ts:new Date().toISOString()};
 notes.push(n);save();renderDoc();renderSide();
 pop.style.display='none';getSelection().removeAllRanges();
 openEd(n);
});

/* ----------------------------------------------------------- soạn thảo */
function openEd(n){
 editing=n;
 $('#edq').textContent=n.quote;
 $('#edcid').textContent=n.cid||'—';
 $('#edloc').textContent=bySid[n.sid].title+(n.orphan?' · MẤT NEO':'');
 $('#edcat').value=n.cat;$('#ednote').value=n.note||'';$('#edtags').value=n.tags||'';
 $('#ed').style.display='flex';setTimeout(()=>$('#ednote').focus(),40);
}
function closeEd(){$('#ed').style.display='none';editing=null}
$('#edsave').onclick=()=>{
 if(!editing)return;
 editing.cat=$('#edcat').value;
 editing.note=$('#ednote').value.trim();
 editing.tags=$('#edtags').value.trim();
 save();renderDoc();renderSide();closeEd();
};
$('#eddel').onclick=()=>{
 if(!editing)return;
 notes=notes.filter(x=>x.id!==editing.id);
 save();renderDoc();renderSide();closeEd();
};
$('#edcancel').onclick=closeEd;
$('#ed').onclick=e=>{if(e.target.id==='ed')closeEd()};
addEventListener('keydown',e=>{
 if(e.key==='Escape'){closeEd();$('#out').style.display='none';pop.style.display='none'}
 if((e.metaKey||e.ctrlKey)&&e.key==='Enter'&&editing)$('#edsave').click();
});

/* ------------------------------------------------------------- sidebar */
function allTags(){
 const s=new Set();
 notes.forEach(n=>(n.tags||'').split(',').map(x=>x.trim())
   .filter(Boolean).forEach(t=>s.add(t)));
 return [...s].sort((a,b)=>a.localeCompare(b,'vi'));
}
function shown(){
 return notes.filter(n=>{
  if(filter.sid&&n.sid!==filter.sid)return false;
  if(filter.cat&&n.cat!==filter.cat)return false;
  if(filter.tag&&!(n.tags||'').split(',').map(x=>x.trim()).includes(filter.tag))return false;
  if(filter.q){const q=filter.q.toLowerCase();
   if(!((n.quote+' '+(n.note||'')+' '+(n.tags||'')).toLowerCase().includes(q)))return false}
  return true;
 }).sort((a,b)=>a.sid===b.sid?a.start-b.start:a.sid.localeCompare(b.sid));
}
function renderSide(){
 const tg=allTags();
 $('#ftag').innerHTML='<option value="">Mọi chủ đề</option>'
   +tg.map(t=>'<option'+(filter.tag===t?' selected':'')+'>'+esc(t)+'</option>').join('');
 const ns=shown();
 $('#cnt').textContent=ns.length+'/'+notes.length+' ghi chú';
 if(!notes.length){
  sb.innerHTML='<p class="mut">Chưa có ghi chú nào.<br><br>'
   +'Bôi đen một đoạn trong tài liệu bên trái, rồi chọn nhãn ở thanh nổi lên. '
   +'Mỗi vệt bôi tự bắt về mã đoạn của sổ tay, nên khi xuất ra .md là đã có '
   +'trích dẫn truy vết sẵn.</p>';return}
 let h='',last='';
 for(const n of ns){
  if(n.sid!==last){last=n.sid;
   h+='<p class="loc">'+esc(bySid[n.sid].title)+'</p>'}
  h+='<div class="note'+(n.orphan?' orphan':'')+'" data-id="'+n.id+'">'
   +'<div class="nh"><span class="chip '+n.cat+'">'+CATS[n.cat]+'</span>'
   +'<span class="cid" data-go="'+n.id+'">'+(n.cid||'?')+'</span>'
   +(n.orphan?'<span class="mut">mất neo</span>':'')+'</div>'
   +'<div class="nq">'+esc(n.quote.length>260?n.quote.slice(0,260)+'…':n.quote)+'</div>'
   +(n.note?'<div class="nt">'+esc(n.note)+'</div>':'')
   +(n.tags?'<div class="tags">#'+esc(n.tags.split(',').map(x=>x.trim())
       .filter(Boolean).join(' #'))+'</div>':'')
   +'<div class="na"><button data-go="'+n.id+'">Tới chỗ bôi</button>'
   +'<button data-edit="'+n.id+'">Sửa</button>'
   +'<button data-copy="'+n.id+'">Chép có mã</button></div></div>';
 }
 sb.innerHTML=h;
}
sb.addEventListener('click',e=>{
 const g=e.target.closest('[data-go]');
 if(g){const n=notes.find(x=>x.id===g.dataset.go);
  if(n&&!n.orphan)jump(n.sid,n.start,n.end);return}
 const d=e.target.closest('[data-edit]');
 if(d){const n=notes.find(x=>x.id===d.dataset.edit);if(n)openEd(n);return}
 const c=e.target.closest('[data-copy]');
 if(c){const n=notes.find(x=>x.id===c.dataset.copy);if(!n)return;
  navigator.clipboard.writeText('"'+n.quote.trim()+'" ['+n.cid+']')
   .then(()=>{c.textContent='Đã chép';setTimeout(()=>c.textContent='Chép có mã',1100)});
  return}
 const hh=e.target.closest('[data-jump]');
 if(hh){jump(hh.dataset.jump,+hh.dataset.a,+hh.dataset.b);return}
});

/* --------------------------------------------------------- tìm toàn văn */
function findAll(v){
 if(!v||v.length<2){renderSide();return}
 const rx=new RegExp(v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'ig');
 let out=[],n=0;
 for(const s of D.sources){const t=D.docs[s.sid];let m;rx.lastIndex=0;
  while((m=rx.exec(t))&&n<80){n++;
   const a=Math.max(0,m.index-70),b=Math.min(t.length,m.index+m[0].length+90);
   out.push('<button class="hit" data-jump="'+s.sid+'" data-a="'+m.index
    +'" data-b="'+(m.index+m[0].length)+'"><span class="mut">'+s.sid+' · '
    +cidAt(s.sid,m.index)+'</span><br>…'+esc(t.slice(a,m.index))+'<mark>'
    +esc(m[0])+'</mark>'+esc(t.slice(m.index+m[0].length,b))+'…</button>')}}
 sb.innerHTML='<p class="loc">'+n+' kết quả trong toàn văn</p>'+out.join('');
}

/* ------------------------------------------------------------- xuất ra */
function stamp(){const d=new Date();
 return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'
   +String(d.getDate()).padStart(2,'0')+' '+String(d.getHours()).padStart(2,'0')
   +':'+String(d.getMinutes()).padStart(2,'0')}
function tagsOf(n){return (n.tags||'').split(',').map(x=>x.trim()).filter(Boolean)}

function mdNotes(){
 const ns=notes.slice().sort((a,b)=>a.sid===b.sid?a.start-b.start:a.sid.localeCompare(b.sid));
 let L=['# Ghi chú đọc — '+D.title,'',
  '> Xuất lúc '+stamp()+' · '+ns.length+' ghi chú · '+D.sources.length+' nguồn.',
  '> Mỗi mục gồm nguyên văn đã bôi, mã đoạn `[S#:c#]` và ghi chú của người đọc.',
  '> Nguyên văn lấy trực tiếp từ bản chuyển Markdown của tài liệu gốc.',''];
 let last='';
 for(const n of ns){
  if(n.sid!==last){last=n.sid;
   L.push('','## '+bySid[n.sid].title+' ('+n.sid+')','',
     '_Tệp gốc: `'+bySid[n.sid].file+'`_','')}
  L.push('### ['+CATS[n.cat]+'] '+(n.cid||'?')+(n.orphan?' — MẤT NEO':''));
  L.push('');
  L.push('> '+n.quote.trim().replace(/\n+/g,'\n> '));
  L.push('');
  L.push('Nguyên văn ở trên trích từ ['+(n.cid||'?')+'].');
  if(n.note)L.push('','**Ghi chú:** '+n.note.replace(/\n+/g,' ').replace(/\.$/,'')
    +' ['+(n.cid||'?')+']');
  const tg=tagsOf(n);
  if(tg.length)L.push('','**Chủ đề:** '+tg.map(t=>'`'+t+'`').join(', '));
  L.push('');
 }
 return L.join('\n');
}

function mdSynthesis(){
 const tg={},none=[];
 for(const n of notes){
  const ts=tagsOf(n);
  if(!ts.length){none.push(n);continue}
  ts.forEach(t=>{(tg[t]=tg[t]||[]).push(n)});
 }
 const keys=Object.keys(tg).sort((a,b)=>tg[b].length-tg[a].length);
 let L=['# Tổng hợp theo chủ đề — '+D.title,'',
  '> Xuất lúc '+stamp()+' · '+keys.length+' chủ đề · '+notes.length+' ghi chú.',
  '> Đây là khung viết, không phải bản thảo. Mỗi chủ đề gom chứng cứ từ nhiều',
  '> nguồn kèm mã đoạn; phần văn của bạn viết vào mục **Diễn giải**, mỗi câu',
  '> thực chứng kết bằng mã tương ứng, rồi chạy `nb_verify.py`.',''];
 if(keys.length){
  L.push('## Bản đồ chủ đề × nguồn','');
  L.push('| Chủ đề | '+D.sources.map(s=>s.sid).join(' | ')+' | Tổng |');
  L.push('|---|'+D.sources.map(()=>'---|').join('')+'---|');
  for(const k of keys){
   const row=D.sources.map(s=>{
    const c=tg[k].filter(n=>n.sid===s.sid).length;return c?String(c):'·'});
   L.push('| '+k+' | '+row.join(' | ')+' | '+tg[k].length+' |');
  }
  L.push('');
 }
 for(const k of keys){
  L.push('','---','','## Chủ đề: '+k,'');
  const bySrc={};tg[k].forEach(n=>{(bySrc[n.sid]=bySrc[n.sid]||[]).push(n)});
  for(const sid of Object.keys(bySrc).sort()){
   L.push('### '+bySid[sid].title+' ('+sid+')','');
   for(const n of bySrc[sid].sort((a,b)=>a.start-b.start)){
    L.push('- **'+CATS[n.cat]+'** ['+(n.cid||'?')+']');
    L.push('  > '+n.quote.trim().replace(/\n+/g,' '));
    if(n.note)L.push('  - '+n.note.replace(/\n+/g,' '));
   }
   L.push('');
  }
  const cids=[...new Set(tg[k].map(n=>n.cid).filter(Boolean))];
  L.push('**Diễn giải.** _(viết vào đây — mỗi câu thực chứng kết bằng mã)_ ['
    +cids.join('; ')+']','');
  const gaps=tg[k].filter(n=>n.cat==='gap');
  if(gaps.length){
   L.push('**Khoảng trống đã ghi nhận:**','');
   gaps.forEach(n=>L.push('- '+(n.note||n.quote.trim().slice(0,140))
     +' ['+(n.cid||'?')+']'));
   L.push('');
  }
 }
 if(none.length){
  L.push('','---','','## Chưa gắn chủ đề ('+none.length+')','');
  none.forEach(n=>L.push('- ['+CATS[n.cat]+'] '+(n.note||n.quote.trim().slice(0,140))
    +' ['+(n.cid||'?')+']'));
  L.push('');
 }
 return L.join('\n');
}

function showOut(name,text,importMode){
 $('#outname').textContent=name;
 $('#outtext').value=text;
 $('#outtext').placeholder=importMode?'Dán toàn bộ nội dung notes.json vào đây…':'';
 $('#outdl').style.display=importMode?'none':'';
 $('#outcopy').style.display=importMode?'none':'';
 $('#outimp').style.display=importMode?'':'none';
 $('#outhint').textContent=importMode
  ? 'Dán nội dung file notes.json rồi bấm "Nạp vào". Ghi chú trùng id sẽ bị bỏ qua.'
  : 'Lưu file này vào thư mục dự án rồi chạy nb_verify.py / nb_reader.py như bình thường.';
 $('#out').style.display='flex';
 $('#outtext').focus();$('#outtext').setSelectionRange(0,0);
 $('#outdl').onclick=()=>{
  const b=new Blob([text],{type:'text/plain;charset=utf-8'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b);a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),3000);
 };
 $('#outcopy').onclick=()=>{navigator.clipboard.writeText(text).then(()=>{
  $('#outcopy').textContent='Đã chép';
  setTimeout(()=>$('#outcopy').textContent='Chép hết',1200)})};
}
$('#outclose').onclick=()=>$('#out').style.display='none';
$('#out').onclick=e=>{if(e.target.id==='out')$('#out').style.display='none'};

$('#exnotes').onclick=()=>{if(!notes.length)return alert('Chưa có ghi chú nào.');
 showOut('notes.md',mdNotes())};
$('#exsyn').onclick=()=>{if(!notes.length)return alert('Chưa có ghi chú nào.');
 showOut('synthesis.md',mdSynthesis())};
$('#exjson').onclick=()=>showOut('notes.json',JSON.stringify(
 {notebook:D.key,title:D.title,exported:new Date().toISOString(),notes:notes},null,1));
$('#imp').onclick=()=>showOut('Nạp notes.json','',true);
$('#outimp').onclick=()=>{
 const raw=$('#outtext').value.trim();
 if(!raw)return alert('Chưa dán gì vào ô.');
 let d;try{d=JSON.parse(raw)}catch(e){return alert('JSON không hợp lệ: '+e.message)}
 const inc=Array.isArray(d)?d:(d.notes||[]);
 if(!inc.length)return alert('Không thấy ghi chú nào trong dữ liệu dán vào.');
 const have=new Set(notes.map(n=>n.id));
 let add=0,bad=0;
 inc.forEach(n=>{
  if(have.has(n.id))return;
  if(!n.sid||!D.docs[n.sid]||!n.quote){bad++;return}
  n.cat=CATS[n.cat]?n.cat:'quote';
  heal(n);notes.push(n);add++;
 });
 save();renderDoc();renderSide();
 $('#out').style.display='none';
 alert('Đã nạp '+add+' ghi chú · bỏ qua '+(inc.length-add-bad)+' trùng'
  +(bad?(' · '+bad+' hỏng'):'')
  +'.\nMất neo: '+notes.filter(n=>n.orphan).length);
};
$('#clr').onclick=()=>{
 if(!notes.length)return;
 if(!confirm('Xoá toàn bộ '+notes.length+' ghi chú trong trình duyệt? '
  +'Nên bấm "Xuất .json" trước.'))return;
 notes=[];save();renderDoc();renderSide();
};

/* --------------------------------------------------------------- khởi */
function stat(){
 const o=notes.filter(n=>n.orphan).length;
 $('#stat').textContent=notes.length+' ghi chú'+(o?(' · '+o+' mất neo'):'');
}
$('#src').innerHTML=D.sources.map(s=>'<option value="'+s.sid+'">'+esc(s.title)
 +' ('+s.sid+')</option>').join('');
$('#src').onchange=e=>{cur=e.target.value;renderDoc();pane.scrollTop=0};
$('#fcat').innerHTML='<option value="">Mọi nhãn</option>'
 +Object.keys(CATS).map(k=>'<option value="'+k+'">'+CATS[k]+'</option>').join('');
$('#fcat').onchange=e=>{filter.cat=e.target.value;renderSide()};
$('#ftag').onchange=e=>{filter.tag=e.target.value;renderSide()};
$('#fsid').innerHTML='<option value="">Mọi nguồn</option>'
 +D.sources.map(s=>'<option value="'+s.sid+'">'+s.sid+'</option>').join('');
$('#fsid').onchange=e=>{filter.sid=e.target.value;renderSide()};
$('#fq').oninput=e=>{filter.q=e.target.value.trim();renderSide()};
$('#find').oninput=e=>{clearTimeout(window._ft);
 window._ft=setTimeout(()=>findAll(e.target.value.trim()),240)};
$('#edcat').innerHTML=Object.keys(CATS).map(k=>'<option value="'+k+'">'
 +CATS[k]+'</option>').join('');
pop.innerHTML=Object.keys(CATS).map(k=>'<button class="chip '+k
 +'" data-cat="'+k+'">'+CATS[k]+'</button>').join('');
load();renderDoc();renderSide();stat();
"""

SHELL = """<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>__CSS__</style>
<div id="top">
 <h1>__TITLE__</h1>
 <select id="src"></select>
 <input id="find" placeholder="Tìm trong toàn văn…" style="width:180px">
 <span class="mut" id="stat"></span><span class="mut" id="ovl"></span>
 <span class="sp"></span>
 <button id="exnotes">Xuất ghi chú .md</button>
 <button id="exsyn" class="pri">Xuất tổng hợp .md</button>
 <button id="exjson">Xuất .json</button>
 <button id="imp">Nạp .json</button>
 <button id="clr">Xoá hết</button>
</div>
<div id="wrap">
 <div id="docpane"><div id="doc"></div></div>
 <aside id="side">
  <div id="sh">
   <b id="cnt">0 ghi chú</b>
   <select id="fsid"></select><select id="fcat"></select><select id="ftag"></select>
   <input id="fq" placeholder="lọc ghi chú…" style="width:100%">
  </div>
  <div id="sb"></div>
 </aside>
</div>
<div id="pop"></div>
<div id="ed"><div id="edbox">
 <h3>Ghi chú cho đoạn đã bôi</h3>
 <p class="mut" id="edloc"></p>
 <div id="edq"></div>
 <div class="fl"><label>Mã đoạn</label><span class="cid" id="edcid"></span></div>
 <div class="fl"><label>Nhãn</label><select id="edcat"></select></div>
 <div class="fl"><label>Chủ đề</label>
  <input id="edtags" placeholder="cách nhau bằng dấu phẩy, vd: coping, supervisor"
   style="flex:1"></div>
 <textarea id="ednote" rows="6"
   placeholder="Ghi chú của bạn: vì sao đoạn này quan trọng, nó chống hay đỡ luận điểm nào, nối với nguồn nào…"></textarea>
 <div class="fl" style="justify-content:flex-end;margin-top:12px">
  <button id="eddel">Xoá</button><button id="edcancel">Đóng</button>
  <button id="edsave" class="pri">Lưu (⌘↵)</button></div>
</div></div>
<div id="out"><div id="outbox">
 <div class="fl"><b id="outname"></b><span class="sp"></span>
  <button id="outcopy">Chép hết</button>
  <button id="outimp" class="pri" style="display:none">Nạp vào</button>
  <button id="outdl" class="pri">Tải file</button>
  <button id="outclose">Đóng</button></div>
 <textarea id="outtext" spellcheck="false"></textarea>
 <p class="mut" id="outhint"></p>
</div></div>
<script type="application/json" id="nbdata">__DATA__</script>
<script>__JS__</script>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notebook", default="notebook")
    ap.add_argument("--out", default="study.html")
    ap.add_argument("--title", default="Bàn đọc & ghi chú")
    a = ap.parse_args()

    idx, docs = load_notebook(a.notebook)
    data = {
        "title": a.title,
        "key": os.path.basename(os.path.abspath(a.notebook)) + "|"
               + "-".join(s["sid"] + ":" + str(s["chars"]) for s in idx["sources"]),
        "sources": [{k: s.get(k) for k in
                     ("sid", "title", "file", "kind", "pages", "n_chunks")}
                    for s in idx["sources"]],
        "chunks": [{k: c.get(k) for k in
                    ("cid", "sid", "start", "end", "order", "page", "heading")}
                   for c in idx["chunks"]],
        "docs": docs,
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    htm = (SHELL.replace("__TITLE__", a.title).replace("__CSS__", CSS)
                .replace("__DATA__", payload).replace("__JS__", JS))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(htm)
    print("→ %s (%d KB, %d nguồn, %d đoạn)"
          % (a.out, len(htm.encode()) // 1024, len(idx["sources"]),
             len(idx["chunks"])))


if __name__ == "__main__":
    main()
