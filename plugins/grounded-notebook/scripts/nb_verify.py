#!/usr/bin/env python3
"""nb_verify — kiểm tra mọi marker trong bản nháp có thật và trích đúng nguyên văn.

    python3 nb_verify.py draft.md
    python3 nb_verify.py draft.md --notebook ./notebook --json

Mã lỗi:
  E1_MALFORMED  marker sai cú pháp
  E1_DANGLING   marker trỏ tới đoạn không tồn tại
  E2_QUOTE      chữ trong ngoặc kép không khớp nguyên văn nguồn đã dẫn
  E3_UNCITED    câu thực chứng thiếu marker            (cảnh báo)
  E4_UNUSED     nguồn đã nạp nhưng chưa trích lần nào  (cảnh báo)
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nb_common as C

HARD = ("E1_MALFORMED", "E1_DANGLING", "E2_QUOTE")

QUOTE_RE = re.compile(r"[\"“]([^\"“”]{8,400})[\"”]")
SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-Ỹ\"“(])")
NUMERIC_RE = re.compile(r"\d+([.,]\d+)?\s?%|\bp\s?[<=>]|\d{4}\b|\b\d+([.,]\d+)?\b")
EMPIRIC_RE = re.compile(
    r"\b(nghiên cứu|khảo sát|kết quả|số liệu|dữ liệu|báo cáo|tỷ lệ|chứng minh|"
    r"cho thấy|chỉ ra|ghi nhận|thống kê|mẫu|study|studies|survey|found|"
    r"reported|showed|evidence|data|results?)\b", re.I)
META_RE = re.compile(
    r"^(bài viết|chương|phần|mục|tôi |chúng tôi |bài này|this (paper|chapter|"
    r"section|study) (will|aims)|dưới đây|sau đây|trước hết|tóm lại)", re.I)


def strip_code(md):
    """Thay nội dung code fence bằng khoảng trắng, giữ nguyên độ dài."""
    out = list(md)
    for m in re.finditer(r"```.*?```", md, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--notebook", default="notebook")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    idx_path = os.path.join(args.notebook, "index.json")
    if not os.path.exists(idx_path):
        print("Không thấy %s" % idx_path, file=sys.stderr)
        return 2
    idx = C.load_index(idx_path)
    srcs = {s["sid"]: s for s in idx["sources"]}
    by_cid = {c["cid"]: c for c in idx["chunks"]}
    docs = {}

    def body(cid):
        c = by_cid[cid]
        if c["sid"] not in docs:
            docs[c["sid"]] = C.read_doc(idx_path, srcs[c["sid"]])
        return docs[c["sid"]][c["start"]:c["end"]]

    raw = open(args.draft, encoding="utf-8").read()
    md = strip_code(raw)
    lines = md.split("\n")
    issues = []
    used = set()

    def line_of(pos):
        return md.count("\n", 0, pos) + 1

    # --- E1 -----------------------------------------------------------
    ok_spans = []
    for m in C.MARKER_RE.finditer(md):
        ok_spans.append(m.span())
        for cid in [x.strip() for x in m.group(1).split(";")]:
            if cid in by_cid:
                used.add(cid)
            else:
                issues.append({"code": "E1_DANGLING", "line": line_of(m.start()),
                               "detail": "mã %s không có trong sổ tay" % cid})
    for m in C.LOOSE_MARKER_RE.finditer(md):
        if any(a <= m.start() and m.end() <= b for a, b in ok_spans):
            continue
        issues.append({"code": "E1_MALFORMED", "line": line_of(m.start()),
                       "detail": "marker sai cú pháp: %s" % m.group(0)})

    # --- E2 / E3 ------------------------------------------------------
    for para in re.finditer(r"[^\n]+(?:\n[^\n]+)*", md):
        ptext = para.group(0)
        pstart = para.start()
        stripped = ptext.lstrip()
        if stripped.startswith(("#", ">", "|", "```")):
            continue
        pos = 0
        for sent in SENT_SPLIT.split(ptext):
            spos = ptext.find(sent, pos)
            pos = spos + len(sent)
            ln = line_of(pstart + max(spos, 0))
            cids = []
            for m in C.MARKER_RE.finditer(sent):
                cids += [x.strip() for x in m.group(1).split(";")]
            cids = [c for c in cids if c in by_cid]

            for q in QUOTE_RE.finditer(sent):
                quote = C.fold(q.group(1))
                if len(quote.split()) < 4:
                    continue
                if not cids:
                    issues.append({"code": "E2_QUOTE", "line": ln,
                                   "detail": "trích nguyên văn nhưng không có "
                                             "marker: “%s…”" % quote[:60]})
                    continue
                if not any(quote in C.fold(body(c)) for c in cids):
                    issues.append({
                        "code": "E2_QUOTE", "line": ln,
                        "detail": "“%s…” không khớp nguyên văn %s"
                                  % (quote[:60], ", ".join(cids))})

            if cids:
                continue
            core = C.MARKER_RE.sub("", sent).strip(" -*•\t")
            if len(core.split()) < 6 or META_RE.match(core):
                continue
            if NUMERIC_RE.search(core) or EMPIRIC_RE.search(core):
                issues.append({"code": "E3_UNCITED", "line": ln,
                               "detail": core[:90]})

    # --- E4 -----------------------------------------------------------
    cited_sids = {by_cid[c]["sid"] for c in used}
    for s in idx["sources"]:
        if s["sid"] not in cited_sids:
            issues.append({"code": "E4_UNUSED", "line": 0,
                           "detail": "%s (%s) chưa được trích lần nào"
                                     % (s["sid"], s["title"][:50])})

    hard = [i for i in issues if i["code"] in HARD]
    soft = [i for i in issues if i["code"] not in HARD]

    if args.json:
        print(json.dumps({"hard": len(hard), "soft": len(soft),
                          "used_chunks": len(used), "issues": issues},
                         ensure_ascii=False, indent=1))
        return 1 if hard else 0

    if not issues:
        print("✓ Sạch. %d đoạn nguồn được trích." % len(used))
        return 0
    for i in hard:
        print("✗ %-13s dòng %-4s %s" % (i["code"], i["line"], i["detail"]))
    for i in soft:
        print("· %-13s %s %s" % (i["code"],
                                 ("dòng %-4s" % i["line"]) if i["line"] else "        ",
                                 i["detail"]))
    print("\n%d lỗi nặng, %d cảnh báo, %d đoạn nguồn được trích."
          % (len(hard), len(soft), len(used)))
    if hard:
        print("Sửa hết lỗi nặng rồi mới dựng reader.")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
