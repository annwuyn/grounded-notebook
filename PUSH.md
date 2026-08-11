# Đưa lên GitHub và cài vào Claude

Tôi không có quyền truy cập tài khoản GitHub của bạn nên không tự push được.
Bốn lệnh dưới đây làm nốt phần đó.

## 1. Tạo repo rỗng

Vào https://github.com/new, đặt tên `grounded-notebook`, để **Public**, và
**không** tick thêm README/`.gitignore`/LICENSE (repo này đã có sẵn).

## 2. Thay chỗ giữ chỗ

Trong `plugins/grounded-notebook/.claude-plugin/plugin.json` và `README.md`,
đổi `GITHUB_USER` thành tài khoản GitHub của bạn:

```bash
cd grounded-notebook
grep -rl GITHUB_USER . | xargs sed -i '' 's/GITHUB_USER/tai-khoan-cua-ban/g'   # macOS
# Linux: grep -rl GITHUB_USER . | xargs sed -i 's/GITHUB_USER/tai-khoan-cua-ban/g'
```

Muốn đổi tên marketplace (`grounded-plugins`) hay tên tác giả thì sửa
`.claude-plugin/marketplace.json` luôn ở bước này. Tên marketplace là thứ người
dùng gõ khi cài: `/plugin install grounded-notebook@<tên-marketplace>`.

## 3. Push

```bash
git init
git add .
git commit -m "grounded-notebook: sổ tay có trích dẫn truy vết"
git branch -M main
git remote add origin https://github.com/tai-khoan-cua-ban/grounded-notebook.git
git push -u origin main
```

Có `gh` CLI thì gọn hơn:

```bash
gh repo create grounded-notebook --public --source=. --push
```

## 4. Cài trong Claude Code

```
/plugin marketplace add tai-khoan-cua-ban/grounded-notebook
/plugin install grounded-notebook@grounded-plugins
```

Nếu bản tóm tắt cài đặt hiện `Run /reload-plugins to activate.` thì chạy lệnh đó.

Kiểm tra trước khi push (chạy trong thư mục repo):

```bash
claude plugin validate .
claude plugin validate ./plugins/grounded-notebook
```

## Cập nhật về sau

Sửa code xong, **bump `version`** trong `plugins/grounded-notebook/.claude-plugin/plugin.json`
rồi push. Không bump thì Claude Code thấy version cũ và giữ nguyên bản đã cache.
Người dùng chạy `/plugin marketplace update` rồi `/plugin update` để nhận bản mới.

## Thử tại chỗ, chưa cần GitHub

```
/plugin marketplace add ./duong-dan/toi/grounded-notebook
/plugin install grounded-notebook@grounded-plugins
```
