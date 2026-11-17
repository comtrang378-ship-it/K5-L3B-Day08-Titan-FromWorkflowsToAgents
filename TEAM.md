# Team

## Thông tin nhóm

- Tên nhóm: Titan
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-Titan-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, file đối chiếu: [GitHub](https://github.com/comtrang378-ship-it/K5-L3B-Day8-Titan-From-Workflows-to-Agents), nhánh `main`; shape: [workflow.py](src/lab8/shapes/workflow.py), [single.py](src/lab8/shapes/single.py), [orchestrator.py](src/lab8/shapes/orchestrator.py), benchmark [benchmark.json](src/reports/benchmark.json) và crash [crash.json](src/reports/crash.json) (`a69f265`); selector CP2: [test_public_matrix.py](src/tests/test_public_matrix.py) (`96c9dc1`); privacy/CP4: [test_shape_trace_privacy.py](src/tests/test_shape_trace_privacy.py) (`15f3011`, `881536e`).
- Bonus topic nhóm chọn: **B1 — Investigator song song và critical path**; bằng chứng và giới hạn: [bonus_report.md](report/team/bonus_report.md).

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
| 1 | Nguyễn Anh Tú | 2A202604088 | comtrang378@gmail.com | [comtrang378-ship-it](https://github.com/comtrang378-ship-it) | Điều phối, workflow và tích hợp |
| 2 | Đăng Thùy Dung | 2A202604116 | dangthuydung1410@gmail.com | [dtdung14](https://github.com/dtdung14) | Kiểm thử và benchmark |
| 3 | Trần Thành Vinh | 2A202603821 | 26ai.vinhtt@vinuni.edu.vn | [vinhs0](https://github.com/vinhs0) | Orchestrator, handoff, trace và crash suite |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

### Phân công cụ thể

- **Nguyễn Anh Tú — điều phối, workflow, tích hợp:** phụ trách `workflow.py`, rà contract chung, ghép các nhánh và chạy cổng host cùng ma trận student.
- **Đăng Thùy Dung — kiểm thử và benchmark:** viết test bảo vệ cho shape single (tool chỉ đọc, trần 8 bước); kiểm tra benchmark public tái lập được, tổng hợp số liệu.
- **Trần Thành Vinh — orchestrator, handoff và an toàn:** phụ trách `orchestrator.py`, allowlist handoff, trace không lộ dữ liệu nhạy cảm; chạy crash suite và rà checklist nộp.
- **Cùng chịu trách nhiệm:** mỗi người thêm hoặc sửa ít nhất một test cho phần mình, tự kiểm thử, commit phần việc riêng; cả nhóm cùng review kết quả benchmark và báo cáo.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Anh Tú | Điều phối, workflow, tích hợp | [workflow.py](src/lab8/shapes/workflow.py), [single.py](src/lab8/shapes/single.py), [orchestrator.py](src/lab8/shapes/orchestrator.py), [benchmark.json](src/reports/benchmark.json), [crash.json](src/reports/crash.json) (`a69f265`); [test_public_matrix.py](src/tests/test_public_matrix.py) (`96c9dc1`); [test_shape_trace_privacy.py](src/tests/test_shape_trace_privacy.py), [ablation_r4.json](src/reports/ablation_r4.json), [group_report.md](report/team/group_report.md), [research_card.md](report/team/research_card.md) (`15f3011`, `881536e`); [TEAM.md](TEAM.md), [báo cáo cá nhân](report/team/2A202604088_NguyenAnhTu.md) (`59bf772`, `46e29ec`); [demo.html](report/team/demo.html) (`6927f48`, `8e56c37`) | Thêm/mở rộng [test_shape_trace_privacy.py](src/tests/test_shape_trace_privacy.py); sửa selector CP2 trong [test_public_matrix.py](src/tests/test_public_matrix.py) |
| Đăng Thùy Dung | Kiểm thử và benchmark | `1c33f34` (test, báo cáo), `e6b32cb` (merge PR #1), `14eca6e` (TEAM.md) | `src/tests/test_single_react.py` (tool chỉ đọc, trần 8 bước, bỏ qua delay trong ticket, trace không lộ secret) |
| Trần Thành Vinh | Orchestrator, handoff, trace, crash suite | `2749e19` ([orchestrator.py](src/lab8/shapes/orchestrator.py): trace allowlist; [báo cáo cá nhân](report/team/2A202603821_TranThanhVinh.md)) | Thêm [test_orchestrator_handoff.py](src/tests/test_orchestrator_handoff.py) (19 test: handoff allowlist, chặn tool ghi, trace/result không lộ secret-PII, crash rồi chạy lại chỉ 1 refund) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202604088_NguyenAnhTu

### Phần việc phụ trách

- Điều phối, triển khai workflow và tích hợp các shape.

### Đóng góp cụ thể

- **CP0–CP1:** điều phối thông tin nhóm/lớp/vai trò, đọc contract và business rules; xác minh smoke/test trên workspace Windows/Python 3.12.10, không đại diện cho máy riêng của thành viên khác.
- **CP2:** triển khai `workflow`, `single`, `orchestrator`; giữ model ở quyền đọc, dùng `compute_compensation` làm nguồn quote và để host kiểm approval/cap/idempotency trước khi ghi. Sửa selector `-k single` để chạy đúng 62 test shape.
- **CP3:** truyền `crash_at` tới host và để crash đi qua luồng resume; dùng handoff allowlist, ghi trace đã sanitize; chạy buggy workflow demo để minh họa vì sao checkpoint đơn lẻ không thay ledger/idempotency.
- **CP4:** thêm/mở rộng privacy regression test cho ticket, secret, phone, address, internal note và item name; chạy crash 20/20 cùng kiểm tra approval, trace, crash-resume và order cap.
- **CP5:** chạy benchmark 4 shape × 14 public claim × 5 seed và ablation workflow–orchestrator; cập nhật ADR, research card, báo cáo nhóm/cá nhân. Kết luận chọn workflow giới hạn ở public corpus; hidden pack không có trong workspace.
- **Demo:** tạo [report/team/demo.html](report/team/demo.html), bộ slide sáu trang giải thích kiến trúc, live claim, trace, benchmark và reliability/evaluation.
- File và commit đối chiếu: [workflow.py](src/lab8/shapes/workflow.py), [single.py](src/lab8/shapes/single.py), [orchestrator.py](src/lab8/shapes/orchestrator.py), [benchmark.json](src/reports/benchmark.json), [crash.json](src/reports/crash.json) (`a69f265`); [test_public_matrix.py](src/tests/test_public_matrix.py) (`96c9dc1`); [test_shape_trace_privacy.py](src/tests/test_shape_trace_privacy.py), [ablation_r4.json](src/reports/ablation_r4.json), [group_report.md](report/team/group_report.md), [research_card.md](report/team/research_card.md) (`15f3011`, `881536e`); [TEAM.md](TEAM.md), [báo cáo cá nhân](report/team/2A202604088_NguyenAnhTu.md) (`59bf772`, `46e29ec`); [demo.html](report/team/demo.html) (`6927f48`, `8e56c37`).

### Bằng chứng

- `python -m lab8.smoke`: pass; `python -m pytest -q`: 57 passed.
- `python -m pytest -q -m student -o addopts=`: 248 passed; crash suite 20/20.
- Test mới: `src/tests/test_shape_trace_privacy.py`.
- CP2 selectors: từng shape đều 62 passed; chi tiết trong báo cáo cá nhân.
- CP3 demo: `python -m lab8.demo.buggy_workflow` cho thấy cách dùng checkpoint đơn lẻ tạo hai refund rows thay vì một.

## 2A202604116_DangThuyDung

### Phần việc phụ trách

- Kiểm thử: test bảo vệ các ràng buộc của shape single. Code `single.py` không thuộc phần việc của Dung.
- Benchmark: kiểm tra benchmark public tái lập được và tổng hợp số liệu cho ADR, research card.

### Đóng góp cụ thể

- **CP1:** cài môi trường Python 3.13 (`src/.venv`), chạy smoke và cổng host; đọc business rules, contract và swarm tham chiếu.
- **CP4:** thêm [test_single_react.py](src/tests/test_single_react.py) (39 test, chạy trong cổng host):
  - `test_single_model_only_dispatches_read_tools`: mọi tool vòng ReAct dispatch trên 14 claim đều thuộc `READONLY_TOOLS`;
  - `test_single_stays_within_step_cap`: `model_calls ≤ 8` trên 14 claim × 5 seed;
  - `test_single_step_cap_fails_without_refund`: chạm trần → `failed`, không có dòng ledger, vẫn có trace;
  - `test_single_ignores_delay_written_in_ticket`: C-002 (ticket ghi trễ 5 ngày, order row 2 ngày) → `denied` ở cả 5 seed, kể cả seed 55 là seed swarm tham chiếu fail;
  - `test_single_trace_has_no_secret_or_ticket_text`: trace và kết quả không chứa `CANARY_SECRET` hay nguyên văn ticket, `run_id` khớp.
- **CP5:** chạy lại benchmark 4 shape × 14 claim × 5 seed ra file tạm, so với [benchmark.json](src/reports/benchmark.json) đã commit: trùng khớp (bỏ qua timestamp), tức số liệu tái lập được; tổng hợp số liệu theo shape cho ADR và research card. Nhóm chốt research card theo câu R4.
- **Tích hợp:** mở PR #1 (`dung/single-agent` → `main`), giải quyết xung đột `TEAM.md` / `research_card.md` khi merge (giữ R4 của nhóm), chạy lại toàn bộ test trước khi merge; gỡ dấu xung đột còn sót trong bảng đóng góp.
- File và commit đối chiếu: [test_single_react.py](src/tests/test_single_react.py), [báo cáo cá nhân](report/team/2A202604116_DangThuyDung.md) (`1c33f34`, `9cbdfd4`, `f6d8b82`); merge (`e6b32cb`, PR #1 → `654c8f5`); TEAM.md (`14eca6e`).

### Bằng chứng

- `python -m pytest -q tests/test_single_react.py`: 39 passed.
- Sau khi merge PR #1 vào `main`: `python -m pytest -q` 96 passed; `python -m pytest -q -m student -o addopts=` 248 passed; `python -m lab8.check_submission` 0 FAIL.
- Số liệu trong `reports/benchmark.json`: workflow 1.000 / 27.86 VND, single 1.000 / 29.38 VND, orchestrator 1.000 / 56.46 VND, swarm 0.986 / 49.57 VND (pass rate / cost per success); run id `R-single-C-001-s11`, `R-single-C-002-s55`.
- Báo cáo chi tiết: [report/team/2A202604116_DangThuyDung.md](report/team/2A202604116_DangThuyDung.md).

## 2A202603821_TranThanhVinh

### Phần việc phụ trách

- Triển khai orchestrator, handoff và trace an toàn; chạy crash suite và rà checklist nộp.

### Đóng góp cụ thể

- `orchestrator.py`: trace chỉ ghi field allowlist (`_trace_order`, `_trace_history`, `_trace_quote`); handoff chỉ có tool đọc; truyền quote đầy đủ và `crash_at` vào `durability.issue_refund`.
- Thêm `src/tests/test_orchestrator_handoff.py` (19 test).

### Bằng chứng

- Cổng host 54 passed; `-m student -k orchestrator` 81 passed; crash suite 20/20; crash theo shape orchestrator 17/17 điểm.
- Chi tiết: [report/team/2A202603821_TranThanhVinh.md](report/team/2A202603821_TranThanhVinh.md). Commit hash: `2749e19`.
