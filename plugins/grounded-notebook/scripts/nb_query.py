#!/usr/bin/env python3
"""nb_query — tìm đoạn nguồn trong sổ tay trước khi viết.

    python3 nb_query.py "động lực|motivation"          # regex, không dấu cũng khớp
    python3 nb_query.py "caregiving" --source S2 -n 15
    python3 nb_query.py --cid S1:p12.3                 # xem nguyên văn 1 đoạn
    python3 nb_query.py --list                         # bảng nguồn
"""
import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nb_common as C


def deaccent(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", nargs="?", help="regex (OR bằng dấu |)")
    ap.add_argument("--notebook", default="notebook")
    ap.add_argument("--source", help="giới hạn trong một nguồn, vd S2")
    ap.add_argument("--cid", help="in nguyên văn một đoạn theo mã")
    ap.add_argument("--list", action="store_true", help="liệt kê nguồn")
    ap.add_argument("-n", "--max", type=int, default=12)
    ap.add_argument("--chars", type=int, default=320)
    ap.add_argument("--context", type=int, default=0,
                    help="in kèm N đoạn liền trước/sau khi dùng --cid")
    args = ap.parse_args()

    idx_path = os.path.join(args.notebook, "index.json")
    if not os.path.exists(idx_path):
        print("Chưa có sổ tay tại %s — chạy nb_ingest.py trước." % idx_path,
              file=sys.stderr)
        return 2
    idx = C.load_index(idx_path)
    srcs = {s["sid"]: s for s in idx["sources"]}
    docs = {}

    def doc(sid):
        if sid not in docs:
            docs[sid] = C.read_doc(idx_path, srcs[sid])
        return docs[sid]

    def body(c):
        return doc(c["sid"])[c["start"]:c["end"]]

    def loc(c):
        s = srcs[c["sid"]]
        where = ("tr. %s" % c["page"]) if c["page"] else "đoạn %d" % (c["order"] + 1)
        head = (" — %s" % c["heading"]) if c["heading"] else ""
        return "%s · %s%s" % (s["title"][:44], where, head)

    if args.list:
        print("| Mã | Tài liệu | Loại | Trang | Đoạn |")
        print("|---|---|---|---|---|")
        for s in idx["sources"]:
            print("| %s | %s | %s | %s | %d |" % (
                s["sid"], s["title"][:60], s["kind"],
                s["pages"] or "-", s["n_chunks"]))
        return 0

    if args.cid:
        by = {c["cid"]: c for c in idx["chunks"]}
        c = by.get(args.cid)
        if not c:
            print("Không có mã %s trong sổ tay." % args.cid, file=sys.stderr)
            return 1
        sib = [x for x in idx["chunks"] if x["sid"] == c["sid"]]
        i = sib.index(c)
        lo, hi = max(0, i - args.context), min(len(sib), i + args.context + 1)
        for j in range(lo, hi):
            mark = "»»" if j == i else "  "
            print("%s [%s] %s\n%s\n" % (mark, sib[j]["cid"], loc(sib[j]),
                                        body(sib[j]).strip()))
        return 0

    if not args.pattern:
        ap.print_help()
        return 2

    try:
        rx = re.compile(args.pattern, re.I)
        rx_da = re.compile(deaccent(args.pattern), re.I)
    except re.error as e:
        print("Regex sai: %s" % e, file=sys.stderr)
        return 2

    hits = 0
    for c in idx["chunks"]:
        if args.source and c["sid"] != args.source:
            continue
        t = body(c)
        if not (rx.search(t) or rx_da.search(deaccent(t))):
            continue
        hits += 1
        if hits > args.max:
            continue
        snip = C.norm_ws(t)[:args.chars]
        print("[%s] %s\n    %s\n" % (c["cid"], loc(c), snip))

    if hits == 0:
        print("Không có đoạn nào khớp. Thử từ khoá rộng hơn hoặc đồng nghĩa.")
    elif hits > args.max:
        print("… còn %d đoạn nữa (dùng -n để xem thêm)." % (hits - args.max))
    return 0


if __name__ == "__main__":
    sys.exit(main())
