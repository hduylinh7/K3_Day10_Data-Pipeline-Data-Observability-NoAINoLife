# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Hoàng Duy Linh |
| MSSV | 2A202601159 |
| Khóa/Lớp | K3 - VinUni |
| Tên nhóm | Nhóm 3 - Data Observability |
| Vai trò chính | RAG & Evaluation Owner |
| Repository | https://github.com/hduylinh7/K3_Day10_Data-Pipeline-Data-Observability-NoAINoLife |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Vector Store & Embedding Index | `src/retrieval/index.py` (`LocalEmbeddingIndex`, `embeddings.py`) | Cleaned DataFrame | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Hoàn thành |
| RAG Agent & Search Tools | `src/retrieval/agent.py`, `qa.py`, `llm.py` | Query string & Chroma collection | `AnswerResult`, `data/results/agent_demo_answers.json` | Hoàn thành |
| Evaluation Test Set Builder | `src/evaluation/testset.py` (`build_test_set`) | Cleaned DataFrame | `data/eval/test_set.json` (40 samples) | Hoàn thành |
| Metrics Evaluation & Scoring | `src/evaluation/metrics.py` (`evaluate_pipeline`, `_token_f1`, `_judge_answer`) | Test set & Chroma index | `data/results/baseline_metrics.json`, `baseline_answers.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Thống nhất Document & Vector Contract | Lê Tiến Minh (Ingestion/Cleaning) | Thống nhất các trường metadata trong `LocalEmbeddingIndex._build_documents` |
| Cung cấp kết quả Metrics cho Report | Nguyễn Tuấn Anh (Observability) | Xuất báo cáo JSON tổng hợp để điền vào Markdown Reports |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng Vector Index | `src/retrieval/index.py` | Tạo Chroma DB collection với `all-MiniLM-L6-v2` | `LocalEmbeddingIndex.build(df, settings)` |
| Sinh bộ câu hỏi kiểm thử | `src/evaluation/testset.py` | Sinh 40 câu hỏi thuộc 4 dạng (`summary`, `authors`, `date`, `categories`) | `data/eval/test_set.json` |
| Tính toán Metrics | `src/evaluation/metrics.py` | Đo Hit Rate (100%), Token F1 (1.0), Judge Score (5.0/5.0) | `data/results/baseline_metrics.json` |
| Đánh giá tác động lỗi | `src/pipelines/corruption_flow.py` | Ghi nhận Hit Rate giảm từ 100% xuống 80% khi bị corruption | `data/results/corrupted_metrics.json` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Tạo mô hình nhúng (Vector Embedding) cho toàn bộ bài báo học thuật, lưu giữ vào cơ sở dữ liệu vector ChromaDB, xây dựng Agent tra cứu dữ liệu, đồng thời lập bộ công cụ tự động chấm điểm đánh giá (Evaluation Framework) để đo lường chính xác tác động của dữ liệu xấu lên chất lượng trả lời.

### Cách triển khai
1. **Embedding & ChromaDB**: Dùng `sentence-transformers/all-MiniLM-L6-v2` tạo vector 384 chiều cho chuỗi `text_for_embedding`. Khởi tạo Chroma persistent client với không gian khoảng cách cosine (`hnsw: space=cosine`).
2. **Test set**: Hàm `build_test_set` duyệt các bài báo sạch, tự động sinh 4 nhóm câu hỏi: tóm tắt nội dung (`summary`), tác giả (`authors`), ngày xuất bản (`date`), danh mục (`categories`) kèm theo Ground Truth chuẩn.
3. **Evaluator**: Hàm `evaluate_pipeline` thực hiện search top-k (k=4), kiểm tra xem `ground_truth_doc_ids` có xuất hiện trong danh sách kết quả trích xuất hay không để tính `retrieval_hit_rate`. Hàm `_token_f1` tính độ trùng khớp từ vựng, và `_judge_answer` chấm điểm câu trả lời trên thang điểm 1-5.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Cleaned DataFrames (`papers_clean.csv`, `*_corrupted.csv`, `*_repaired.csv`) |
| Output | Chroma DB persistent directory (`data/chroma`), metrics JSON files (`baseline_metrics.json`, v.v.) |
| Module phụ thuộc | `src/retrieval/embeddings.py`, `src/retrieval/llm.py` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `src/observability/reporting.py` |
| Điều kiện lỗi cần xử lý | Tự động chuyển sang Heuristic Evaluator (dựa trên F1) nếu không có LLM API Key |

### Cách xác minh

```bash
python script/run_phase1.py
```

- **Kết quả mong đợi:** Tạo collection `papers-baseline` chứa 24 documents và file `baseline_metrics.json` với Hit Rate = 1.0.
- **Kết quả thực tế:** Hit Rate = 1.0, Token F1 = 1.0000, Judge Score = 5.00 / 5.0.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn chiến lược sinh câu hỏi và Ground Truth cho bộ test set.
- **Các phương án đã cân nhắc:**
  1. *Phương án A*: Dùng LLM tự động viết các câu hỏi tự do ngẫu nhiên.
  2. *Phương án B*: Thiết kế câu hỏi mẫu theo khuôn định dạng chuẩn (`Who authored...`, `When was...`, `What is the summary...`) trích xuất trực tiếp từ các trường thông tin chuẩn của bài báo.
- **Phương án đã chọn:** Phương án B.
  - **Lý do:** Phương án B đảm bảo tính nhất quán 100% (deterministic), không bị ảnh hưởng bởi tính vô định của LLM khi sinh câu hỏi, giúp việc tái hiện đánh giá hoàn toàn khách quan.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Quá trình tải mô hình `sentence-transformers/all-MiniLM-L6-v2` mất nhiều thời gian ở lần chạy đầu tiên.
- **Cách xử lý:** Sử dụng decorator `@lru_cache(maxsize=4)` trong `embeddings.py` để cache instance mô hình trong bộ nhớ, tránh việc load lại mô hình nhiều lần giữa các lượt query.
- **Cách xác minh sau khi sửa:** Thời gian thực thi tìm kiếm vector diễn ra dưới 50ms cho mỗi query.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index**: Raw JSON -> parse `PaperRecord` -> cleaning & ghép `text_for_embedding` -> MiniLM encode thành vector float -> nạp vào ChromaDB collection.
2. **Evaluation set và Ground Truth**: 40 câu hỏi cố định chứa `ground_truth` và `ground_truth_doc_ids`. Khi agent trả lời, evaluator đối chiếu ID tài liệu trích xuất và tính `retrieval_hit_rate` và `token_f1`.
3. **Quality vs Freshness**: Quality checks đo tính toàn vẹn (null, unique, min length) của dữ liệu hiện tại; Freshness monitoring đo mốc thời gian ngày xuất bản (`age_days` <= 180) để đảm bảo tri thức không bị lạc hậu.
4. **Giữ nguyên test set**: Để đo lường chính xác tác động tiêu cực của corruption và hiệu quả phục hồi của repair trên cùng một thước đo cố định.
5. **Repair thành công**: Khi `retrieval_hit_rate` phục hồi từ 80% lên 100%, Quality checks quay về `PASSED` và Freshness trở lại `FRESH`.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | Việc xóa 2 bản ghi khiến 8 mẫu test set bị trượt retrieval |
| `mean_token_f1` | 1.0000 | 0.8030 | 1.0000 | F1 sụt giảm tương ứng khi thiếu thông tin trong ngữ cảnh |
| `judge_accuracy` | 100.0% | 80.0% | 100.0% | Trùng khớp với sự suy sụp của chỉ số retrieval |
| `mean_judge_score` | 5.00 | 4.20 | 5.00 | Điểm số đánh giá giảm rõ rệt khi dữ liệu bị nhiễu và đứt gãy |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Hiểu sâu về cơ chế vector search (cosine distance, HNSW indexing) trong ChromaDB.
2. Thấy rõ tác động trực tiếp của dữ liệu rác lên khả năng retrieval và sinh câu trả lời của RAG Agent.
3. Kỹ năng thiết kế hệ thống đánh giá RAG tự động (RAG Evaluation Framework).
---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Hoàng Duy Linh
**Ngày xác nhận:** 2026-08-06
