#!/usr/bin/env python3
"""nb_notes — từ notes.json dựng danh sách ghi chú và bản tổng hợp .md

    python3 nb_notes.py notes.json
    python3 nb_notes.py notes.json --notebook ./notebook \
        --notes notes.md --synthesis synthesis.md
    python3 nb_notes.py notes.json --check            # chỉ kiểm, không ghi file

Việc chính là kiểm lại: mỗi ghi chú phải neo đúng nguyên văn trong sổ tay và
mã đoạn phải khớp vị trí. Ghi chú lệch offset sẽ được neo lại bằng cách tìm
nguyên văn trong tài liệu; ghi chú không tìm thấy nguyên văn bị đánh dấu MẤT
NEO và không được đưa vào bản tổng hợp.

Hai file .md xuất ra dùng cú pháp mã [S#:c#] nên chạy được ngay:

    python3 nb_verify.py synthesis.md
    python3 nb_reader.py synthesis.md --out reader.html
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime

CATS = {"quote": "Trích dẫn", "method": "Phương pháp", "finding": "Kết quả",
        "gap": "Khoảng trống", "theory": "Lý thuyết"}


def fold(s):
    """Chuẩn hoá để so khớp — giống nb_common.fold."""
    s = unicodedata.normalize("NFC", s)
    s = (s.replace("‘", "'").replace("’", "'")
          .replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-")
          .replace(" ", " ").replace("​", ""))
    return re.sub(r"\s+", " ", s).strip()


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
        docs[s["sid"]] = open(p, encoding="utf-8").read()
    return idx, docs


def cid_at(chunks, sid, pos):
    best, bd = None, 10 ** 18
    for c in chunks:
        if c["sid"] != sid:
            continue
        if c["start"] <= pos < c["end"]:
            return c["cid"]
        d = min(abs(pos - c["start"]), abs(pos - c["end"]))
        if d < bd:
            bd, best = d, c["cid"]
    return best


def reanchor(notes, docs, chunks):
    """Trả về (ok, orphan). Sửa start/end/cid tại chỗ khi tìm lại được."""
    ok, orphan = [], []
    for n in notes:
        t = docs.get(n.get("sid"), "")
        q = n.get("quote", "")
        if not q or not t:
            n["_why"] = "thiếu nguyên văn hoặc nguồn không có trong sổ tay"
            orphan.append(n)
            continue
        if t[n.get("start", -1):n.get("end", -1)] == q:
            pass
        else:
            i = t.find(q)
            if i < 0:
                fq = fold(q)
                j = fold(t).find(fq)
                n["_why"] = ("không tìm thấy nguyên văn trong %s" % n["sid"]
                             if j < 0 else
                             "nguyên văn chỉ khớp sau khi chuẩn hoá khoảng "
                             "trắng — tài liệu có thể đã nạp lại")
                orphan.append(n)
                continue
            n["start"], n["end"] = i, i + len(q)
            n["_moved"] = True
        want = cid_at(chunks, n["sid"], n["start"])
        if want and n.get("cid") != want:
            n["_recid"] = n.get("cid")
            n["cid"] = want
        ok.append(n)
    return ok, orphan


def tags_of(n):
    return [x.strip() for x in (n.get("tags") or "").split(",") if x.strip()]


def bq(s):
    """Đưa nguyên văn vào blockquote, giữ xuống dòng."""
    return "\n".join("> " + l for l in s.strip().split("\n"))


def md_notes(notes, srcs, title):
    ns = sorted(notes, key=lambda n: (n["sid"], n["start"]))
    L = ["# Ghi chú đọc — %s" % title, "",
         "> Dựng lúc %s · %d ghi chú · %d nguồn."
         % (datetime.now().strftime("%Y-%m-%d %H:%M"), len(ns), len(srcs)),
         "> Mỗi mục gồm nguyên văn đã bôi, mã đoạn `[S#:c#]` và ghi chú của "
         "người đọc.",
         "> Nguyên văn lấy trực tiếp từ bản chuyển Markdown của tài liệu gốc "
         "và đã được đối chiếu lại.", ""]
    last = ""
    for n in ns:
        if n["sid"] != last:
            last = n["sid"]
            s = srcs[last]
            L += ["", "## %s (%s)" % (s["title"], last), "",
                  "_Tệp gốc: `%s`_" % s["file"], ""]
        L += ["### [%s] %s" % (CATS.get(n.get("cat"), "?"), n.get("cid", "?")),
              "", bq(n["quote"]), "",
              "Nguyên văn ở trên trích từ [%s]." % n.get("cid", "?")]
        if n.get("note"):
            L += ["", "**Ghi chú:** %s [%s]"
                  % (" ".join(n["note"].split()).rstrip("."),
                     n.get("cid", "?"))]
        tg = tags_of(n)
        if tg:
            L += ["", "**Chủ đề:** " + ", ".join("`%s`" % t for t in tg)]
        L.append("")
    return "\n".join(L)


def md_synthesis(notes, srcs, order, title):
    by_tag, none = {}, []
    for n in notes:
        tg = tags_of(n)
        if not tg:
            none.append(n)
        for t in tg:
            by_tag.setdefault(t, []).append(n)
    keys = sorted(by_tag, key=lambda k: (-len(by_tag[k]), k))
    L = ["# Tổng hợp theo chủ đề — %s" % title, "",
         "> Dựng lúc %s · %d chủ đề · %d ghi chú."
         % (datetime.now().strftime("%Y-%m-%d %H:%M"), len(keys), len(notes)),
         "> Đây là khung viết, không phải bản thảo. Mỗi chủ đề gom chứng cứ "
         "từ nhiều nguồn kèm mã đoạn;",
         "> phần văn của bạn viết vào mục **Diễn giải**, mỗi câu thực chứng "
         "kết bằng mã tương ứng,",
         "> rồi chạy `nb_verify.py` để kiểm.", ""]
    if keys:
        L += ["## Bản đồ chủ đề × nguồn", "",
              "| Chủ đề | " + " | ".join(order) + " | Tổng |",
              "|---|" + "---|" * (len(order) + 1)]
        for k in keys:
            row = []
            for sid in order:
                c = sum(1 for n in by_tag[k] if n["sid"] == sid)
                row.append(str(c) if c else "·")
            L.append("| %s | %s | %d |" % (k, " | ".join(row), len(by_tag[k])))
        L.append("")
    for k in keys:
        L += ["", "---", "", "## Chủ đề: %s" % k, ""]
        per = {}
        for n in by_tag[k]:
            per.setdefault(n["sid"], []).append(n)
        for sid in sorted(per):
            L += ["### %s (%s)" % (srcs[sid]["title"], sid), ""]
            for n in sorted(per[sid], key=lambda x: x["start"]):
                L.append("- **%s** [%s]"
                         % (CATS.get(n.get("cat"), "?"), n.get("cid", "?")))
                L.append("  > " + " ".join(n["quote"].split()))
                if n.get("note"):
                    L.append("  - " + " ".join(n["note"].split()))
            L.append("")
        cids = []
        for n in by_tag[k]:
            if n.get("cid") and n["cid"] not in cids:
                cids.append(n["cid"])
        L += ["**Diễn giải.** _(viết vào đây — mỗi câu thực chứng kết bằng "
              "mã)_ [%s]" % "; ".join(cids), ""]
        gaps = [n for n in by_tag[k] if n.get("cat") == "gap"]
        if gaps:
            L += ["**Khoảng trống đã ghi nhận:**", ""]
            for n in gaps:
                L.append("- %s [%s]"
                         % (n.get("note") or " ".join(n["quote"].split())[:140],
                            n.get("cid", "?")))
            L.append("")
    if none:
        L += ["", "---", "", "## Chưa gắn chủ đề (%d)" % len(none), ""]
        for n in sorted(none, key=lambda x: (x["sid"], x["start"])):
            L.append("- [%s] %s [%s]"
                     % (CATS.get(n.get("cat"), "?"),
                        n.get("note") or " ".join(n["quote"].split())[:140],
                        n.get("cid", "?")))
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notes_json")
    ap.add_argument("--notebook", default="notebook")
    ap.add_argument("--notes", default="notes.md")
    ap.add_argument("--synthesis", default="synthesis.md")
    ap.add_argument("--title", default=None)
    ap.add_argument("--check", action="store_true",
                    help="chỉ kiểm neo và mã, không ghi file")
    a = ap.parse_args()

    idx, docs = load_notebook(a.notebook)
    srcs = {s["sid"]: s for s in idx["sources"]}
    order = [s["sid"] for s in idx["sources"]]

    raw = json.load(open(a.notes_json, encoding="utf-8"))
    payload = raw if isinstance(raw, list) else raw.get("notes", [])
    if not payload:
        sys.exit("Không thấy ghi chú nào trong %s" % a.notes_json)
    title = a.title or (raw.get("title") if isinstance(raw, dict) else None) \
        or os.path.basename(os.path.abspath(a.notebook))

    ok, orphan = reanchor(payload, docs, idx["chunks"])
    moved = [n for n in ok if n.get("_moved")]
    recid = [n for n in ok if n.get("_recid")]

    print("%d ghi chú: %d neo đúng, %d neo lại, %d mã sửa lại, %d mất neo."
          % (len(payload), len(ok) - len(moved), len(moved), len(recid),
             len(orphan)))
    for n in moved:
        print("  · neo lại  %s:%d  %s…"
              % (n["sid"], n["start"], " ".join(n["quote"].split())[:52]))
    for n in recid:
        print("  · mã %s → %s  %s…"
              % (n["_recid"], n["cid"], " ".join(n["quote"].split())[:44]))
    for n in orphan:
        print("  ✗ MẤT NEO %s — %s | %s…"
              % (n.get("sid", "?"), n.get("_why", ""),
                 " ".join(n.get("quote", "").split())[:44]), file=sys.stderr)

    tagged = sum(1 for n in ok if tags_of(n))
    print("%d/%d ghi chú đã gắn chủ đề." % (tagged, len(ok)))
    if a.check:
        return 1 if orphan else 0

    open(a.notes, "w", encoding="utf-8").write(md_notes(ok, srcs, title))
    open(a.synthesis, "w", encoding="utf-8").write(
        md_synthesis(ok, srcs, order, title))
    print("→ %s\n→ %s" % (a.notes, a.synthesis))
    print("Kiểm tiếp:  python3 nb_verify.py %s" % a.synthesis)
    return 1 if orphan else 0


if __name__ == "__main__":
    sys.exit(main())
