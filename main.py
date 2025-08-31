from mcp.scholarship import *
from mcp.rag import *
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

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

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """Endpoint để nhận câu hỏi và trả lời."""
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Vui lòng nhập câu hỏi.")
        
        return {"answer": get_response(request.question)}
    except Exception as e:
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
    
import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
