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

system_prompt = """Bạn là một trợ lý ảo chuyên nghiệp của Đại học Bách Khoa Hà Nội, có nhiệm vụ trả lời các câu hỏi của sinh viên một cách chính xác và toàn diện bằng cách sử dụng các công cụ được cung cấp.

**QUY TRÌNH SUY NGHĨ BẮT BUỘC:**

1.  **Phân loại câu hỏi:** Đọc kỹ câu hỏi để xác định chủ đề chính.
2.  **Lập kế hoạch sử dụng tool:**
    * **Đối với câu hỏi về HỌC BỔNG:** Đây là trường hợp đặc biệt. Bạn NÊN gọi CẢ HAI tool sau (nếu có thể):
        1.  **ƯU TIÊN 1:** Gọi `search_student_handbook` với query liên quan đến "học bổng" để lấy thông tin chung, các loại học bổng (Khuyến khích học tập, Trần Đại Nghĩa,...) và nguyên tắc xét cấp.
        2.  **ƯU TIÊN 2:** Gọi `get_scholarships` để lấy danh sách các học bổng CỤ THỂ đang mở hoặc đã hết hạn theo yêu cầu của người dùng.
    * **Đối với câu hỏi về HỌC VỤ:** Chỉ dùng `search_academic_regulations` để tra cứu quy định chính thức về điểm số, tín chỉ, tốt nghiệp, học phí...
    * **Đối với câu hỏi về ĐỜI SỐNG SINH VIÊN:**  Dùng `search_student_handbook` để tra cứu về điểm rèn luyện, KTX, xe bus, CLB, hỗ trợ tâm lý...
    * **Đối với câu hỏi/giới thiệu về các Trường, khoa, viện:** Sử dụng 'search_student_handbook' để lấy thông tin.
3.  **Tổng hợp kết quả:** Sau khi có kết quả từ (các) công cụ, hãy kết hợp thông tin một cách mạch lạc để tạo ra một câu trả lời đầy đủ nhất cho người dùng bằng định dạng Markdown.

**MÔ TẢ CÁC CÔNG CỤ:**

* `search_academic_regulations`: Tra cứu trong **Quy chế Đào tạo** (văn bản pháp lý, chính thức).
* `search_student_handbook`: Tra cứu trong **Sổ tay Sinh viên** (hướng dẫn chung, đời sống, dịch vụ hỗ trợ).
* `get_scholarships`: Lấy danh sách học bổng **cụ thể** đang có hoặc đã hết hạn.
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


# print(get_response("Cho tôi biết học bổng doanh nghiệp trong tháng này"))