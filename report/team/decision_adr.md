# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: `654c8f5`
- Run id dẫn chứng: R-workflow-C-001-s11 (reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: Không phát hiện trong kiểm tra public; hidden chưa chạy

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Chọn workflow vì đây là shape ít tự chủ nhất và đạt pass rate 1.000, pass^5 1.000 trên 14 claim × 5 seed. Nó có chi phí mô phỏng thấp nhất (27.86 VND/lần thành công), thấp hơn single (29.38), orchestrator (56.46) và swarm (49.57); seed variance bằng 0. Đây chỉ là kết luận trên bộ public với MockLLM và bảng giá mô phỏng.

## Có đáng đổi lấy multi-agent không

Không trên kết quả hiện tại: single và orchestrator không tăng pass rate, còn chi phí cao hơn; swarm có một trial sai do tin số ngày trong ticket ở seed 55. Chỉ xem xét đổi nếu kiểm thử hidden đại diện cho workload thật cho thấy cải thiện đáng kể về độ đúng hoặc một yêu cầu vận hành cần thiết khác, đồng thời vẫn qua must-pass.

## Trace và bằng chứng

Trace ghi claim/order view đã allowlist, quote, quyết định và kết quả gọi host. Không ghi ticket nguyên văn, parent secret, header, principal id, điện thoại, địa chỉ, ghi chú nội bộ hay tên hàng. Trace được ghi dưới `src/traces/` khi chạy trực tiếp; benchmark dùng thư mục tạm riêng cho từng trial.

## Giới hạn

MockLLM không phải model sản xuất; latency là `unavailable`, chi phí chỉ mô phỏng. Public set có 14 claim, không thay thế bộ hidden 40 claim × 5 seed. Không sửa JSON cho đủ 0.75.
