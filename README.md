# grounded-notebook

Sổ tay nghiên cứu kiểu NotebookLM cho Claude. Nạp tài liệu vào, tài liệu tự
chuyển sang Markdown và cắt thành đoạn có mã. Sau đó mọi nội dung Claude viết ra
đều mang trích dẫn trong câu, và **bấm vào trích dẫn là mở đúng đoạn nguồn ngay
trong khung làm việc** — không mở tab ngoài, không cần file gốc.

```
[S1:p12.3]  →  nguồn S1, trang 12, đoạn 3
[S2:c45]    →  nguồn S2, đoạn 45  (tài liệu không phân trang)
```

## Cài đặt

```
/plugin marketplace add annwuyn/grounded-notebook
/plugin install grounded-notebook@grounded-plugins
```

Cài thư viện Python tương ứng định dạng bạn dùng:

```bash
pip install pdfplumber python-docx python-pptx openpyxl beautifulsoup4 markdown
```

Không có thư viện nào là bắt buộc hết — chỉ cần cái khớp với loại file đang nạp.
Riêng `markdown` chỉ để bản đọc đẹp hơn; thiếu thì plugin dùng bộ render rút gọn
có sẵn.

## Dùng

| Lệnh | Việc |
|---|---|
| `/grounded-notebook:load docs/` | Nạp tài liệu, chuyển sang Markdown, cắt đoạn |
| `/grounded-notebook:ask "câu hỏi"` | Hỏi đáp trên tài liệu, mỗi ý kèm mã nguồn |
| `/grounded-notebook:write "tổng quan về X"` | Viết bài có trích dẫn, verify, dựng bản đọc |
| `/grounded-notebook:annotate` | Dựng bàn đọc để tự bôi đen, ghi chú, xuất tổng hợp |
| `/grounded-notebook:reader` | Verify lại và dựng lại bản đọc |
| `/grounded-notebook:status` | Xem sổ tay đang có gì |

Không gõ lệnh cũng được: đưa tài liệu rồi nói "nạp mấy file này vào sổ tay rồi
viết tổng quan tài liệu có trích dẫn truy vết", skill sẽ tự kích hoạt.

Định dạng nạp được: PDF, DOCX, PPTX, XLSX, HTML, Markdown, TXT, CSV/TSV, JSON.
PDF bản scan cần OCR trước — plugin sẽ báo nếu file không có lớp text.

## Bản đọc hoạt động thế nào

Hai cột: bài viết bên trái, panel nguồn bên phải (màn hình hẹp thì panel trượt
lên từ dưới). Bấm chip trích dẫn:

- panel hiện tên tài liệu, vị trí, **nguyên văn** đoạn nguồn
- kèm đoạn liền trước và liền sau để soi ngữ cảnh, tránh trích cắt xén
- nút **Mở toàn văn tại đoạn này** nhảy tới đúng vị trí trong toàn văn và tô sáng
- ô tìm kiếm quét toàn bộ nguồn, bấm kết quả là nhảy tới chỗ đó
- `Esc` quay về danh sách nguồn kèm số lần trích của từng tài liệu
- mã hỏng hiện viền đỏ đứt nét ngay trong bài

`reader.html` tự chứa hoàn toàn: không gọi mạng, không phụ thuộc file ngoài. Gửi
cho đồng nghiệp qua email vẫn bấm được trích dẫn.

## Tự đọc và ghi chú

Không phải lúc nào cũng muốn giao hẳn việc đọc cho Claude. `annotate` dựng một
bàn làm việc HTML để bạn tự đọc:

```
/grounded-notebook:annotate
```

Mở `study.html`, chọn tài liệu, **bôi đen** đoạn bất kỳ. Thanh nổi lên với năm
nhãn — Trích dẫn, Phương pháp, Kết quả, Khoảng trống, Lý thuyết — chọn xong thì
viết ghi chú và gắn chủ đề. Mỗi vệt bôi **tự bắt về mã đoạn** theo offset ký tự,
nên bạn không phải gõ mã nào.

Ba nút xuất ở thanh trên:

- **notes.md** — danh sách theo nguồn: nguyên văn, mã đoạn, ghi chú, chủ đề.
- **synthesis.md** — khung viết tổng quan tài liệu: bảng chủ đề × nguồn, mỗi chủ
  đề gom chứng cứ từ mọi nguồn kèm mã, chừa sẵn mục **Diễn giải** với dãy mã đã
  gom để bạn viết vào; nhãn *Khoảng trống* tách thành mục riêng.
- **notes.json** — bản gốc để nạp lại hoặc đưa qua CLI.

Ghi chú lưu trong `localStorage` của trình duyệt, không nằm trong file — xuất
`.json` định kỳ. `nb_notes.py` dựng lại hai file `.md` từ `.json` và **kiểm lại
neo**: offset lệch thì tự neo lại theo nguyên văn, mã sai vị trí thì sửa, không
tìm thấy nguyên văn thì báo mất neo và loại khỏi bản tổng hợp.

Hai file `.md` xuất ra dùng đúng cú pháp mã của sổ tay nên chạy thẳng được qua
`nb_verify.py` và `nb_reader.py`.

## Vì sao trích dẫn không bịa được

Trích dẫn không phải do mô hình "nhớ" mà là mã trỏ tới khoảng ký tự cụ thể trong
file Markdown đã chuyển đổi. Trước khi dựng bản đọc, `nb_verify.py` chạy bốn phép
kiểm:

| Mã | Ý nghĩa | Mức |
|---|---|---|
| `E1_MALFORMED` / `E1_DANGLING` | mã sai cú pháp hoặc trỏ tới đoạn không tồn tại | chặn |
| `E2_QUOTE` | chữ trong ngoặc kép không khớp nguyên văn nguồn đã dẫn | chặn |
| `E3_UNCITED` | câu có số liệu hoặc khẳng định thực chứng mà thiếu mã | cảnh báo |
| `E4_UNUSED` | nguồn đã nạp nhưng chưa trích lần nào | cảnh báo |

Còn lỗi chặn thì không dựng bản đọc.

## Dùng script trực tiếp

Sáu script chạy độc lập, không cần Claude:

```bash
NB=plugins/grounded-notebook/scripts

python3 $NB/nb_ingest.py docs/                    # → ./notebook/
python3 $NB/nb_ingest.py --append them.pdf
python3 $NB/nb_query.py "caregiving|chăm sóc"     # regex, bỏ dấu vẫn khớp
python3 $NB/nb_query.py --cid S1:p12.3 --context 1
python3 $NB/nb_query.py --list
python3 $NB/nb_verify.py draft.md
python3 $NB/nb_reader.py draft.md --out reader.html --title "Tổng quan"
python3 $NB/nb_reader.py draft.md --lite          # corpus lớn

python3 $NB/nb_annot.py --out study.html          # bàn đọc: bôi đen + ghi chú
python3 $NB/nb_notes.py notes.json                # → notes.md + synthesis.md
python3 $NB/nb_notes.py notes.json --check        # chỉ kiểm neo, không ghi file
```

Sổ tay nằm gọn trong `./notebook/`: `index.json` và thư mục `markdown/` chứa bản
chuyển đổi của từng tài liệu. Đọc được bằng mắt thường, sửa được bằng tay.

## Cấu trúc repo

```
.claude-plugin/marketplace.json          catalog để /plugin marketplace add
plugins/grounded-notebook/
  .claude-plugin/plugin.json
  commands/                              6 slash command
  skills/grounded-notebook/SKILL.md      quy trình và luật trích dẫn
  scripts/                               nb_ingest · nb_query · nb_verify · nb_reader
                                         nb_annot · nb_notes
```

## Giấy phép

MIT © annwuyn.
