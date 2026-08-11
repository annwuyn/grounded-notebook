---
description: Dựng bàn đọc để bôi đen và ghi chú trên tài liệu, rồi xuất tổng hợp có mã
argument-hint: "[--out study.html] [--title \"…\"] hoặc đường dẫn notes.json để dựng lại .md"
---

Yêu cầu: $ARGUMENTS

Lệnh này phục vụ khâu **đọc và ghi chú** trước khi viết. Hai chế độ, tự nhận
theo tham số:

## A. Chưa có ghi chú → dựng bàn đọc

Sổ tay phải có sẵn. Chưa có `notebook/index.json` thì chạy
`/grounded-notebook:load` trước, đừng dựng bàn đọc trên sổ tay trống.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_annot.py" --notebook ./notebook \
    --out study.html --title "…"
```

Đưa `study.html` ra khung làm việc ngay, kèm hướng dẫn ngắn ba ý:

- Bôi đen đoạn bất kỳ → thanh nổi lên với năm nhãn: **Trích dẫn / Phương pháp /
  Kết quả / Khoảng trống / Lý thuyết**.
- Hộp ghi chú mở ra: viết nhận xét, gắn **chủ đề** cách nhau bằng dấu phẩy —
  chính chủ đề này thành mục trong bản tổng hợp. Lưu bằng `⌘↵`.
- Mỗi vệt bôi tự bắt về mã đoạn `[S#:c#]` theo offset ký tự, nên bản xuất đã có
  trích dẫn truy vết sẵn.

Nói rõ hai giới hạn, đừng để người dùng mất công: ghi chú nằm trong
`localStorage` của trình duyệt chứ không nằm trong file, nên cần **Xuất .json**
định kỳ; và nạp lại sổ tay bằng tài liệu khác là đổi khoá lưu.

## B. Đã có `notes.json` → dựng `.md` và kiểm neo

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_notes.py" notes.json \
    --notebook ./notebook --notes notes.md --synthesis synthesis.md
```

Đây là đường nên dùng khi đã có nhiều ghi chú, vì nó kiểm lại neo: offset lệch
thì neo lại theo nguyên văn, mã sai vị trí thì sửa, không tìm thấy nguyên văn
thì báo `MẤT NEO` và loại khỏi bản tổng hợp (exit 1).

**Báo lại đầy đủ những gì script in ra** — số ghi chú neo lại, mã đã sửa, và
từng ghi chú mất neo. Mất neo thường có nghĩa tài liệu đã được nạp lại khác đi;
nói thẳng điều đó thay vì lặng lẽ bỏ qua.

Rồi verify và dựng bản đọc như bình thường:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_verify.py" synthesis.md
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/nb_reader.py" synthesis.md --out reader.html
```

Nguyên văn trong bản xuất nằm trong blockquote nên `nb_verify.py` bỏ qua — nó
đúng theo cấu trúc vì được cắt trực tiếp từ tài liệu. Cái bị kiểm là phần văn
người dùng viết ở mục **Diễn giải**.

## Nối sang bước viết

`synthesis.md` là khung, không phải bản thảo: bảng chủ đề × nguồn, mỗi chủ đề
gom chứng cứ kèm mã, chừa sẵn mục **Diễn giải** với dãy mã đã gom. Người dùng
muốn viết tiếp thì chuyển sang quy trình của `/grounded-notebook:write`, dùng
`synthesis.md` làm bản đồ chứng cứ thay cho việc truy vấn lại từ đầu.
