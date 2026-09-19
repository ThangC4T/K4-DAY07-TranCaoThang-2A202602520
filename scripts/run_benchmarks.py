import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.models import Document
from src.chunking import ChunkingStrategyComparator, compute_similarity, FixedSizeChunker, SentenceChunker, RecursiveChunker
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed
from main import load_documents_from_files

def main():
    print("=== 1. TEST 5 CẶP CÂU DỰ ĐOÁN COSINE SIMILARITY ===")
    pairs = [
        ("Quy định nộp đơn phúc khảo bài thi kết thúc học phần", "Thủ tục chấm phúc khảo và khiếu nại điểm thi môn học"),
        ("Sinh viên đăng ký học phần trong học kỳ chính", "Điều kiện xét cấp học bổng khuyến khích học tập"),
        ("Thời hạn mượn giáo trình và sách tham khảo tại thư viện", "Công thức nấu món phở bò truyền thống Hà Nội"),
        ("Nội quy lưu trú và giờ giới nghiêm tại ký túc xá", "Sinh viên về muộn sau 23h tại ký túc xá phải xuất trình giấy tờ"),
        ("Quy chế giảng viên chấm thi và nộp bảng điểm", "Thời hạn sinh viên nộp học phí học kỳ"),
    ]
    for i, (a, b) in enumerate(pairs, 1):
        sim = compute_similarity(_mock_embed(a), _mock_embed(b))
        print(f"Cặp {i}:")
        print(f"  A: {a}")
        print(f"  B: {b}")
        print(f"  Score: {sim:.4f}")

    print("\n=== 2. SO SÁNH CHUNKING STRATEGIES TRÊN TÀI LIỆU ĐẠI HỌC ===")
    sample_docs = [
        "data/university/course-registration.md",
        "data/university/scholarship-policy.md",
        "data/university/library-services.md",
    ]
    comparator = ChunkingStrategyComparator()
    for doc_path in sample_docs:
        text = Path(doc_path).read_text(encoding="utf-8")
        # remove frontmatter for chunking comparison
        if text.startswith("---"):
            text = text.split("---", 2)[-1].strip()
        comp = comparator.compare(text, chunk_size=200)
        print(f"\nTài liệu: {doc_path} (Độ dài: {len(text)} ký tự)")
        for strat, stats in comp.items():
            print(f"  - {strat}: count={stats['count']}, avg_length={stats['avg_length']:.1f}")

    print("\n=== 3. CHẠY 5 BENCHMARK QUERIES TRÊN VECTOR STORE ===")
    files = [
        "data/university/course-registration.md",
        "data/university/library-services.md",
        "data/university/scholarship-policy.md",
        "data/university/dormitory-regulations.md",
        "data/university/faculty-grade-submission.md",
        "data/university/exam-re-evaluation.md",
    ]
    docs = load_documents_from_files(files)
    store = EmbeddingStore(collection_name="uni_kb", embedding_fn=_mock_embed)
    store.add_documents(docs)

    queries = [
        {
            "id": 1,
            "query": "Sinh viên có thể đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong một học kỳ chính?",
            "gold": "Tối thiểu 14 tín chỉ và tối đa 24 tín chỉ (sinh viên bị cảnh báo học vụ tối đa 14 tín chỉ).",
            "filter": None,
        },
        {
            "id": 2,
            "query": "Tiêu chuẩn về điểm GPA và điểm rèn luyện để đạt học bổng Xuất sắc là bao nhiêu?",
            "gold": "GPA từ 9.0 trở lên (thang 10) hoặc từ 3.6 trở lên (thang 4), ĐRL từ 90 điểm trở lên.",
            "filter": None,
        },
        {
            "id": 3,
            "query": "Hạn nộp và xử lý điểm số kết thúc học phần đối với sinh viên là bao lâu?",
            "gold": "Sinh viên có 07 ngày làm việc để nộp đơn phúc khảo điểm (trong khi giảng viên có 10 ngày làm việc để nhập điểm). Lọc audience=student tránh lấy nhầm hạn nộp của giảng viên.",
            "filter": {"audience": "student"},
        },
        {
            "id": 4,
            "query": "Thời hạn nộp đơn phúc khảo và lệ phí phúc khảo một bài thi là bao nhiêu?",
            "gold": "Thời hạn 07 ngày làm việc kể từ ngày công bố điểm, lệ phí 50.000 VNĐ/bài thi.",
            "filter": None,
        },
        {
            "id": 5,
            "query": "Sinh viên đại học được mượn bao nhiêu cuốn sách giáo trình về nhà và trong bao lâu?",
            "gold": "Được mượn tối đa 5 cuốn giáo trình/sách tham khảo trong thời gian 14 ngày (gia hạn thêm 7 ngày).",
            "filter": None,
        },
    ]

    def simple_llm(prompt: str) -> str:
        # Simple extraction for demo
        for line in prompt.splitlines():
            if line.strip().startswith("-") or ("Context" not in line and "Question" not in line and "Based on" not in line and "Answer:" not in line and len(line.strip()) > 30):
                return line.strip()[:180]
        return "Trả lời tổng hợp từ ngữ cảnh truy xuất."

    agent = KnowledgeBaseAgent(store=store, llm_fn=simple_llm)

    for q in queries:
        print(f"\n--- Benchmark Query {q['id']} ---")
        print(f"Câu hỏi: {q['query']}")
        print(f"Filter: {q['filter']}")
        if q["filter"]:
            results = store.search_with_filter(q["query"], top_k=3, metadata_filter=q["filter"])
        else:
            results = store.search(q["query"], top_k=3)
        top1 = results[0] if results else None
        print(f"Top-1 Doc ID: {top1['id']} (Score: {top1['score']:.4f})")
        print(f"Top-1 Preview: {top1['content'][:120].replace(chr(10), ' ')}...")
        ans = agent.answer(q["query"], top_k=3)
        print(f"Agent Answer: {ans}")

if __name__ == "__main__":
    main()
