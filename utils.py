from mcp.rag import llm
import re
from vietnam_number import n2w
from datetime import datetime

# Từ điển dịch tên tháng sang tiếng Việt
MONTHS_VI = {
    'January': 'tháng Một',
    'February': 'tháng Hai',
    'March': 'tháng Ba',
    'April': 'tháng Tư',
    'May': 'tháng Năm',
    'June': 'tháng Sáu',
    'July': 'tháng Bảy',
    'August': 'tháng Tám',
    'September': 'tháng Chín',
    'October': 'tháng Mười',
    'November': 'tháng Mười Một',
    'December': 'tháng Mười Hai'
}

def preprocess_text(text: str) -> str:
    """
    Tiền xử lý văn bản: chuyển số, ngày tháng, ký tự đặc biệt, viết tắt sang dạng đầy đủ.
    """
    # 1. Mở rộng từ viết tắt (Ưu tiên số 1)
    abbreviations = {
        "sv": "sinh viên",
        "hcm": "hồ chí minh",
        "CNTT&TT" : "công nghệ thông tin và truyền thông"
    }
    for abbr, full_text in abbreviations.items():
        text = re.sub(r'\b' + re.escape(abbr) + r'\b', full_text, text, flags=re.IGNORECASE)

    # 2. Chuyển đổi ngày tháng (Dùng datetime - Ưu tiên số 2)
    matches = list(re.finditer(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', text))
    if matches:
        processed_text_parts = []
        last_index = 0
        for match in matches:
            date_str = match.group(0)
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                
                day_str = n2w(date_obj.strftime("%d"))
                month_str = MONTHS_VI[date_obj.strftime("%B")]
                year_str = n2w(date_obj.strftime("%Y"))
                
                formatted_date = f"ngày {day_str} {month_str} năm {year_str}"
                
                processed_text_parts.append(text[last_index:match.start()])
                processed_text_parts.append(formatted_date)
            except (ValueError, IndexError):
                processed_text_parts.append(text[last_index:match.end()])
            
            last_index = match.end()
        
        processed_text_parts.append(text[last_index:])
        text = ''.join(processed_text_parts)

    # 3. Chuyển đổi các con số còn lại thành chữ (Ưu tiên số 3)
    matches = list(re.finditer(r'(\d[\d\.,]*)', text))
    if matches:
        processed_text_parts = []
        last_index = 0
        for match in matches:
            processed_text_parts.append(text[last_index:match.start()])
            number_str = match.group(0).replace('.', '').replace(',', '')
            try:
                processed_text_parts.append(n2w(number_str))
            except (ValueError, IndexError):
                processed_text_parts.append(match.group(0))
            last_index = match.end()
        processed_text_parts.append(text[last_index:])
        text = ''.join(processed_text_parts)
    
    # 4. Thay thế ký tự đặc biệt (Ưu tiên số 4 - Cuối cùng)
    # Bây giờ, chuỗi ngày tháng đã được xử lý xong, không còn ký tự '/'
    text = text.replace("&", " và ")
    text = text.replace("/", " trên ")
    text = text.replace("lẽ", "")
    
    # 5. Loại bỏ các ký tự không mong muốn và khoảng trắng thừa
    # Tinh chỉnh regex để xử lý tốt hơn
    print(text)
    return re.sub(r'\s+', ' ', text).strip()

# print(preprocess_text("""
# Đại học Bách khoa Hà Nội được thành lập ngày 6/3/1956. Trường đã chuyển thành Đại học Bách khoa Hà Nội theo Quyết định số 1512/QĐ-TTg ngày 02/12/2022 của Thủ tướng Chính phủ. Hiện tại, Đại học Bách khoa Hà Nội có hơn 200.000 cựu sinh viên, với cơ cấu gồm 10 Trường & Khoa đào tạo, 03 Khoa đào tạo cơ bản, 06 Viện/Trung tâm nghiên cứu và 12 Phòng nghiên cứu trọng điểm.
# """))