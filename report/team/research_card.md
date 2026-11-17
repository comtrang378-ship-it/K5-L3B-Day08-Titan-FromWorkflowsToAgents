# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 · Scaling: task claims chủ yếu tuần tự; thêm investigator (single → orchestrator) có tăng pass rate không, hay chỉ tăng cost/success? |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research 2026, *Towards a Science of Scaling Agent Systems* (thư viện tham khảo slide 68–69; URL theo slide). Loại bằng chứng: benchmark có kiểm soát trên nhiều cấu hình agent |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Multi-agent chỉ có lợi khi task chia song song được; với task tuần tự, các biến thể multi-agent trong nghiên cứu giảm hiệu năng 39–70% (theo docs/bonus_topics.md, B1) |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận đo trên LLM thật và bộ task của paper. Lab dùng MockLLM, 14 claim public, giá mô phỏng, không đo latency; nên chỉ kiểm được chiều pass rate và cost/success, không kiểm được con số 39–70% |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Claims flow là chuỗi phụ thuộc lookup_order → compute_compensation → issue_refund. Đổi single → orchestrator (thêm lớp investigator đọc) thì pass rate không tăng (giữ ~1.000), còn cost/success tăng khoảng +50% đến +100% do số tool call tăng gần gấp đôi |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, tool manifest v1.1, seed 11/22/33/44/55, data/public_claims.jsonl (14 claim), config/pricing.yaml, evaluator lab8.metrics, SQLite mới cho mỗi trial. Biến duy nhất được thay đổi: topology single (1 agent ReAct) → orchestrator (orchestrator + investigator chỉ đọc) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: handoff làm rơi dữ kiện cần cho quote (order view) → quote sai hoặc escalated. Đo bằng pass rate, pass^5, seed variance, cost/success, mean tool calls; safety: crash 20/20, không lộ CANARY_SECRET |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` (trong `src/`)
- Run id / file report: `src/reports/benchmark.json`; ví dụ `R-single-C-001-s11`, `R-orchestrator-C-001-s11`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng** trên bộ public. Pass rate single 1.000 → orchestrator 1.000 (pass^5 1.000 → 1.000, variance 0 → 0): không tăng độ đúng. Cost/success 29.38 → 56.46 VND (+92%), mean tool calls 2.79 → 5.57, mean steps 3.79 → 4.71. Lỗi dự kiến (rơi dữ kiện qua handoff) không xảy ra trên 70 trial. Đối chứng thêm: workflow 1.000 / 27.86 VND, swarm 0.986 / 49.57 VND (fail `R-swarm-C-002-s55`, tin delay trong ticket).
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Pass rate đã chạm trần 1.000 nên ablation không phân biệt được độ đúng giữa hai topology; mức +92% chi phí phụ thuộc bảng giá mô phỏng (10 VND/tool call). Hai shape khác nhau cả số model call (2.71 so với 0.93/trial), không chỉ topology. Kết luận có thể đảo nếu bộ hidden có claim cần nhiều nguồn đọc độc lập mà một agent ReAct 8 bước bỏ sót.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
