import os
import uuid
from typing import Optional, Dict
from fastapi import UploadFile


class FileHandler:
    """文件处理工具类，用于处理图片和PDF上传"""
    
    def __init__(self, upload_dir: str = "../data"):
        """
        初始化文件处理器
        
        Args:
            upload_dir: 文件上传目录
        """
        self.upload_dir = upload_dir
        self.images_dir = os.path.join(upload_dir, "images")
        self.pdf_dir = os.path.join(upload_dir, "pdf")
        
        # 创建目录（如果不存在）
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
    
    async def save_file(self, file: UploadFile) -> Dict[str, str]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            Dict[str, str]: 包含文件路径、URL等信息的字典
        """
        file_ext = file.filename.split(".")[-1].lower()
        
        # 根据文件类型选择保存目录
        if file_ext in ["jpg", "jpeg", "png", "gif", "bmp"]:
            save_dir = self.images_dir
            file_type = "image"
        elif file_ext in ["pdf"]:
            save_dir = self.pdf_dir
            file_type = "pdf"
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        # 生成唯一文件名
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(save_dir, file_name)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # 构建文件URL
        file_url = f"/data/{file_type}s/{file_name}"
        
        return {
            "file_path": file_path,
            "file_name": file_name,
            "file_ext": file_ext,
            "file_type": file_type,
            "file_url": file_url,
            "full_url": f"http://localhost:8000{file_url}"
        }
    
    def get_file_path(self, file_name: str, file_type: str) -> Optional[str]:
        """
        根据文件名和类型获取文件路径
        
        Args:
            file_name: 文件名
            file_type: 文件类型 (image/pdf)
            
        Returns:
            Optional[str]: 文件路径，如果文件不存在则返回None
        """
        if file_type == "image":
            file_path = os.path.join(self.images_dir, file_name)
        elif file_type == "pdf":
            file_path = os.path.join(self.pdf_dir, file_name)
        else:
            return None
        
        return file_path if os.path.exists(file_path) else None
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否删除成功
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False