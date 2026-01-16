"""
OCR工具集成
LangChain工具格式
"""
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from src.utils.logger import logger

class OCRInput(BaseModel):
    """OCR工具输入"""
    image_path: str = Field(description="图片路径")
    language: str = Field(default="ch", description="语言代码")
    use_gpu: bool = Field(default=True, description="是否使用GPU")

class OCROutput(BaseModel):
    """OCR工具输出"""
    text: str = Field(description="识别出的文本")
    confidence: float = Field(description="平均置信度")
    layout: Dict[str, Any] = Field(description="布局信息")
    processing_time: float = Field(description="处理时间")

class PaddleOCRTool(BaseTool):
    """PaddleOCR工具"""
    
    name: str = "paddle_ocr"
    description: str = "使用PaddleOCR识别图片中的文字，支持中文、英文等多种语言"
    args_schema: Type[BaseModel] = OCRInput
    return_direct: bool = True
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.engine = None
        
    async def initialize(self):
        """初始化OCR引擎"""
        from paddleocr import PaddleOCR
        
        self.engine = PaddleOCR(
            use_angle_cls=self.config.get("use_angle_cls", True),
            lang=self.config.get("language", "ch"),
            use_gpu=self.config.get("use_gpu", True),
            show_log=False
        )
        
        logger.info("PaddleOCR工具初始化完成")
    
    def _run(
        self,
        image_path: str,
        language: str = "ch",
        use_gpu: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """同步运行"""
        import asyncio
        return asyncio.run(self._arun(image_path, language, use_gpu, run_manager))
    
    async def _arun(
        self,
        image_path: str,
        language: str = "ch",
        use_gpu: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """异步运行"""
        import time
        from PIL import Image
        import numpy as np
        
        if not self.engine:
            await self.initialize()
        
        logger.info(f"运行PaddleOCR: {image_path}")
        start_time = time.time()
        
        try:
            # 读取图片
            image = Image.open(image_path)
            image_np = np.array(image)
            
            # 运行OCR
            result = self.engine.ocr(image_np, cls=True)
            
            # 解析结果
            parsed_result = self._parse_result(result)
            processing_time = time.time() - start_time
            
            output = OCROutput(
                text=parsed_result["text"],
                confidence=parsed_result["confidence"],
                layout=parsed_result["layout"],
                processing_time=processing_time
            )
            
            logger.info(f"PaddleOCR完成, 文本长度: {len(parsed_result['text'])}, 置信度: {parsed_result['confidence']:.2f}")
            
            return output.dict()
            
        except Exception as e:
            error_msg = f"PaddleOCR失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise
    
    def _parse_result(self, result) -> Dict[str, Any]:
        """解析OCR结果"""
        if not result or not result[0]:
            return {
                "text": "",
                "confidence": 0.0,
                "layout": {}
            }
        
        items = []
        texts = []
        confidences = []
        
        for line in result[0]:
            if len(line) >= 2:
                points = line[0]
                bbox = [point for point in points]
                
                text, confidence = line[1]
                
                items.append({
                    "text": text,
                    "bbox": bbox,
                    "confidence": confidence
                })
                
                texts.append(text)
                confidences.append(confidence)
        
        # 计算平均置信度
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 提取布局
        layout = self._extract_layout(items)
        
        return {
            "text": "\n".join(texts),
            "confidence": avg_confidence,
            "layout": layout
        }
    
    def _extract_layout(self, items: List[Dict]) -> Dict[str, Any]:
        """提取布局信息"""
        if not items:
            return {}
        
        all_x1 = [item["bbox"][0][0] for item in items]
        all_y1 = [item["bbox"][0][1] for item in items]
        all_x2 = [item["bbox"][2][0] for item in items]
        all_y2 = [item["bbox"][2][1] for item in items]
        
        return {
            "bounding_box": {
                "x1": min(all_x1),
                "y1": min(all_y1),
                "x2": max(all_x2),
                "y2": max(all_y2)
            },
            "item_count": len(items),
            "text_blocks": self._group_into_text_blocks(items)
        }
    
    def _group_into_text_blocks(self, items: List[Dict]) -> List[Dict]:
        """将项目分组为文本块"""
        if not items:
            return []
        
        # 按Y坐标排序
        items.sort(key=lambda x: x["bbox"][0][1])
        
        blocks = []
        current_block = []
        y_threshold = 20
        
        for item in items:
            if not current_block:
                current_block.append(item)
            else:
                last_item = current_block[-1]
                y_diff = abs(item["bbox"][0][1] - last_item["bbox"][0][1])
                
                if y_diff < y_threshold:
                    current_block.append(item)
                else:
                    blocks.append(current_block)
                    current_block = [item]
        
        if current_block:
            blocks.append(current_block)
        
        # 转换块格式
        formatted_blocks = []
        for block in blocks:
            formatted_blocks.append({
                "items": block,
                "text": " ".join([item["text"] for item in block]),
                "bbox": self._calculate_block_bbox(block)
            })
        
        return formatted_blocks
    
    def _calculate_block_bbox(self, items: List[Dict]) -> List[float]:
        """计算块的边界框"""
        all_x1 = [item["bbox"][0][0] for item in items]
        all_y1 = [item["bbox"][0][1] for item in items]
        all_x2 = [item["bbox"][2][0] for item in items]
        all_y2 = [item["bbox"][2][1] for item in items]
        
        return [
            min(all_x1), min(all_y1),
            max(all_x2), max(all_y2)
        ]