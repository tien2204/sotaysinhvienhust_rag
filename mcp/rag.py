import os
from typing import Annotated, List, Tuple

from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from dotenv import load_dotenv

load_dotenv()

from .tools import (
    get_scholarships,
    search_student_handbook,
    search_academic_regulations,
    search_law_vietnam,
    search_website
)

# --- Khởi tạo ---

os.environ["LANGCHAIN_PROJECT"] = "HUST-AI-Assistant"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
tools = [
    get_scholarships,
    search_academic_regulations,
    search_student_handbook,
    search_law_vietnam,
    search_website,
]

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

# --- NODES ---

def agent_node(state: AgentState):
    """Gọi LLM để quyết định hành động tiếp theo."""
    print("--- NODE: AGENT ---")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# --- CONDITIONAL EDGES ---

def should_continue(state: AgentState) -> str:
    """Quyết định có tiếp tục gọi tool hay kết thúc."""
    if isinstance(state["messages"][-1], AIMessage) and state["messages"][-1].tool_calls:
        return "continue_to_tool"
    return "end"

# --- XÂY DỰNG GRAPH ---
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("action", tool_node)

graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges("agent", should_continue, {"continue_to_tool": "action", "end": END})
graph_builder.add_edge("action", "agent")

graph = graph_builder.compile()


# --- SYSTEM PROMPT TỐI ƯU ---
system_prompt = """
Bạn là trợ lý ảo của Đại học Bách Khoa Hà Nội, chuyên trả lời câu hỏi cho sinh viên. Luôn dựa vào lịch sử hội thoại để hiểu ngữ cảnh.

QUY TẮC BẮT BUỘC:
1.  KIỂM DUYỆT TRƯỚC: Đầu tiên, hãy kiểm tra câu hỏi. Nếu nó chứa nội dung nhạy cảm (chính trị, tôn giáo) hoặc không phù hợp, hãy trả lời ngay lập tức bằng câu sau và dừng lại: "Xin lỗi, tôi là trợ lý ảo của Đại học Bách Khoa Hà Nội và chỉ có thể trả lời các câu hỏi liên quan đến quy chế, học bổng và đời sống sinh viên tại trường."
2.  QUY TRÌNH TÌM KIẾM:
    a. Ưu tiên dùng tool nội bộ: Luôn thử `search_student_handbook`, `search_academic_regulations`, `get_scholarships`, `search_law_vietnam` trước.
    b. Bắt buộc dùng tool dự phòng: Nếu các tool nội bộ không có kết quả hoặc kết quả không đủ thông tin, BẮT BUỘC phải gọi `search_website` để tìm câu trả lời.
    c. Trả lời khi không tìm thấy: Nếu đã thử tất cả các tool mà vẫn không có thông tin, hãy trả lời: "Tôi không tìm thấy thông tin chính xác về [chủ đề câu hỏi]."
3.  ĐỊNH DẠNG TRẢ LỜI: Ngắn gọn, đi thẳng vào vấn đề, không chào hỏi.
4.  KHÔNG NÓI VỀ QUÁ TRÌNH: Không bao giờ nói "Tôi đang tìm kiếm...", chỉ đưa ra câu trả lời cuối cùng.
"""

def get_response(question: str, message_history: List[BaseMessage]) -> Tuple[str, List[BaseMessage]]:
    """
    Xử lý một câu hỏi, có tính đến lịch sử hội thoại.
    """
    messages_for_run = [
        SystemMessage(content=system_prompt),
        *message_history,
        HumanMessage(content=question)
    ]

    final_state = graph.invoke({"messages": messages_for_run})
    
    final_answer = final_state["messages"][-1].content
    
    updated_history = message_history + [
        HumanMessage(content=question),
        AIMessage(content=final_answer)
    ]
    
    return final_answer, updated_history

if __name__ == "__main__":
    conversation_history = []
    
    q1 = "Giới thiệu về trường cơ khí đại học bách khoa hà nội"
    print(f"User: {q1}")
    answer1, conversation_history = get_response(q1, conversation_history)
    print(f"Bot: {answer1}\n")
    
    q2 = "tên của hiệu trưởng trường đấy là gì?"
    print(f"User: {q2}")
    answer2, conversation_history = get_response(q2, conversation_history)
    print(f"Bot: {answer2}\n")
    
    print("--- FINAL CONVERSATION HISTORY ---")
    for msg in conversation_history:
        print(f"{msg.type.upper()}: {msg.content}")
