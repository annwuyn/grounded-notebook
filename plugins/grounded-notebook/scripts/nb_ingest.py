#!/usr/bin/env python3
"""nb_ingest — nạp tài liệu vào sổ tay: chuyển sang Markdown rồi index hoá.

    python3 nb_ingest.py tai_lieu/            # nạp cả thư mục
    python3 nb_ingest.py a.pdf b.docx         # nạp từng file
    python3 nb_ingest.py --append c.pdf       # thêm vào sổ tay có sẵn
    python3 nb_ingest.py --notebook ./nb x/   # đổi thư mục sổ tay
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nb_common as C


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for n in sorted(names):
                    if n.startswith("."):
                        continue
                    if os.path.splitext(n)[1].lower() in C.SUPPORTED:
                        files.append(os.path.join(root, n))
        elif os.path.isfile(p):
            files.append(p)
        else:
            C.warn("không tìm thấy: %s" % p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--notebook", default="notebook",
                    help="thư mục sổ tay (mặc định ./notebook)")
    ap.add_argument("--append", action="store_true",
                    help="thêm nguồn vào sổ tay đã có")
    args = ap.parse_args()

    nb = args.notebook
    mdd = os.path.join(nb, "markdown")
    idx_path = os.path.join(nb, "index.json")
    os.makedirs(mdd, exist_ok=True)

    if args.append and os.path.exists(idx_path):
        idx = C.load_index(idx_path)
    else:
        idx = {"version": 2, "sources": [], "chunks": []}
    idx["updated"] = datetime.datetime.now().isoformat(timespec="seconds")

    have = {s["file"] for s in idx["sources"]}
    next_n = len(idx["sources"]) + 1

    files = collect(args.inputs)
    if not files:
        print("Không có file nào để nạp.", file=sys.stderr)
        return 1

    added = 0
    for path in files:
        rel = os.path.relpath(path)
        if rel in have:
            print("  = bỏ qua (đã có): %s" % rel)
            continue
        try:
            text, pages, kind = C.to_markdown(path)
        except Exception as e:
            C.warn("%s → lỗi chuyển đổi: %s" % (rel, e))
            continue
        if len(text.strip()) < 30:
            C.warn("%s → gần như không có text (PDF scan? cần OCR trước)" % rel)
            continue

        sid = "S%d" % next_n
        name = "%s__%s.md" % (sid, C.slugify(
            os.path.splitext(os.path.basename(path))[0]))
        with open(os.path.join(mdd, name), "w", encoding="utf-8") as f:
            f.write(text)

        chunks = C.chunk_document(text, pages, sid)
        idx["sources"].append({
            "sid": sid,
            "title": os.path.splitext(os.path.basename(path))[0],
            "file": rel,
            "kind": kind,
            "pages": len(pages),
            "chars": len(text),
            "n_chunks": len(chunks),
            "markdown": os.path.join("markdown", name),
        })
        idx["chunks"].extend(chunks)
        next_n += 1
        added += 1
        print("  + %-4s %-52s %s%d đoạn" % (
            sid, os.path.basename(path)[:52],
            ("%d trang, " % len(pages)) if pages else "", len(chunks)))

    C.save_index(idx_path, idx)

    print("\nSổ tay: %s" % os.path.abspath(nb))
    print("Đã nạp %d tài liệu mới — tổng %d nguồn, %d đoạn.\n"
          % (added, len(idx["sources"]), len(idx["chunks"])))
    print("| Mã | Tài liệu | Loại | Đoạn |")
    print("|---|---|---|---|")
    for s in idx["sources"]:
        print("| %s | %s | %s | %d |"
              % (s["sid"], s["title"][:60], s["kind"], s["n_chunks"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
