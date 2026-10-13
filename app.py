import streamlit as st
from groq import Groq
import os

# ==================== CẤU HÌNH ====================
st.set_page_config(
    page_title="Trợ lý CSKH - Tư vấn Sản phẩm",
    page_icon="💬",
    layout="centered"
)

# Lấy API key từ Streamlit Secrets hoặc biến môi trường
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ Chưa cấu hình GROQ_API_KEY. Vui lòng thêm vào Secrets trên Streamlit Cloud.")
    st.stop()

client = Groq(api_key=api_key)

# ==================== LOAD KIẾN THỨC ====================
@st.cache_data
def load_knowledge():
    try:
        with open("knowledge.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
# KIẾN THỨC MẪU (HÃY THAY BẰNG DỮ LIỆU THẬT CỦA CÔNG TY)

## 1. Sản phẩm / Dịch vụ
- **Sản phẩm A**: Mô tả ngắn gọn, lợi ích chính, giá...
- **Sản phẩm B**: ...

## 2. Chương trình khuyến mại hiện tại
- KM 1: Điều kiện, thời hạn, cách áp dụng...
- KM 2: ...

## 3. Kịch bản tư vấn
### Khi khách hỏi về giá
- Bước 1: ...
- Bước 2: ...

### Khi khách phân vân
- ...

## 4. Quy trình chuyển lead sang phòng Kinh doanh
- Khi nào chuyển: ...
- Thông tin bắt buộc cần thu thập: Họ tên, SĐT, Nhu cầu, Sản phẩm quan tâm...
- Mẫu ghi chú chuyển lead: ...
"""

knowledge = load_knowledge()

# ==================== SYSTEM PROMPT ====================
SYSTEM_PROMPT = f"""Bạn là **Trợ lý Tư vấn nội bộ** của phòng Dịch vụ Khách hàng.

Nhiệm vụ của bạn:
1. Trả lời chính xác mọi câu hỏi về sản phẩm, dịch vụ, khuyến mại dựa trên kiến thức được cung cấp.
2. Đưa ra kịch bản tư vấn cụ thể, dễ áp dụng cho nhân viên CSKH.
3. Hướng dẫn cách tiếp nhận thông tin khách hàng và chuyển lead sang phòng Kinh doanh phù hợp.
4. Nếu không có thông tin trong kiến thức → trả lời rõ: "Hiện tại tôi chưa có thông tin này, bạn vui lòng hỏi lại quản lý hoặc cập nhật knowledge."

Quy tắc quan trọng:
- Chỉ trả lời dựa trên kiến thức bên dưới, tuyệt đối không bịa.
- Trả lời ngắn gọn, rõ ràng, dùng bullet point và bảng khi cần.
- Luôn ưu tiên hỗ trợ nhân viên nói chuyện với khách hàng hiệu quả.
- Khi cần chuyển lead, hãy liệt kê rõ thông tin cần thu thập và mẫu tin nhắn chuyển.

===== KIẾN THỨC =====
{knowledge}
===== HẾT KIẾN THỨC =====
"""

# ==================== GIAO DIỆN ====================
st.title("💬 Trợ lý CSKH - Tư vấn Sản phẩm & Dịch vụ")
st.caption("Dành cho nhân viên phòng Dịch vụ Khách hàng • Không cần đăng nhập • Chạy bằng Groq (miễn phí)")

# Sidebar
with st.sidebar:
    st.header("📌 Hướng dẫn sử dụng")
    st.markdown("""
    - Hỏi bất kỳ thông tin về sản phẩm, khuyến mại, kịch bản tư vấn...
    - Ví dụ:
      - "Kịch bản tư vấn sản phẩm A khi khách hỏi giá"
      - "Hiện đang có khuyến mại nào?"
      - "Cách chuyển lead sang phòng Kinh doanh"
    """)
    st.divider()
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("Phiên bản Groq Free • Quy mô nhỏ")

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập câu hỏi
if prompt := st.chat_input("Nhân viên CSKH hỏi gì đi..."):
    # Thêm câu hỏi của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gọi Groq
    with st.chat_message("assistant"):
        with st.spinner("Đang suy nghĩ..."):
            try:
                # Chuẩn bị messages cho Groq
                groq_messages = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ]
                for msg in st.session_state.messages:
                    groq_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",  # Model mạnh, chất lượng tốt trên free tier
                    messages=groq_messages,
                    temperature=0.3,
                    max_tokens=2048
                )

                answer = response.choices[0].message.content
                st.markdown(answer)

                # Lưu câu trả lời
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"Lỗi khi gọi Groq: {str(e)}")
