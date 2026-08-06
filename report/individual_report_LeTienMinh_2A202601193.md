# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Lê Tiến Minh |
| MSSV | 2A202601193 |
| Khóa/Lớp | K3 - VinUni |
| Tên nhóm | Nhóm 3 - Data Observability |
| Vai trò chính | Lead & Data Foundation Integrator |
| Repository | https://github.com/hduylinh7/K3_Day10_Data-Pipeline-Data-Observability-NoAINoLife |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw Ingestion | `src/ingestion/crossref.py` (`parse_crossref_payload`, `fetch_source_records`, `load_raw_records`) | Crossref REST API | `data/raw/crossref_response.json`, `crossref_records.json` | Hoàn thành |
| Cleaning & Data Modeling | `src/ingestion/cleaning.py` (`build_clean_dataframe`) | List `PaperRecord` objects | `data/clean/papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Data Corruption Simulation | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | Cleaned DataFrame | `data/clean/*_corrupted.csv`, `data/results/corruption_log.json` | Hoàn thành |
| Pipeline Orchestration | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Settings & All modules | `script/run_phase1.py`, `script/run_corruption_flow.py` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Tích hợp môi trường & Build Editable | Cả nhóm | Chạy `pip install -e .` giúp tự động resolve module paths |
| Handoff Clean DataFrame & Raw records | Hoàng Duy Linh (RAG/Eval) & Nguyễn Tuấn Anh (Observability) | Đảm bảo schema ổn định cho Vector Store và Quality Checkers |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Ingestion & Retry logic | `src/ingestion/crossref.py` | Ingest 24 records từ Crossref API, lưu raw JSON | `python script/run_phase1.py` |
| Cleaning & Helper text | `src/ingestion/cleaning.py` | Tạo `text_for_embedding`, `age_days`, khử trùng lặp | Kiểm tra `data/clean/papers_clean.csv` |
| Corruption Engine | `src/ingestion/corruption.py` | Tạo 6 loại lỗi dữ liệu & lưu nhật ký corruption log | Kiểm tra `data/results/corruption_log.json` |
| End-to-end Orchestration | `src/pipelines/phase1.py`, `corruption_flow.py` | Chạy tự động baseline & corruption flow | `python script/run_corruption_flow.py` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng nền tảng dữ liệu (Data Foundation) tin cậy, tự động lấy dữ liệu bài báo từ nguồn bên ngoài (Crossref), làm sạch HTML/văn bản rác, định hình schema thống nhất cho Embedding/Indexing, đồng thời xây dựng bộ công cụ giả lập lỗi dữ liệu (Data Corruption) và cơ chế tự phục hồi (Repair) từ bản ghi nguồn thô.

### Cách triển khai
1. **Ingestion**: Dùng `requests` gọi Crossref REST API `https://api.crossref.org/works` với query/filter, áp dụng exponential backoff cho mã status 429/503. Lưu dữ liệu thô dạng `dict` và `PaperRecord`.
2. **Cleaning**: Loại bỏ thẻ XML/HTML `<jats:p>`, chuẩn hóa khoảng trắng, parse ngày ISO `YYYY-MM-DD`, tính `age_days` so với `run_date`, tạo chuỗi ghép `text_for_embedding` chứa toàn bộ thông tin ngữ cảnh.
3. **Corruption**: Hàm `corrupt_clean_dataframe` thực hiện drop 2 bản ghi mới nhất, xóa rỗng summary (row 0), chèn nhiễu text (row 1), truncate title (row 2), sửa ngày về 2020 (row 3) và nhân đôi bản ghi cuối.
4. **Repair**: Tái thực thi hàm `build_clean_dataframe` trực tiếp trên danh sách bản ghi thô `data/raw/crossref_records.json` để đưa dữ liệu về trạng thái chuẩn ban đầu.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | External Crossref REST API / JSON Raw Snapshots |
| Output | Cleaned DataFrames (`papers_clean.csv`, `papers_clean_corrupted.csv`, `papers_clean_repaired.csv`) |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py` |
| Module sử dụng output | `src/retrieval/index.py`, `src/observability/quality.py`, `src/evaluation/testset.py` |
| Điều kiện lỗi cần xử lý | API rate limit (429/503), thiếu title/summary, lỗi format ngày xuất bản |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tự động tạo đầy đủ các file raw, clean, corrupted và repaired artifacts trong `data/`.
- **Kết quả thực tế:** Cả 2 script chạy thành công 100%, tạo đúng 24 bản ghi clean và 23 bản ghi corrupted.
- **Artifact/log:** `data/clean/papers_clean.csv`, `data/results/corruption_log.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án xử lý khi gặp lỗi mạng hoặc bị rate limit từ Crossref API.
- **Các phương án đã cân nhắc:**
  1. *Phương án A*: Báo lỗi trực tiếp và dừng pipeline.
  2. *Phương án B*: Tự động fallback nạp dữ liệu thô từ file snapshot JSON local (`data/raw/crossref_records.json`) khi đã có sẵn.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Đảm bảo pipeline có tính ổn định cao (resilience), có thể chạy offline phục vụ quá trình test/dev liên tục mà không bị nghẽn do mạng.
- **Bằng chứng quyết định phù hợp:** Pipeline có thể chạy lại tức thì mà không cần tốn thời gian chờ request HTTP.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'pipelines'` khi thực thi script.
- **Lệnh hoặc bước tái hiện:** `python script/run_phase1.py`
- **Nguyên nhân gốc:** Thư mục `src/` chưa được cài đặt vào PYTHONPATH của môi trường Python hiện tại.
- **Cách xử lý:** Cấu hình file `pyproject.toml` và chạy lệnh `python -m pip install -e .` để biến `src/` thành editable package.
- **Cách xác minh sau khi sửa:** Chạy `python script/run_phase1.py` thành công.
- **Điều học được:** Tầm quan trọng của việc đóng gói project đúng chuẩn Python packaging.

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
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | Việc xóa 2 bản ghi trực tiếp làm mất 20% khả năng retrieval |
| `mean_token_f1` | 1.0000 | 0.8030 | 1.0000 | Dữ liệu lỗi làm giảm chất lượng câu trả lời của agent |
| `judge_accuracy` | 100.0% | 80.0% | 100.0% | Điểm đánh giá giảm tương ứng với tỷ lệ mất thông tin |
| `mean_judge_score` | 5.00 | 4.20 | 5.00 | Giảm từ 5.0/5.0 xuống 4.2/5.0 |
| Quality checks | PASSED | FAILED | PASSED | Phát hiện vi phạm summary length và unique constraint |
| Freshness status | FRESH | STALE | FRESH | Phát hiện 1 bản ghi bị đẩy ngày về năm 2020 |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Dữ liệu đầu vào (Data Quality) quyết định trực tiếp đến hiệu năng của hệ thống RAG Agent ("Garbage in, garbage out").
2. Việc theo dõi dữ liệu (Data Observability) giúp phát hiện sớm vi phạm schema trước khi người dùng nhận câu trả lời sai.
3. Luồng tự động khôi phục (Repair) từ nguồn dữ liệu thô là thành phần cốt lõi của một Data Pipeline bền vững.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Tiến Minh
**Ngày xác nhận:** 2026-08-06

