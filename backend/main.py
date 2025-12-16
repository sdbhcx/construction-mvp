from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime

app = FastAPI(
    title="施工进度智能记录与查询系统",
    description="基于多Agent架构的施工记录与查询系统MVP",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型 - 施工记录
class ConstructionRecord(BaseModel):
    project_id: str
    date: str
    activity_type: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: str
    description: Optional[str] = None
    workers_count: Optional[int] = None
    equipment: Optional[str] = None
    issues: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    created_by: Optional[str] = "system"

# 模拟数据库（实际项目中使用PostgreSQL）
construction_records = []

# 上传目录
UPLOAD_DIR = "../data/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "施工进度智能记录与查询系统API"}

# 上传图片并创建施工记录
@app.post("/api/records")
async def create_record(
    record: ConstructionRecord,
    file: Optional[UploadFile] = File(None)
):
    # 处理图片上传
    image_url = None
    if file:
        # 生成唯一文件名
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        image_url = f"/data/images/{file_name}"
    
    # 创建记录
    new_record = {
        "record_id": str(uuid.uuid4()),
        "project_id": record.project_id,
        "date": record.date,
        "activity_type": record.activity_type,
        "quantity": record.quantity,
        "unit": record.unit,
        "location": record.location,
        "description": record.description,
        "workers_count": record.workers_count,
        "equipment": record.equipment,
        "issues": record.issues,
        "image_url": image_url,
        "audio_url": record.audio_url,
        "created_by": record.created_by,
        "created_at": datetime.now().isoformat()
    }
    
    # 保存到模拟数据库
    construction_records.append(new_record)
    
    return {"success": True, "data": new_record}

# 获取施工记录列表
@app.get("/api/records")
async def get_records(
    project_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    activity_type: Optional[str] = Query(None)
):
    filtered_records = construction_records.copy()
    
    # 过滤记录
    if project_id:
        filtered_records = [r for r in filtered_records if r["project_id"] == project_id]
    if date:
        filtered_records = [r for r in filtered_records if r["date"] == date]
    if location:
        filtered_records = [r for r in filtered_records if location in r["location"]]
    if activity_type:
        filtered_records = [r for r in filtered_records if activity_type in r["activity_type"]]
    
    # 按时间倒序排列
    filtered_records.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"success": True, "data": filtered_records}

# 自然语言查询（基础实现）
@app.post("/api/query")
async def natural_language_query(question: str = Query(...)):
    # 基于规则的简单查询处理
    question = question.lower()
    
    # 示例："今天有哪些施工活动？"
    if "今天" in question or "今日" in question:
        today = datetime.now().strftime("%Y-%m-%d")
        today_records = [r for r in construction_records if r["date"] == today]
        return {"success": True, "answer": f"今日施工活动：{[r['activity_type'] for r in today_records]}", "data": today_records}
    
    # 示例："上周浇筑了多少混凝土？"
    elif "混凝土" in question and ("上周" in question or "过去7天" in question):
        # 简单计算（实际项目中需要日期范围查询）
        concrete_records = [r for r in construction_records if "混凝土" in r["activity_type"]]
        total = sum(r.get("quantity", 0) for r in concrete_records)
        return {"success": True, "answer": f"上周混凝土总浇筑量：{total}方", "data": concrete_records}
    
    # 示例："A区最近在做什么？"
    elif "A区" in question or "a区" in question:
        a_records = [r for r in construction_records if "A区" in r["location"] or "a区" in r["location"]]
        a_records.sort(key=lambda x: x["created_at"], reverse=True)
        recent = a_records[:5] if len(a_records) > 5 else a_records
        return {"success": True, "answer": f"A区最近施工活动：{[r['activity_type'] for r in recent]}", "data": recent}
    
    # 示例："最近有什么施工问题？"
    elif "问题" in question or "异常" in question or "故障" in question:
        problem_records = [r for r in construction_records if r.get("issues")]
        problem_records.sort(key=lambda x: x["created_at"], reverse=True)
        return {"success": True, "answer": f"最近施工问题：{[r['issues'] for r in problem_records]}", "data": problem_records}
    
    # 示例："最近7天有多少工人？"
    elif "工人" in question or "人数" in question:
        # 简单计算（实际项目中需要日期范围查询）
        recent_records = construction_records[-7:] if len(construction_records) > 7 else construction_records
        total_workers = sum(r.get("workers_count", 0) for r in recent_records)
        avg_workers = total_workers / len(recent_records) if recent_records else 0
        return {"success": True, "answer": f"最近7天平均工人数量：{avg_workers:.1f}人", "data": recent_records}
    
    else:
        return {"success": True, "answer": "抱歉，我暂时无法理解您的问题，请尝试换一种方式提问。", "data": []}

# 获取统计数据
@app.get("/api/stats")
async def get_stats():
    if not construction_records:
        return {"success": True, "data": {"total_records": 0}}
    
    # 计算统计数据
    total_records = len(construction_records)
    total_concrete = sum(r.get("quantity", 0) for r in construction_records if "混凝土" in r["activity_type"])
    
    # 施工活动类型分布
    activity_types = {}
    for r in construction_records:
        activity = r["activity_type"]
        activity_types[activity] = activity_types.get(activity, 0) + 1
    
    # 近7天平均工人数量
    recent_records = construction_records[-7:] if total_records > 7 else construction_records
    total_workers = sum(r.get("workers_count", 0) for r in recent_records)
    avg_workers = total_workers / len(recent_records) if recent_records else 0
    
    # 问题记录数量
    problem_count = len([r for r in construction_records if r.get("issues")])
    
    return {
        "success": True,
        "data": {
            "total_records": total_records,
            "total_concrete": total_concrete,
            "activity_types": activity_types,
            "avg_workers_7d": avg_workers,
            "problem_count": problem_count
        }
    }
