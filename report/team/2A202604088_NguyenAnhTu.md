# Báo cáo cá nhân — Nguyễn Anh Tú

## 1. Thông tin thành viên

- Họ tên: Nguyễn Anh Tú
- MSSV: 2A202604088
- Email: comtrang378@gmail.com
- GitHub: [comtrang378-ship-it](https://github.com/comtrang378-ship-it)

## 2. Phần việc phụ trách

Điều phối, workflow và tích hợp theo phân công trong [TEAM.md](../../TEAM.md).

## 3. Đóng góp cụ thể

- Commit `a69f265` chứa phần triển khai ba shape và benchmark/crash evidence; commit `15f3011` bổ sung test trace privacy, ablation và báo cáo.
- Quyết định kỹ thuật: giữ quyết định tiền trong `compute_compensation` và để `durability.issue_refund` kiểm approval/cap/idempotency; không dùng nội dung ticket làm policy input.
- Kiểm thử hồi quy mới `src/tests/test_shape_trace_privacy.py` được thêm trong commit `15f3011`.

## 4. Bằng chứng

- `python -m lab8.smoke`: pass.
- `python -m pytest -q`: 57 passed.
- `python -m pytest -q -m student -o addopts=`: 248 passed.
- `tests/test_shape_trace_privacy.py`: 3 trường hợp (workflow, single, orchestrator) passed trong cổng host.
- Run id: `R-workflow-C-001-s11`; kết quả ở `src/reports/benchmark.json`.
- Crash safety: 20/20 trong `src/reports/crash.json`.

## 5. Công cụ AI đã dùng

Đã dùng Copilot SDK trong VS Code để hỗ trợ triển khai shape, rà contract và soạn báo cáo. Kết quả được kiểm tra bằng smoke, pytest, benchmark và crash suite. Thành viên cần tự đọc lại thay đổi và xác nhận mình giải thích được ranh giới code/model, quote đầy đủ và trace redaction.

## 6. Tự đánh giá

Đã có implementation cho ba shape và các kiểm tra public đều xanh; workflow là lựa chọn phù hợp nhất với bộ public vì pass rate giữ ở 1.000 trong khi chi phí mô phỏng thấp nhất. Hạn chế là chưa có hidden pack để tự kiểm. Trước khi nộp, cần review trực tiếp mã nguồn và nộp commit của mình lên repo nhóm.
