# Orderly — Web app quản lý đơn hàng

Ứng dụng full-stack quản lý đơn hàng với frontend HTML/CSS/JavaScript thuần, REST API FastAPI và dữ liệu lưu bền vững trong SQLite.

## Chức năng

- Thêm, xem, sửa và xóa đơn hàng.
- Ba trạng thái: **Mới**, **Đang xử lý**, **Hoàn thành**.
- Thống kê tổng số đơn, số đơn theo trạng thái và tổng doanh thu.
- Tìm kiếm theo khách hàng/sản phẩm/mã đơn và lọc theo trạng thái.
- Giao diện dark mode responsive cho desktop và mobile.
- SQLite là nguồn dữ liệu duy nhất; frontend giao tiếp với backend qua Fetch API.

## Cách chạy

Yêu cầu Python 3.10 trở lên.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Mở <http://127.0.0.1:8000>. Backend phục vụ cả giao diện và API; tài liệu API có tại <http://127.0.0.1:8000/docs>.

File `backend/orders.db` được tự động tạo ở lần chạy đầu tiên.

Nếu muốn chạy frontend bằng server riêng, giữ backend ở cổng `8000`, rồi mở terminal khác tại thư mục gốc:

```powershell
python -m http.server 5500 -d frontend
```

Sau đó mở <http://127.0.0.1:5500>. Frontend tự nhận biết môi trường local và gọi API ở cổng `8000`.

## Cấu trúc

```text
frontend/
  index.html
  styles.css
  app.js
backend/
  main.py
  database.py
  models.py
  requirements.txt
README.md
```
