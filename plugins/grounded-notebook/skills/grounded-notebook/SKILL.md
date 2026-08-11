---
name: grounded-notebook
description: Sổ tay nghiên cứu kiểu NotebookLM — nạp tài liệu (PDF/DOCX/PPTX/XLSX/HTML/MD/CSV) tự chuyển sang Markdown, rồi viết bất kỳ nội dung nào với trích dẫn truy vết bấm được mở đúng đoạn nguồn ngay trong khung làm việc. Dùng khi người dùng đưa tài liệu và muốn tổng quan tài liệu, tóm tắt, hỏi đáp trên tài liệu, viết báo cáo hay bài nghiên cứu mà mọi khẳng định phải chỉ được về nguồn — hoặc khi họ nói "nạp tài liệu", "sổ tay", "grounded", "trích dẫn truy vết", "chống bịa nguồn", "như NotebookLM".
---

# Grounded Notebook

Mô phỏng cơ chế của NotebookLM: tài liệu được chuyển sang Markdown và cắt thành
đoạn có mã; mọi câu thực chứng trong bản viết mang mã trỏ về đúng đoạn; người đọc
bấm mã là thấy nguyên văn đoạn nguồn và toàn văn tài liệu, tất cả nằm trong một
file HTML tự chứa mở thẳng trong khung làm việc.

`${CLAUDE_PLUGIN_ROOT}/scripts/` chứa sáu script. Gán một lần đầu phiên:

```bash
NB="${CLAUDE_PLUGIN_ROOT}/scripts"
```

## Nguyên tắc bất di bất dịch

1. **Không có đoạn nguồn thì không có câu.** Chỉ viết một khẳng định thực chứng
   khi đã tìm được đoạn cụ thể trong sổ tay nói điều đó. Không lấy từ trí nhớ rồi
   gắn mã cho có.
2. **Mã phải trỏ đúng đoạn đã đọc.** Trước khi viết mã, đọc lại nội dung đoạn đó
   bằng `nb_query.py --cid`. Không đoán "chắc là ở gần đó".
3. **Ngoặc kép là nguyên văn tuyệt đối.** Chữ trong `"..."` phải sao chép từng ký
   tự từ nguồn. Muốn diễn giải hoặc dịch sang tiếng Việt thì bỏ ngoặc kép.
4. **Không bỏ bước verify.** Bản nháp chưa qua `nb_verify.py` sạch lỗi nặng thì
   chưa phải bản nháp.
5. Không tìm được nguồn cho một ý quan trọng thì viết thẳng
   `> **[THIẾU NGUỒN]** <điều cần tìm>` thay vì gắn mã gần đúng.
6. Câu siêu ngôn ngữ ("Phần này trình bày…", "Tôi lập luận rằng…") không cần mã.

## Quy ước mã

| Loại nguồn | Mã | Nghĩa |
|---|---|---|
| Có phân trang | `[S1:p12.3]` | nguồn S1, trang 12, đoạn thứ 3 trên trang |
| Không phân trang | `[S2:c45]` | nguồn S2, đoạn thứ 45 |
| Nhiều nguồn cho một ý | `[S1:p12.3; S3:c8]` | ngăn bằng chấm phẩy trong cùng cặp ngoặc |

PDF và PPTX có "trang" (PPTX tính theo slide, XLSX theo sheet). Mã đặt cuối câu,
trước dấu chấm. Mã chính là `cid` trong sổ tay — không tự chế chuỗi nào khác.

## Quy trình

### Bước 1 — Nạp tài liệu

```bash
python3 "$NB"/nb_ingest.py <file hoặc thư mục>...      # tạo ./notebook/
python3 "$NB"/nb_ingest.py --append tai_lieu_moi.pdf   # thêm về sau
```

Mỗi tài liệu được chuyển sang Markdown lưu tại `notebook/markdown/`, cắt đoạn
70–90 từ, giữ số trang thật của PDF và đường dẫn heading của DOCX/MD. Sau khi
chạy, **báo lại cho người dùng bảng ánh xạ S1/S2/S3 → tên tài liệu**.

Nếu một PDF báo "gần như không có text" thì đó là bản scan, cần OCR trước khi nạp.

### Bước 2 — Đọc trước khi viết

Không viết một chữ nào trước khi đã lọc đoạn liên quan:

```bash
python3 "$NB"/nb_query.py "từ khoá|đồng nghĩa|synonym"   # regex, bỏ dấu vẫn khớp
python3 "$NB"/nb_query.py "chăm sóc" --source S2 -n 20
python3 "$NB"/nb_query.py --cid S1:p12.3 --context 1     # xem nguyên văn + ngữ cảnh
python3 "$NB"/nb_query.py --list                         # bảng nguồn
```

Lặp với nhiều bộ từ khoá cho từng luận điểm. Với corpus lớn, dựng "bản đồ chứng
cứ": mỗi luận điểm → danh sách mã + trích đoạn ngắn. Đủ dày mới viết.

Khi người dùng chỉ hỏi đáp trên tài liệu (không cần bản viết), trả lời ngay trong
hội thoại nhưng vẫn kèm mã sau mỗi ý, và nói rõ điều gì tài liệu không trả lời được.

### Bước 2b — Người dùng tự đọc và ghi chú (tuỳ chọn)

Khi người dùng muốn tự đọc tài liệu chứ không giao hẳn cho Claude — điển hình là
làm tổng quan tài liệu cho luận án — dựng bàn đọc để họ bôi đen và ghi chú:

```bash
python3 "$NB"/nb_annot.py --notebook ./notebook --out study.html --title "…"
```

Bôi đen một đoạn là gắn được nhãn (trích dẫn / phương pháp / kết quả / khoảng
trống / lý thuyết), viết ghi chú và gắn chủ đề. Mỗi vệt bôi tự bắt về mã đoạn
theo offset ký tự, nên bản xuất đã có trích dẫn truy vết sẵn. Ghi chú lưu trong
`localStorage` của trình duyệt — nhắc người dùng **Xuất .json** định kỳ.

Có `notes.json` rồi thì dựng hai file `.md`:

```bash
python3 "$NB"/nb_notes.py notes.json --notebook ./notebook \
    --notes notes.md --synthesis synthesis.md
```

`nb_notes.py` kiểm lại neo: offset lệch thì neo lại theo nguyên văn, mã sai vị
trí thì sửa, không tìm thấy nguyên văn thì báo `MẤT NEO` và loại khỏi bản tổng
hợp. **Báo lại đầy đủ những gì nó in ra**, nhất là ghi chú mất neo — đó là dấu
hiệu tài liệu đã được nạp lại khác đi.

`synthesis.md` là khung viết chứ chưa phải bản thảo: bảng chủ đề × nguồn, mỗi
chủ đề gom chứng cứ kèm mã, chừa sẵn mục **Diễn giải** với dãy mã đã gom. Dùng
nó làm bản đồ chứng cứ cho bước 3 thay vì truy vấn lại từ đầu.

### Bước 3 — Viết bản nháp có mã

Viết `draft.md` bình thường, mỗi câu thực chứng kết bằng mã:

```markdown
Mạng xã hội "accelerated the process of globalization" [S1:p93.2], đồng thời làm
mờ ranh giới giữa không gian riêng tư và không gian nghề nghiệp [S3:c10; S1:p94.1].

> **[THIẾU NGUỒN]** Cần số liệu bỏ học của nghiên cứu sinh có con nhỏ.
```

### Bước 4 — Verify rồi dựng reader

```bash
python3 "$NB"/nb_verify.py draft.md
python3 "$NB"/nb_reader.py draft.md --out reader.html --title "…"
```

| Mã lỗi | Ý nghĩa | Xử lý |
|---|---|---|
| `E1_MALFORMED` / `E1_DANGLING` | mã sai cú pháp hoặc không tồn tại | **bắt buộc sửa** |
| `E2_QUOTE` | chữ trong ngoặc kép không khớp nguồn đã dẫn | **bắt buộc sửa** — chép lại đúng nguyên văn, hoặc bỏ ngoặc kép |
| `E3_UNCITED` | câu có số liệu/khẳng định thực chứng mà thiếu mã | tìm nguồn, hoặc hạ giọng thành nhận định của tác giả |
| `E4_UNUSED` | nguồn chưa dùng lần nào | báo người dùng — có thể là nguồn thừa hoặc bị bỏ sót |

Chạy lại đến khi hết lỗi nặng (exit code 0). Chỉ khi đó mới dựng reader.

### Bước 5 — Giao sản phẩm

Đưa `reader.html` ra cho người dùng xem ngay trong khung làm việc: đặt file vào
thư mục output của phiên rồi trình bày nó (trên claude.ai/Cowork file HTML sẽ
render thành khung đọc; trong terminal thì mở bằng trình duyệt). File tự chứa
hoàn toàn — không gọi mạng, không phụ thuộc file ngoài, gửi cho người khác vẫn
bấm được trích dẫn.

Luôn giao đủ ba thứ: `draft.md` (bản gốc để sửa tiếp), `notebook/` (sổ tay để
verify và dựng lại), `reader.html` (bản đọc). Sửa bản viết thì sửa `draft.md` rồi
chạy lại bước 4 — không sửa tay `reader.html`.

## Reader hoạt động thế nào

Hai cột: bài viết bên trái, panel nguồn bên phải (trên màn hình hẹp panel trượt
lên từ dưới). Bấm chip `S1:p93.2` → panel hiện tên tài liệu, vị trí, nguyên văn
đoạn nguồn, đoạn liền trước và liền sau để soi ngữ cảnh, nút **Mở toàn văn tại
đoạn này** (nhảy tới đúng vị trí trong toàn văn Markdown và tô sáng), nút chép
nguyên văn. Ô tìm kiếm quét toàn bộ nguồn. `Esc` quay về danh sách nguồn kèm số
lần trích của từng tài liệu. Mã hỏng hiện viền đỏ đứt nét ngay trong bài.

`--lite` chỉ nhúng đoạn được trích ± 2 đoạn kề khi corpus quá lớn.

## Kết hợp với việc khác

- Cần APA/MLA thật: giữ `[S1:p93.2]` làm tầng truy vết nội bộ, bước cuối chuyển
  sang `(Seymour, 2021, tr. 93)` và giữ `draft.md` bản có mã làm bản kiểm chứng.
- Thư mục nguồn lớn: nạp một lần rồi `--append` dần, không nạp lại từ đầu.
- Thiếu thư viện chuyển đổi: `pip install pdfplumber python-docx python-pptx
  openpyxl beautifulsoup4 markdown`. Chỉ cần cái tương ứng định dạng đang dùng.
