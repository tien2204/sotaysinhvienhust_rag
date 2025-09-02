import os
from typing import Annotated, List

from langchain_core.messages import BaseMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode 
from typing_extensions import TypedDict, Literal
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
os.environ["LANGCHAIN_TRACING_V2"] = "true" 

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
    question = state["messages"][-1].content
    classification_result = query_classifier.invoke({"query": question})
    print(f"--- CLASSIFICATION RESULT: {classification_result} ---")
    return {"classification": classification_result}

def agent_node(state: AgentState):
    """
    Gọi LLM để quyết định hành động tiếp theo: trả lời hoặc gọi tool.
    """
    print("--- NODE: AGENT---")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def rejection_node(state: AgentState):
    """Node xử lý câu hỏi không an toàn."""
    print("---NODE: REJECTION---")
    rejection_message = AIMessage(
        content="Xin lỗi, tôi là trợ lý ảo của Đại học Bách Khoa Hà Nội và chỉ có thể trả lời các câu hỏi liên quan đến quy chế, học bổng và đời sống sinh viên tại trường. Tôi không thể hỗ trợ các chủ đề khác."
    )
    return {"messages": [rejection_message]}

def should_classify(state: AgentState) -> Literal["agent_node", "rejection_node"]:
    """Quyết định đi đâu sau khi phân loại."""
    if state["classification"] == "safe":
        return "agent_node"
    else:
        return "rejection_node"

def should_continue(state: AgentState) -> str:
    """
    Quyết định luồng đi tiếp theo sau khi Agent Node chạy.
    """
    if state["messages"][-1].tool_calls:
        return "continue_to_tool"
    return "end"

graph_builder = StateGraph(AgentState)

graph_builder.add_node("classifier", classification_node)
graph_builder.add_node("rejection", rejection_node)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("action", tool_node)

# Đặt agent là điểm bắt đầu
graph_builder.set_entry_point("classifier")

# Thêm cạnh điều kiện
graph_builder.add_conditional_edges(
    "classifier",
    should_classify,
    {
        "agent_node": "agent",
        "rejection_node": "rejection"
    }
)
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        # Nếu cần gọi tool, đi đến node "action"
        "continue_to_tool": "action",
        "end": END,
    },
)
# Các cạnh cố định
graph_builder.add_edge("action", "agent")
graph_builder.add_edge("rejection", END)


# Biên dịch graph thành một đối tượng có thể chạy được
graph = graph_builder.compile()

system_prompt = """
Bạn là một trợ lý ảo chuyên nghiệp của Đại học Bách Khoa Hà Nội, có nhiệm vụ trả lời các câu hỏi của sinh viên một cách chính xác bằng cách sử dụng các công cụ được cung cấp.

ĐỊNH DẠNG TRẢ LỜI (QUAN TRỌNG):
    1. Súc tích cho TTS: Vì câu trả lời sẽ được đọc thành tiếng, hãy trả lời ngắn gọn, trực tiếp, đi thẳng vào vấn đề. Sử dụng câu văn đơn giản, rõ ràng. Trả lời trong không quá 5 câu. Hạn chế viết tắt.
    2. Không chào hỏi: Bắt đầu ngay vào phần thông tin chính, không dùng các câu chào hỏi xã giao như "Chào bạn,".
QUY TRÌNH SUY NGHĨ BẮT BUỘC:
    1. Phân tích câu hỏi: Đọc kỹ câu hỏi để hiểu rõ ý định của người dùng, bao gồm cả các mốc thời gian cụ thể.
    2. Lập kế hoạch sử dụng tool:
        2.1 Đối với câu hỏi về học bổng:
            Nếu người dùng hỏi về một tháng cụ thể (ví dụ: "tháng 8", "tháng chín"), hãy suy luận ra năm phù hợp (thường là năm hiện tại) và gọi tool với định dạng YYYY-MM. Ví dụ: "học bổng tháng 9" -> get_scholarships(time_period="2025-09").
            Nếu câu hỏi mang tính chung chung về "chính sách học bổng", hãy gọi cả search_student_handbook và get_scholarships.
        2.2 Đối với câu hỏi về HỌC VỤ: Dùng search_academic_regulations (ví dụ: điểm số, tín chỉ, tốt nghiệp).
        2.3 Đối với câu hỏi về ĐỜI SỐNG SINH VIÊN: Dùng search_student_handbook (ví dụ: KTX, xe bus, CLB).
        2.4 Đối với câu hỏi/giới thiệu về các Trường, khoa, viện: Sử dụng search_student_handbook để lấy thông tin.
        2.5 Đối với câu hỏi liên quan đến PHÁP LUẬT VIỆT NAM: Dùng search_law_vietnam. (ví dụ: Hiến pháp, Bộ luật, dân sự, hình sự, lao động)
        2.6 Đối với câu hỏi cần thông tin thời sự hoặc ngoài cơ sở dữ liệu, ngoài các mô tả các tool trên: Dùng search_website.
    3. Tổng hợp kết quả: Kết hợp thông tin từ các công cụ và trả lời người dùng một cách mạch lạc theo định dạng đã yêu cầu ở trên.
MÔ TẢ CÁC CÔNG CỤ:
    1. get_scholarships: Dùng để lấy danh sách học bổng. Tham số time_period rất linh hoạt, có thể là từ khóa ("this_month") hoặc tháng cụ thể ("2025-08").
    2. search_academic_regulations: Tra cứu trong Quy chế Đào tạo (văn bản học thuật chính thức).
    3. search_student_handbook: Tra cứu trong Sổ tay Sinh viên (hướng dẫn đời sống, dịch vụ).
    4. search_law_vietnam: Tra cứu văn bản pháp luật Việt Nam.
    5. search_website: Tìm kiếm và scrape nội dung web.
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
    print(get_response("Thủ tướng Việt Nam là ai?"))