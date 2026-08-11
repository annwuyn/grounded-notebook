---
description: Xem sổ tay đang có nguồn nào, bao nhiêu đoạn
---

Báo cáo tình trạng sổ tay hiện tại.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_query.py" --list
```

Chưa có `notebook/index.json` thì nói rõ sổ tay còn trống và hướng dẫn chạy
`/grounded-notebook:load`. Có rồi thì trình bày bảng nguồn, và nếu trong thư mục
có `draft.md` thì chạy thêm `nb_verify.py draft.md` để báo luôn tình trạng trích
dẫn của bản nháp.
