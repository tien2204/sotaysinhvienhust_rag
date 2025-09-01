import os
from typing import Annotated, List

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode 
from typing_extensions import TypedDict

from .tools import get_scholarships, search_student_handbook, search_academic_regulations

# --- Khởi tạo ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
tool = [get_scholarships, search_academic_regulations, search_student_handbook]

# Gắn (bind) các tool vào LLM để nó biết cách gọi
llm_with_tools = llm.bind_tools(tool)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]


def agent_node(state: AgentState):
    """
    Gọi LLM để quyết định hành động tiếp theo: trả lời hoặc gọi tool.
    """
    print("---NODE: AGENT---")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tool)

def should_continue(state: AgentState) -> str:
    """
    Quyết định luồng đi tiếp theo sau khi Agent Node chạy.
    """
    if state["messages"][-1].tool_calls:
        return "continue_to_tool"
    return "end"

graph_builder = StateGraph(AgentState)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("action", tool_node)

# Đặt agent là điểm bắt đầu
graph_builder.set_entry_point("agent")

# Thêm cạnh điều kiện
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        # Nếu cần gọi tool, đi đến node "action"
        "continue_to_tool": "action",
        "end": END,
    },
)

# Sau khi thực thi tool, quay lại agent để nó xử lý kết quả
graph_builder.add_edge("action", "agent")

# Biên dịch graph thành một đối tượng có thể chạy được
graph = graph_builder.compile()
# --- Sửa trong rag.py ---
system_prompt = """Bạn là một trợ lý ảo chuyên nghiệp của Đại học Bách Khoa Hà Nội, có nhiệm vụ trả lời các câu hỏi của sinh viên một cách chính xác và toàn diện bằng cách sử dụng các công cụ được cung cấp.

**QUY TRÌNH SUY NGHĨ BẮT BUỘC:**

1.  **Phân tích câu hỏi:** Đọc kỹ câu hỏi để hiểu rõ ý định của người dùng, bao gồm cả các mốc thời gian cụ thể.
2.  **Lập kế hoạch sử dụng tool:**
    * **Đối với câu hỏi về học bổng:**
        * Nếu người dùng hỏi về một tháng cụ thể (ví dụ: "tháng 8", "tháng chín"), hãy suy luận ra năm phù hợp (thường là năm hiện tại) và gọi tool với định dạng `YYYY-MM`. Ví dụ: "học bổng tháng 9" -> `get_scholarships(time_period="2025-09")`.
        * Nếu câu hỏi mang tính chung chung về "chính sách học bổng", hãy gọi cả `search_student_handbook` và `get_scholarships`.
    * **Đối với câu hỏi về HỌC VỤ:** Dùng `search_academic_regulations` (ví dụ: điểm số, tín chỉ, tốt nghiệp).
    * **Đối với câu hỏi về ĐỜI SỐNG SINH VIÊN:** Dùng `search_student_handbook` (ví dụ: KTX, xe bus, CLB).
    * **Đối với câu hỏi/giới thiệu về các Trường, khoa, viện:** Sử dụng 'search_student_handbook' để lấy thông tin.
3.  **Tổng hợp kết quả:** Kết hợp thông tin từ các công cụ và trả lời người dùng một cách mạch lạc.

**MÔ TẢ CÁC CÔNG CỤ:**

* `get_scholarships`: Dùng để lấy danh sách học bổng. Tham số `time_period` rất linh hoạt, có thể là từ khóa ("this_month") hoặc tháng cụ thể ("2025-08").
* `search_academic_regulations`: Tra cứu trong **Quy chế Đào tạo** (văn bản học thuật chính thức).
* `search_student_handbook`: Tra cứu trong **Sổ tay Sinh viên** (hướng dẫn đời sống, dịch vụ).
"""

def get_response(question: str) -> str:
    if not question or not question.strip():
        return "Vui lòng đặt câu hỏi."

    from langchain_core.messages import HumanMessage, SystemMessage
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]

    final_state = graph.invoke({"messages": messages})
    final_answer = final_state["messages"][-1].content
    return final_answer

if __name__ == "__main__":
    print(get_response("Cho tôi biết về chính sách học bổng của HUST và thông tin chi tiết học bổng doanh nghiệp trong tháng trước"))