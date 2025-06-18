# 素材草稿助手

一个基于PyQt6的素材草稿管理工具，支持高级文件下载功能。

## 主要功能

- 素材草稿管理
- 高级文件下载功能（支持进度条、断点续传、暂停/恢复）
- 用户认证和管理

## 技术栈

- Python 3.8+
- PyQt6 (GUI框架)
- SQLite (本地数据库)

## 安装和运行

### 依赖安装

```bash
pip install -r requirements.txt
```

### 运行主程序

```bash
python main.py
```

### 测试下载功能

```bash
python demo/test_download.py
```

## 下载服务使用说明

下载服务是本应用的核心功能之一，提供了高级的文件下载功能，包括：

1. 支持异步子进程下载，不阻塞主UI线程
2. 实时显示下载进度
3. 支持断点续传
4. 支持暂停/恢复下载
5. 支持取消下载
6. 支持下载进度回调，方便与UI集成

### 基本使用

```python
from app.services.download_service import DownloadService

# 初始化下载服务
download_service = DownloadService()

# 创建下载任务
task = await download_service.create_download_task(
    file_url="https://example.com/file.zip",
    task_name="示例文件",  # 可选，默认使用文件名
    file_path="/path/to/save/file.zip"  # 可选，默认使用默认下载目录
)

# 开始下载
await download_service.start_download(task.id)

# 暂停下载
download_service.pause_download(task.id)

# 恢复下载
download_service.resume_download(task.id)

# 取消下载
download_service.cancel_download(task.id)

# 删除任务
download_service.delete_task(task.id, delete_file=False)  # delete_file=True 同时删除文件
```

### 注册回调

```python
# 注册进度回调
download_service.register_progress_callback(on_progress_update)

# 注册状态回调
download_service.register_status_callback(on_status_update)

# 回调函数示例
def on_progress_update(task):
    print(f"下载进度: {task.progress:.1f}%")

def on_status_update(task, status_message):
    print(f"下载状态: {status_message}")
```

### 获取下载信息

```python
# 获取所有任务
tasks = download_service.get_all_tasks()

# 获取活动任务
active_tasks = download_service.get_active_tasks()

# 获取任务详细信息
task = download_service.get_task_by_id(task_id)
print(f"任务名称: {task.task_name}")
print(f"进度: {task.progress:.1f}%")
print(f"状态: {task.status_text}")
print(f"已下载: {task.formatted_downloaded}")
print(f"总大小: {task.formatted_size}")

# 获取下载速度
speed = download_service.get_download_speed(task_id)
```

## 项目结构

```
jy-draft/
  - app/                 # 应用程序代码
    - models/            # 数据模型
    - services/          # 服务层
      - api/             # API服务
    - utils/             # 工具类
  - demo/                # 演示和测试程序
  - template/            # 模板文件
  - main.py              # 主程序入口
  - requirements.txt     # 依赖文件
```
