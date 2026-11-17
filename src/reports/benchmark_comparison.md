# So sánh 4 phương pháp

Kết quả benchmark public của A. Workflow, B. Single, C. Orchestrator và D. Swarm.
Mỗi phương pháp chạy trên cùng 14 claim và 5 seed (`11, 22, 33, 44, 55`),
tổng cộng 70 trial/shape. Số liệu được lấy từ
[`benchmark.json`](./benchmark.json), cập nhật ngày 2026-11-15.

| Chỉ số | A. Workflow | B. Single | C. Orchestrator | D. Swarm |
| --- | ---: | ---: | ---: | ---: |
| Số lượt chạy | 70 | 70 | 70 | 70 |
| Số lượt thành công | 70 | 70 | 70 | 69 |
| Pass rate | 100.00% | 100.00% | 100.00% | 98.57% |
| Pass^5 | 100.00% | 100.00% | 100.00% | 92.86% |
| Seed variance | 0.000000 | 0.000000 | 0.000000 | 0.000816 |
| Cost/success (VND mô phỏng) | 27.86 | 29.38 | 56.46 | 49.57 |
| Model calls trung bình/trial | 0.00 | 2.71 | 0.93 | 3.00 |
| Mean steps/trial | 3.79 | 3.79 | 4.71 | 2.80 |

## Cách đọc kết quả

- **Pass^5** là tỷ lệ claim pass ở cả 5 seed, không phải lũy thừa của pass rate.
- **Seed variance** là population variance của pass rate theo từng seed.
- **Cost/success** là tổng chi phí mô phỏng chia số lượt thành công; đây không phải
  giá API thật. Benchmark dùng MockLLM và latency thực không được đo.
- Swarm có số bước trung bình thấp nhất, nhưng có một lượt fail
  (`status resolved != denied`) và pass^5 thấp hơn các shape còn lại.
- Trên bộ public này, workflow có cost/success thấp nhất; kết quả không tự suy rộng
  sang hidden set hay môi trường production.

## Tái lập

Chạy lệnh từ thư mục `src/`:

```powershell
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

`ablation_r4.json` chỉ chứa workflow và orchestrator; dùng `benchmark.json` làm
nguồn cho bảng so sánh đủ bốn phương pháp.
