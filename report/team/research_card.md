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
| CÂU | R1 / R2 / R3 / R4 | R4 — Evaluation confounders |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Liu et al., “AgentBench: Evaluating LLMs as Agents,” ICLR 2024, https://arxiv.org/abs/2308.03688 — benchmark nghiên cứu trên 8 môi trường tương tác. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Tác giả xây dựng benchmark gồm 8 môi trường để đánh giá khả năng reasoning và decision-making của LLM khi làm agent; abstract báo cáo hiệu năng khác nhau giữa các nhóm model và nêu các dạng khó khăn như reasoning dài hạn, ra quyết định và instruction following. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết quả của AgentBench áp dụng cho model, prompt, môi trường và tác vụ trong benchmark của paper; không trực tiếp dự đoán kết quả của workflow xử lý claim LogiX-VN hoặc MockLLM. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Workflow so với orchestrator sẽ có pass rate gần như nhau (chênh không quá 0.02) trên public set, nhưng workflow giảm cost/success khoảng 35–55% nhờ ít model/tool orchestration hơn. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | So sánh workflow và orchestrator; giữ MockLLM, tool registry, pricing, 14 public claim, seed 11/22/33/44/55, as_of và evaluator cố định. Biến so sánh là shape. Số model/tool call được đo như kết quả của kiến trúc, không giữ cố định. Mỗi trial dùng SQLite mới. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Rủi ro là ticket chứa chỉ dẫn/số ngày gây quyết định sai hoặc một trace không hợp lệ. Đo pass rate, pass^5, seed min–max/variance, cost/success và steps; ma trận trial cũng kiểm tra contract, policy denial và trace. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,orchestrator --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r4.json`
- Run id / file report: `R-workflow-C-001-s11`, `R-orchestrator-C-001-s11`; `src/reports/ablation_r4.json`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Hypothesis được ủng hộ trên public set: cả hai pass rate và pass^5 đều 1.000, seed variance 0; workflow cost/success 27.86 VND so với orchestrator 56.46 VND, giảm khoảng 50.7%. Mean/p95 steps lần lượt 3.79/4 và 4.71/5. Đây là kết quả mô phỏng, không phải ước lượng thống kê cho production.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
