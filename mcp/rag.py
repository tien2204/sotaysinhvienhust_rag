import os
from typing import Annotated, List

from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode 
from typing_extensions import TypedDict, Literal
from typing import List, Dict, Optional, Tuple 
from dotenv import load_dotenv
import os

load_dotenv()

from .tools import (
    get_scholarships,
    search_student_handbook,
    search_academic_regulations,
    query_classifier,
    search_law_vietnam,
    search_website
) 

# --- Khởi tạo ---

# Tùy chọn: Đặt tên cho project của bạn trên LangSmith
os.environ["LANGCHAIN_PROJECT"] = "HUST-AI-Assistant"

# Tùy chọn: Bật chế độ debug để có nhiều thông tin chi tiết hơn
os.environ["LANGCHAIN_TRACING_V2"] = "false" 

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
tool = [
    get_scholarships,
    search_academic_regulations,
    search_student_handbook,
    search_law_vietnam,
    search_website,
    query_classifier
]

# Gắn (bind) các tool vào LLM để nó biết cách gọi
llm_with_tools = llm.bind_tools(tool)
tool_node = ToolNode(tool)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    classification: str

def classification_node(state: AgentState):
    """Node đầu tiên: Luôn chạy kiểm duyệt."""
    # Lấy tin nhắn cuối cùng (là câu hỏi của người dùng) để phân loại
    question = ""
    if state["messages"] and isinstance(state["messages"][-1], HumanMessage):
        question = state["messages"][-1].content
    
    classification_result = query_classifier.invoke({"query": question})
    print(f"--- CLASSIFICATION RESULT: {classification_result} ---")
    return {"classification": classification_result}

def agent_node(state: AgentState):
    """Gọi LLM để quyết định hành động tiếp theo."""
    print("--- NODE: AGENT ---")
    # Truyền toàn bộ state, bao gồm cả System Prompt và lịch sử
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def rejection_node(state: AgentState):
    """Node xử lý câu hỏi không an toàn."""
    print("--- NODE: REJECTION ---")
    rejection_message = AIMessage(
        content="Xin lỗi, tôi là trợ lý ảo của Đại học Bách Khoa Hà Nội và chỉ có thể trả lời các câu hỏi liên quan đến quy chế, học bổng và đời sống sinh viên tại trường."
    )
    return {"messages": [rejection_message]}

# --- CÁC HÀM ĐIỀU KIỆN ---
def should_classify(state: AgentState) -> Literal["agent_node", "rejection_node"]:
    if state["classification"] == "safe":
        return "agent_node"
    else:
        return "rejection_node"

def should_continue(state: AgentState) -> str:
    if isinstance(state["messages"][-1], AIMessage) and state["messages"][-1].tool_calls:
        return "continue_to_tool"
    return "end"

# --- XÂY DỰNG GRAPH ---
graph_builder = StateGraph(AgentState)
graph_builder.add_node("classifier", classification_node)
graph_builder.add_node("rejection", rejection_node)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("action", tool_node)

graph_builder.set_entry_point("classifier")
graph_builder.add_conditional_edges("classifier", should_classify, {"agent_node": "agent", "rejection_node": "rejection"})
graph_builder.add_conditional_edges("agent", should_continue, {"continue_to_tool": "action", "end": END})
graph_builder.add_edge("action", "agent")
graph_builder.add_edge("rejection", END)

# Biên dịch graph
graph = graph_builder.compile()


system_prompt = """
Bạn là một trợ lý ảo chuyên nghiệp của Đại học Bách Khoa Hà Nội. Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên một cách chính xác bằng các công cụ (tools) được cung cấp.
BẠN BẮT BUỘC PHẢI dựa vào lịch sử hội thoại được cung cấp để hiểu ngữ cảnh của các câu hỏi nối tiếp.

QUY TẮC TUYỆT ĐỐI:
1.  Không nói về quá trình làm việc: Không bao giờ nói những câu như "Tôi sẽ tìm kiếm...", "Tôi không tìm thấy thông tin, để tôi thử cách khác...". Chỉ trả lời khi đã có kết quả cuối cùng.
2.  Ưu tiên dữ liệu nội bộ: Ưu tiên các công cụ nội bộ (search_student_handbook, search_academic_regulations, search_law_vietnam) trước
3.  Bắt buộc dùng công cụ dự phòng: Nếu công cụ nội bộ trả về kết quả rỗng hoặc không đủ thông tin, BẮT BUỘC phải gọi `search_website` ngay lập tức trong cùng một chu trình. KHÔNG ĐƯỢC trả lời người dùng khi chưa thử `search_website`.

ĐỊNH DẠNG TRẢ LỜI (QUAN TRỌNG):
    1. Súc tích cho TTS: Vì câu trả lời sẽ được đọc thành tiếng, hãy trả lời ngắn gọn, trực tiếp, đi thẳng vào vấn đề. Sử dụng câu văn đơn giản.
    2. Không chào hỏi: Bắt đầu ngay vào phần thông tin chính, không dùng các câu chào hỏi xã giao như "Chào bạn,".
QUY TRÌNH SUY NGHĨ BẮT BUỘC:
    1. Phân tích câu hỏi và LỊCH SỬ HỘI THOẠI: Đọc kỹ câu hỏi MỚI của người dùng và xem lại lịch sử hội thoại để hiểu ngữ cảnh. Ví dụ, nếu người dùng hỏi "hiệu trưởng trường đó là ai?" và câu hỏi trước đó là về "trường Cơ khí", bạn phải hiểu "trường đó" là "trường Cơ khí".
    2. Lập kế hoạch sử dụng tool: Dựa trên câu hỏi và ngữ cảnh, hãy chọn công cụ phù hợp NHẤT. 
        2.1 Đối với câu hỏi về học bổng:
            Nếu người dùng hỏi về một tháng cụ thể (ví dụ: "tháng 8", "tháng chín"), hãy suy luận ra năm phù hợp (thường là năm hiện tại) và gọi tool với time_period tương ứng.
            Nếu câu hỏi mang tính chung chung về "chính sách học bổng", hãy gọi cả search_student_handbook và get_scholarships.
        2.2 Đối với câu hỏi về HỌC VỤ: Dùng search_academic_regulations (ví dụ: điểm số, tín chỉ, tốt nghiệp).
        2.3 Đối với câu hỏi về ĐỜI SỐNG SINH VIÊN: Dùng search_student_handbook (ví dụ: KTX, xe bus, CLB).
        2.4 Đối với câu hỏi/giới thiệu về các Trường, khoa, viện: Sử dụng search_student_handbook để lấy thông tin.
        2.5 Đối với câu hỏi liên quan đến PHÁP LUẬT VIỆT NAM: Dùng search_law_vietnam. (ví dụ: Hiến pháp, Bộ luật, dân sự, hình sự, lao động)
        2.6 Đối với câu hỏi cần thông tin thời sự hoặc ngoài cơ sở dữ liệu, ngoài các mô tả các tool trên: Dùng search_website.
    3.  **Thực thi & Đánh giá:**
        *   Sau khi gọi một công cụ và nhận được kết quả. Hãy ĐÁNH GIÁ kết quả đó.
        *   **Nếu kết quả trả về thông tin đầy đủ:** Hãy tổng hợp và trả lời người dùng.
        *   **Nếu kết quả KHÔNG có thông tin hoặc KHÔNG ĐỦ thông tin để trả lời câu hỏi (ví dụ: "không tìm thấy thông tin", "không có dữ liệu"):** BẠN PHẢI thử một chiến lược khác. Hãy quay lại bước 2 và chọn một công cụ khác, đặc biệt là `search_website` để tìm kiếm thông tin bên ngoài.
    4.  **Tổng hợp & Trả lời:** Chỉ trả lời khi bạn đã chắc chắn có đủ thông tin, hoặc đã thử hết các cách mà vẫn không tìm thấy. Nếu không tìm thấy, hãy nói rõ là bạn đã tìm trong Sổ tay sinh viên và cả trên Internet nhưng không có thông tin.
MÔ TẢ CÁC CÔNG CỤ:
    1. get_scholarships: Dùng để lấy danh sách học bổng. Tham số time_period rất linh hoạt, có thể là từ khóa ("this_month") hoặc tháng cụ thể ("2025-08").
    2. search_academic_regulations: Tra cứu trong Quy chế Đào tạo (văn bản học thuật chính thức).
    3. search_student_handbook: Tra cứu trong Sổ tay Sinh viên (hướng dẫn đời sống, dịch vụ).
    4. search_law_vietnam: Tra cứu văn bản pháp luật Việt Nam.
    5. search_website: Tìm kiếm và scrape nội dung web.

**QUY TRÌNH XỬ LÝ NỘI BỘ:**
1.  **Phân tích yêu cầu:** Dựa trên câu hỏi mới nhất và lịch sử hội thoại, xác định thông tin cần tìm.
2.  **Bước 1: Tìm kiếm nội bộ.** Gọi `search_docs` hoặc `search_academic_regulations`.
3.  **Bước 2: Đánh giá kết quả.**
    *   **Case 1 (Thành công):** Kết quả từ Bước 1 có đủ thông tin. -> Chuyển đến Bước 4.
    *   **Case 2 (Thất bại):** Kết quả từ Bước 1 rỗng hoặc không đủ. -> Chuyển đến Bước 3.
4.  **Bước 3: Tìm kiếm bên ngoài (Dự phòng).** Gọi `search_website` với một truy vấn rõ ràng.
5.  **Bước 4: Tổng hợp và trả lời.**
    *   Dựa trên tất cả thông tin thu thập được (từ Bước 1 và/hoặc Bước 3), tạo ra một câu trả lời cuối cùng, ngắn gọn, đi thẳng vào vấn đề.
    *   Nếu sau khi đã thử tất cả các công cụ mà vẫn không có thông tin, hãy trả lời: "Tôi không tìm thấy thông tin chính xác về [chủ đề câu hỏi]."

**VÍ DỤ LUỒNG SUY NGHĨ NỘI BỘ:**
-   **User:** "hiệu trưởng trường cơ khí là ai?"
-   **Suy nghĩ của Agent:**
    1.  *Lịch sử có nhắc đến "trường cơ khí". Câu hỏi là về "hiệu trưởng".*
    2.  *Thử tìm nội bộ trước. Gọi `search_docs(query='hiệu trưởng trường cơ khí đại học bách khoa hà nội')`.*
    3.  *Tool `search_docs` trả về: "không có thông tin".*
    4.  *Kết quả không đủ. Kích hoạt quy trình dự phòng. Gọi `search_website(query='hiệu trưởng trường cơ khí HUST 2024')`.*
    5.  *Tool `search_website` trả về: "PGS. TS. Trương Hoành Sơn là hiệu trưởng...".*
    6.  *Đã có đủ thông tin. Tổng hợp và trả lời người dùng.*
-   **Câu trả lời cuối cùng cho user:** "Hiệu trưởng hiện tại của Trường Cơ khí là PGS. TS. Trương Hoành Sơn."    
"""

def get_response(question: str, message_history: List[BaseMessage]) -> Tuple[str, List[BaseMessage]]:
    """
    Xử lý một câu hỏi, có tính đến lịch sử hội thoại.
    """
    # Tạo danh sách tin nhắn cho lần chạy này
    messages_for_run = [
        SystemMessage(content=system_prompt), # SỬA LỖI: Dùng SystemMessage và đúng tên biến
        *message_history,
        HumanMessage(content=question)
    ]

    # Chạy graph với toàn bộ lịch sử
    final_state = graph.invoke({"messages": messages_for_run})
    
    # Câu trả lời của bot là tin nhắn cuối cùng trong state
    final_answer = final_state["messages"][-1].content
    
    # Lịch sử mới bao gồm câu hỏi của user và câu trả lời của bot
    updated_history = message_history + [
        HumanMessage(content=question),
        AIMessage(content=final_answer) # Có thể dùng AIMessage hoặc BaseMessage từ final_state
    ]
    
    return final_answer, updated_history

if __name__ == "__main__":
    # Bắt đầu hội thoại với history rỗng
    conversation_history = []
    
    # Câu hỏi đầu tiên
    q1 = "Giới thiệu về trường cơ khí đại học bách khoa hà nội"
    print(f"User: {q1}")
    answer1, conversation_history = get_response(q1, conversation_history)
    print(f"Bot: {answer1}\n")
    
    # Câu hỏi thứ hai
    q2 = "tên của hiệu trưởng trường đấy là gì?"
    print(f"User: {q2}")
    answer2, conversation_history = get_response(q2, conversation_history)
    print(f"Bot: {answer2}\n")

    # In ra để xem toàn bộ lịch sử
    print("--- FINAL CONVERSATION HISTORY ---")
    for msg in conversation_history:
        print(f"{msg.type.upper()}: {msg.content}")
