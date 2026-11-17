# Báo cáo cá nhân — Nguyễn Anh Tú

## 1. Thông tin thành viên

- Họ tên: Nguyễn Anh Tú
- MSSV: 2A202604088
- Email: comtrang378@gmail.com
- GitHub: [comtrang378-ship-it](https://github.com/comtrang378-ship-it)

## 2. Phần việc phụ trách

Điều phối, workflow và tích hợp theo phân công trong [TEAM.md](../../TEAM.md).

## 3. Đóng góp cụ thể

- Commits: `a69f265` triển khai shape/evidence; `96c9dc1` sửa selector CP2; `15f3011` thêm trace test/ablation/report; `881536e` hoàn thiện kiểm tra CP4; `59bf772` lưu metadata CP4.
- Quyết định kỹ thuật: giữ quyết định tiền trong `compute_compensation` và để `durability.issue_refund` kiểm approval/cap/idempotency; không dùng nội dung ticket làm policy input.
- Kiểm thử hồi quy `src/tests/test_shape_trace_privacy.py` được thêm trong `15f3011` và mở rộng CP4 trong `881536e`.

## 4. Bằng chứng

- `python -m lab8.smoke`: pass.
- `python -m pytest -q`: 57 passed.
- `python -m pytest -q -m student -o addopts=`: 248 passed.
- CP2 workflow: `python -m pytest -q -m student -o addopts= -k workflow` — 62 passed.
- CP2 single: `python -m pytest -q -m student -o addopts= -k single` — 62 passed after renaming the shared matrix test to avoid a `-k single` name collision.
- CP2 orchestrator: `python -m pytest -q -m student -o addopts= -k orchestrator` — 62 passed.
- `tests/test_shape_trace_privacy.py`: 3 trường hợp (workflow, single, orchestrator) passed trong cổng host.
- Run id: `R-workflow-C-001-s11`; kết quả ở `src/reports/benchmark.json`.
- Crash safety: 20/20 trong `src/reports/crash.json`.
- CP4 approval/trace/crash tests: 24 passed.
- CP4 crash-resume T12 trên bốn shape: 4 passed; T13/T14 về order refund cap: 40 passed.
- Test trace privacy đưa marker canary trong ticket, parent secret và phone/address/internal note/item name; marker không xuất hiện trong trace, RunResult hoặc stdout ở cả ba shape.
- `check_submission`: 0 FAIL; gói hidden không có trong workspace nên không có số liệu hidden về leak/bypass.
- CP3 demo: `python -m lab8.demo.buggy_workflow` in `unsafe refund rows: 2 (the host ledger must stay at 1)`, cho thấy checkpoint đơn lẻ không đảm bảo exactly-once effect.

## Ghi chú CP2

- **Mức tự chủ:** workflow chạy các bước Python cố định; single dùng ReAct nhưng bị giới hạn tối đa 8 bước và chỉ gọi tool đọc; orchestrator chuyển handoff đã sanitize cho investigator chỉ đọc rồi tự quyết định gọi host.
- **Vì sao truyền quote đầy đủ:** `issue_refund` tính phần còn được hoàn theo tổng đã refund của order. Nếu shape tự trừ trước, host trừ lần nữa và có thể trả thiếu, như T14.
- **Vì sao không tự từ chối quote dương:** shape phải gọi `issue_refund` để host ghi audit `policy_denied` khi approval không hợp lệ hoặc order đã hoàn đủ. Nếu shape chặn trước, audit bắt buộc sẽ thiếu.

## Ghi chú CP4

- Host kiểm `approval_id` gắn đúng claim, trạng thái và hạn approval; quote dương bị host từ chối được ghi `policy_denied`. T13 xác nhận order đã hoàn đủ bị chặn; T14 xác nhận phần entitlement tăng chỉ được trả phần chênh bởi host.
- Trace là phần của ranh giới bảo mật vì grader đọc trace và các file `<run_id>*` để xác nhận format, freshness, `run_id` và không rò secret/PII. Grader fail-closed với trace thiếu, cũ, sai JSON hoặc sai `run_id`.
- Chưa có hidden pack nên chỉ có thể khẳng định các kiểm tra public/fixtures đã chạy, không thể khẳng định hidden secret-leak hay approval-bypass count.

## 5. Công cụ AI đã dùng

Đã dùng Copilot SDK trong VS Code để hỗ trợ triển khai shape, rà contract và soạn báo cáo. Kết quả được kiểm tra bằng smoke, pytest, benchmark và crash suite. Thành viên cần tự đọc lại thay đổi và xác nhận mình giải thích được ranh giới code/model, quote đầy đủ và trace redaction.

## 6. Tự đánh giá

Đã có implementation cho ba shape và các kiểm tra public đều xanh; workflow là lựa chọn phù hợp nhất với bộ public vì pass rate giữ ở 1.000 trong khi chi phí mô phỏng thấp nhất. Hạn chế là chưa có hidden pack để tự kiểm. Trước khi nộp, cần review trực tiếp mã nguồn và nộp commit của mình lên repo nhóm.
