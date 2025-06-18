#!/usr/bin/env python3
"""
剪映草稿生成脚本 - 改进版
支持命令行参数配置，具有更好的错误处理和模块化设计
"""

import os
import json
import argparse
import sys
from typing import Dict, List, Any, Optional
import pyJianYingDraft as draft
from pyJianYingDraft import Intro_type, Transition_type, trange, tim


class JianYingDraftGenerator:
    """剪映草稿生成器"""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """
        初始化草稿生成器
        
        Args:
            width: 视频宽度
            height: 视频高度
        """
        self.width = width
        self.height = height
        self.script = None
        
    def create_script(self, has_audio=False, has_video=False, has_text=False, has_voice=False) -> None:
        """
        创建剪映草稿脚本
        
        Args:
            has_audio: 是否需要音频轨道
            has_video: 是否需要视频轨道
            has_text: 是否需要文本轨道
            has_voice: 是否需要配音轨道（包括配音和字幕）
        """
        try:
            self.script = draft.Script_file(self.width, self.height)
            # 根据参数添加相应轨道
            if has_audio:
                self.script.add_track(draft.Track_type.audio, track_name="background")
                print("已添加音频轨道")
            if has_voice:
                self.script.add_track(draft.Track_type.audio, track_name="voice")  # 配音也是音频轨道类型，但单独创建一个轨道
                print("已添加配音轨道")
                # 如果有配音，也添加字幕轨道
                #self.script.add_track(draft.Track_type.subtitle, track_name="subtitle")
                print("已添加字幕轨道")
            if has_video:
                self.script.add_track(draft.Track_type.video)
                print("已添加视频轨道")
            if has_text:
                self.script.add_track(draft.Track_type.text)
                print("已添加文本轨道")
            print(f"成功创建 {self.width}x{self.height} 分辨率的草稿脚本")
        except Exception as e:
            raise RuntimeError(f"创建草稿脚本失败: {e}")
    
    def validate_video_data(self, video_data: Dict[str, Any]) -> bool:
        """
        验证视频数据的有效性
        
        Args:
            video_data: 视频数据字典
            
        Returns:
            bool: 数据是否有效
        """
        required_fields = ['origin_name', 'duration']
        for field in required_fields:
            if field not in video_data:
                print(f"警告: 视频数据缺少必要字段 '{field}': {video_data}")
                return False
        
        # 验证duration是否为有效数字
        try:
            # 新的JSON格式中duration可能是浮点数
            duration = float(video_data['duration'])
            if duration <= 0:
                print(f"警告: 视频时长无效 (duration={duration}): {video_data}")
                return False
        except (ValueError, TypeError):
            print(f"警告: 视频时长格式错误: {video_data}")
            return False
            
        return True
        
    def validate_voice_data(self, voice_data: Dict[str, Any]) -> bool:
        """
        验证配音数据的有效性
        
        Args:
            voice_data: 配音数据字典
            
        Returns:
            bool: 数据是否有效
        """
        required_fields = ['voice_origin_name', 'voice_duration', 'srt_origin_name']
        for field in required_fields:
            if field not in voice_data:
                print(f"警告: 配音数据缺少必要字段 '{field}': {voice_data}")
                return False
        
        # 验证voice_duration是否为有效数字
        try:
            duration = float(voice_data['voice_duration'])
            if duration <= 0:
                print(f"警告: 配音时长无效 (voice_duration={duration}): {voice_data}")
                return False
        except (ValueError, TypeError):
            print(f"警告: 配音时长格式错误: {voice_data}")
            return False
            
        return True
    
    def add_video_segment(self, video_path: str, start_time: str, duration: float, 
                         volume: float = 1.0, add_transition: bool = False) -> Optional[draft.Video_segment]:
        """
        添加视频片段
        
        Args:
            video_path: 视频文件路径
            start_time: 开始时间 (如 "0s")
            duration: 持续时间 (秒)，浮点数
            volume: 音量 (0.0-1.0)
            add_transition: 是否添加转场效果
            
        Returns:
            Video_segment: 创建的视频片段，失败返回None
        """
        try:
            if not os.path.exists(video_path):
                print(f"错误: 视频文件不存在: {video_path}")
                return None
            
            video_material = draft.Video_material(video_path)
            video_segment = draft.Video_segment(
                video_material,
                trange(start_time, f"{duration:.2f}s"),  # 保留2位小数
                volume=volume
            )
            
            # todo 暂不支持转场特效
            # if add_transition:
            #     video_segment.add_transition(Transition_type.信号故障)
            
            self.script.add_segment(video_segment)
            print(f"成功添加视频: {os.path.basename(video_path)}, 开始时间: {start_time}, 时长: {duration}s")
            return video_segment
            
        except Exception as e:
            print(f"错误: 添加视频片段失败 {video_path}: {e}")
            return None
    
    def add_audio_segment(self, audio_path: str, start_time: str, duration: float,
                         volume: float = 1.0) -> Optional[draft.Audio_segment]:
        """
        添加音频片段
        
        Args:
            audio_path: 音频文件路径
            start_time: 开始时间 (如 "0s")
            duration: 持续时间 (秒)，浮点数
            volume: 音量 (0.0-1.0)
            
        Returns:
            Audio_segment: 创建的音频片段，失败返回None
        """
        try:
            if not os.path.exists(audio_path):
                print(f"错误: 音频文件不存在: {audio_path}")
                return None
            
            audio_material = draft.Audio_material(audio_path)
            audio_segment = draft.Audio_segment(
                audio_material,
                trange(start_time, f"{duration:.2f}s"),  # 保留2位小数
                volume=volume
            )
            
            self.script.add_segment(audio_segment)
            print(f"成功添加音频: {os.path.basename(audio_path)}, 开始时间: {start_time}, 时长: {duration}s")
            return audio_segment
            
        except Exception as e:
            print(f"错误: 添加音频片段失败 {audio_path}: {e}")
            return None
    
    def add_text_segment(self, text: str, timerange: Any, font_type: str = "文轩体",
                        color: tuple = (1.0, 1.0, 0.0), position_y: float = -0.8) -> Optional[draft.Text_segment]:
        """
        添加文本片段
        
        Args:
            text: 文本内容
            timerange: 时间范围
            font_type: 字体类型
            color: 文字颜色 RGB
            position_y: Y轴位置
            
        Returns:
            Text_segment: 创建的文本片段，失败返回None
        """
        try:
            text_segment = draft.Text_segment(
                text, timerange,
                font=getattr(draft.Font_type, font_type, draft.Font_type.文轩体),
                style=draft.Text_style(color=color),
                clip_settings=draft.Clip_settings(transform_y=position_y)
            )
            
            # 添加出场动画
            text_segment.add_animation(draft.Text_outro.故障闪动, duration=tim("1s"))
            # 添加文本气泡效果和花字效果 (可选)
            text_segment.add_bubble("361595", "6742029398926430728")
            text_segment.add_effect("7296357486490144036")
            
            self.script.add_segment(text_segment)
            print(f"成功添加文本: {text}")
            return text_segment
            
        except Exception as e:
            print(f"错误: 添加文本片段失败: {e}")
            return None
    
    def process_video_data_list(self, video_data_list: List[Dict], asset_dir: str) -> bool:
        """
        批量处理视频数据列表
        
        Args:
            video_data_list: 视频数据列表
            asset_dir: 素材目录路径
            
        Returns:
            bool: 处理是否成功
        """
        if not video_data_list:
            print("警告: 视频数据列表为空")
            return True
        
        current_start_seconds = 0
        last_video_segment = None
        
        for i, video_data in enumerate(video_data_list):
            if not self.validate_video_data(video_data):
                print(f"跳过无效的视频数据 (第{i+1}个)")
                continue
            
            video_name = video_data['origin_name']
            video_duration = float(video_data['duration'])  # 使用浮点数
            video_path = os.path.join(asset_dir, video_name)
            
            start_time = f"{current_start_seconds}s"
            # add_transition = (i > 0)  # 第一个视频不加转场
            
            video_segment = self.add_video_segment(
                video_path, start_time, video_duration,  # 保留浮点数
                volume=1.0
            )
            
            if video_segment:
                last_video_segment = video_segment
                current_start_seconds += video_duration
            else:
                print(f"跳过失败的视频: {video_name}")
        
        return last_video_segment is not None
    
    def process_audio_data_list(self, audio_data_list: List[Dict], asset_dir: str) -> bool:
        """
        批量处理音频数据列表
        
        Args:
            audio_data_list: 音频数据列表
            asset_dir: 素材目录路径
            
        Returns:
            bool: 处理是否成功
        """
        if not audio_data_list:
            print("提示: 音频数据列表为空，跳过音频处理")
            return True
        
        current_start_seconds = 0
        
        for i, audio_data in enumerate(audio_data_list):
            if not self.validate_video_data(audio_data):  # 复用验证方法
                print(f"跳过无效的音频数据 (第{i+1}个)")
                continue
            
            audio_name = audio_data['origin_name']
            audio_duration = float(audio_data['duration'])  # 使用浮点数
            audio_path = os.path.join(asset_dir, audio_name)
            
            start_time = f"{current_start_seconds}s"
            
            audio_segment = self.add_audio_segment(
                audio_path, start_time, audio_duration, volume=1.0  # 保留浮点数
            )
            
            if audio_segment:
                current_start_seconds += audio_duration
            else:
                print(f"跳过失败的音频: {audio_name}")
        
        return True
        
    def process_voice_data_list(self, voice_data_list: List[Dict], asset_dir: str) -> bool:
        """
        批量处理配音数据列表，包括配音和对应的字幕
        
        Args:
            voice_data_list: 配音数据列表
            asset_dir: 素材目录路径
            
        Returns:
            bool: 处理是否成功
        """
        if not voice_data_list:
            print("提示: 配音数据列表为空，跳过配音处理")
            return True
        
        current_start_seconds = 0
        
        for i, voice_data in enumerate(voice_data_list):
            if not self.validate_voice_data(voice_data):
                print(f"跳过无效的配音数据 (第{i+1}个)")
                continue
            
            # 1. 处理配音文件
            voice_name = voice_data['voice_origin_name']
            voice_duration = float(voice_data['voice_duration'])
            voice_path = os.path.join(asset_dir, voice_name)
            
            start_time = f"{current_start_seconds}s"
            
            # 配音音量可以设置得稍大一些，以便突出配音
            voice_segment = self.add_audio_segment(
                voice_path, start_time, voice_duration, volume=1.2  # 保留浮点数
            )
            
            # 2. 处理字幕文件
            srt_name = voice_data['srt_origin_name']
            srt_path = os.path.join(asset_dir, srt_name)
            
            if os.path.exists(srt_path):
                try:
                    # 导入字幕，使用配音时长作为时间偏移
                    time_offset = f"{current_start_seconds}s"
                    self.script.import_srt(srt_path, track_name="subtitle", time_offset=time_offset)
                    print(f"成功导入字幕: {srt_name}, 时间偏移: {time_offset}")
                except Exception as e:
                    print(f"导入字幕文件失败 {srt_name}: {e}")
            else:
                print(f"警告: 字幕文件不存在: {srt_path}")
            
            if voice_segment:
                current_start_seconds += voice_duration
            else:
                print(f"跳过失败的配音: {voice_name}")
        
        return True
    
    def save_draft(self, output_path: str) -> bool:
        """
        保存草稿到指定路径
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.script:
                raise RuntimeError("草稿脚本未初始化")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            self.script.dump(output_path)
            print(f"草稿已成功保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"错误: 保存草稿失败: {e}")
            return False


def read_json_file(file_path: str, config_name: str) -> Optional[List]:
    """
    从文件读取JSON配置
    
    Args:
        file_path: JSON文件路径
        config_name: 配置名称（用于错误提示）
        
    Returns:
        List: 解析后的列表，失败返回空列表
    """
    if not file_path:
        print(f"提示: {config_name}文件路径为空，将跳过相关处理")
        return []
    
    try:
        if not os.path.exists(file_path):
            print(f"错误: {config_name}文件不存在: {file_path}")
            return []
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            print(f"错误: {config_name}文件内容必须是有效的JSON数组: {file_path}")
            return []
        
        print(f"成功读取 {config_name}文件，包含 {len(data)} 项: {file_path}")
        return data
        
    except json.JSONDecodeError as e:
        print(f"错误: {config_name}文件JSON格式错误: {file_path}: {e}")
        return []
    except Exception as e:
        print(f"错误: 读取{config_name}文件失败: {file_path}: {e}")
        return []


def validate_json_config(json_str: str, config_name: str) -> Optional[List]:
    """
    验证JSON配置字符串的正确性
    
    Args:
        json_str: JSON字符串
        config_name: 配置名称（用于错误提示）
        
    Returns:
        List: 解析后的列表，失败返回空列表
    """
    if not json_str:
        print(f"提示: {config_name}字符串为空，将跳过相关处理")
        return []
    
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            print(f"错误: {config_name}字符串必须是有效的JSON数组")
            return []
        
        print(f"成功解析 {config_name}字符串，包含 {len(data)} 项")
        return data
        
    except json.JSONDecodeError as e:
        print(f"错误: {config_name}字符串JSON格式错误: {e}")
        return []


def validate_paths(dump_path: str, asset_dir: str) -> bool:
    """
    验证路径的有效性
    
    Args:
        dump_path: 输出路径
        asset_dir: 素材目录路径
        
    Returns:
        bool: 路径是否有效
    """
    try:
        # 基本路径检查
        if not dump_path or dump_path.endswith('/') or dump_path.endswith('\\'):
            print(f"错误: 输出路径无效，必须包含文件名: {dump_path}")
            return False
            
        if not asset_dir or not (asset_dir.endswith('/') or asset_dir.endswith('\\')) and not os.path.isdir(asset_dir):
            print(f"错误: 素材目录路径无效: {asset_dir}")
            return False
        
        # 验证素材目录
        if not os.path.exists(asset_dir):
            print(f"错误: 素材目录不存在: {asset_dir}")
            return False
        else:
            print(f"素材目录检查通过: {asset_dir}")
        
        # 验证输出路径的父目录
        dump_dir = os.path.dirname(dump_path)
        if not dump_dir:
            print(f"错误: 输出路径必须包含目录: {dump_path}")
            return False
            
        if dump_dir and not os.path.exists(dump_dir):
            try:
                os.makedirs(dump_dir, exist_ok=True)
                print(f"创建输出目录: {dump_dir}")
            except Exception as e:
                print(f"错误: 无法创建输出目录 {dump_dir}: {e}")
                return False
        
        # 检查输出路径是否可写
        try:
            # 检查目录是否可写
            test_file = os.path.join(dump_dir, '.write_test_temp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            print(f"错误: 输出目录不可写: {dump_dir}: {e}")
            return False
            
        print(f"输出路径检查通过: {dump_path}")
        return True
    except Exception as e:
        print(f"路径验证过程中出现错误: {e}")
        return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="剪映草稿生成脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 从JSON文件读取配置(推荐)
  python jianying-draft-generator.py \\
    --material_dir "C:/素材目录" \\
    --draft_path "C:/jianyingpro/draft/draft_content.json" \\
    --width 1920 \\
    --height 1080 \\
    --video-json-file "video_config.json" \\
    --audio-json-file "audio_config.json" \\
    --voice-json-file "voice_config.json"

  # 查看JSON文件格式示例
  python jianying-draft-generator.py --json-format-examples
  
  # 兼容旧版本：直接使用JSON字符串(不推荐，不方便编辑)
  python jianying-draft-generator.py \\
    --material_dir "C:/素材目录" \\
    --draft_path "C:/jianyingpro/draft/draft_content.json" \\
    --video-json '[{"duration":58.47,"origin_name":"视频1.mp4"}]'
        """
    )
    
    parser.add_argument('--draft_path', required=True,
                      help='输出草稿文件路径 (必需)')
    parser.add_argument('--material_dir', required=True,
                      help='素材目录路径 (必需)')
    parser.add_argument('--width', type=int, default=1920,
                      help='视频宽度 (默认: 1920)')
    parser.add_argument('--height', type=int, default=1080,
                      help='视频高度 (默认: 1080)')
    
    # JSON文件参数
    parser.add_argument('--video-json-file', default='',
                      help='视频片段JSON配置文件路径')
    parser.add_argument('--audio-json-file', default='',
                      help='音频片段JSON配置文件路径')
    parser.add_argument('--voice-json-file', default='',
                      help='配音和字幕片段JSON配置文件路径')
    
    # 保留字符串参数，保证向后兼容性
    parser.add_argument('--video-json', default='',
                      help='视频片段JSON配置字符串（已弃用，请使用--video-json-file）')
    parser.add_argument('--audio-json', default='',
                      help='音频片段JSON配置字符串（已弃用，请使用--audio-json-file）')
    parser.add_argument('--voice-json', default='',
                      help='配音和字幕片段JSON配置字符串（已弃用，请使用--voice-json-file）')
    
    parser.add_argument('--text', default='',
                      help='文本内容 (默认为空)')
    
    # 辅助命令
    parser.add_argument('--json-format-examples', action='store_true',
                      help='显示JSON配置文件格式示例并退出')
    
    return parser.parse_args()


def normalize_path(path: str) -> str:
    """
    规范化文件路径，处理不同操作系统的路径格式
    
    Args:
        path: 原始路径
        
    Returns:
        str: 规范化后的路径
    """
    # 替换反斜杠为正斜杠
    path = path.replace('\\', '/')
    
    # 处理Windows路径中的冒号
    if ':' in path and not path.startswith('/'):
        # Windows路径格式：C:/Users/...
        return path
    
    return path

def print_json_format_examples():
    """打印JSON文件格式示例"""
    print("=" * 80)
    print("JSON文件格式示例:")
    print("=" * 80)
    
    print("\n1. 视频配置文件示例 (video_config.json):")
    print("""[
  {
    "md5": "9e361540cb6601e9a901ad89f77e9796",
    "duration": 58.47,
    "origin_name": "视频片段1.mp4",
    "width": 1080,
    "height": 1920
  },
  {
    "md5": "8a1377d7329ff18d3e0606b404c8fd49",
    "duration": 42.21,
    "origin_name": "视频片段2.mp4",
    "width": 1080,
    "height": 1920
  }
]""")

    print("\n2. 音频配置文件示例 (audio_config.json):")
    print("""[
  {
    "md5": "8a1377d7329ff18d3e0606b404c8fd49",
    "duration": 226.25,
    "origin_name": "背景音乐1.mp3"
  },
  {
    "md5": "7b1377d7329ff18d3e0606b404c8fd48",
    "duration": 185.32,
    "origin_name": "背景音乐2.mp3"
  }
]""")

    print("\n3. 配音配置文件示例 (voice_config.json):")
    print("""[
  {
    "voice_md5": "8a1377d7329ff18d3e0606b404c8fd49",
    "voice_duration": 10.63,
    "voice_origin_name": "配音片段1.wav",
    "srt_origin_name": "字幕片段1.srt"
  },
  {
    "voice_md5": "7b1377d7329ff18d3e0606b404c8fd48",
    "voice_duration": 15.21,
    "voice_origin_name": "配音片段2.wav",
    "srt_origin_name": "字幕片段2.srt"
  }
]""")
    print("=" * 80)
    print("使用以上格式创建相应的JSON文件，然后通过--video-json-file、--audio-json-file、--voice-json-file参数指定文件路径")
    print("=" * 80)
    sys.exit(0)

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 如果指定了显示JSON格式示例，则打印示例并退出
        if args.json_format_examples:
            print_json_format_examples()
            # 函数内部会调用sys.exit(0)，不会继续执行
        
        print("=" * 50)
        print("剪映草稿生成脚本 - 开始执行")
        print("=" * 50)
        
        # 规范化路径
        material_dir = normalize_path(args.material_dir)
        draft_path = normalize_path(args.draft_path)
        
        # 验证路径
        if not validate_paths(draft_path, material_dir):
            return 1
        
        # 尝试从文件读取配置，如果文件路径为空或读取失败则尝试从字符串解析
        # 视频配置
        if args.video_json_file:
            video_data_list = read_json_file(args.video_json_file, "视频配置")
        else:
            video_data_list = validate_json_config(args.video_json, "视频配置")
        
        # 音频配置
        if args.audio_json_file:
            audio_data_list = read_json_file(args.audio_json_file, "音频配置")
        else:
            audio_data_list = validate_json_config(args.audio_json, "音频配置")
        
        # 配音配置
        if args.voice_json_file:
            voice_data_list = read_json_file(args.voice_json_file, "配音配置")
        else:
            voice_data_list = validate_json_config(args.voice_json, "配音配置")
        
        # 确定是否需要各种轨道
        has_audio = bool(audio_data_list)
        has_video = bool(video_data_list)
        has_voice = bool(voice_data_list)
        has_text = bool(args.text and video_data_list)  # 只有当有文本内容且有视频时才添加文本轨道
        
        print(f"视频数据: {len(video_data_list)}项")
        print(f"音频数据: {len(audio_data_list)}项")
        print(f"配音数据: {len(voice_data_list)}项")
        
        # 检查是否有任何媒体数据
        has_any_media = has_audio or has_voice or has_video
        
        if not has_any_media:
            print("警告: 没有任何媒体数据(视频/音频/配音)，不创建草稿")
            return 0
        
        # 创建草稿生成器
        generator = JianYingDraftGenerator(args.width, args.height)
        generator.create_script(has_audio=has_audio, has_video=has_video, has_text=has_text, has_voice=has_voice)
        
        # 处理音频数据
        if has_audio:
            if not generator.process_audio_data_list(audio_data_list, material_dir):
                print("警告: 音频处理出现问题，但继续执行")
        else:
            print("没有音频数据，跳过音频轨道处理")
            
        # 处理配音数据
        if has_voice:
            if not generator.process_voice_data_list(voice_data_list, material_dir):
                print("警告: 配音处理出现问题，但继续执行")
        else:
            print("没有配音数据，跳过配音轨道处理")
        
        # 处理视频数据
        if has_video:
            if not generator.process_video_data_list(video_data_list, material_dir):
                print("错误: 视频处理失败")
                return 1
        else:
            print("没有视频数据，跳过视频轨道处理")
        
        # 添加文本片段 (如果有视频和文本内容)
        if has_text:
            # 计算总时长作为文本时间范围
            total_duration = sum(float(v.get('duration', 0)) for v in video_data_list 
                               if generator.validate_video_data(v))
            if total_duration > 0:
                text_timerange = trange("0s", f"{total_duration:.2f}s")  # 保留两位小数
                generator.add_text_segment(args.text, text_timerange)
        elif args.text and not video_data_list:
            print("有文本内容但没有视频数据，无法添加文本片段")
        
        # 保存草稿
        if not generator.save_draft(draft_path):
            return 1
        
        print("=" * 50)
        print("草稿生成完成!")
        print("=" * 50)
        return 0
        
    except KeyboardInterrupt:
        print("\n用户中断执行")
        return 1
    except Exception as e:
        print(f"未预期的错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())