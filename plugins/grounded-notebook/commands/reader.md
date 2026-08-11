---
description: Verify lại bản nháp rồi dựng lại bản đọc HTML bấm được
argument-hint: "[đường dẫn draft.md] [--lite]"
---

Dựng lại bản đọc cho bản nháp: $ARGUMENTS (mặc định `draft.md`).

1. Chạy verify trước, luôn luôn:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_verify.py" <draft>
   ```
   Còn lỗi nặng thì dừng lại, báo lỗi và đề xuất cách sửa — không dựng reader
   trên bản nháp có mã hỏng.
2. Sạch lỗi nặng thì dựng:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_reader.py" <draft> --out reader.html
   ```
   Thêm `--lite` nếu corpus lớn và file vượt ~4 MB.
3. Đưa `reader.html` ra khung làm việc cho người dùng mở ngay.
