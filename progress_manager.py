import threading
import time
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProgressInfo:
    task_id: str
    status: TaskStatus
    current_step: int
    total_steps: int
    current_item: int
    total_items: int
    message: str
    start_time: float
    
    @property
    def progress_percentage(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.current_item / self.total_items) * 100

class ProgressManager:
    """进度管理器 - 跟踪CSV生成进度"""
    
    def __init__(self):
        self._progress_data: Dict[str, ProgressInfo] = {}
        self._lock = threading.Lock()
    
    def start_task(self, task_id: str, total_items: int = 0) -> None:
        """开始新任务"""
        with self._lock:
            self._progress_data[task_id] = ProgressInfo(
                task_id=task_id,
                status=TaskStatus.PENDING,
                current_step=0,
                total_steps=5,  # 下载、解压、处理、生成、完成
                current_item=0,
                total_items=total_items,
                message="任务开始",
                start_time=time.time()
            )
    
    def update_progress(self, task_id: str, status: TaskStatus, 
                       current_step: int = None, current_item: int = None, 
                       total_items: int = None, message: str = None) -> None:
        """更新任务进度"""
        with self._lock:
            if task_id not in self._progress_data:
                return
            
            progress = self._progress_data[task_id]
            progress.status = status
            
            if current_step is not None:
                progress.current_step = current_step
            if current_item is not None:
                progress.current_item = current_item
            if total_items is not None:
                progress.total_items = total_items
            if message is not None:
                progress.message = message
    
    def get_progress(self, task_id: str) -> Optional[ProgressInfo]:
        """获取任务进度"""
        with self._lock:
            return self._progress_data.get(task_id)
    
    def complete_task(self, task_id: str, success: bool = True, message: str = None) -> None:
        """完成任务"""
        with self._lock:
            if task_id not in self._progress_data:
                return
            
            progress = self._progress_data[task_id]
            progress.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            progress.current_step = progress.total_steps
            progress.current_item = progress.total_items
            if message:
                progress.message = message
    
    def cleanup_task(self, task_id: str) -> None:
        """清理完成的任务（可选，用于内存管理）"""
        with self._lock:
            self._progress_data.pop(task_id, None)

# 全局进度管理器实例
progress_manager = ProgressManager()
