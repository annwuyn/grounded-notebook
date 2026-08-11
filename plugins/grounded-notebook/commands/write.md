---
description: Viết nội dung có trích dẫn truy vết, verify rồi dựng bản đọc bấm được
argument-hint: "<yêu cầu viết, ví dụ: tổng quan tài liệu về X, 1500 chữ>"
---

Viết theo yêu cầu: $ARGUMENTS

Theo đúng quy trình trong skill `grounded-notebook`, không rút gọn bước nào:

1. **Đọc trước.** Truy vấn `nb_query.py` với nhiều bộ từ khoá cho từng luận
   điểm, dựng bản đồ chứng cứ (luận điểm → mã + trích đoạn). Chỉ khi đủ dày mới
   viết. Xác nhận nguyên văn bằng `--cid` trước khi gắn bất kỳ mã nào.
2. **Viết `draft.md`**, mỗi câu thực chứng kết bằng mã. Chữ trong ngoặc kép phải
   là nguyên văn tuyệt đối. Ý quan trọng không có nguồn thì ghi
   `> **[THIẾU NGUỒN]** …` chứ không gắn mã gần đúng.
3. **Verify:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_verify.py" draft.md
   ```
   Sửa hết E1/E2. Xử lý hoặc giải thích từng E3/E4. Chạy lại tới khi exit 0.
4. **Dựng bản đọc:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_reader.py" draft.md --out reader.html --title "…"
   ```
5. **Giao:** đưa `reader.html` ra khung làm việc cho người dùng xem ngay, kèm
   `draft.md`. Tóm tắt ngắn: bao nhiêu trích dẫn, nguồn nào chưa dùng, chỗ nào
   còn thiếu nguồn.
