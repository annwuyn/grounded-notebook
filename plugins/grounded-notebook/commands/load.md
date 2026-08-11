---
description: Nạp tài liệu vào sổ tay — tự chuyển sang Markdown và cắt đoạn có mã
argument-hint: "<file hoặc thư mục>… [--append]"
---

Nạp tài liệu vào sổ tay grounded-notebook.

Đường dẫn người dùng đưa: $ARGUMENTS

Việc cần làm:

1. Nếu $ARGUMENTS rỗng, tìm tài liệu trong thư mục hiện tại và các thư mục con
   phổ biến (`docs/`, `sources/`, `tai-lieu/`, `uploads/`), liệt kê cho người
   dùng xác nhận trước khi nạp.
2. Chạy:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_ingest.py" $ARGUMENTS
   ```
   Thêm `--append` khi `notebook/index.json` đã tồn tại và người dùng đang bổ
   sung nguồn mới.
3. Nếu script báo thiếu thư viện, cài đúng thư viện cho định dạng đang nạp rồi
   chạy lại: `pip install pdfplumber python-docx python-pptx openpyxl beautifulsoup4`
4. Nếu có PDF báo "gần như không có text", nói rõ đó là bản scan và cần OCR
   trước khi nạp — đừng lặng lẽ bỏ qua.
5. Trình bày bảng ánh xạ mã nguồn → tên tài liệu mà script in ra, rồi gợi ý bước
   tiếp theo: `/grounded-notebook:ask` để hỏi, hoặc `/grounded-notebook:write`
   để viết.

Đọc skill `grounded-notebook` nếu chưa nắm quy ước mã.
