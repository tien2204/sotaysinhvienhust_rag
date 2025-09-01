import requests
import json
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

# --- Các hàm xử lý và làm sạch dữ liệu (giữ nguyên) ---

# Dữ liệu tĩnh về chuyên ngành và tỉnh thành
CAREER_MAP = {
    "Điện tử viễn thông": 47, "Công nghệ thông tin": 48, "Kỹ thuật cơ khí": 49,
    "Kỹ thuật cơ điện tử": 50, "Kỹ thuật hàng không": 51, "Kỹ thuật tàu thủy": 52,
    "Kỹ thuật nhiệt": 53, "Kỹ thuật điện - điện tử": 54, "Kỹ thuật điều khiển và tự động hóa": 55,
    "Kỹ thuật điện tử truyền thông": 56, "Kỹ thuật y sinh": 57, "Kỹ thuật máy tính": 58,
    "Truyền thông và mạng máy tính": 59, "Khoa học máy tính": 60, "Kỹ thuật phần mềm": 61,
    "Hệ thống thông tin": 62, "Toán tin": 63, "Kỹ thuật hóa học": 64,
    "Kỹ thuật in và truyền thông": 65, "Kỹ thuật sinh học": 66, "Công nghệ thực phẩm": 67,
    "Kỹ thuật môi trường": 68, "Kỹ thuật vật liệu": 69, "Kỹ thuật luyện kim": 70,
    "Kỹ thuật dệt": 71, "Công nghệ may": 72, "Sư phạm kỹ thuật công nghiệp": 73,
    "Vật lý kỹ thuật": 74, "Kế toán": 75, "Kỹ thuật hạt nhân": 76, "Ngôn ngữ anh": 77,
    "Quản trị kinh doanh": 78, "Tài chính- Ngân hàng": 79, "Quản lý công nghiệp": 80,
    "Kinh tế công nghiệp": 81
}

CAREER_MAP_LOWER = {key.lower(): value for key, value in CAREER_MAP.items()}


VIETNAM_CITIES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu", "Bắc Ninh",
    "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", "Bình Thuận", "Cà Mau", "Cần Thơ",
    "Cao Bằng", "Đà Nẵng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội", "Hà Tĩnh", "Hải Dương", "Hải Phòng",
    "Hậu Giang", "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình",
    "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh",
    "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
    "Thừa Thiên Huế", "Tiền Giang", "TP Hồ Chí Minh", "Trà Vinh", "Tuyên Quang", "Vĩnh Long",
    "Vĩnh Phúc", "Yên Bái"
]

def html_to_text(html_string: str) -> str:
    """Chuyển đổi một chuỗi HTML thành văn bản thuần túy."""
    if not html_string:
        return ""
    try:
        soup = BeautifulSoup(html_string, 'lxml')
        for li in soup.find_all('li'):
            li.insert(0, '- ')
        text = soup.get_text(separator='\n').strip()
        return '\n'.join(line.strip() for line in text.splitlines() if line.strip())
    except Exception:
        return html_string

def parse_job_data(raw_job: dict) -> dict:
    """
    Nhận một dictionary tin tuyển dụng thô và trả về một dictionary sạch.
    """
    return {
        "title": raw_job.get("Title", "Chưa có tiêu đề"),
        "company_name": raw_job.get("CompanyName", "Không rõ tên công ty"),
        "salary": raw_job.get("AmountType", "Theo thỏa thuận"),
        "deadline": raw_job.get("Deadline", "Không có hạn nộp") or "Không có hạn nộp",
        "location": raw_job.get("WorkAddress", "Không rõ"),
        "work_type": raw_job.get("WorkType", "Không rõ"),
        "experience_required": raw_job.get("WorkExperience", "Không yêu cầu"),
        "majors_required": raw_job.get("CareerRequire", "Không yêu cầu cụ thể"),
        "positions_available": raw_job.get("QuantityCandidate", 1),
        
        "description": raw_job.get("WorkDescription", ""),
        "requirements": raw_job.get("WorkRequire", ""),
        "benefits": raw_job.get("Benefit", ""),
        
        "contact_name": raw_job.get("ContactName"),
        "contact_email": raw_job.get("ContactEmail"),
        "contact_phone": raw_job.get("ContactPhone")
    }


def get_raw_jobs_from_page(page_number: int, location_code: int, page_size: int = 20) -> Optional[List[Dict]]:
    """
    Hàm này giờ có nhiệm vụ lấy dữ liệu thô từ API.
    """
    url = "https://ctsv.hust.edu.vn/api-t/HWRecruitment/GetPublishRecruitment"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://ctsv.hust.edu.vn',
        'Referer': 'https://ctsv.hust.edu.vn/',
        'Content-Length':'50',
        'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }
    
    payload = {
        "filter": {}, # Gửi filter rỗng
        "NumberRow": page_size,
        "PageNumber": page_number,
        "PublishLocation": location_code
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get('RecruitmentLst', [])
    except Exception as e:
        print(f"Lỗi khi crawl trang {page_number} cho location {location_code}: {e}")
        return None

def fetch_jobs(
    location_code: int,
    career: Optional[str] = None,
    city: Optional[str] = None
) -> List[Dict]:
    """
    Hàm chính để crawl và lọc việc làm.
    Nó sẽ crawl toàn bộ dữ liệu trước, sau đó mới áp dụng bộ lọc.
    """
    all_clean_jobs = []
    
    # --- PHẦN 1: CRAWL TOÀN BỘ DỮ LIỆU ---
    print(f"Bắt đầu crawl toàn bộ dữ liệu cho location_code={location_code}...")
    current_page = 1
    while True:
        # Giới hạn 10 trang để tránh crawl quá lâu
        if current_page > 5:
            print("Đã đạt giới hạn số trang crawl. Dừng lại.")
            break
            
        print(f"Đang crawl trang {current_page}...")
        raw_jobs_on_page = get_raw_jobs_from_page(current_page, location_code=location_code)
        
        if raw_jobs_on_page is None or not raw_jobs_on_page:
            print("Hết dữ liệu. Kết thúc crawl.")
            break
        
        # --- PHẦN 2: XỬ LÝ VÀ LÀM SẠCH DỮ LIỆU ---
        for raw_job in raw_jobs_on_page:
            clean_job = parse_job_data(raw_job)
            all_clean_jobs.append(clean_job)
            
        current_page += 1
        time.sleep(0.5)

    print(f"Crawl xong. Có tổng cộng {len(all_clean_jobs)} tin tuyển dụng.")

    # --- PHẦN 3: LỌC DỮ LIỆU TRÊN CODE ---
    filtered_results = all_clean_jobs
    
    if city:
        print(f"Áp dụng bộ lọc thành phố: '{city}'")
        normalized_city = city.strip().lower()
        filtered_results = [
            job for job in filtered_results if normalized_city in job.get('location', '').lower()
        ]

    if career:
        print(f"Áp dụng bộ lọc chuyên ngành (case-insensitive): '{career}'")
        normalized_career = career.strip().lower()
        filtered_results = [
            job for job in filtered_results if normalized_career in job.get('majors_required', '').lower()
        ]

    print(f"Sau khi lọc, còn lại {len(filtered_results)} kết quả.")
    return filtered_results

if __name__ == "__main__":
    print(get_raw_jobs_from_page(1, 1))