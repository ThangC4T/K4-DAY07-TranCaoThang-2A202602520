import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.models import Document
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed
from main import load_documents_from_files, SAMPLE_FILES

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass


def get_llm_function():
    """Tự động phát hiện Gemini API Key hoặc OpenAI API Key, nếu không có thì dùng Smart Extractive LLM."""
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            print("✨ Đã kích hoạt mô hình AI thật: Google Gemini!")
            def gemini_llm(prompt: str) -> str:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                )
                return response.text.strip()
            return gemini_llm
        except Exception as e:
            print(f"⚠️ Không thể kết nối Gemini ({e}), chuyển về chế độ trích xuất nội bộ.")

    # Fallback: Trích xuất thông minh từ nội dung ngữ cảnh
    def smart_extractive_llm(prompt: str) -> str:
        # Tách lấy phần ngữ cảnh
        if "Question:" in prompt:
            parts = prompt.split("Question:")
            context_part = parts[0]
            question_part = parts[1].split("Answer:")[0].strip()
        else:
            context_part = prompt
            question_part = ""

        # Lọc các đoạn nội dung thực tế (bỏ các dòng header template)
        lines = [line.strip() for line in context_part.splitlines() if line.strip()]
        meaningful_lines = []
        for line in lines:
            if line.startswith("Context ") or line.startswith("Based on"):
                continue
            if len(line) > 15:
                meaningful_lines.append(line)

        if not meaningful_lines:
            return "Tôi không tìm thấy thông tin phù hợp trong cơ sở tri thức để trả lời câu hỏi này."

        # Ghép các điều khoản quan trọng nhất
        top_content = "\n".join(meaningful_lines[:4])
        return (
            f"Dựa trên quy chế và tài liệu học vụ tra cứu được:\n\n"
            f"{top_content}\n\n"
            f"💡 (Mẹo: Bạn có thể thêm GEMINI_API_KEY vào file .env để trợ lý trả lời mượt mà tự nhiên như ChatGPT!)"
        )

    return smart_extractive_llm


def main():
    print("=" * 60)
    print("🎓 TRỢ LÝ ẢO TƯ VẤN QUY ĐỊNH & DỊCH VỤ ĐẠI HỌC (RAG CHATBOT)")
    print("=" * 60)
    print("Đang nạp cơ sở tri thức từ data/university/ ...")
    
    docs = load_documents_from_files(SAMPLE_FILES)
    store = EmbeddingStore(collection_name="chat_store", embedding_fn=_mock_embed)
    store.add_documents(docs)
    
    llm_fn = get_llm_function()
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)
    
    print(f"✅ Đã nạp thành công {store.get_collection_size()} tài liệu.")
    print("Bạn có thể đặt câu hỏi về: Đăng ký tín chỉ, Học bổng, Thư viện, Ký túc xá, Phúc khảo...")
    print("Gõ 'exit' hoặc 'quit' để kết thúc cuộc trò chuyện.\n")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "thoat", "q"}:
                print("\n👋 Tạm biệt bạn! Chúc bạn học tập tốt!")
                break

            print("\n🤖 Trợ lý đang tra cứu dữ liệu...")
            # Kiểm tra xem câu hỏi có hướng tới sinh viên không để ưu tiên
            results = store.search(user_input, top_k=2)
            if results:
                best = results[0]
                print(f"📄 Nguồn tham chiếu: {best['metadata'].get('source', best['id'])} (Điểm tin cậy: {best['score']:.3f})")
            
            answer = agent.answer(user_input, top_k=2)
            print(f"\n💬 Trợ lý AI:\n{answer}\n")
            print("-" * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Đã dừng chat.")
            break
        except Exception as e:
            print(f"\n❌ Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()
