# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: Titan
- Lớp: L3B
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md).
- Commits: `a69f265` (shape/public benchmark/crash), `96c9dc1` (CP2 test selector), `15f3011` (privacy test/ablation), `881536e` (CP4 tests), `59bf772` (evidence metadata), `bd8f5a7` (CP0–CP5 report update).
- CP1 trên workspace này: Python 3.12.10 / Windows; smoke pass; host suite khi setup 54 passed; TEAM có thành viên và vai trò. Không thể xác minh smoke trên máy riêng của các thành viên khác.

## Tiến độ theo checkpoint

| CP | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| CP0 — repo và nhóm | Repo nhóm đã tồn tại, remote GitHub trỏ tới repo Titan, nhánh `main`; thông tin và vai trò có trong TEAM. | Nhóm xác nhận dùng lớp L3B. File hướng dẫn mẫu vẫn ghi L3A; nếu coach yêu cầu áp dụng đúng mẫu thì cần xác nhận quy ước tên repo. |
| CP1 — cài đặt/contracts | Hoàn tất trên workspace Windows/Python 3.12.10; smoke pass, business rules/contracts đã được dùng trong triển khai. Host suite ban đầu 54 passed; hiện là 57 sau khi thêm ba privacy regression cases. | Chưa xác minh môi trường trên máy từng thành viên. |
| CP2 — ba shape | Hoàn tất; mỗi shape có đúng 62 student tests pass. | Selector `-k single` đã được sửa để chỉ chạy shape single. |
| CP3 — handoff/ledger/crash | Hoàn tất; ba shape forward `crash_at`, handoff orchestrator dùng allowlist, retry/crash-resume nằm trong student tests. | Demo `lab8.demo.buggy_workflow` in `unsafe refund rows: 2`, minh họa checkpoint đơn lẻ không thay ledger. |
| CP4 — must-pass | Crash suite 20/20; approval/order-cap và test trace/PII/secret đã chạy. | Không có hidden pack; leak/bypass counts chính thức chỉ giảng viên xác minh được. |
| CP5 — benchmark/decision | Benchmark 4 shape × 14 claim × 5 seed, ablation workflow–orchestrator, ADR và research card đã điền. | Không có `student_drop/`; hidden self-check chưa chạy. |

## 2. Mục tiêu và cách tiếp cận

Mục tiêu là chạy cùng quy trình claim hoàn phí qua workflow, single agent, orchestrator và swarm tham chiếu, trong khi giữ quyết định tiền, kiểm approval và ghi ledger ở code/host. Nhóm chọn workflow làm kiến trúc ít tự chủ nhất trong các shape đạt kết quả public chính xác. Phân công hiện tại: Nguyễn Anh Tú phụ trách workflow/tích hợp; Đăng Thùy Dung phụ trách single/ReAct và benchmark; Trần Thành Vinh phụ trách orchestrator, handoff, trace và crash suite. Việc ghi nhận commit và test riêng của từng thành viên cần được cập nhật theo đóng góp thực tế.

## 3. Giải pháp

- **Workflow:** đọc claim qua `get_claim_view`, từ chối thiếu order id, xác minh quyền sở hữu bằng `lookup_order`, tính quote bằng `compute_compensation`, rồi chuyển quote đầy đủ cho `durability.issue_refund`. Không dùng ticket để quyết định số ngày trễ.
- **Single:** chạy ReAct tối đa 8 bước với các tool đọc; model không có quyền ghi refund. Code đọc kết quả quote và gọi host sau vòng lặp.
- **Orchestrator:** tạo handoff bằng `make_handoff` với allowlist tool đọc, chạy investigator và dùng kết quả order/quote đã được giới hạn để gọi host. Trace ghi handoff đã sanitize.

Ở cả ba shape, host chịu trách nhiệm approval, cap theo order, idempotency và audit. Trace chỉ ghi các view đã allowlist, quote, quyết định và kết quả gọi host; không ghi ticket thô, parent secret, raw header, số điện thoại, địa chỉ, internal note hay tên hàng. Test hồi quy `src/tests/test_shape_trace_privacy.py` thay ticket và parent secret bằng marker kiểm thử, sau đó xác nhận chúng không xuất hiện trong trace hoặc RunResult.

## 4. Kết quả

Benchmark public gồm 14 claim × 5 seed, cùng MockLLM, bảng giá mô phỏng và evaluator; mỗi trial có SQLite riêng. Số liệu lấy từ `src/reports/benchmark.json`.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean / p95 steps |
|---|---:|---:|---:|---:|---:|---:|
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 27.86 | 3.79 / 4 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 29.38 | 3.79 / 4 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.46 | 4.71 / 5 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Crash suite đạt **20/20** (`src/reports/crash.json`). Bộ student đạt 248 passed; cổng host đạt 57 passed, bao gồm ba trường hợp trace privacy mới. Mỗi selector CP2 (`-k workflow`, `-k single`, `-k orchestrator`) chạy đúng 62 test sau khi đổi tên test ma trận chung để tránh `-k single` khớp tên test thay vì chỉ shape. Swarm có một trial sai: T02 ở seed 55, khi ticket ghi trễ 5 ngày còn order ghi 2 ngày. Các shape nhóm viết không gặp lỗi này trên public set. Gói hidden không có trong workspace, vì vậy chưa có kết quả tự kiểm hidden và không thể kết luận pass rate 40 × 5.

Workflow được chọn vì đạt cùng độ chính xác public như single và orchestrator, đồng thời có cost/success thấp nhất; đây là kết luận giới hạn ở bộ public. Phân tích thêm ablation workflow–orchestrator nằm trong [research_card.md](./research_card.md).

## 5. Khó khăn và cách xử lý

Starter ban đầu để ba shape ở dạng stub; khi chưa cài đặt, các test student tương ứng được kỳ vọng thất bại. Sau khi hoàn thiện flow và truyền `crash_at` tới host, nhóm chạy lại smoke, host suite, toàn bộ ma trận student, crash suite và benchmark. Kết quả hiện tại: `lab8.smoke pass`, 57 host tests passed, 248 student tests passed và crash safety 20/20.

## 6. Tổng hợp đóng góp

Phân công theo shape và đầu việc được ghi trong [TEAM.md](../../TEAM.md). Kiểm thử hồi quy `src/tests/test_shape_trace_privacy.py` bao phủ cả ba shape và CP2 selector được kiểm trong `src/tests/test_public_matrix.py`. Lịch sử hiện tại ghi các commit triển khai/tích hợp của Nguyễn Anh Tú; chưa xác minh được commit kỹ thuật riêng của Đăng Thùy Dung hay Trần Thành Vinh. Báo cáo cá nhân của hai thành viên này và khai báo công cụ AI/tự đánh giá vẫn cần chính họ cung cấp; không suy đoán thay.

## 7. Hạn chế và hướng cải thiện

MockLLM là mô phỏng seeded, không đại diện cho model sản xuất; cost là VND mô phỏng và latency là `unavailable`. Public set chỉ có 14 claim, nên kết quả không thay thế hidden 40 claim × 5 seed. So sánh shape giữ corpus, seed, pricing và evaluator cố định nhưng số lần gọi model/tool khác nhau do chính kiến trúc; đây là outcome cần đo, đồng thời giới hạn khả năng quy kết nhân quả chỉ cho topology. Cần chạy hidden self-check/grader và rà soát bảo mật trên môi trường chấm trước khi nộp.

## 8. Tài liệu tham khảo

- Liu et al., [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688), ICLR 2024.
- [Lab 8 README](../../README.md), [business rules](../../docs/business_rules.md), [contracts](../../docs/contracts.md), [metrics](../../docs/metrics.md).
