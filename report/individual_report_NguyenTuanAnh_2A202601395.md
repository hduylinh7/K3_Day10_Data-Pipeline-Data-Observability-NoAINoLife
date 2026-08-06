# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Tuấn Anh |
| MSSV | 2A202601395 |
| Khóa/Lớp | K3 - VinUni |
| Tên nhóm | NoAINoLife |
| Vai trò chính | Data Observability & Reporting Owner |
| Repository | https://github.com/hduylinh7/K3_Day10_Data-Pipeline-Data-Observability-NoAINoLife |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data Quality Checks | `src/observability/quality.py` (`run_data_quality_checks`) | DataFrame & Settings | `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json` | Hoàn thành |
| Freshness Monitoring | `src/observability/quality.py` (`build_freshness_report`) | DataFrame & Settings | `data/quality/freshness_report.json`, `*_freshness_report.json` | Hoàn thành |
| Comparative Markdown Reports | `src/observability/reporting.py` (`generate_phase1_report`, `generate_corruption_report`) | Metrics & Quality Dicts | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm tra chất lượng dữ liệu sạch | Lê Tiến Minh (Ingestion/Cleaning) | Xác nhận 24 bản ghi sạch đạt 100% tiêu chí Quality Gate trước khi embed |
| Đối chiếu số liệu đánh giá | Hoàng Duy Linh (RAG/Eval) | Tổng hợp chính xác số liệu sụt giảm retrieval vào báo cáo so sánh |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng Cổng Kiểm soát Chất lượng (Quality Gates) | `src/observability/quality.py` | Đánh giá 6 tiêu chuẩn quality checks (null, unique, length, count, freshness) | `data/quality/baseline_quality.json` |
| Theo dõi độ tươi mới (Freshness Monitoring) | `src/observability/quality.py` | Phát hiện 0 dòng stale ở baseline, 1 dòng stale ở corrupted | `data/quality/freshness_report.json` |
| Xuất Báo cáo Markdown Tự động | `src/observability/reporting.py` | Sinh báo cáo đối chiếu 3 trạng thái Baseline vs Corrupted vs Repaired | `data/reports/corruption_report.md` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng lớp giám sát dữ liệu (Data Observability), tự động kiểm tra tính toàn vẹn (completeness, uniqueness, validity, timeliness) của dữ liệu trước khi đưa vào RAG Agent, đồng thời tổng hợp các báo cáo so sánh (Markdown Reports) phục vụ công tác audit và chứng minh thực nghiệm.

### Cách triển khai
1. **Quality Checks**: Hàm `run_data_quality_checks` kiểm tra tổng số dòng (>0), tính rỗng của `paper_id` và `title`, tính trùng lặp của `paper_id`, độ dài summary (>=20 chars) và ngưỡng ngày xuất bản (`age_days` <= 180). Kết quả trả về cấu trúc JSON chứa trạng thái `PASSED`/`FAILED` từng quy tắc.
2. **Freshness Monitoring**: Hàm `build_freshness_report` trích xuất `latest_published`, `oldest_published`, đếm số lượng dòng vượt quá ngưỡng 180 ngày (`stale_rows`) và đánh giá cờ `is_fresh`.
3. **Reporting**: Hàm `generate_corruption_report` format dữ liệu thành bảng so sánh Markdown trực quan, tính toán tự động mức thay đổi (impact %) và mức phục hồi (recovery %) của từng chỉ số.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | DataFrames sạch / hỏng / phục hồi, dictionary kết quả metrics từ Evaluator |
| Output | File JSON kiểm tra quality/freshness (`data/quality/`), báo cáo Markdown (`data/reports/`) |
| Module phụ thuộc | `src/core/config.py`, `src/core/utils.py` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Xử lý an toàn khi DataFrame rỗng hoặc thiếu một số cột đặc thù |

### Cách xác minh

```bash
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tạo file `corrupted_quality.json` chứa thông tin vi phạm quality check và `corruption_report.md` chứa bảng đối chiếu.
- **Kết quả thực tế:** Báo cáo ghi nhận chính xác 3 vi phạm quality và 1 dòng stale date ở dữ liệu corrupted, và phục hồi hoàn toàn ở dữ liệu repaired.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Định nghĩa ngưỡng cảnh báo độ tươi mới (Freshness Threshold) phù hợp cho bài báo học thuật.
- **Các phương án đã cân nhắc:**
  1. *Phương án A*: Dùng mốc cố định tính từ ngày chạy pipeline (`age_days` <= 30 ngày).
  2. *Phương án B*: Thiết lập ngưỡng linh hoạt 180 ngày (`freshness_threshold_days = 180`) phù hợp với chu kỳ xuất bản của nghiên cứu khoa học.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Chu kỳ công bố bài báo học thuật thường mất nhiều tháng, ngưỡng 180 ngày giúp phản ánh chính xác các bài báo mới trong năm mà không gắn nhầm cờ stale cho tài liệu hợp lệ.

---
## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Báo cáo Markdown bị rỗng thông tin khi một số trường thông tin trong dict metrics bị khuyết.
- **Cách xử lý:** Sử dụng phương thức `.get(key, default_value)` sẵn có trong Python để đảm bảo mọi trường thông tin đều có giá trị mặc định an toàn.
- **Cách xác minh sau khi sửa:** Xuất báo cáo Markdown hoàn chỉnh ngay cả khi chưa chạy qua pass Ragas.

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
| Quality checks status | PASSED | FAILED | PASSED | Cổng kiểm soát lập tức báo FAILED khi dữ liệu bị sửa đổi |
| Freshness status | FRESH | STALE | FRESH | Báo động STALE khi ngày xuất bản bị đẩy về năm 2020 |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | Tương quan thuận 100% với tín hiệu Data Quality |
| `mean_token_f1` | 1.0000 | 0.8030 | 1.0000 | Phục hồi hoàn hảo sau khi Data Quality quay về PASSED |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Tầm quan trọng của lớp Data Observability trong việc bảo vệ tính đúng đắn cho các ứng dụng AI/LLM.
2. Cách xây dựng các quy tắc Data Quality Gates và Freshness Monitoring bài bản.
3. Kỹ năng tổng hợp và tự động hóa báo cáo phân tích số liệu (Automated Reporting).

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Nguyễn Tuấn Anh
**Ngày xác nhận:** 2026-08-06
