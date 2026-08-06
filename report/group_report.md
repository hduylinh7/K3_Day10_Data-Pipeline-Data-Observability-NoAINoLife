# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K3 - VinUni |
| Tên nhóm | NoAINoLife |
| Repository | https://github.com/hduylinh7/K3_Day10_Data-Pipeline-Data-Observability-NoAINoLife |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Lê Tiến Minh | 2A202601193 | Lead & Data Foundation Integrator | Ingestion (`src/ingestion/crossref.py`), Cleaning (`src/ingestion/cleaning.py`), Corruption (`src/ingestion/corruption.py`), Pipelines (`src/pipelines/`) |
| 2 | Hoàng Duy Linh | 2A202601159 | RAG & Evaluation Owner | Vector Store & Index (`src/retrieval/index.py`), RAG Agent (`src/retrieval/agent.py`), Test set builder (`src/evaluation/testset.py`), Metrics evaluator (`src/evaluation/metrics.py`) |
| 3 | Nguyễn Tuấn Anh | 2A202601395 | Data Observability & Reporting Owner | Quality checks & Freshness report (`src/observability/quality.py`), Comparative Markdown Report (`src/observability/reporting.py`), Report artifacts (`data/quality/`, `data/reports/`) |

---

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành 100% hai pha của bài lab bài bản và end-to-end:
1. **Pha 1 (Baseline)**: Ingestion thành công 24 bản ghi học thuật từ Crossref REST API, làm sạch dữ liệu, xây dựng Vector Database với ChromaDB và MiniLM embedding, tự động tạo bộ câu hỏi test set (40 mẫu) và đánh giá baseline đạt **100% Retrieval Hit Rate**, **1.0 Token F1** và **5.0/5.0 Judge Score**. Các cổng kiểm soát Data Quality và Freshness Monitoring đạt trạng thái `PASSED` và `FRESH`.
2. **Pha 2 (Corruption, Repair & Comparison)**: Giả lập 6 dạng lỗi dữ liệu thực tế (drop latest, summary rỗng, text nhiễu, tiêu đề truncated, stale date, trùng lặp). Kết quả đo lường ghi nhận chất lượng RAG sụt giảm rõ rệt (**Retrieval Hit Rate giảm từ 100% xuống 80%**, **Judge Accuracy giảm xuống 80%**, Data Quality chuyển sang `FAILED` và Freshness báo `STALE` 1 dòng). Pipeline đã tự động thực hiện **Repair** từ dữ liệu nguồn thô `data/raw/`, khôi phục thành công 100% các chỉ số retrieval và generation về mức baseline.

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response (crossref_response.json) / raw records (crossref_records.json)
    -> cleaning & data modeling (papers_clean.csv)
    -> MiniLM embedding + ChromaDB index (collection: papers-baseline)
    -> evaluation test set generation (test_set.json) & baseline evaluation
    -> quality & freshness checks (baseline_quality.json, freshness_report.json)
    -> controlled data corruption (papers_clean_corrupted.csv, corruption_log.json)
    -> re-index (papers-corrupted) & re-evaluate corrupted pipeline
    -> data repair from raw records (papers_clean_repaired.csv)
    -> re-index (papers-repaired) & re-evaluate repaired pipeline
    -> comparative observability report (corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref REST API (`/works`) | Fetch REST API, retry 429/503, parse JSON thành `PaperRecord` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Lê Tiến Minh |
| Cleaning | Raw `PaperRecord` objects | Làm sạch HTML, parse ngày, tính `age_days`, ghép `text_for_embedding`, khử trùng lặp | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Lê Tiến Minh |
| Embedding/Index | Cleaned DataFrame | MiniLM embeddings (`all-MiniLM-L6-v2`), ChromaDB persistent collection | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Hoàng Duy Linh |
| Evaluation | Cleaned DataFrame & Chroma index | Sinh 40 mẫu test set (`summary`, `authors`, `date`, `categories`), tính Hit Rate, F1, Judge Score | `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `baseline_answers.json` | Hoàng Duy Linh |
| Observability | Cleaned/Corrupted DataFrame | Kiểm tra completeness, uniqueness, summary length, age threshold, tổng hợp report Markdown | `data/quality/*.json`, `data/reports/phase1_report.md`, `corruption_report.md` | Nguyễn Tuấn Anh |
| Corruption/Repair | Clean DataFrame & Raw records | Tạo 6 dạng lỗi dữ liệu, log biến đổi; repair tự động tái nạp cleaning từ raw records | `data/clean/*_corrupted.csv`, `data/clean/*_repaired.csv`, `data/results/corruption_log.json` | Lê Tiến Minh |
| Orchestration | Settings & All modules | Điều phối thứ tự chạy baseline và corruption flow | `script/run_phase1.py`, `script/run_corruption_flow.py` | Lê Tiến Minh |

---

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` days |
| Heuristic Evaluator Fallback | Tự động kích hoạt khi chưa có API Key |

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline Pipeline (Pha 1):
```bash
python script/run_phase1.py
```

Corruption & Repair Flow (Pha 2):
```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công | 2026-08-06 10:24 | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 10:25 | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | `https://api.crossref.org/works` |
| Query/filter | `query=agentic retrieval augmented generation large language model`, `from-pub-date: 180 days, has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 10:15 UTC |
| Số record nhận được | 24 records |
| Cơ chế retry/backoff | Exponential backoff (max 3 retries) cho các mã HTTP 429 và 503 |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | String | Có | Mã DOI định danh bài báo | Bỏ qua nếu thiếu |
| `title` | String | Có | Tiêu đề bài báo | Bỏ qua nếu rỗng |
| `summary` | String | Có | Tóm tắt / Abstract bài báo | Bỏ qua nếu rỗng |
| `authors` | List[String] | Có | Danh sách tác giả | Gán `["Unknown Author"]` nếu rỗng |
| `categories` | List[String] | Có | Thể loại / Chủ đề | Gán `["General"]` nếu rỗng |
| `published` | String (YYYY-MM-DD) | Có | Ngày xuất bản | Mặc định ngày hiện tại nếu lỗi format |
| `age_days` | Integer | Có | Số ngày tuổi tính đến `run_date` | Tính bằng `(run_date - pub_date).days` |
| `text_for_embedding` | String | Có | Chuỗi văn bản hợp nhất để embed | Kết hợp Title, Authors, Published, Categories, Summary |

---

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 40 câu hỏi (10 bài báo x 4 dạng câu hỏi) |
| Các `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | Trực tiếp lấy từ `paper_id` của bản ghi trong cleaned dataset |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB persistent (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 |
| LLM provider/model | `gemini` / `gemini-2.5-flash` (với fallback Heuristic F1) |
| Test set dùng chung | `data/eval/test_set.json` |

*Giải thích*: Giữ nguyên bộ test set cố định xuyên suốt cả 3 trạng thái (Baseline, Corrupted, Repaired) là bắt buộc để đảm bảo tính công bằng và chính xác khi so sánh tác động trực tiếp của data corruption và hiệu quả phục hồi của repair flow.

---

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/crossref_response.json`, `crossref_records.json` | Có | Khả năng truy vết 100% |
| Cleaned dataset | `data/clean/papers_clean.csv`, `papers_clean.json` | Có | 24 bản ghi sạch |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` | Có | Collection `papers-baseline` |
| Evaluation set | `data/eval/test_set.json` | Có | 40 câu hỏi kiểm thử |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Metrics đầy đủ |
| Quality/freshness | `data/quality/baseline_quality.json`, `freshness_report.json` | Có | 100% PASSED & FRESH |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo Markdown Phase 1 |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | **100.0%** (1.0) | Top-4 retrieval luôn chứa đúng tài liệu chứa câu trả lời |
| `mean_token_f1` | **1.0000** | Câu trả lời của agent trùng khớp hoàn toàn với Ground Truth |
| `judge_accuracy` | **100.0%** (1.0) | Evaluator chấm 100% câu trả lời đạt yêu cầu |
| `mean_judge_score` | **5.00 / 5.0** | Điểm trung bình tuyệt đối |

---

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `min_row_count` | Completeness | > 0 | PASSED (24 rows) | `data/quality/baseline_quality.json` |
| `paper_id_not_null` | Completeness | 0 nulls | PASSED (0 nulls) | `data/quality/baseline_quality.json` |
| `paper_id_unique` | Uniqueness | 0 duplicates | PASSED (0 duplicates) | `data/quality/baseline_quality.json` |
| `title_not_null` | Completeness | 0 nulls | PASSED (0 nulls) | `data/quality/baseline_quality.json` |
| `summary_sufficient_length` | Validity | 0 short summaries | PASSED (0 short) | `data/quality/baseline_quality.json` |
| `freshness_threshold` | Timeliness | 0 rows > 180 days | PASSED (0 stale) | `data/quality/baseline_quality.json` |

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | Cleaned DataFrame `papers_clean.csv` |
| Timestamp mới nhất | `2026-08-05` |
| Ngưỡng freshness | `180` ngày |
| Trạng thái baseline | `FRESH` |
| Lý do | Tất cả các bài báo đều có ngày xuất bản trong khoảng 180 ngày gần đây |

---

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| Drop latest records | Xóa 2 bản ghi mới nhất | 2 records | `min_row_count` giảm | Retrieval hit rate giảm 20% | Nạp lại đầy đủ từ `data/raw/` |
| Blank summary | Xóa rỗng summary của bài báo | 1 record | `summary_sufficient_length` FAILED | Token F1 & Score giảm | Tái tạo lại summary từ raw JSON |
| Inject noise | Thêm văn bản nhiễu `CORRUPTED_NOISE_TEXT` | 1 record | Đảo lộn embedding vector | Score bị ảnh hưởng | Làm sạch lại từ raw records |
| Truncate title | Cắt tiêu đề bài báo còn 5 ký tự | 1 record | Exact lookup FAILED | Không tìm được bài báo | Phục hồi tiêu đề gốc từ raw |
| Stale date | Sửa ngày xuất bản về năm 2020 | 1 record | `freshness_threshold` STALE | Freshness report báo lỗi | Parse lại ngày gốc từ raw |
| Add duplicates | Nhân đôi bản ghi cuối | 1 record | `paper_id_unique` FAILED | Gây dư thừa trong vector store | Khử trùng lặp theo `paper_id` |

- **Corruption log path**: `data/results/corruption_log.json` (Có đầy đủ nhật ký tác động).
- **Giải thích Repair**: Quá trình repair tuyệt đối không sửa tay hay patch trên file kết quả. Repair thực hiện chạy lại quy trình ETL chuẩn hóa từ snapshot dữ liệu thô ban đầu `data/raw/crossref_records.json`, đảm bảo tính minh bạch và có thể kiểm tra lại.

---

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | -20.0% | +20.0% | Giảm rõ rệt khi mất record; khôi phục hoàn toàn sau repair |
| `mean_token_f1` | 1.0000 | 0.8030 | 1.0000 | -0.1970 | +0.1970 | Dữ liệu lỗi làm giảm chất lượng câu trả lời |
| `judge_accuracy` | 100.0% | 80.0% | 100.0% | -20.0% | +20.0% | Đánh giá suy giảm đúng tỷ lệ lỗi retrieval |
| `mean_judge_score` | 5.00 | 4.20 | 5.00 | -0.80 | +0.80 | Điểm đánh giá giảm từ 5.0 xuống 4.2 |
| Quality checks status | PASSED | FAILED | PASSED | Phát hiện 3 vi phạm quality | Đã khôi phục trạng thái PASSED |
| Freshness status | FRESH | STALE | FRESH | Phát hiện 1 dòng stale date | Đã khôi phục trạng thái FRESH |

### Hai kết luận quan trọng:
1. **Data Corruption → Quality Failure → Agent Degradation**: Khi dữ liệu bị xóa bớt bản ghi và sửa ngày/tóm tắt, cổng Data Quality ngay lập tức chuyển sang `FAILED` và `STALE`, kéo theo `retrieval_hit_rate` sụt giảm 20%.
2. **Automated Repair → Quality Recovery → Agent Recovery**: Khi kích hoạt luồng Repair tái nạp từ nguồn thô đáng tin cậy, toàn bộ tín hiệu Data Quality chuyển về `PASSED`, và các chỉ số RAG Agent khôi phục 100% về mức Baseline.

---

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy `python script/run_phase1.py` gặp lỗi `ModuleNotFoundError: No module named 'pipelines'`.
- **Nguyên nhân:** Môi trường Python chưa nhận diện được package trong thư mục `src/` nếu chỉ cài đặt `requirements.txt`.
- **Cách xử lý:** Thực hiện cài đặt project dưới dạng editable package bằng lệnh `python -m pip install -e .` (được cấu hình trong `pyproject.toml`).
- **Cách xác minh:** Chạy thành công `python script/run_phase1.py` mà không cần set thủ công `PYTHONPATH`.

---

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Số lượng bản ghi mẫu (24 records) | Quy mô corpus nhỏ | Mở rộng lấy 100+ bản ghi từ Crossref API |
| Heuristic Evaluator làm fallback | Chưa dùng hết sức mạnh LLM Judge khi offline | Cấu hình API Key cố định cho Gemini/OpenAI để chạy full LLM Judge |

---

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.

