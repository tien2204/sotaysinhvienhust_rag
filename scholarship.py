from datetime import datetime
from bs4 import BeautifulSoup
from typing import Optional
import requests
import json
import re

class Scholarship:
    """
    Một class để biểu diễn thông tin chi tiết về một học bổng.
    Class này sẽ phân tích cú pháp dữ liệu JSON và lưu trữ nó một cách có cấu trúc.
    """

    def __init__(self, data: dict):
        """
        Khởi tạo một đối tượng Scholarship từ một dictionary dữ liệu.
        
        Args:
            data (dict): Dictionary chứa dữ liệu thô của học bổng.
        """
        self.document_id: Optional[int] = data.get('DocumentId')
        self.title: Optional[str] = data.get('Title')
        self.deadline_str: Optional[str] = data.get('Deadline')
        self.total_price: Optional[str] = data.get('TotalPrice')
        self.description: Optional[str] = data.get('Description')
        self.html_content: Optional[str] = data.get('Content')
        self.quantity: Optional[int] = data.get('Quantity')
        self.type_info: Optional[str] = data.get('TypeInfo')
        self.contact_email: Optional[str] = data.get('ContactEmail')
        self.creator_email: Optional[str] = data.get('CreateMail')

        # Xử lý các trường dữ liệu để có định dạng tốt hơn
        self.deadline: Optional[datetime] = self._parse_deadline()
        self.plain_text_content: str = self._parse_html_to_text()

    def _parse_deadline(self) -> Optional[datetime]:
        """Chuyển đổi chuỗi deadline thành đối tượng datetime."""
        if self.deadline_str:
            try:
                # Thử phân tích chuỗi với định dạng 'YYYY-MM-DD HH:MM:SS'
                return datetime.strptime(self.deadline_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"Cảnh báo: Không thể phân tích chuỗi deadline: {self.deadline_str}")
                return None
        return None

    def _parse_html_to_text(self) -> str:
        """Chuyển đổi nội dung HTML thành văn bản thuần túy (plain text)."""
        if self.html_content:
            soup = BeautifulSoup(self.html_content, 'html.parser')
            # Thêm khoảng trắng giữa các thẻ để dễ đọc hơn
            for p in soup.find_all('p'):
                p.append(' ')
            return soup.get_text(separator='\n').strip()
        return ""

    def is_active(self) -> bool:
        """Kiểm tra xem học bổng còn hạn nộp hay không."""
        if self.deadline:
            return datetime.now() < self.deadline
        # Mặc định là không active nếu không có thông tin deadline
        return False

    def __repr__(self) -> str:
        """Trả về một biểu diễn chuỗi của đối tượng, hữu ích cho việc debug."""
        return f"Scholarship(id={self.document_id}, title='{self.title}')"

    def display(self):
        """In thông tin chi tiết của học bổng ra console một cách dễ đọc."""
        print("="*50)
        print(f"Tiêu đề: {self.title}")
        print(f"ID: {self.document_id}")
        print(f"Loại học bổng: {self.type_info}")
        print(f"Giá trị: {self.total_price}")
        print(f"Số lượng: {self.quantity} suất")
        print(f"Hạn nộp: {self.deadline.strftime('%H:%M:%S %d/%m/%Y') if self.deadline else 'Không có'}")
        print(f"Trạng thái: {'Còn hạn' if self.is_active() else 'Hết hạn'}")
        print(f"Email liên hệ: {self.contact_email or 'Không có'}")
        print("-"*20)
        print("Nội dung chi tiết (văn bản thuần túy):")
        print(self.plain_text_content)
        print("="*50)
        
    def get_full_info_string(self) -> str:
        """
        Trả về một chuỗi duy nhất chứa toàn bộ thông tin chi tiết của học bổng,
        đã được định dạng và lọc các dấu xuống dòng thừa.
        """
        deadline_formatted = self.deadline.strftime('%H:%M:%S %d/%m/%Y') if self.deadline else 'Không có'
        status = 'Còn hạn' if self.is_active() else 'Hết hạn'
        contact = self.contact_email or 'Không có'

        # Ghép các phần thông tin lại
        info_parts = [
            f"Tiêu đề: {self.title}",
            f"ID: {self.document_id}",
            f"Loại học bổng: {self.type_info}",
            f"Giá trị: {self.total_price}",
            f"Số lượng: {self.quantity} suất",
            f"Hạn nộp: {deadline_formatted}",
            f"Trạng thái: {status}",
            f"Email liên hệ: {contact}",
            "--------------------",
            "Nội dung chi tiết:",
            self.plain_text_content
        ]
        
        # Nối các phần tử lại thành một chuỗi duy nhất
        full_string = "\n".join(str(part) for part in info_parts if part is not None)
        
        # Thay thế hai hoặc nhiều dấu xuống dòng liên tiếp bằng một dấu duy nhất
        cleaned_string = re.sub(r'\n{2,}', '\n', full_string)
        
        return cleaned_string.strip()



def crawl_all_scholarships():
    """
    Hàm để crawl toàn bộ danh sách học bổng từ API GetApprovedScholarship
    bằng cách gửi một yêu cầu POST với payload JSON rỗng.

    Returns:
        list: Một danh sách các học bổng, hoặc None nếu có lỗi.
    """
    api_url = "https://ctsv.hust.edu.vn/api-t/HWScholarship/GetApprovedScholarship"

    # Payload là một đối tượng JSON rỗng, dựa trên header được cung cấp
    payload = {}

    # Headers được cập nhật chính xác theo request header bạn cung cấp
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer null',
        'Content-Type': 'application/json',
        'Origin': 'https://ctsv.hust.edu.vn',
        'Referer': 'https://ctsv.hust.edu.vn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    
    print("Đang crawl TẤT CẢ học bổng với header và payload chính xác...")

    try:
        # Gửi yêu cầu POST với tham số `json` để gửi payload dưới dạng JSON
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        return data["ScholarshipLst"] # trả về list các JSON thể hiện thông tin học bổng

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi yêu cầu đến API: {e}")
        return None
    except json.JSONDecodeError:
        print("Lỗi: Không thể phân tích dữ liệu JSON từ phản hồi.")
        return None
    except Exception as e:
        print(f"Đã có lỗi không xác định xảy ra: {e}")
        return None