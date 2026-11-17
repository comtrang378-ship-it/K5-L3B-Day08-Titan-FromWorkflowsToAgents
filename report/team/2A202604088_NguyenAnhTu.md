# Báo cáo cá nhân — Nguyễn Anh Tú

## 1. Thông tin thành viên

- Họ tên: Nguyễn Anh Tú
- MSSV: 2A202604088
- Email: comtrang378@gmail.com
- GitHub: [comtrang378-ship-it](https://github.com/comtrang378-ship-it)

## 2. Phần việc phụ trách

Điều phối, workflow và tích hợp theo phân công trong [TEAM.md](../../TEAM.md).

## 3. Đóng góp cụ thể

- Commit hiện có `a69f265` chứa phần triển khai ba shape, TEAM và bằng chứng benchmark/crash. Đây là commit tích hợp, không phải commit riêng từng shape.
- Quyết định kỹ thuật: giữ quyết định tiền trong `compute_compensation` và để `durability.issue_refund` kiểm approval/cap/idempotency; không dùng nội dung ticket làm policy input.
- Commit `a69f265` không thay đổi test file. Kiểm thử hồi quy mới `src/tests/test_shape_trace_privacy.py` đang có trong working tree; cần review và commit cùng thay đổi test để đáp ứng checklist đóng góp.

## 4. Bằng chứng

- `python -m lab8.smoke`: pass.
- `python -m pytest -q`: 54 passed.
- `python -m pytest -q -m student -o addopts=`: 248 passed.
- `tests/test_shape_trace_privacy.py`: 3 trường hợp (workflow, single, orchestrator) passed trong cổng host.
- Run id: `R-workflow-C-001-s11`; kết quả ở `src/reports/benchmark.json`.
- Crash safety: 20/20 trong `src/reports/crash.json`.

## 5. Công cụ AI đã dùng

Đã dùng Copilot SDK trong VS Code để hỗ trợ triển khai shape, rà contract và soạn báo cáo. Kết quả được kiểm tra bằng smoke, pytest, benchmark và crash suite. Thành viên cần tự đọc lại thay đổi và xác nhận mình giải thích được ranh giới code/model, quote đầy đủ và trace redaction.

## 6. Tự đánh giá

Đã có implementation cho ba shape và các kiểm tra public đều xanh; workflow là lựa chọn phù hợp nhất với bộ public vì pass rate giữ ở 1.000 trong khi chi phí mô phỏng thấp nhất. Hạn chế là chưa có hidden pack để tự kiểm và chưa có commit riêng chứa kiểm thử trace privacy mới. Trước khi nộp, cần review trực tiếp mã nguồn, commit test/báo cáo và cập nhật hash cuối.
