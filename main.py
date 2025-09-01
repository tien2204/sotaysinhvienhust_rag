from mcp.scholarship import *
from mcp.rag import *
from mcp.jobs import *
from mcp.activities import *
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum

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

class JobType(str, Enum):
    hot = "hot"
    new = "new"
    internship = "internship"

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
