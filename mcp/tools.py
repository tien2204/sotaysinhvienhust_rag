from .scholarship import *

import os
from datetime import datetime, timedelta
from typing import List, Optional
import calendar
from typing import Dict, List
from langchain_core.tools import tool
from pinecone import Pinecone
from dotenv import load_dotenv
load_dotenv()


from langchain_google_genai import ChatGoogleGenerativeAI
classifier_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# --- Khởi tạo Pinecone (chỉ cho tool tìm kiếm sổ tay) ---

pinecone_api_key = os.getenv("PICONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = "sotayhust"  
index = pc.Index(index_name)

def get_similar_doc(text, namespace, topk = 5):
    results = index.search(
        namespace="semantic_chunker", 
        query={
            "inputs": {"text": text}, 
            "top_k": topk
        },
        fields=["text"]
    )
    list_doc = []
    for doc in results["result"]['hits']:
        list_doc.append(doc['fields']['text'])
    return list_doc

# --- TOOL KIỂM DUYỆT NỘI DUNG ---
@tool
def query_classifier(query: str) -> str:
    """
    Phân loại câu hỏi của người dùng vào một trong các danh mục sau: 'safe', 'sensitive_political'.
    """

    system_prompt = f"""
    Bạn là một chuyên gia kiểm duyệt nội dung cho một chatbot của trường đại học.
    Nhiệm vụ của bạn là phân loại câu hỏi của sinh viên vào MỘT trong hai danh mục sau đây:
    1. safe: Các câu hỏi liên quan trực tiếp đến đời sống, học tập, quy chế, học bổng, chính sách tại Đại học Bách Khoa Hà Nội.
    2. sensitive_political: Các câu hỏi chứa nội dung về chính trị, tôn giáo, các vấn đề xã hội nhạy cảm, bạo lực, thù ghét, hoặc không phù hợp với môi trường giáo dục.

    Hãy chỉ trả về TÊN của danh mục (ví dụ: "safe" hoặc "sensitive_political"), không giải thích gì thêm.

    Câu hỏi cần phân loại: "{query}"
    """
    
    print(f"---TOOL: Classifying query: '{query}'---")
    
    # Gọi LLM để phân loại
    response = classifier_llm.invoke(system_prompt)
    
    # Xử lý kết quả trả về từ LLM
    classification = response.content.strip().lower()
    
    if "sensitive_political" in classification:
        return "sensitive_political"
    
    return "safe"
# --- Định nghĩa Tool 1: Tìm kiếm Sổ tay Sinh viên ---
@tool
def search_student_handbook(query: str) -> List[str]:
    """
    Sử dụng để tra cứu thông tin về ĐỜI SỐNG SINH VIÊN và CÁC DỊCH VỤ HỖ TRỢ trong Sổ tay Sinh viên.
    Rất hữu ích cho các câu hỏi về: điểm rèn luyện, hoạt động ngoại khóa, câu lạc bộ,
    ký túc xá, nhà trọ, các tuyến xe bus, hỗ trợ tâm lý, hướng nghiệp, việc làm thêm,
    quy tắc ứng xử văn hóa, quy định về học bổng và thông tin liên hệ các phòng ban, khoa, viện.
    """
    print(f"---SỬ DỤNG TOOL: search_docs với query: {query}---")
    return get_similar_doc(query, namespace = "semantic_chunker")

@tool
def search_academic_regulations(query: str) -> List[str]:
    """
    Sử dụng để tra cứu các QUY ĐỊNH HỌC THUẬT CHÍNH THỨC trong Quy chế Đào tạo.
    Dùng cho các câu hỏi về: tín chỉ, điểm số (GPA/CPA), đăng ký học phần, cảnh báo học tập,
    điều kiện tốt nghiệp, đồ án tốt nghiệp, nghỉ học tạm thời, buộc thôi học, học phí,
    học cùng lúc hai chương trình, và các vấn đề học vụ khác.
    """
    print(f"---TOOL: search_academic_regulations (namespace: QCDT2025) | Query: {query}---")
    return get_similar_doc(query, namespace="QCDT2025")

# --- Định nghĩa Tool 2: Lấy Học bổng theo Ngày ---
# @tool
def get_scholarships(
    time_period: str = "upcoming", status: str = "all"
) -> List[Dict]:
    """
    Sử dụng để lấy danh sách học bổng, có thể lọc theo thời gian và trạng thái (còn hạn/hết hạn).
    
    Tham số `status` chấp nhận: "open", "expired", "all".
    
    Tham số `time_period` chấp nhận:
    - Các từ khóa: "upcoming", "this_week", "this_month", "last_7_days", "last_month".
    - Tháng cụ thể: chuỗi "YYYY-MM" (ví dụ: "2025-08" cho tháng 8 năm 2025).
    - Ngày cụ thể: chuỗi "YYYY-MM-DD" (ví dụ: "2025-09-01").
    """
    print(f"---TOOL: get_scholarships (time_period: {time_period}, status: {status})---")

    all_scholarships = crawl_all_scholarships()
    if not all_scholarships:
        return [{"error": "Không thể crawl dữ liệu học bổng."}]

    today = datetime.now()
    start_dt, end_dt = None, None

    # --- Logic thông minh để xác định khoảng thời gian ---
    time_period_mapping = {
        "upcoming": (today, today + timedelta(days=30)),
        "this_week": (today - timedelta(days=today.weekday()), (today - timedelta(days=today.weekday())) + timedelta(days=6)),
        "this_month": (today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1])),
        "last_7_days": (today - timedelta(days=7), today),
        "last_month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1)),
    }

    if time_period in time_period_mapping:
        start_dt, end_dt = time_period_mapping[time_period]
    else:
        # **LOGIC MỚI: Cố gắng diễn giải time_period như một ngày/tháng cụ thể**
        try:
            # Thử định dạng YYYY-MM (cho cả tháng)
            parsed_date = datetime.strptime(time_period, "%Y-%m")
            start_dt = parsed_date.replace(day=1)
            last_day = calendar.monthrange(parsed_date.year, parsed_date.month)[1]
            end_dt = parsed_date.replace(day=last_day)
        except ValueError:
            try:
                # Thử định dạng YYYY-MM-DD (cho ngày cụ thể)
                parsed_date = datetime.strptime(time_period, "%Y-%m-%d")
                start_dt = end_dt = parsed_date
            except ValueError:
                return [{"error": f"Giá trị time_period '{time_period}' không hợp lệ. Phải là từ khóa hoặc theo định dạng YYYY-MM, YYYY-MM-DD."}]

    # Đảm bảo bao trọn cả ngày
    start_dt = start_dt.replace(hour=0, minute=0, second=0)
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    # --- Lọc học bổng (ĐÃ SỬA LỖI) ---
    filtered_list = []
    for hb in all_scholarships:
        try:
            # SỬA LỖI 1: Luôn đảm bảo truy cập key 'Deadline' tồn tại trong dict
            if 'Deadline' not in hb or not hb['Deadline']:
                continue
            
            deadline_dt = datetime.strptime(hb['Deadline'], '%Y-%m-%d %H:%M:%S')
            if not (start_dt <= deadline_dt <= end_dt):
                continue
            
            is_expired = deadline_dt < today
            current_status = "Expired" if is_expired else "Open"

            if status == "all" or (status == "open" and not is_expired) or (status == "expired" and is_expired):
                # SỬA LỖI 2: Xây dựng dictionary kết quả bằng cách truy cập key an toàn với .get()
                hb = Scholarship(hb)
                filtered_list.append(hb.get_full_info_string())
        except (ValueError, KeyError, TypeError) as e:
            # Bắt lỗi rộng hơn để tránh làm sập tool nếu dữ liệu không nhất quán
            print(f"Bỏ qua học bổng bị lỗi: {hb.get('Title')}, Lỗi: {e}")
            continue

    if not filtered_list:
        return [{"message": f"Không tìm thấy học bổng nào với trạng thái '{status}' trong khoảng thời gian '{time_period}'."}]

    return filtered_list

if __name__ == "__main__":
    print(get_scholarships("2025-08", "all"))