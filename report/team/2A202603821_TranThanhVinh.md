# Báo cáo cá nhân — 2A202603821_TranThanhVinh

## 1. Thông tin thành viên

- Họ tên: Trần Thành Vinh
- MSSV: 2A202603821
- Email: 26ai.vinhtt@vinuni.edu.vn
- GitHub: [vinhs0](https://github.com/vinhs0)

## 2. Phần việc phụ trách

- Shape C `orchestrator` (`src/lab8/shapes/orchestrator.py`): orchestrator + investigator chỉ đọc.
- Handoff allowlist (`handoff.v1`) giữa orchestrator và investigator.
- Trace an toàn: không lộ secret / PII.
- Chạy crash suite và rà checklist nộp bài.

## 3. Đóng góp cụ thể

Commit chính (nhánh `TranThanhVinh`):

- `2749e19`: trace allowlist trong `orchestrator.py` + `test_orchestrator_handoff.py` (đã merge vào `main`).
- `04fed9a`: orchestrator fail-closed, `run_claim` không ném exception + `test_orchestrator_robustness.py`.
- Commit kế tiếp (`test(orchestrator): ...durability`): `test_orchestrator_durability.py`.

Quyết định kỹ thuật:

- **Trace theo allowlist tường minh, không tin vào lọc của tool.** Trước đây event `investigation` ghi nguyên kết quả `lookup_order` / `lookup_refund_history`, event `quote` ghi nguyên quote. Hiện các tool đã lọc sẵn (`lookup_order` chỉ trả `ORDER_FIELDS`), nên chưa có lỗ rò. Nhưng nếu sau này tool thêm field thì field đó sẽ tự chảy vào trace. Tôi thêm `_trace_order`, `_trace_history`, `_trace_quote` để chỉ ghi các field đã liệt kê (order_id, status, delay_days, shipping_fee_vnd, paid_vnd, damage_verified, carrier; refund_count, refunded_vnd; amount_vnd, reason, clause_ids, parts). `RunResult` và hành vi không đổi.
- **Handoff `facts` để rỗng.** Dữ kiện đơn chỉ có sau khi investigator chạy `lookup_order`, nên đưa vào handoff là vòng lặp. Investigator nhận `claim_id`, `principal_scope=owner_order_only` và 4 tool chỉ đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`). Không có tool ghi, không có `parent_secret`, header hay claim row.
- **Tiền và ghi ledger do code.** Orchestrator lấy quote từ `compute_compensation`, truyền **quote đầy đủ** vào `durability.issue_refund` (host tự trừ phần đã hoàn: T13, T14). Có truyền `crash_at`, không bắt `InjectedCrash` (chỉ ghi trace rồi ném lại).
- **Fail-closed thay vì ném exception (`04fed9a`).** `docs/contracts.md` yêu cầu `run_claim` không ném exception; grader ghi trial đó là `exception:<lỗi>` và tính fail (C1). Lỗi bất ngờ giờ trả `status=failed`, ghi trace mới đúng contract v1, `error_reason=exception:<Type>`. Chỉ ghi **tên kiểu** exception, không ghi message, vì message có thể chứa dữ liệu dòng (SĐT, secret). `InjectedCrash` vẫn được ném lại để T12 thấy crash.

Test đã thêm (đều marker `student`):

`src/tests/test_orchestrator_robustness.py` (10 test, `04fed9a`):

- `test_unexpected_error_returns_failed_with_clean_trace`: investigator ném `RuntimeError` (message chứa SĐT) / `KeyError`. Kết quả `failed`, không có refund, trace đúng contract và không lộ message.
- `test_injected_crash_is_still_raised`: crash injection vẫn lan ra ngoài.
- `test_ticket_injection_does_not_change_outcome`: thay ticket của 7 claim (C-001, C-002, C-006, C-007, C-009, C-013, C-014) bằng prompt injection ("ignore policy", đơn giả O-999, trễ 9 ngày, 9.999.999đ). Trên 5 seed, status, quote và ledger vẫn đúng nhãn; trace không chứa chữ bị chèn.

`src/tests/test_orchestrator_durability.py` (40 test). `lab8.crash_test` không chạy qua orchestrator, nên bộ này bù chỗ đó:

- `test_crash_then_resume_commits_exactly_once`: 3 điểm crash × mọi claim public có refund (gồm T08 approval thấp hơn quote, T14 trần theo đơn). Resume xong còn đúng 1 dòng ledger với số tiền theo nhãn và 1 audit `refund_committed`.
- `test_resume_on_another_seed_still_one_refund`: crash ở seed 11, resume ở seed 55 rồi 22. Vẫn 1 refund 120.000 cho T14.
- `test_rerun_same_claim_is_idempotent`: chạy lại cùng claim nhiều lần (T11). Không thêm dòng, không thêm audit.
- `test_gate_denied_claim_never_refunds_even_with_crash`: T07, T13 (cổng host từ chối) với mọi `crash_at`. Kết quả `denied`, quote đầy đủ, 0 dòng ledger, có audit `policy_denied` (must-pass 1).

`src/tests/test_orchestrator_handoff.py` (19 test, `2749e19`):

- `test_make_handoff_drops_secrets_from_facts`: `parent_secret`, SĐT, địa chỉ, `raw_headers`, giá trị `CANARY_SECRET_*` ngoài allowlist bị loại; chỉ còn `ALLOWED_FIELDS` / `FACT_KEYS`.
- `test_make_handoff_rejects_canary_inside_allowed_fact`: canary nằm trong fact được phép thì `HandoffError`.
- `test_make_handoff_rejects_write_tools`: `issue_refund`, `append_audit` thì `HandoffError`.
- `test_orchestrator_trace_and_result_have_no_sensitive_values`: mọi claim public × seed 11, 22, 33, 44, 55. Kiểm trace đúng contract v1 (file tồn tại, `run_id` khớp, `events` là list). Trace và `RunResult` không chứa canary, secret, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng. Event handoff chỉ có key allowlist, `allowed_tools ⊆ READONLY_TOOLS`.
- `test_orchestrator_crash_then_rerun_commits_once`: crash ở `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint` trên C-001. Lần đầu ném `InjectedCrash`; chạy lại ra `resolved`, đúng 1 dòng `refund_ledger` (35.000) và 1 audit `refund_committed`.

## 4. Bằng chứng

Lệnh chạy trong `src/`:

| Lệnh | Kết quả |
| --- | --- |
| `python -m pytest -q` (cổng host) | 110 passed |
| `python -m pytest -q -m student -o addopts=` (ma trận student đầy đủ) | 317 passed |
| `python -m pytest -q -m student -o addopts= -k orchestrator` | 131 passed |
| `python -m pytest -q -m student -o addopts= tests/test_orchestrator_handoff.py tests/test_orchestrator_robustness.py tests/test_orchestrator_durability.py` | 69 passed (19 + 10 + 40) |
| `python -m lab8.crash_test --count 20 --out reports/crash.json` | `crash_safety` 20/20 |
| `python -m lab8.check_submission` | shape orchestrator: format đúng, 12/12 claim public pass ở seed 11 |

Ghi chú crash suite: `lab8.crash_test` gọi thẳng `durability.issue_refund` và swarm (CR-20), không chạy qua shape orchestrator. Vì vậy tôi chạy thêm một script riêng: lặp lại 17 điểm crash có tham số (5 `before_effect`, 7 `after_effect_before_checkpoint`, 5 `after_checkpoint`) với `orchestrator.run_claim("C-001", seed=11)`. Mỗi điểm dùng SQLite mới, crash rồi resume. Kết quả: 17/17 điểm còn đúng 1 dòng ledger và 1 audit `refund_committed`; workflow, single, swarm cũng 17/17. Test `test_orchestrator_crash_then_rerun_commits_once` giữ lại ba loại điểm crash này trong bộ test.

Rà checklist nộp (gửi nhóm):

- `check_submission` còn 1 FAIL: `research_card.md` chưa điền.
- Tên repo trong `TEAM.md` đang là L3B, trong khi commit `034c6c4` của đề yêu cầu mẫu `K5-L3A-...`.
- `group_report.md` mới là template.
- Còn thiếu báo cáo cá nhân của Tú và Dung, cùng test của workflow và single.
- Hash trong ADR và `TEAM.md` cần điền sau khi commit.
- Các file thước đo (`metrics.py`, `durability.py`, `policy.py`, `config/`, `data/`) không đổi so với `main`.

## 5. Công cụ AI đã dùng

- Claude Code: rà an toàn trace / handoff của orchestrator, viết `test_orchestrator_handoff.py`, script crash theo shape, rà checklist nộp bài, soạn nháp báo cáo này.
- Cách tự kiểm tra: tự chạy lại cổng host, bộ student `-k orchestrator`, crash suite và `check_submission` (bảng ở mục 4); đọc diff `orchestrator.py` để chắc `RunResult` không đổi; đối chiếu event trace với `docs/contracts.md`.

## 6. Tự đánh giá

...
