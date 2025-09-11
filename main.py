from mcp.scholarship import *
from mcp.rag import *
from mcp.jobs import *
from mcp.activities import *
from utils import preprocess_text
import gtts
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
import io
import uuid # Thêm thư viện uuid để tạo session id
from typing import List, Dict, Optional 
from langchain_core.messages import BaseMessage


app = FastAPI()

# --- BỘ NHỚ LƯU TRỮ CÁC PHIÊN HỘI THOẠI (SESSION STORE) ---
# Đây là một giải pháp đơn giản dùng dictionary.
# Dữ liệu sẽ bị mất khi khởi động lại server.
# Key: session_id (str), Value: list of BaseMessage
conversation_histories: Dict[str, List[BaseMessage]] = {}

# Cho phép CORS để frontend có thể truy cập API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường phát triển, cho phép tất cả các origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    # Client sẽ gửi kèm session_id để duy trì cuộc hội thoại
    session_id: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    # Server sẽ trả về session_id để client dùng cho lần gọi tiếp theo
    session_id: str

class JobType(str, Enum):
    hot = "hot"
    new = "new"
    internship = "internship"
    
class TTSRequest(BaseModel):
    text: str
    speaker_id : int = 1

EXTERNAL_TTS_URL = "https://9721771d4d78.ngrok-free.app"
@app.post("/tts", summary="Tổng hợp văn bản thành giọng nói với logic ưu tiên")
async def text_to_speech(request: TTSRequest):
    """
    Ưu tiên 1: Gọi API TTS ngoài qua Ngrok.
    Ưu tiên 2: Nếu thất bại, dùng gTTS làm phương án dự phòng.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Văn bản không được để trống.")
    # --- ƯU TIÊN 1: THỬ GỌI API BÊN NGOÀI ---
    if EXTERNAL_TTS_URL:
        print(f"--> [Ưu tiên 1] Thử gọi API ngoài: {EXTERNAL_TTS_URL}")
        print(request)
        try:
            external_payload = {"text": preprocess_text(request.text), "speaker_id": request.speaker_id}
            # Đặt timeout hợp lý để không phải chờ quá lâu
            response = requests.post(f"{EXTERNAL_TTS_URL}/tts", json=external_payload, timeout=60)

            # Nếu request thành công (status code 2xx)
            if response.ok:
                print("--> [Ưu tiên 1] Thành công! Trả về audio từ API ngoài.")
                return Response(content=response.content, media_type='audio/wav')
            else:
                # Nếu service trả về lỗi (4xx, 5xx), ghi nhận và chuyển sang gTTS
                print(f"--> [Ưu tiên 1] Thất bại. Status: {response.status_code}. Chuyển sang gTTS.")

        except requests.exceptions.RequestException as e:
            print(f"--> [Ưu tiên 1] Thất bại. Lỗi mạng hoặc timeout: {e}. Chuyển sang gTTS.")

    # --- ƯU TIÊN 2 (DỰ PHÒNG): SỬ DỤNG GTTS ---
    print("--> [Ưu tiên 2] Sử dụng gTTS làm phương án dự phòng.")
    try:
        mp3_fp = io.BytesIO()
        tts = gtts.gTTS(text=request.text, lang='vi')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # gTTS trả về audio/mpeg (MP3)
        return Response(content=mp3_fp.read(), media_type="audio/mpeg")

    except Exception as e:
        print(f"--> [Ưu tiên 2] Lỗi khi tạo audio bằng gTTS: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {str(e)}")
    
@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """
    Endpoint để nhận câu hỏi và trả lời, có duy trì ngữ cảnh hội thoại.
    """
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Vui lòng nhập câu hỏi.")
        
        # --- LOGIC QUẢN LÝ PHIÊN ---
        session_id = request.session_id
        
        # 1. Nếu client không gửi session_id hoặc id không tồn tại, tạo phiên mới.
        if not session_id or session_id not in conversation_histories:
            session_id = str(uuid.uuid4())
            conversation_histories[session_id] = []
            print(f"--- Bắt đầu phiên hội thoại mới: {session_id} ---")

        # 2. Lấy lịch sử hội thoại của phiên hiện tại.
        current_history = conversation_histories[session_id]
        
        # 3. Gọi hàm get_response đã được sửa đổi với câu hỏi và lịch sử.
        final_answer, updated_history = get_response(request.question, current_history)
        
        # 4. Cập nhật lại lịch sử cho phiên này trong bộ nhớ.
        conversation_histories[session_id] = updated_history
        
        # 5. Trả về câu trả lời và session_id cho client.
        return {"answer": final_answer, "session_id": session_id}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
# -------------------------------
# OpenAI-style Chat Completions API
# -------------------------------
from pydantic import Field

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="sotay-llm")
    messages: List[ChatMessage]
    session_id: Optional[str] = None

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Endpoint tương thích OpenAI API (/v1/chat/completions).
    Cho phép các công cụ (như LangChain, OpenAI SDK) gọi trực tiếp.
    """
    try:
        # Lấy hoặc tạo session 
        session_id = request.session_id or str(uuid.uuid4())
        history = conversation_histories.get(session_id, [])

        # Lấy message cuối cùng của user
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        if not user_message:
            raise HTTPException(status_code=400, detail="Không có user message trong request")

        # Gọi LLM (RAG) 
        final_answer, updated_history = get_response(user_message, history)
        conversation_histories[session_id] = updated_history

        # Trả về kết quả theo format OpenAI 
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(uuid.uuid1().time),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": final_answer},
                    "finish_reason": "stop"
                }
            ],
            "session_id": session_id
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/scholarships", response_model=List[dict])
async def get_scholarships():
    """
    Endpoint để lấy danh sách tất cả học bổng.
    """
    try:
        scholarships_data = crawl_all_scholarships()
        if scholarships_data is None:
            raise HTTPException(status_code=500, detail="Không thể crawl dữ liệu học bổng.")
        
        return scholarships_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {str(e)}")

@app.get("/jobs", response_model=List[dict])
async def get_jobs(
    job_type: JobType,
    career: Optional[str] = Query(None, description="Tên chuyên ngành cần lọc, ví dụ: 'công nghệ thông tin'"),
    city: Optional[str] = Query(None, description="Tên tỉnh/thành phố cần lọc, ví dụ: 'Hà Nội'")
):
    """
    Lấy danh sách việc làm, có thể lọc theo chuyên ngành (không phân biệt hoa/thường) và thành phố.
    """
    location_mapping = {"hot": 1, "new": 2, "internship": 3}
    location_code = location_mapping[job_type.value]

    career_id = None
    if career:
        career_id = CAREER_MAP_LOWER.get(career.lower())
        
        if career_id:
            print(f"Đã tìm thấy chuyên ngành '{career}' với ID: {career_id}")
        else:
            print(f"Không tìm thấy chuyên ngành '{career}' trong danh sách.")

    if city and city not in VIETNAM_CITIES:
        raise HTTPException(status_code=400, detail="Tên thành phố không hợp lệ.")
        
    try:
        jobs_data = fetch_jobs(
            location_code=location_code,
            career=career,
            city=city
        )
        if jobs_data is None:
             raise HTTPException(status_code=500, detail="Không thể crawl dữ liệu việc làm.")
        return jobs_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ.")

@app.get("/jobs/careers", response_model=List[str])
async def get_careers():
    """Cung cấp danh sách các chuyên ngành để lọc."""
    return list(CAREER_MAP.keys())

@app.get("/jobs/cities", response_model=List[str])
async def get_cities():
    """Cung cấp danh sách các tỉnh/thành phố để lọc."""
    return VIETNAM_CITIES

@app.get("/activities", response_model=List[dict])
async def get_activities():
    """
    Endpoint để lấy danh sách các hoạt động, sự kiện.
    """
    try:
        activities_data = fetch_activities()
        
        if activities_data is None:
             raise HTTPException(status_code=500, detail="Không thể crawl dữ liệu hoạt động.")
        return activities_data
    except Exception as e:
        print(f"Lỗi tại endpoint /activities: {e}")
        raise HTTPException(status_code=500, detail="Lỗi server nội bộ.")

@app.get("/activities/{activity_id}", response_model=Dict)
async def get_activity_details(activity_id: int):
    """
    Endpoint để lấy thông tin chi tiết của một hoạt động dựa trên ID.
    """
    try:
        details_data = fetch_activity_details(activity_id=activity_id)
        
        if not details_data:
             raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động.")
        return details_data
        
    except Exception as e:
        print(f"Lỗi tại endpoint /activities/{activity_id}: {e}")
        raise HTTPException(status_code=500, detail="Lỗi server nội bộ.")


import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
