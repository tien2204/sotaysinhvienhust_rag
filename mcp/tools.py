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

# --- Khởi tạo Pinecone (chỉ cho tool tìm kiếm sổ tay) ---

pinecone_api_key = os.getenv("PICONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = "sotayhust"  
index = pc.Index(index_name)

def get_similar_doc(text, namespace, topk = 10):
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
@tool
def get_scholarships(
    time_period: str = "upcoming", status: str = "all"
) -> List[Dict]:
    """
    Sử dụng để lấy danh sách học bổng, có thể lọc theo thời gian và trạng thái (còn hạn/hết hạn).
    
    Tham số `status` chấp nhận:
    - "open": (Mặc định) Học bổng còn hạn.
    - "expired": Học bổng đã hết hạn.
    - "all": Tất cả học bổng.
    
    Tham số `time_period` để lọc deadline trong khoảng thời gian, chấp nhận:
    - "upcoming": (Mặc định) Học bổng có hạn trong 30 ngày tới.
    - "this_week", "this_month": Tuần này, tháng này.
    - "last_7_days", "last_month": 7 ngày qua, tháng trước.
    """
    print(f"---TOOL: get_scholarships (time_period: {time_period}, status: {status})---")

    all_scholarships = crawl_all_scholarships()[:2]
    if not all_scholarships:
        return [{"error": "Không thể crawl dữ liệu học bổng."}]

    # --- Logic xác định khoảng thời gian (không đổi) ---
    today = datetime.now()
    start_dt, end_dt = None, None
    time_period_mapping = {
        "upcoming": (today, today + timedelta(days=30)),
        "this_week": (today - timedelta(days=today.weekday()), (today - timedelta(days=today.weekday())) + timedelta(days=6)),
        "this_month": (today.replace(day=1), today.replace(day=calendar.monthrange(today.year, today.month)[1])),
        "last_7_days": (today - timedelta(days=7), today),
        "last_month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1), today.replace(day=1) - timedelta(days=1)),
    }
    if time_period in time_period_mapping:
        start_dt, end_dt = time_period_mapping[time_period]
        start_dt = start_dt.replace(hour=0, minute=0, second=0)
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
    else:
        return [{"error": f"Giá trị time_period không hợp lệ: {time_period}"}]

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

# print(get_scholarships("this_month", "all"))