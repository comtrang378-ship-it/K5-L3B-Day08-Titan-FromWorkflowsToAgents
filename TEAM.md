# Team

## Thông tin nhóm

- Tên nhóm: Titan
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-Titan-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: Chưa xác nhận

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
| 1 | Nguyễn Anh Tú | 2A202604088 | comtrang378@gmail.com | [comtrang378-ship-it](https://github.com/comtrang378-ship-it) | Điều phối, workflow và tích hợp |
| 2 | Đăng Thùy Dung | 2A202604116 | Chưa cung cấp | [dtdung14](https://github.com/dtdung14) | Single agent / ReAct và benchmark |
| 3 | Trần Thành Vinh | 2A202603821 | Chưa cung cấp | Chưa cung cấp | Orchestrator, handoff, trace và crash suite |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

### Phân công cụ thể

- **Nguyễn Anh Tú — điều phối, workflow, tích hợp:** phụ trách `workflow.py`, rà contract chung, ghép các nhánh và chạy cổng host cùng ma trận student.
- **Đăng Thùy Dung — single agent / ReAct, benchmark:** phụ trách `single.py`, kiểm tra giới hạn 8 bước và tool chỉ đọc; chạy benchmark public, tổng hợp số liệu.
- **Trần Thành Vinh — orchestrator, handoff và an toàn:** phụ trách `orchestrator.py`, allowlist handoff, trace không lộ dữ liệu nhạy cảm; chạy crash suite và rà checklist nộp.
- **Cùng chịu trách nhiệm:** mỗi người thêm hoặc sửa ít nhất một test cho phần mình, tự kiểm thử, commit phần việc riêng; cả nhóm cùng review kết quả benchmark và báo cáo.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Anh Tú | Điều phối, workflow, tích hợp | Chờ commit | Cần bổ sung test workflow |
| Đăng Thùy Dung | Single agent / ReAct, benchmark | `a69f265` (single.py), `1c33f34` (test, báo cáo) | `src/tests/test_single_react.py` (tool chỉ đọc, trần 8 bước, bỏ qua delay trong ticket, trace không lộ secret) |
| Trần Thành Vinh | Orchestrator, handoff, trace, crash suite | Chờ commit | Cần bổ sung test orchestrator/handoff |

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

- Cần ghi commit và test đã thêm/sửa sau khi hoàn thành.

### Bằng chứng

- Cần bổ sung sau khi commit.

## 2A202604116_DangThuyDung

### Phần việc phụ trách

- Triển khai single agent / ReAct, kiểm tra giới hạn 8 bước và phụ trách benchmark public.

### Đóng góp cụ thể

- Viết `src/lab8/shapes/single.py` (push chung trong commit `a69f265`); thêm `src/tests/test_single_react.py` (39 test); chạy lại benchmark, xác nhận khớp `reports/benchmark.json`; điền `research_card.md`.

### Bằng chứng

- Báo cáo chi tiết: `report/team/2A202604116_DangThuyDung.md`.

## 2A202603821_TranThanhVinh

### Phần việc phụ trách

- Triển khai orchestrator, handoff và trace an toàn; chạy crash suite và rà checklist nộp.

### Đóng góp cụ thể

- Cần ghi commit và test đã thêm/sửa sau khi hoàn thành.

### Bằng chứng

- Cần bổ sung sau khi commit.
