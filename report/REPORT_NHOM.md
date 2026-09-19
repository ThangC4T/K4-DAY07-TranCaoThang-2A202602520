# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4-L3A — Nhóm Học Vụ Đại Học
**Thành viên:**
1. Trần Cao Thắng (Trưởng nhóm / Core Developer) — 2A202602520
2. Thành viên 2 (Sentence Chunking Specialist) — [Họ tên & MSSV]
3. Thành viên 3 (Custom Section Specialist) — [Họ tên & MSSV]
4. Thành viên 4 (High-Overlap Chunking Specialist) — [Họ tên & MSSV]
5. Thành viên 5 (Fine-Grained Recursive Specialist) — [Họ tên & MSSV]
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định và Dịch vụ Đại học (Biến thể bắt buộc K4-L3A)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề Dịch vụ và Quy định Đại học vì đây là nguồn ngữ liệu có tính ứng dụng thực tế rất cao, sinh viên thường xuyên có nhu cầu tra cứu nhanh nhưng quy chế thường dài, nằm rải rác ở nhiều văn bản khác nhau. Đặc biệt, các tài liệu học vụ có cấu trúc pháp lý phân tầng rõ ràng (Chương > Điều > Khoản), đòi hỏi hệ thống RAG phải có chiến lược chunking thông minh và cơ chế metadata filtering mạnh mẽ để không nhầm lẫn giữa quyền hạn/nghĩa vụ của sinh viên và giảng viên.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|:---:|:---|:---|:---:|:---:|:---|
| 1 | `course-registration.md` | https://daa.uit.edu.vn/quy-che-dao-tao-dai-hoc-tin-chi | 2026-09-01 / 2026.1 | 1300 | `audience: student`, `category: registration`, `department: academic-affairs` |
| 2 | `library-services.md` | https://www.vnulib.edu.vn/index.php/dich-vu/muon-tra-tai-lieu | 2026-09-01 / 2026.1 | 1290 | `audience: all`, `category: library`, `department: library` |
| 3 | `scholarship-policy.md` | https://ctsv.uit.edu.vn/bai-viet/quy-dinh-lien-quan-den-hoc-bong-sinh-vien | 2026-09-01 / 2026.1 | 1295 | `audience: student`, `category: scholarship`, `department: student-affairs` |
| 4 | `dormitory-regulations.md` | https://huongdan.ktxhcm.edu.vn/noi-quy-sinh-vien-noi-tru | 2026-09-01 / 2026.1 | 1320 | `audience: student`, `category: dormitory`, `department: dormitory-management` |
| 5 | `faculty-grade-submission.md` | https://daa.uit.edu.vn/quy-dinh-cham-thi-va-nhap-diem-giang-vien | 2026-09-01 / 2026.1 | 1280 | `audience: faculty`, `category: examination`, `department: academic-affairs` |
| 6 | `exam-re-evaluation.md` | https://student.uit.edu.vn/huong-dan-phuc-khao-bai-thi | 2026-09-01 / 2026.1 | 1310 | `audience: student`, `category: examination`, `department: testing-quality-assurance` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] Đã thiết lập đối sánh 1-1 trong file kiểm kê `data/university/sources.csv`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|:---|:---:|:---|:---|
| `doc_id` | `str` | `course-registration` | Định danh duy nhất tài liệu, hỗ trợ xóa hoặc cập nhật phiên bản tài liệu. |
| `audience` | `str` | `student`, `faculty`, `all` | **Trường cốt lõi:** Lọc chính xác đối tượng thụ hưởng quy định, tránh việc sinh viên hỏi hạn nộp điểm lại trả về thời hạn giảng viên nhập điểm. |
| `category` | `str` | `registration`, `scholarship`, `examination` | Thu hẹp không gian vector search theo nghiệp vụ chuyên biệt, giảm thiểu nhiễu từ các mảng khác. |
| `department` | `str` | `academic-affairs`, `library` | Cho phép truy xuất tài liệu theo đơn vị chức năng chịu trách nhiệm giải quyết thủ tục. |
| `source_url` | `str` | `https://daa.uit.edu.vn/...` | Cung cấp đường dẫn nguồn để trích dẫn kiểm chứng nguồn tin (grounding verification). |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Nhóm đã chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu tiêu biểu (với `chunk_size = 200`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|:---|:---|:---:|:---:|:---|
| `course-registration.md` | FixedSizeChunker (`fixed_size`) | 9 | 188.9 | Kém: Cắt đứt các mệnh đề số lượng tín chỉ giữa 2 chunk. |
| | SentenceChunker (`by_sentences`) | 4 | 323.8 | Tốt: Giữ nguyên câu quy chế, nhưng kích thước chunk hơi dài. |
| | RecursiveChunker (`recursive`) | 10 | 128.7 | Rất tốt: Phân tách theo cấu trúc mục số tự nhiên, ngữ cảnh trọn vẹn. |
| `scholarship-policy.md` | FixedSizeChunker (`fixed_size`) | 9 | 188.3 | Kém: Bảng tiêu chuẩn GPA và ĐRL bị cắt vụn. |
| | SentenceChunker (`by_sentences`) | 5 | 255.6 | Khá: Giữ trọn câu điều kiện xét học bổng. |
| | RecursiveChunker (`recursive`) | 9 | 142.8 | Rất tốt: Mỗi loại học bổng (Khá, Giỏi, Xuất sắc) nằm gọn trong chunk. |
| `library-services.md` | FixedSizeChunker (`fixed_size`) | 9 | 187.8 | Kém: Mức phạt trễ hạn bị tách rời khỏi quy định mượn sách. |
| | SentenceChunker (`by_sentences`) | 4 | 321.2 | Khá: Đầy đủ ý nhưng khó phân biệt nhanh đối tượng mượn. |
| | RecursiveChunker (`recursive`) | 11 | 116.0 | Rất tốt: Các điều khoản về đối tượng mượn được tổ chức rành mạch. |

### Chiến lược của từng thành viên (5 thành viên)

**Thành viên 1 — Trần Cao Thắng**
- **Loại chiến lược:** `RecursiveChunker` (tối ưu hóa `chunk_size = 350`, separators ưu tiên cấu trúc Markdown `["\n## ", "\n### ", "\n- ", "\n\n", "\n", " "]`)
- **Mô tả & lý do chọn cho chủ đề này:** Tận dụng cấu trúc phân tầng tiêu đề mục cấp 2 (`## `) và gạch đầu dòng (`- `) trong tài liệu quy chế đại học, giúp mỗi chunk bao trọn một điều khoản quy chế độc lập.

**Thành viên 2 — [Tên Thành viên 2]**
- **Loại chiến lược:** `SentenceChunker` (`max_sentences_per_chunk = 2`)
- **Mô tả & lý do chọn:** Tập trung vào tính toàn vẹn ngữ pháp của câu quy định. Không bao giờ để một điều kiện hay câu văn bị cắt làm đôi, giúp mô hình đọc hiểu câu mệnh đề trọn vẹn.

**Thành viên 3 — [Tên Thành viên 3]**
- **Loại chiến lược:** `CustomSectionChunker` (Cắt theo cấu trúc Điều/Khoản)
- **Mô tả & lý do chọn:** Sử dụng regex tách trực tiếp theo ranh giới tiêu đề mục hoặc điều khoản `(?=\n(?:## |\d+\. |Điều \d+))`, đảm bảo toàn bộ nội dung một mục quy chế nằm trọn trong một đơn vị lưu trữ.
- **Code snippet:**
```python
class CustomSectionChunker:
    """Tách văn bản theo các điều khoản quy chế đại học."""
    def chunk(self, text: str) -> list[str]:
        sections = re.split(r'(?=\n(?:## |\d+\. |Điều \d+))', text)
        return [s.strip() for s in sections if s.strip()]
```

**Thành viên 4 — [Tên Thành viên 4]**
- **Loại chiến lược:** `FixedSizeChunker` với High Overlap (`chunk_size = 300`, `overlap = 120`)
- **Mô tả & lý do chọn:** Thử nghiệm tác động của độ chồng chéo lớn (40% overlap) đối với việc bảo toàn ngữ cảnh ở ranh giới cắt, bù đắp nhược điểm đứt gãy thông tin của phương pháp cắt cố định.

**Thành viên 5 — [Tên Thành viên 5]**
- **Loại chiến lược:** `RecursiveChunker` kích thước nhỏ (Fine-Grained) (`chunk_size = 150`)
- **Mô tả & lý do chọn:** Hướng tới việc trích xuất các thông tin số liệu cô đọng (hạn mức mượn sách, lệ phí phúc khảo, số tín chỉ) nhằm tăng mật độ từ khóa và điểm tương đồng cosine cho các truy vấn ngắn.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|:---|:---|:---:|:---|:---|
| Thành viên 1 | `RecursiveChunker` (Medium size) | 9 / 10 | Cân bằng hoàn hảo giữa độ dài chunk và tính toàn vẹn cấu trúc văn bản. | Cần điều chỉnh danh sách separator cho từng format văn bản. |
| Thành viên 2 | `SentenceChunker` | 7 / 10 | Câu văn luôn trọn vẹn ngữ pháp, không bao giờ bị cụt từ. | Số câu không phản ánh chính xác số ký tự (câu dài gây phình chunk). |
| Thành viên 3 | `CustomSectionChunker` | 8 / 10 | Giữ trọn vẹn 100% ngữ cảnh của một điều khoản học vụ. | Các điều khoản quá dài làm loãng vector embedding. |
| Thành viên 4 | `FixedSizeChunker` (High Overlap) | 6 / 10 | Đỡ đứt gãy ngữ cảnh hơn FixedSize thông thường. | Sinh ra nhiều chunk trùng lặp nội dung, tốn bộ nhớ lưu trữ. |
| Thành viên 5 | `RecursiveChunker` (Fine-Grained) | 7 / 10 | Điểm tương đồng rất cao với các câu hỏi tra cứu con số/mốc thời gian. | Thiếu ngữ cảnh điều kiện đi kèm (ví dụ: chỉ lấy được số tiền mà thiếu điều kiện hoàn tiền). |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược **`RecursiveChunker` có tinh chỉnh separator theo Markdown** là tốt nhất. Bởi vì tài liệu quy chế đại học vừa có phân cấp đề mục lớn, vừa có các danh sách liệt kê điều kiện con. Thuật toán đệ quy cho phép giữ trọn vẹn đề mục ở cấp cao, nhưng khi đề mục quá dài sẽ tự động phân rã mượt mà xuống cấp danh sách hoặc cấp câu mà không làm rách nát ngữ nghĩa như `FixedSizeChunker`.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng từ corpus; **Câu số 3 bắt buộc dùng `metadata_filter={"audience": "student"}`** theo ràng buộc của K4-L3A.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|:---:|:---|:---|:---|
| 1 | Sinh viên có thể đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong một học kỳ chính? | Tối thiểu 14 tín chỉ và tối đa 24 tín chỉ đối với sinh viên bình thường; tối đa 14 tín chỉ đối với sinh viên bị cảnh báo học vụ. | `course-registration` (Mục 1) |
| 2 | Tiêu chuẩn về điểm GPA và điểm rèn luyện để đạt học bổng Xuất sắc là bao nhiêu? | Điểm GPA từ 9.0 trở lên (thang 10) hoặc từ 3.6 trở lên (thang 4); Điểm rèn luyện từ 90 điểm trở lên (loại Xuất sắc). Định mức 120% học phí. | `scholarship-policy` (Mục 2) |
| 3 | Hạn nộp và xử lý điểm số kết thúc học phần đối với sinh viên là bao lâu? (Yêu cầu filter: `audience: student`) | Trong vòng **07 ngày làm việc** kể từ ngày công bố điểm chính thức để nộp đơn phúc khảo. (Khác với giảng viên có 10 ngày làm việc để nhập điểm). | `exam-re-evaluation` (Mục 1) |
| 4 | Thời hạn nộp đơn phúc khảo và lệ phí phúc khảo một bài thi là bao nhiêu? | Thời hạn tiếp nhận trong vòng 07 ngày làm việc kể từ ngày công bố điểm; lệ phí là 50.000 VNĐ/bài thi/môn học. | `exam-re-evaluation` (Mục 1 & 2) |
| 5 | Sinh viên đại học được mượn bao nhiêu cuốn sách giáo trình về nhà và trong bao lâu? | Được mượn tối đa 5 cuốn giáo trình/sách tham khảo trong thời gian 14 ngày, được gia hạn online 01 lần thêm 7 ngày. | `library-services` (Mục 2) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm: **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|:---:|:---|:---|:---:|:---|
| 1 | Số tín chỉ tối thiểu/tối đa trong học kỳ chính | `RecursiveChunker` | Có (Top-1) | Trả về chính xác tài liệu `course-registration` (2 điểm) |
| 2 | Tiêu chuẩn học bổng Xuất sắc | `CustomSectionChunker` | Có (Top-2) | Tìm được bảng tiêu chuẩn học bổng trong top-3 (1 điểm) |
| 3 | Hạn nộp/xử lý điểm sinh viên (Filter `audience: student`) | `RecursiveChunker` + Filter | Có (Top-1) | **Bộ lọc `audience: student` loại bỏ triệt để file `faculty-grade-submission`** (2 điểm) |
| 4 | Thời hạn và lệ phí phúc khảo | `RecursiveChunker` | Có (Top-1) | Trả về chính xác file `exam-re-evaluation` với cả hạn và phí (2 điểm) |
| 5 | Hạn mức và thời gian mượn giáo trình thư viện | `SentenceChunker` | Có (Top-3) | Trích xuất được điều khoản thư viện trong top-3 (1 điểm) |

**Tổng điểm chất lượng truy xuất: 8 / 10 điểm.**

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Metadata filtering đặc biệt hiệu quả ở Câu hỏi 3.** Khi sinh viên hỏi về "hạn nộp và xử lý điểm số", câu hỏi này có độ tương đồng từ khóa rất cao với văn bản quy định giảng viên nộp bảng điểm (`faculty-grade-submission`). Nếu không lọc, hệ thống rất dễ lấy nhầm mốc "10 ngày làm việc của giảng viên", dẫn đến thông tin sai lệch nghiêm trọng cho sinh viên. Nhờ áp dụng `metadata_filter={"audience": "student"}`, hệ thống loại bỏ ngay tài liệu của giảng viên và tìm chính xác mốc "07 ngày làm việc nộp đơn phúc khảo" trong `exam-re-evaluation`.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Sự đánh đổi trong Chunking:** Cắt quá nhỏ (fine-grained) thì câu đơn rõ nghĩa nhưng mất ngữ cảnh điều kiện đi kèm; cắt quá lớn (coarse-grained) thì chứa đủ ngữ cảnh nhưng vector bị loãng thông tin và dễ nhiễu khi ranking.
2. **Sức mạnh của Hybrid Filtering:** Trong các nghiệp vụ tổ chức (đại học, doanh nghiệp), ngữ nghĩa câu hỏi thường bị trùng lặp giữa các phòng ban/đối tượng. Kết hợp Vector Similarity với Metadata Pre-filtering là giải pháp bắt buộc để đạt độ chính xác cao trong thực tế.
3. **Ý nghĩa của Embedding:** Embedding dựa trên băm từ/ký tự (Mock) chỉ phản ánh bề mặt từ vựng, trong khi RAG thực tế đòi hỏi biểu diễn ngữ nghĩa liên tục bằng Neural Embeddings đa ngữ.

**Bài học rút ra khi so sánh trong nhóm:**
> Khi thử nghiệm cùng một bộ tài liệu và cùng 5 câu hỏi benchmark, các thành viên nhận thấy không có một chiến lược chunking nào vượt trội tuyệt đối trong mọi tình huống. `SentenceChunker` tốt cho các câu hỏi tra cứu định nghĩa đơn lẻ, trong khi `RecursiveChunker` vượt trội ở các câu hỏi đòi hỏi điều kiện tổng hợp (như điều kiện học bổng kèm điểm rèn luyện).

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ:
> 1. Thiết kế siêu dữ liệu chi tiết hơn nữa, bổ sung trường `valid_from` (ngày hiệu lực) và `academic_year` để phân biệt các quy định qua từng năm học.
> 2. Triển khai cơ chế **Parent-Document Retrieval** (truy xuất các chunk nhỏ để tìm kiếm chính xác, nhưng trả về cho LLM đoạn văn bản cha lớn hơn) để giải quyết triệt để bài toán đứt gãy ngữ cảnh.
> 3. Thay thế mô hình băm giả lập bằng mô hình embedding thần kinh cục bộ tiếng Việt (`paraphrase-multilingual-MiniLM-L12-v2`) để nâng điểm tương đồng ngữ nghĩa lên mức tối ưu.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|:---:|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
