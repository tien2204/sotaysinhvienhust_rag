# mcp/activities.py

import requests
import json
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

def html_to_text(html_string: str) -> str:
    """
    Chuyển đổi một chuỗi HTML thành văn bản thuần túy,
    giữ lại định dạng và dọn dẹp các dòng trắng thừa.
    """
    if not html_string:
        return ""
    try:
        soup = BeautifulSoup(html_string, 'lxml')
        
        # Lấy văn bản, dùng separator='\n' để mỗi thẻ block tạo một dòng mới
        text = soup.get_text(separator='\n')
        
        # Dùng regex để thay thế 3+ dấu xuống dòng bằng 2 dấu
        # và dọn dẹp các dòng chỉ có khoảng trắng
        clean_text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        final_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        
        return final_text.strip()
    except Exception:
        return html_string

# --- HÀM PARSER ĐÃ ĐƯỢC CẬP NHẬT THEO CẤU TRÚC MỚI ---
def parse_activity_data(raw_activity: dict) -> dict:
    """Parser cho danh sách tóm tắt (không đổi)."""
    base_url = "https://ctsv.hust.edu.vn"
    avatar_path = raw_activity.get("Avatar")
    image_url = f"{base_url}/{avatar_path}" if avatar_path else None
    
    return {
        "id": raw_activity.get("AId"),
        "title": raw_activity.get("AName", "Chưa có tiêu đề"),
        "organizer": raw_activity.get("GName", "Không rõ đơn vị tổ chức"),
        "activity_type": raw_activity.get("AType", "Không rõ"),
        "start_time": raw_activity.get("StartTime"),
        "image_url": image_url,
    }


def parse_detailed_activity_data(raw_activity: dict) -> dict:
    """
    HÀM MỚI: Parser cho dữ liệu chi tiết, bao gồm cả tiêu chí.
    """
    # Dùng lại parser cơ bản để lấy thông tin chung
    clean_data = parse_activity_data(raw_activity)
    
    # Xử lý và thêm thông tin chi tiết
    clean_data.update({
        "finish_time": raw_activity.get("FinishTime"),
        "location": raw_activity.get("APlace", "Không rõ địa điểm"),
        "description": html_to_text(raw_activity.get("ADesc")),
        "registration_deadline": raw_activity.get("Deadline"),
    })
    
    # Xử lý danh sách tiêu chí
    criteria_list = []
    raw_criteria = raw_activity.get("CriteriaLst", [])
    if raw_criteria and isinstance(raw_criteria, list):
        for item in raw_criteria:
            name = item.get("CName", "Không rõ tiêu chí")
            points = item.get("CMaxPoint", 0)
            criteria_list.append(f"{name} (Tối đa: {points} điểm)")
            
    clean_data["criteria"] = criteria_list
    
    return clean_data

# --- CÁC HÀM CRAWL ---
def get_raw_activities_from_page(page_number: int, signature: str = "sample string 4", page_size: int = 1000) -> Optional[List[Dict]]:
    """Lấy danh sách hoạt động thô từ một trang cụ thể."""
    url = "https://ctsv.hust.edu.vn/api-t/Activity/GetPublishActivity"
    headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    payload = {
        "Signature": signature,
        "NumberRow": page_size,
        "PageNumber": page_number
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # --- THAY ĐỔI CHÍNH Ở ĐÂY ---
        # Key chứa danh sách là "Activities", không phải "ActivityLst"
        return data.get('Activities', []) 
        
    except Exception as e:
        print(f"Lỗi khi crawl trang hoạt động {page_number}: {e}")
        return None

def fetch_activities(max_pages: int = 5) -> List[Dict]:
    """
    Crawl và xử lý tin hoạt động cho một 'signature' cụ thể.
    """
    all_clean_activities = []
    
    for page_num in range(1, max_pages + 1):
        print(f"Đang crawl trang hoạt động {page_num}...")
        raw_activities_on_page = get_raw_activities_from_page(page_num)
        
        if raw_activities_on_page is None or not raw_activities_on_page:
            print(f"Hết dữ liệu ở trang {page_num}. Dừng lại.")
            break
            
        for raw_activity in raw_activities_on_page:
            clean_activity = parse_activity_data(raw_activity)
            all_clean_activities.append(clean_activity)
        
        time.sleep(0.5)
        
    print(f"Crawl xong. Có tổng cộng {len(all_clean_activities)} hoạt động.")
    return all_clean_activities

def fetch_activity_details(activity_id: int) -> Optional[Dict]:
    """
    HÀM MỚI: Gọi API GetActivityById để lấy thông tin chi tiết.
    """
    url = "https://ctsv.hust.edu.vn/api-t/Activity/GetActivityById"
    headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    payload = {"AId": activity_id}
    
    print(f"--- Fetching details for Activity ID: {activity_id} ---")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Dữ liệu chi tiết nằm trong list "Activities", ta lấy phần tử đầu tiên
        activity_list = data.get('Activities', [])
        if activity_list:
            # Gửi dữ liệu thô qua parser để làm sạch
            return parse_detailed_activity_data(activity_list[0])
        return None
        
    except Exception as e:
        print(f"Lỗi khi crawl chi tiết hoạt động {activity_id}: {e}")
        return None
    
if __name__ == "__main__":
    res = fetch_activity_details(14505)
    print(res)
    print(type(res))