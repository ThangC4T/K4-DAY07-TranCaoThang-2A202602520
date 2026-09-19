# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Cao Thắng
**Mã sinh viên:** 2A202602520
**Nhóm:** Nhóm K4-L3A (Đại học & Quy định học vụ)
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) thể hiện hai vector embedding chỉ về cùng một hướng trong không gian nhiều chiều. Về mặt ngữ nghĩa, điều này chỉ ra rằng hai đoạn văn bản có chủ đề, ý nghĩa hoặc ngữ cảnh sử dụng tương đồng sâu sắc, bất kể độ dài ngắn của chúng có thể chênh lệch.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên nộp đơn xin phúc khảo bài thi kết thúc học phần tại cổng thông tin đào tạo."
- Câu B: "Thủ tục khiếu nại và chấm lại điểm thi môn học được thực hiện trên hệ thống học vụ trực tuyến."
- Tại sao tương đồng: Cả hai câu đều nói về cùng một nghiệp vụ (phúc khảo/khiếu nại điểm thi môn học) và phương thức thực hiện (online qua cổng thông tin trường), dù sử dụng các từ đồng nghĩa khác nhau ("phúc khảo" vs "chấm lại điểm", "nộp đơn" vs "thủ tục khiếu nại").

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Quy chế xét cấp học bổng khuyến khích học tập dựa trên điểm rèn luyện và GPA."
- Câu B: "Công thức nấu món phở bò truyền thống chuẩn vị Bắc với hoa hồi và quế chi."
- Tại sao khác: Hai câu thuộc hai miền kiến thức hoàn toàn độc lập và không liên quan ngữ cảnh (một bên là quy chế học vụ đại học, một bên là ẩm thực nấu ăn).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị chi phối mạnh bởi độ dài (độ lớn/magnitude) của vector, khiến hai văn bản có cùng nội dung nhưng khác biệt về số lượng từ (ví dụ: một tóm tắt ngắn và một bài phân tích dài) bị đẩy ra xa nhau. Trong khi đó, Cosine Similarity chỉ đo góc giữa hai vector (chuẩn hóa độ dài về mặt hình học), giúp nắm bắt đúng ý nghĩa ngữ nghĩa mà không bị sai lệch bởi độ dài đoạn văn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy giữa các chunk (step): `step = chunk_size - overlap = 500 - 50 = 450` ký tự.
> - Số lượng chunks: `ceil((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.111...) = 23`.
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Khi overlap = 100: `step = 500 - 100 = 400` ký tự. Số lượng chunks là `ceil((10000 - 100) / 400) = ceil(9900 / 400) = ceil(24.75) = 25` chunks (tăng thêm 2 chunks).
> - Muốn độ chồng chéo nhiều hơn nhằm đảm bảo tính liên tục của ngữ cảnh tại ranh giới giữa các chunk, tránh việc một điều khoản quy chế, một thực thể hoặc một câu mệnh đề bị cắt đứt giữa chừng, giúp retriever tìm đúng và agent hiểu trọn vẹn thông tin.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng regex `re.split(r'(?<=[.!?])\s+', text.strip())` có kỹ thuật positive lookbehind để nhận diện dấu chấm, dấu chấm than, dấu hỏi chấm kèm khoảng trắng hoặc xuống dòng làm ranh giới câu mà không làm mất dấu câu gốc. Xử lý các edge cases như văn bản rỗng, khoảng trắng thừa ở đầu/cuối câu và gom các câu thành các khối có tối đa `max_sentences_per_chunk` câu bằng vòng lặp bước nhảy (step-slicing).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo cơ chế đệ quy chia để trị với danh sách các dấu phân cách ưu tiên giảm dần: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), ký tự (`""`). Trường hợp cơ sở (base case) là khi văn bản ngắn hơn hoặc bằng `chunk_size` thì giữ nguyên, hoặc khi không còn separator nào thì cắt cưỡng bức theo kích thước cố định; ở mỗi bước, text được tách theo separator hiện tại, các đoạn con vượt kích thước tiếp tục được đệ quy, sau đó ghép nối các đoạn hợp lệ lại sao cho tổng chiều dài mỗi chunk không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với mỗi document nạp vào, phương thức `_make_record` chuẩn hóa bản ghi gồm `id`, `content`, `metadata` (tự động bổ sung `doc_id` nếu thiếu) và sinh vector nhúng thông qua `self._embedding_fn`. Trong `search`, query được nhúng thành vector truy vấn, sau đó tính tích vô hướng (dot-product) với từng vector đã lưu trữ qua `_dot`, sắp xếp danh sách kết quả theo điểm `score` giảm dần và trích xuất `top_k` bản ghi phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Trong `search_with_filter`, tôi áp dụng chiến lược **Pre-filtering (Lọc trước)**: duyệt danh sách tài liệu và chỉ giữ lại các record thỏa mãn tất cả các cặp khóa - giá trị trong `metadata_filter` rồi mới tính điểm tương đồng trên tập ứng viên này, giúp tăng tốc độ và đảm bảo kết quả 100% khớp điều kiện lọc. Với `delete_document`, phương thức duyệt và loại bỏ tất cả các record có `id` hoặc `metadata['doc_id']` khớp với mã cần xóa, sau đó so sánh kích thước trước và sau để trả về `True/False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Phương thức `answer` thực hiện đúng chu trình RAG: đầu tiên gọi `self.store.search(question, top_k)` để truy xuất các đoạn ngữ cảnh liên quan nhất từ vector store. Sau đó, ngữ cảnh được đánh số thứ tự (`Context 1`, `Context 2`...) và tiêm vào template prompt kèm câu hỏi gốc, cuối cùng ủy quyền cho hàm `self.llm_fn(prompt)` để mô hình ngôn ngữ sinh câu trả lời căn cứ trên thông tin đã cấp (grounding).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
test_chunker_classes_exist (tests.test_solution.TestClassBasedInterfaces.test_chunker_classes_exist) ... ok
test_mock_embedder_exists (tests.test_solution.TestClassBasedInterfaces.test_mock_embedder_exists) ... ok
test_counts_are_positive (tests.test_solution.TestCompareChunkingStrategies.test_counts_are_positive) ... ok
test_each_strategy_has_count_and_avg_length (tests.test_solution.TestCompareChunkingStrategies.test_each_strategy_has_count_and_avg_length) ... ok
test_returns_three_strategies (tests.test_solution.TestCompareChunkingStrategies.test_returns_three_strategies) ... ok
test_identical_vectors_return_1 (tests.test_solution.TestComputeSimilarity.test_identical_vectors_return_1) ... ok
test_opposite_vectors_return_minus_1 (tests.test_solution.TestComputeSimilarity.test_opposite_vectors_return_minus_1) ... ok
test_orthogonal_vectors_return_0 (tests.test_solution.TestComputeSimilarity.test_orthogonal_vectors_return_0) ... ok
test_zero_vector_returns_0 (tests.test_solution.TestComputeSimilarity.test_zero_vector_returns_0) ... ok
test_add_documents_increases_size (tests.test_solution.TestEmbeddingStore.test_add_documents_increases_size) ... ok
test_add_more_increases_further (tests.test_solution.TestEmbeddingStore.test_add_more_increases_further) ... ok
test_initial_size_is_zero (tests.test_solution.TestEmbeddingStore.test_initial_size_is_zero) ... ok
test_search_results_have_content_key (tests.test_solution.TestEmbeddingStore.test_search_results_have_content_key) ... ok
test_search_results_have_score_key (tests.test_solution.TestEmbeddingStore.test_search_results_have_score_key) ... ok
test_search_results_sorted_by_score_descending (tests.test_solution.TestEmbeddingStore.test_search_results_sorted_by_score_descending) ... ok
test_search_returns_at_most_top_k (tests.test_solution.TestEmbeddingStore.test_search_returns_at_most_top_k) ... ok
test_search_returns_list (tests.test_solution.TestEmbeddingStore.test_search_returns_list) ... ok
test_delete_reduces_collection_size (tests.test_solution.TestEmbeddingStoreDeleteDocument.test_delete_reduces_collection_size) ... ok
test_delete_returns_false_for_nonexistent_doc (tests.test_solution.TestEmbeddingStoreDeleteDocument.test_delete_returns_false_for_nonexistent_doc) ... ok
test_delete_returns_true_for_existing_doc (tests.test_solution.TestEmbeddingStoreDeleteDocument.test_delete_returns_true_for_existing_doc) ... ok
test_filter_by_department (tests.test_solution.TestEmbeddingStoreSearchWithFilter.test_filter_by_department) ... ok
test_no_filter_returns_all_candidates (tests.test_solution.TestEmbeddingStoreSearchWithFilter.test_no_filter_returns_all_candidates) ... ok
test_returns_at_most_top_k (tests.test_solution.TestEmbeddingStoreSearchWithFilter.test_returns_at_most_top_k) ... ok
test_chunks_respect_size (tests.test_solution.TestFixedSizeChunker.test_chunks_respect_size) ... ok
test_correct_number_of_chunks_no_overlap (tests.test_solution.TestFixedSizeChunker.test_correct_number_of_chunks_no_overlap) ... ok
test_empty_text_returns_empty_list (tests.test_solution.TestFixedSizeChunker.test_empty_text_returns_empty_list) ... ok
test_no_overlap_no_shared_content (tests.test_solution.TestFixedSizeChunker.test_no_overlap_no_shared_content) ... ok
test_overlap_creates_shared_content (tests.test_solution.TestFixedSizeChunker.test_overlap_creates_shared_content) ... ok
test_returns_list (tests.test_solution.TestFixedSizeChunker.test_returns_list) ... ok
test_single_chunk_if_text_shorter (tests.test_solution.TestFixedSizeChunker.test_single_chunk_if_text_shorter) ... ok
test_answer_non_empty (tests.test_solution.TestKnowledgeBaseAgent.test_answer_non_empty) ... ok
test_answer_returns_string (tests.test_solution.TestKnowledgeBaseAgent.test_answer_returns_string) ... ok
test_root_main_entrypoint_exists (tests.test_solution.TestProjectStructure.test_root_main_entrypoint_exists) ... ok
test_src_package_exists (tests.test_solution.TestProjectStructure.test_src_package_exists) ... ok
test_chunks_within_size_when_possible (tests.test_solution.TestRecursiveChunker.test_chunks_within_size_when_possible) ... ok
test_empty_separators_falls_back_gracefully (tests.test_solution.TestRecursiveChunker.test_empty_separators_falls_back_gracefully) ... ok
test_handles_double_newline_separator (tests.test_solution.TestRecursiveChunker.test_handles_double_newline_separator) ... ok
test_returns_list (tests.test_solution.TestRecursiveChunker.test_returns_list) ... ok
test_chunks_are_strings (tests.test_solution.TestSentenceChunker.test_chunks_are_strings) ... ok
test_respects_max_sentences (tests.test_solution.TestSentenceChunker.test_respects_max_sentences) ... ok
test_returns_list (tests.test_solution.TestSentenceChunker.test_returns_list) ... ok
test_single_sentence_max_gives_many_chunks (tests.test_solution.TestSentenceChunker.test_single_sentence_max_gives_many_chunks) ... ok

----------------------------------------------------------------------
Ran 42 tests in 0.016s

OK
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|:---:|:---|:---|:---:|:---:|:---:|
| 1 | Quy định nộp đơn phúc khảo bài thi kết thúc học phần | Thủ tục chấm phúc khảo và khiếu nại điểm thi môn học | cao | 0.0743 | Sai (khi dùng MockEmbedder) |
| 2 | Sinh viên đăng ký học phần trong học kỳ chính | Điều kiện xét cấp học bổng khuyến khích học tập | thấp | 0.0246 | Đúng |
| 3 | Thời hạn mượn giáo trình và sách tham khảo tại thư viện | Công thức nấu món phở bò truyền thống Hà Nội | thấp | -0.1807 | Đúng |
| 4 | Nội quy lưu trú và giờ giới nghiêm tại ký túc xá | Sinh viên về muộn sau 23h tại ký túc xá phải xuất trình giấy tờ | cao | -0.0379 | Sai (khi dùng MockEmbedder) |
| 5 | Quy chế giảng viên chấm thi và nộp bảng điểm | Thời hạn sinh viên nộp học phí học kỳ | thấp | 0.0579 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là ở cặp 4: hai câu có quan hệ nhân quả và cùng ngữ cảnh hẹp rất rõ ràng về nội quy KTX nhưng điểm tương đồng thực tế lại bị âm (-0.0379). Điều này phơi bày đặc tính của `MockEmbedder`: nó hoạt động dựa trên hàm băm MD5 ký tự giả lập ngẫu nhiên (hash collision / pseudorandom), hoàn toàn không hiểu ngữ nghĩa từ vựng (semantic understanding). Để biểu diễn được ý nghĩa thực sự của văn bản trong RAG production, ta bắt buộc phải dùng các mô hình ngôn ngữ nhúng sâu (Neural Embedding Models như MiniLM đa ngữ, OpenAI hoặc Gemini) vốn được huấn luyện trên không gian ngữ nghĩa liên tục.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|:---:|:---|:---|:---:|:---:|:---|
| 1 | Sinh viên có thể đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong một học kỳ chính? | `# Quy định đăng ký học phần và điều chỉnh kế hoạch học tập ... Tối thiểu 14 tín chỉ, tối đa 24 tín chỉ` | 0.0918 | Có | Sinh viên học lực bình thường đăng ký từ 14 đến 24 tín chỉ. |
| 2 | Tiêu chuẩn về điểm GPA và điểm rèn luyện để đạt học bổng Xuất sắc là bao nhiêu? | `# Nội quy lưu trú và quy định sinh hoạt ký túc xá ... Ưu tiên sinh viên diện chính sách...` (Nhiễu do mock) | 0.2560 | Không (ở Top-1, nhưng Top-2 có `scholarship-policy`) | Trả lời sai do Top-1 nhầm sang nội quy KTX. |
| 3 | Hạn nộp và xử lý điểm số kết thúc học phần đối với sinh viên là bao lâu? (Filter `audience: student`) | `# Hướng dẫn quy trình nộp đơn phúc khảo ... Thời hạn tiếp nhận đơn trong vòng 07 ngày làm việc` | 0.1646 | Có (nhờ bộ lọc `audience: student` loại bỏ quy chế giảng viên) | Sinh viên có 07 ngày làm việc để nộp đơn phúc khảo. |
| 4 | Thời hạn nộp đơn phúc khảo và lệ phí phúc khảo một bài thi là bao nhiêu? | `# Hướng dẫn quy trình nộp đơn phúc khảo ... Thời hạn 07 ngày làm việc, lệ phí 50.000 VNĐ/môn` | 0.1576 | Có | Thời hạn 07 ngày làm việc, lệ phí 50.000 VNĐ/bài thi. |
| 5 | Sinh viên đại học được mượn bao nhiêu cuốn sách giáo trình về nhà và trong bao lâu? | `# Quy định đăng ký học phần...` (Nhiễu do mock embedding) | 0.1668 | Không (Top-1 trúng ĐKHP, Top-3 mới có Thư viện) | Chưa lấy được đúng điều khoản thư viện ở Top-1. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5** câu hỏi có chứa chunk liên quan trong Top-3.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng trong văn bản quy phạm học vụ có tính phân tầng cao, việc cắt văn bản theo độ dài cố định hoặc hàm băm từ khóa thường dẫn đến thất bại khi đối chiếu ngữ nghĩa. Tuy nhiên, việc bổ sung siêu dữ liệu (Metadata Schema) chặt chẽ và áp dụng **Metadata Pre-filtering** (đặc biệt là lọc đối tượng `audience: student`) đã cứu vãn được độ chính xác của hệ thống RAG, ngăn chặn triệt để việc nhầm lẫn giữa quy định của sinh viên và quy chế nội bộ dành cho giảng viên.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|:---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
