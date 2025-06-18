import json
import uuid
import time
import shutil
from pathlib import Path
from datetime import datetime

def create_backup(original_path):
    """创建备份文件"""
    if not Path(original_path).exists():
        return  # 如果原文件不存在，不需要备份
    
    backup_dir = Path(original_path).parent
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{Path(original_path).stem}_backup_{timestamp}.json"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(original_path, backup_path)
    print(f"已创建备份文件: {backup_path}")

def apply_template_and_update_meta(template_path, meta_info_path, project_name, project_path):
    """
    应用模板并更新元信息文件
    
    :param template_path: 模板JSON文件路径
    :param meta_info_path: root_meta_info.json文件路径
    :param project_name: 新项目的名称
    :param project_path: 新项目的路径
    """
    # 1. 创建备份
    create_backup(meta_info_path)
    
    # 2. 读取并更新模板
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    # 计算新值
    new_id = str(uuid.uuid4()).upper()
    current_time = int(time.time() * 1000000)  # 微秒时间戳
    
    # 使用pathlib处理路径，确保格式正确
    project_folder = Path(project_path).resolve()
    project_root = project_folder.parent
    
    # 更新模板字段（使用pathlib的as_posix()生成斜杠一致的路径）
    updates = {
        "draft_cover": (project_folder / "draft_cover.jpg").as_posix(),
        "draft_fold_path": project_folder.as_posix(),
        "draft_id": new_id,
        "draft_json_file": (project_folder / "draft_content.json").as_posix(),
        "draft_name": project_name,
        "draft_root_path": project_root.as_posix(),
        "draft_timeline_materials_size": 0,
        "tm_draft_create": current_time,
        "tm_draft_modified": current_time,
        "tm_duration": 0
    }
    template.update(updates)
    
    # 3. 读取并更新元信息文件
    try:
        with open(meta_info_path, 'r+', encoding='utf-8') as f:
            meta_info = json.load(f)
            
            # 添加到 all_draft_store
            if 'all_draft_store' not in meta_info:
                meta_info['all_draft_store'] = []
            meta_info['all_draft_store'].append(template)
            
            # draft_ids 加1
            if 'draft_ids' in meta_info:
                meta_info['draft_ids'] += 1
            else:
                meta_info['draft_ids'] = 1
            
            # 写回文件
            f.seek(0)
            json.dump(meta_info, f, ensure_ascii=False, indent=4)
            f.truncate()
    except Exception as e:
        print(f"更新元信息文件时出错: {e}")
        raise
    
    return new_id

# 使用示例
if __name__ == "__main__":
    # root_meta_info 中 all_draft_store 数组中的一项-模板json文件
    template_path = "C:/Users/eleven/Desktop/jy-draft/template/root_meta_item_template.json"
    # 剪映草稿箱json文件
    meta_info_path = "C:/Users/eleven/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft/root_meta_info.json"
    
    # 新项目信息
    project_name = "0617"
    project_path = "C:/Users/eleven/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft/" + project_name
    
    try:
        # 应用模板并更新
        new_draft_id = apply_template_and_update_meta(
            template_path,
            meta_info_path,
            project_name,
            project_path
        )
        
        print(f"新项目已创建，ID: {new_draft_id}")
    except Exception as e:
        print(f"程序执行失败: {e}")