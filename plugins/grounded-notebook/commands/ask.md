---
description: Hỏi đáp trên tài liệu đã nạp, mọi câu trả lời đều kèm mã nguồn
argument-hint: "<câu hỏi>"
---

Trả lời câu hỏi sau **chỉ dựa trên** tài liệu trong sổ tay: $ARGUMENTS

Bắt buộc:

1. Kiểm tra `notebook/index.json` có tồn tại. Chưa có thì bảo người dùng chạy
   `/grounded-notebook:load` trước.
2. Truy vấn sổ tay trước khi trả lời, nhiều bộ từ khoá cho tới khi đủ chứng cứ:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_query.py" "từ khoá|đồng nghĩa"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_query.py" --cid <mã> --context 1
   ```
3. Trả lời ngay trong hội thoại, mỗi ý thực chứng kèm mã dạng `[S1:p12.3]`.
   Không dùng kiến thức nền để lấp chỗ trống.
4. Nói thẳng phần nào tài liệu không trả lời được, thay vì suy đoán.
5. Nếu người dùng muốn bản đọc bấm được, gợi ý `/grounded-notebook:write`.
