# Báo cáo cá nhân — 2A202604116_DangThuyDung

## 1. Thông tin thành viên

- Họ tên: Đăng Thùy Dung
- MSSV: 2A202604116
- Email: (tự điền)
- GitHub: [dtdung14](https://github.com/dtdung14)

## 2. Phần việc phụ trách

- Shape B `single` (một agent ReAct): kiểm tra giới hạn 8 bước, model chỉ được chọn tool đọc, tiền do `compute_compensation` tính và chỉ host ghi ledger.
- Benchmark public 4 shape × 14 claim × 5 seed và tổng hợp số liệu cho ADR, research card.

## 3. Đóng góp cụ thể

- Viết shape B `src/lab8/shapes/single.py`. Code được push chung trong commit `a69f265` của nhóm (do Nguyễn Anh Tú đẩy lên khi ghép các shape). Các quyết định kỹ thuật:
  - Claim không tồn tại → `failed`; thiếu `order_id` → `needs_info`, không vào vòng ReAct và không ghi ledger.
  - `decide` chỉ chọn tool đọc theo thứ tự `lookup_order` → `compute_compensation`. Order không thấy được (sai principal) → `escalated`. Kết quả lạ → `failed`.
  - Mỗi bước `decide` gọi MockLLM một lần và tính vào `Budget`, để chi phí so được với các shape khác.
  - `run_react(..., max_steps=8)`; chạm trần thì trả `failed` / `step_cap`.
  - Quote lấy từ order row qua `compute_compensation`, không từ số ngày trong ticket. Quote 0 → `denied`, không gọi `issue_refund`.
  - Sau vòng lặp, code (không phải model) gọi `durability.issue_refund` với **quote đầy đủ** và `crash_at`. Host tự trừ phần đơn đã được hoàn (T13, T14). Không bắt `InjectedCrash`: chỉ ghi trace rồi ném lại. Host từ chối → `denied`; xung đột số tiền → `failed`.
  - Trace chỉ ghi claim_id/order_id, kết quả tool cuối, quote và quyết định; mọi nhánh return đều ghi trace qua `finish()`.
- Thêm test `src/tests/test_single_react.py` (39 test, chạy trong cổng host `python -m pytest -q`):
  - `test_single_model_only_dispatches_read_tools`: ghi lại mọi tool mà vòng ReAct dispatch trên 14 claim public, khẳng định tất cả thuộc `READONLY_TOOLS`.
  - `test_single_stays_within_step_cap`: `model_calls ≤ 8` trên 14 claim × 5 seed.
  - `test_single_step_cap_fails_without_refund`: giả lập vòng lặp chạm trần → `failed`, `step_cap`, không có dòng ledger, vẫn có trace.
  - `test_single_ignores_delay_written_in_ticket`: C-002 (ticket ghi trễ 5 ngày, order row 2 ngày) → `denied` ở cả 5 seed, kể cả seed 55 là seed swarm tham chiếu fail.
  - `test_single_trace_has_no_secret_or_ticket_text`: trace và kết quả không chứa `CANARY_SECRET` hay nguyên văn ticket; `run_id` trong trace khớp kết quả.
- Chạy lại benchmark và so với `src/reports/benchmark.json` đã commit: trùng khớp hoàn toàn (bỏ qua timestamp), tức số liệu tái lập được.
- Tổng hợp số liệu benchmark (pass rate, pass^5, variance, cost/success theo shape) để nhóm dùng cho ADR và research card. Nhóm chốt research card theo câu R4 do Nguyễn Anh Tú điền (`src/reports/ablation_r4.json`).

## 4. Bằng chứng

Lệnh (chạy trong `src/`):

```bash
python -m pytest -q tests/test_single_react.py           # 39 passed
python -m pytest -q -m student -o addopts= -k single     # pass
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

Trích `src/reports/benchmark.json` (MockLLM, giá mô phỏng):

| Shape | pass | pass^5 | variance | cost/success (VND) | mean model calls | mean tool calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 0.000000 | 27.86 | 0.00 | 2.79 |
| single | 1.000 | 1.000 | 0.000000 | 29.38 | 2.71 | 2.79 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 56.46 | 0.93 | 5.57 |
| swarm | 0.986 | 0.929 | 0.000816 | 49.57 | 3.00 | 4.66 |

- Run id: `R-single-C-001-s11`, `R-single-C-002-s55`. Trial fail duy nhất: `R-swarm-C-002-s55` (`status resolved != denied`).
- Ma trận student của single: 62/62 test T01–T14 pass (`python -m pytest -q -m student -o addopts= -k single`); T11 (gọi lại) và T12 (crash rồi chạy lại) đều chỉ ra một refund.
- Code `single.py`: commit `a69f265` (push chung của nhóm). Commit test và báo cáo của tôi: `1c33f34`.

## 5. Công cụ AI đã dùng

- Claude Code: đọc đề và code, chạy test, gợi ý các trường hợp cần test cho single, soạn nháp test và báo cáo.
- Tự kiểm tra: chạy test mới, cổng host, ma trận student và benchmark trên máy; đối chiếu từng số trong báo cáo với `reports/benchmark.json`, không chép số tay.

## 6. Tự đánh giá

- Single đạt pass rate 1.000, pass^5 1.000 trên bộ public và qua đủ ma trận T01–T14. Nó đắt hơn workflow khoảng 5% (29.38 so với 27.86 VND/lần thành công) vì mỗi bước tốn một lần gọi model, trong khi `decide` thực chất đi theo đường cố định. Model không thêm độ đúng nào trên bộ này, nên nhóm chọn workflow là hợp lý.
- Điểm tôi sẽ cải thiện nếu có thêm thời gian: cho `decide` gọi `lookup_refund_history` khi cần để giải thích được phần đã hoàn trước đó trong câu trả lời cho khách (host vẫn là bên áp trần).
- Giới hạn: MockLLM không phải model thật, latency `unavailable`, bộ public chỉ có 14 claim. Test step-cap dùng vòng lặp giả lập vì `decide` hiện không bao giờ tự chạm trần.
