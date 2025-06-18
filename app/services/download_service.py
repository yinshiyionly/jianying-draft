import os
import asyncio
import time
import multiprocessing
import threading
import signal
import aiohttp
import traceback
import json
from typing import Optional, Dict, Any, List, Callable, Tuple
from datetime import datetime
from queue import Queue
import uuid
import logging

from ..utils.logger import service_logger
from ..models.download_task import DownloadTask
from ..models.user import User
from ..config import settings


class DownloadProcess(multiprocessing.Process):
    """下载进程类，用于在单独进程中处理下载任务"""
    
    def __init__(self, task_id: int, file_url: str, file_path: str, 
                 downloaded_size: int = 0, pipe_conn=None):
        """初始化下载进程
        
        Args:
            task_id: 任务ID
            file_url: 文件URL
            file_path: 保存路径
            downloaded_size: 已下载大小，用于断点续传
            pipe_conn: 管道连接，用于和主进程通信
        """
        super().__init__()
        self.task_id = task_id
        self.file_url = file_url
        self.file_path = file_path
        self.downloaded_size = downloaded_size
        self.pipe_conn = pipe_conn
        self.daemon = True  # 设置为守护进程
        self.stop_event = multiprocessing.Event()
        self.pause_event = multiprocessing.Event()
        
    def run(self):
        """进程运行入口"""
        try:
            # 设置信号处理
            signal.signal(signal.SIGTERM, self.handle_terminate)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # 执行下载
            self.download_file()
            
        except Exception as e:
            error_msg = f"下载进程异常: {str(e)}\n{traceback.format_exc()}"
            self.send_status("error", error_msg)
            
    def handle_terminate(self, signum, frame):
        """处理终止信号"""
        self.stop_event.set()
        
    def send_progress(self, downloaded_size, file_size=None):
        """发送进度信息到主进程
        
        Args:
            downloaded_size: 已下载大小
            file_size: 文件总大小，可选
        """
        if self.pipe_conn:
            data = {
                "type": "progress",
                "task_id": self.task_id,
                "downloaded_size": downloaded_size
            }
            if file_size is not None:
                data["file_size"] = file_size
                
            self.pipe_conn.send(json.dumps(data))
            
    def send_status(self, status, message=""):
        """发送状态信息到主进程
        
        Args:
            status: 状态名称
            message: 状态详细信息
        """
        if self.pipe_conn:
            data = {
                "type": "status",
                "task_id": self.task_id,
                "status": status,
                "message": message
            }
            self.pipe_conn.send(json.dumps(data))
            
    def download_file(self):
        """执行文件下载"""
        import requests
        
        self.send_status("downloading", "开始下载")
        
        # 配置请求头，支持断点续传
        headers = {}
        if self.downloaded_size > 0:
            headers['Range'] = f'bytes={self.downloaded_size}-'
            
        try:
            # 创建会话对象
            session = requests.Session()
            
            # 发送请求
            response = session.get(
                self.file_url, 
                headers=headers,
                stream=True,
                timeout=settings.DOWNLOAD_TIMEOUT
            )
            
            if response.status_code not in [200, 206]:
                error_msg = f"下载失败，HTTP状态码: {response.status_code}"
                self.send_status("error", error_msg)
                return
            
            # 获取文件总大小
            file_size = int(response.headers.get('Content-Length', 0))
            if file_size > 0:
                total_size = self.downloaded_size + file_size
                self.send_progress(self.downloaded_size, total_size)
            else:
                # 如果服务器未返回内容长度
                total_size = None
                
            # 打开文件准备写入
            file_mode = 'ab' if self.downloaded_size > 0 else 'wb'
            with open(self.file_path, file_mode) as f:
                downloaded = self.downloaded_size
                chunk_size = settings.DOWNLOAD_CHUNK_SIZE
                last_update_time = time.time()
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    # 检查是否需要停止
                    if self.stop_event.is_set():
                        self.send_status("canceled", "下载已取消")
                        return
                        
                    # 检查是否需要暂停
                    if self.pause_event.is_set():
                        self.send_status("paused", "下载已暂停")
                        # 等待恢复信号
                        while self.pause_event.is_set() and not self.stop_event.is_set():
                            time.sleep(0.1)
                            
                        if self.stop_event.is_set():
                            self.send_status("canceled", "下载已取消")
                            return
                            
                        self.send_status("downloading", "下载已恢复")
                    
                    if chunk:  # 过滤空数据块
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 定期更新进度
                        current_time = time.time()
                        if current_time - last_update_time >= 0.3:  # 每0.3秒更新一次
                            self.send_progress(downloaded, total_size)
                            last_update_time = current_time
            
            # 下载完成
            self.send_progress(downloaded, downloaded)
            self.send_status("completed", "下载完成")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求错误: {str(e)}"
            self.send_status("error", error_msg)
        except Exception as e:
            error_msg = f"下载错误: {str(e)}\n{traceback.format_exc()}"
            self.send_status("error", error_msg)


class DownloadService:
    """高级下载服务类，负责处理下载任务的业务逻辑"""
    
    def __init__(self):
        """初始化下载服务"""
        self.logger = service_logger
        self.active_downloads = {}  # {task_id: 进程和管道信息}
        self.progress_callbacks = []  # 进度回调函数列表
        self.status_callbacks = []  # 状态回调函数列表
        
        # 默认下载目录
        self.default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "jy_draft")
        os.makedirs(self.default_download_dir, exist_ok=True)
        
        # 启动消息处理线程
        self.message_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.message_thread.start()
    
    def register_progress_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        """注册进度回调函数
        
        Args:
            callback: 回调函数，接收任务对象作为参数
        """
        self.progress_callbacks.append(callback)
    
    def register_status_callback(self, callback: Callable[[DownloadTask, str], None]) -> None:
        """注册状态回调函数
        
        Args:
            callback: 回调函数，接收任务对象和状态描述作为参数
        """
        self.status_callbacks.append(callback)
    
    def _notify_progress(self, task: DownloadTask) -> None:
        """通知进度回调
        
        Args:
            task: 下载任务
        """
        for callback in self.progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                self.logger.error(f"进度回调错误: {str(e)}")
    
    def _notify_status(self, task: DownloadTask, status_message: str) -> None:
        """通知状态回调
        
        Args:
            task: 下载任务
            status_message: 状态描述
        """
        for callback in self.status_callbacks:
            try:
                callback(task, status_message)
            except Exception as e:
                self.logger.error(f"状态回调错误: {str(e)}")
    
    def _process_messages(self):
        """处理来自下载进程的消息"""
        while True:
            try:
                # 检查所有活动下载的管道
                for task_id, download_info in list(self.active_downloads.items()):
                    pipe_conn = download_info.get('pipe_conn')
                    
                    if pipe_conn and pipe_conn.poll():
                        # 有消息可读
                        try:
                            message = pipe_conn.recv()
                            self._handle_download_message(json.loads(message))
                        except (EOFError, json.JSONDecodeError) as e:
                            self.logger.error(f"读取下载进程消息错误: {str(e)}")
                
                # 清理已完成的进程
                self._cleanup_finished_processes()
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"消息处理线程异常: {str(e)}\n{traceback.format_exc()}")
                time.sleep(1)  # 出错后稍长休眠
    
    def _handle_download_message(self, message):
        """处理下载进程发送的消息
        
        Args:
            message: 消息字典
        """
        msg_type = message.get('type')
        task_id = message.get('task_id')
        
        if not task_id:
            return
            
        task = DownloadTask.get_by_id(task_id)
        if not task:
            self.logger.error(f"无法找到任务: {task_id}")
            return
            
        if msg_type == 'progress':
            # 处理进度更新
            downloaded_size = message.get('downloaded_size', 0)
            file_size = message.get('file_size')
            
            task.update_progress(downloaded_size, file_size)
            self._notify_progress(task)
            
        elif msg_type == 'status':
            # 处理状态更新
            status = message.get('status')
            status_message = message.get('message', '')
            
            if status == 'downloading':
                task.status = DownloadTask.STATUS_DOWNLOADING
                task.save()
            elif status == 'completed':
                task.mark_as_completed()
                # 完成后清理资源
                self._cleanup_download(task_id)
            elif status == 'paused':
                task.mark_as_paused()
            elif status == 'canceled':
                task.mark_as_canceled()
                # 取消后清理资源
                self._cleanup_download(task_id)
            elif status == 'error':
                task.mark_as_failed(status_message)
                # 错误后清理资源
                self._cleanup_download(task_id)
                
            self._notify_status(task, status_message)
    
    def _cleanup_download(self, task_id):
        """清理下载资源
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.active_downloads:
            download_info = self.active_downloads[task_id]
            process = download_info.get('process')
            pipe_conn = download_info.get('pipe_conn')
            
            # 关闭管道
            if pipe_conn:
                try:
                    pipe_conn.close()
                except:
                    pass
            
            # 清理进程
            if process and process.is_alive():
                try:
                    process.terminate()
                except:
                    pass
            
            # 从活动下载中移除
            del self.active_downloads[task_id]
    
    def _cleanup_finished_processes(self):
        """清理已完成的进程"""
        for task_id, download_info in list(self.active_downloads.items()):
            process = download_info.get('process')
            if process and not process.is_alive():
                self._cleanup_download(task_id)
    
    async def create_download_task(
        self, 
        file_url: str, 
        task_name: str = None, 
        file_path: str = None, 
        user_id: Optional[int] = None
    ) -> DownloadTask:
        """创建下载任务
        
        Args:
            file_url: 文件URL
            task_name: 任务名称，默认使用URL中的文件名
            file_path: 保存路径，默认使用默认下载目录
            user_id: 用户ID
            
        Returns:
            DownloadTask: 创建的任务对象
            
        Raises:
            ValueError: URL为空或无效
        """
        if not file_url:
            raise ValueError("文件URL不能为空")
        
        # 从URL中提取文件名
        filename = os.path.basename(file_url.split('?')[0])
        if not filename:
            filename = f"download_{int(time.time())}"
        
        # 设置任务名称
        if not task_name:
            task_name = filename
        
        # 设置保存路径
        if not file_path:
            file_path = os.path.join(self.default_download_dir, filename)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 检查是否已存在相同URL的任务
        existing_task = DownloadTask.get_by_url(file_url, user_id)
        
        if existing_task:
            # 如果任务已完成或失败，可以重新开始
            if existing_task.status in [DownloadTask.STATUS_COMPLETED, DownloadTask.STATUS_FAILED, DownloadTask.STATUS_CANCELED]:
                existing_task.status = DownloadTask.STATUS_PENDING
                existing_task.downloaded_size = 0
                existing_task.error_message = None
                existing_task.file_path = file_path
                existing_task.save()
                return existing_task
            else:
                # 任务正在进行中
                return existing_task
        
        # 创建新任务
        task = DownloadTask()
        task.file_url = file_url
        task.task_name = task_name
        task.file_path = file_path
        task.user_id = user_id
        task.status = DownloadTask.STATUS_PENDING
        task.save()
        
        self.logger.info(f"创建下载任务: {task.id}, URL: {file_url}")
        self._notify_status(task, "任务已创建")
        
        return task
    
    async def start_download(self, task_id: int) -> None:
        """开始下载任务
        
        Args:
            task_id: 任务ID
            
        Raises:
            ValueError: 任务不存在或无法开始
        """
        task = DownloadTask.get_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 检查任务状态
        if task.status == DownloadTask.STATUS_DOWNLOADING:
            self.logger.info(f"任务已在下载中: {task_id}")
            return
        
        # 检查是否已经在活动下载列表中
        if task_id in self.active_downloads:
            download_info = self.active_downloads[task_id]
            process = download_info.get('process')
            
            if process and process.is_alive():
                # 如果处于暂停状态，恢复下载
                if task.status == DownloadTask.STATUS_PAUSED:
                    pause_event = download_info.get('pause_event')
                    if pause_event:
                        pause_event.clear()  # 清除暂停标志
                        
                        # 更新任务状态
                        task.status = DownloadTask.STATUS_DOWNLOADING
                        task.save()
                        
                        self.logger.info(f"恢复下载任务: {task_id}")
                        self._notify_status(task, "恢复下载")
                return
        
        # 更新任务状态
        if task.status != DownloadTask.STATUS_PAUSED:
            task.downloaded_size = 0
            
        task.status = DownloadTask.STATUS_DOWNLOADING
        task.save()
        
        # 创建管道用于进程间通信
        parent_conn, child_conn = multiprocessing.Pipe()
        
        # 创建和启动下载进程
        stop_event = multiprocessing.Event()
        pause_event = multiprocessing.Event()
        
        process = DownloadProcess(
            task_id=task.id,
            file_url=task.file_url,
            file_path=task.file_path,
            downloaded_size=task.downloaded_size,
            pipe_conn=child_conn
        )
        process.stop_event = stop_event
        process.pause_event = pause_event
        process.start()
        
        # 添加到活动下载列表
        self.active_downloads[task_id] = {
            'process': process,
            'pipe_conn': parent_conn,
            'stop_event': stop_event,
            'pause_event': pause_event,
            'start_time': time.time()
        }
        
        self.logger.info(f"开始下载任务: {task_id}, URL: {task.file_url}")
        self._notify_status(task, "开始下载")
    
    def pause_download(self, task_id: int) -> None:
        """暂停下载任务
        
        Args:
            task_id: 任务ID
            
        Raises:
            ValueError: 任务不存在或无法暂停
        """
        task = DownloadTask.get_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        if task.status != DownloadTask.STATUS_DOWNLOADING:
            self.logger.info(f"任务未在下载中，无法暂停: {task_id}")
            return
        
        # 设置暂停标志
        if task_id in self.active_downloads:
            download_info = self.active_downloads[task_id]
            pause_event = download_info.get('pause_event')
            
            if pause_event:
                pause_event.set()  # 设置暂停标志
                
        self.logger.info(f"暂停下载任务: {task_id}")
        self._notify_status(task, "正在暂停下载")
    
    def resume_download(self, task_id: int) -> None:
        """恢复下载任务
        
        Args:
            task_id: 任务ID
            
        Raises:
            ValueError: 任务不存在或无法恢复
        """
        task = DownloadTask.get_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        if not task.can_resume:
            self.logger.info(f"任务无法恢复: {task_id}, 当前状态: {task.status}")
            return
        
        # 如果任务在活动下载列表中且被暂停，直接恢复
        if task_id in self.active_downloads and task.status == DownloadTask.STATUS_PAUSED:
            download_info = self.active_downloads[task_id]
            process = download_info.get('process')
            pause_event = download_info.get('pause_event')
            
            if process and process.is_alive() and pause_event:
                pause_event.clear()  # 清除暂停标志
                
                # 更新任务状态
                task.status = DownloadTask.STATUS_DOWNLOADING
                task.save()
                
                self.logger.info(f"恢复下载任务: {task_id}")
                self._notify_status(task, "恢复下载")
                return
        
        # 如果任务不在活动下载列表中或进程已结束，重新启动下载
        task.resume()
        self.logger.info(f"重新启动下载任务: {task_id}")
        self._notify_status(task, "重新启动下载")
        
        # 启动下载任务
        asyncio.create_task(self.start_download(task_id))
    
    def cancel_download(self, task_id: int) -> None:
        """取消下载任务
        
        Args:
            task_id: 任务ID
            
        Raises:
            ValueError: 任务不存在
        """
        task = DownloadTask.get_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 设置停止标志
        if task_id in self.active_downloads:
            download_info = self.active_downloads[task_id]
            stop_event = download_info.get('stop_event')
            
            if stop_event:
                stop_event.set()  # 设置停止标志
        else:
            # 如果不在活动下载中，直接更新状态
            task.mark_as_canceled()
            self.logger.info(f"取消下载任务: {task_id}")
            self._notify_status(task, "下载已取消")
    
    def delete_task(self, task_id: int, delete_file: bool = False) -> None:
        """删除下载任务
        
        Args:
            task_id: 任务ID
            delete_file: 是否同时删除已下载的文件
            
        Raises:
            ValueError: 任务不存在
        """
        task = DownloadTask.get_by_id(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 如果任务正在下载，先取消下载
        if task.status == DownloadTask.STATUS_DOWNLOADING:
            self.cancel_download(task_id)
        
        # 删除文件
        if delete_file and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
                self.logger.info(f"删除文件: {task.file_path}")
            except Exception as e:
                self.logger.error(f"删除文件失败: {task.file_path}, 错误: {str(e)}")
        
        # 删除任务
        task.delete()
        self.logger.info(f"删除下载任务: {task_id}")
        self._notify_status(task, "任务已删除")
    
    def get_all_tasks(self, user_id: Optional[int] = None) -> List[DownloadTask]:
        """获取所有下载任务
        
        Args:
            user_id: 用户ID，可选
            
        Returns:
            List[DownloadTask]: 任务列表
        """
        if user_id:
            return DownloadTask.get_by_user(user_id)
        else:
            return DownloadTask.get_all()
    
    def get_active_tasks(self) -> List[DownloadTask]:
        """获取正在进行的下载任务
        
        Returns:
            List[DownloadTask]: 活动任务列表
        """
        return DownloadTask.get_active_tasks()
    
    def get_task_by_id(self, task_id: int) -> Optional[DownloadTask]:
        """通过ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[DownloadTask]: 任务对象，不存在则返回None
        """
        return DownloadTask.get_by_id(task_id)
    
    def set_download_directory(self, directory: str) -> None:
        """设置默认下载目录
        
        Args:
            directory: 目录路径
            
        Raises:
            ValueError: 目录无效
        """
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except:
                raise ValueError(f"无法创建目录: {directory}")
        
        self.default_download_dir = directory
        self.logger.info(f"设置默认下载目录: {directory}")
    
    def get_download_speed(self, task_id: int) -> float:
        """获取下载速度 (bytes/s)
        
        Args:
            task_id: 任务ID
            
        Returns:
            float: 下载速度 (bytes/s)
        """
        if task_id not in self.active_downloads:
            return 0
            
        download_info = self.active_downloads[task_id]
        start_time = download_info.get('start_time', 0)
        
        task = DownloadTask.get_by_id(task_id)
        if not task or task.status != DownloadTask.STATUS_DOWNLOADING:
            return 0
            
        elapsed = time.time() - start_time
        if elapsed <= 0:
            return 0
            
        return task.downloaded_size / elapsed
    
    def get_download_status(self, task_id: int) -> Dict[str, Any]:
        """获取下载状态详细信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        task = DownloadTask.get_by_id(task_id)
        if not task:
            return {}
            
        result = {
            "status": task.status,
            "progress": task.progress,
            "downloaded_size": task.downloaded_size,
            "file_size": task.file_size,
            "is_active": task_id in self.active_downloads
        }
        
        if task.status == DownloadTask.STATUS_DOWNLOADING:
            result["speed"] = self.get_download_speed(task_id)
            
        return result
        
    def cleanup(self):
        """清理所有下载任务和资源"""
        # 停止所有活动下载
        for task_id, download_info in list(self.active_downloads.items()):
            process = download_info.get('process')
            stop_event = download_info.get('stop_event')
            
            if stop_event:
                stop_event.set()
                
            if process and process.is_alive():
                try:
                    process.join(0.5)  # 等待进程结束
                    if process.is_alive():
                        process.terminate()  # 强制终止
                except:
                    pass
                    
        # 清空活动下载列表
        self.active_downloads.clear()


# 创建单例实例
download_service = DownloadService() 