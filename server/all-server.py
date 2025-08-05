import os
import io
import base64
import json
import time
import threading
import traceback
from queue import Queue
import tempfile
import requests
import jwt
import re
import numpy as np
import cv2
import wave
import tensorflow.lite as tflite
import librosa
import soundfile as sf
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response, session,abort,send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from mysql.connector import Error
import urllib  # 导入整个urllib模块
import uuid
# 在文件顶部的导入区域添加这一行
from werkzeug.middleware.proxy_fix import ProxyFix
from gradio_client import Client, handle_file
import tempfile

from urllib.parse import quote  # 新增导入语句
from urllib.parse import urljoin


# 在现有导入基础上添加以下内容
import websockets
import asyncio
from threading import Thread
import json as json_lib
from datetime import datetime
import aiohttp_wsgi
from aiohttp import web
from urllib.parse import unquote  # 确保导入unquote函数
import sys

import pathlib  # 添加这行导入语句
import mimetypes  # 新增：导入mimetypes模块
# 第三方库可用性检查
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("警告：未安装vosk库，语音识别功能不可用")

try:
    from pydub import AudioSegment, utils
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("警告：未安装pydub库，音频处理功能可能受限")

# 表情识别相关模块检查
try:
    from model import CNN2, CNN3
    from utils import index2emotion
    from blazeface import blaze_detect
    EMOTION_AVAILABLE = True
except ImportError:
    EMOTION_AVAILABLE = False
    print("警告：表情识别识别相关模块缺失，表情识别功能不可用")
    # 初始化Gradio客户端
try:
    lip_sync_client = Client("http://localhost:7860/")
    print("✅ 对口型视频生成服务客户端初始化成功")
except Exception as e:
    lip_sync_client = None
    print(f"❌ 对口型视频生成服务客户端初始化失败: {str(e)}")

# 初始化Flask应用 - 只定义一次
app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域请求并支持凭证
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
app.secret_key = 'your_secret_key'  # 用于session加密

try:
    # 测试能否访问本地服务
    test_response = requests.get("http://localhost:9872", timeout=5)
    print("requests 测试成功，9872 端口可访问")
except Exception as e:
    print("requests 测试失败：", str(e))  # 关键：打印 requests 库的错误
# Ollama 本地服务配置
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5vl:7b"
TEMP_DIR = "D:/Temp/gradio"    # 存储临时文件到 gradio 子目录

# 全局变量
latest_pose_detection = {
    "pose": "等待检测",
    "fps": 0,
    "score": 0
}
emotion_model = None
frame_queue = Queue(maxsize=10)  # 增大队列容量
detection_queue = Queue(maxsize=10)
is_processing = False

# 配置
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
STATE_FOLDER = 'processing_states'
MAX_PROCESS_TIME = 45  # 每个阶段最大处理时间(秒)，小于50秒前端超时
# 创建必要的文件夹
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(STATE_FOLDER, exist_ok=True)

# 处理状态存储
processing_states = {}
state_lock = threading.Lock()

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:2794840873@localhost/blogdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义用户模型
class SqlUser(db.Model):
    __tablename__ = 'sqlusers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    blogs = db.Column(db.Text, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    isLiked = db.Column(db.Text, nullable=True)
    friends = db.Column(db.Text, nullable=True)
    friendsApply = db.Column(db.Text, nullable=True)

# 安全数据转换函数 - 解决float32序列化问题
def convert_to_serializable(obj):
    """将对象转换为JSON可序列化的格式，特别处理numpy类型"""
    if isinstance(obj, np.float32) or isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # 将numpy数组转换为Python列表
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(v) for v in obj]
    else:
        return obj

# 创建数据库连接池
def get_db_connection():
    """创建数据库连接"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='2794840873',
            database='blogdb'
        )
        return connection
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

# ====================== 用户语调提取功能 ======================
def extract_f0(audio_data, sample_rate=16000):
    """提取音频基频F0特征"""
    # 转换为单声道并归一化
    y = audio_data.astype(np.float32)
    y = librosa.to_mono(y)
    y = librosa.util.normalize(y)
    
    # 提取基频F0
    f0, _, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C6'),
        sr=sample_rate
    )
    
    valid_f0 = f0[~np.isnan(f0)]
    if len(valid_f0) == 0:
        return {
            "f0_mean": 0,
            "f0_max": 0,
            "f0_min": 0,
            "tone_type": "静音"
        }
    
    f0_mean = float(np.mean(valid_f0))
    if f0_mean < 100:
        tone_type = "低沉"
    elif f0_mean < 300:
        tone_type = "正常"
    else:
        tone_type = "高亢"
    
    return {
        "f0_mean": round(f0_mean, 1),
        "f0_max": round(float(np.max(valid_f0)), 1),
        "f0_min": round(float(np.min(valid_f0)), 1),
        "tone_type": tone_type
    }

@app.route('/lip_sync/c_res', methods=['POST'])
def lip_sync_c_res():
    """转发到/c_res接口 - 控制是否强制缩小分辨率"""
    try:
        if not lip_sync_client:
            return jsonify({"status": "error", "message": "对口型服务客户端未初始化"}), 503
            
        data = request.json or {}
        value = data.get('value', False)
        
        result = lip_sync_client.predict(
            value=value,
            api_name="/c_res"
        )
        
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"调用/c_res接口失败: {str(e)}"
        }), 500

@app.route('/lip_sync/display_video_path', methods=['POST'])
def lip_sync_display_video_path():
    """转发到/display_video_path接口 - 上传视频并获取地址"""
    try:
        if not lip_sync_client:
            return jsonify({"status": "error", "message": "对口型服务客户端未初始化"}), 503
            
        if 'video' not in request.files:
            return jsonify({"status": "error", "message": "请上传视频文件"}), 400
        
        # 保存上传的视频到临时文件
        video_file = request.files['video']
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            video_file.save(temp_file)
            temp_file_path = temp_file.name
        
        # 调用API
        result = lip_sync_client.predict(
            video={"video": handle_file(temp_file_path)},
            api_name="/display_video_path"
        )
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
        return jsonify({
            "status": "success",
            "video_path": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"调用/display_video_path接口失败: {str(e)}"
        }), 500

@app.route('/lip_sync/display_audio_path', methods=['POST'])
def lip_sync_display_audio_path():
    """转发到/display_audio_path接口 - 上传音频并获取地址"""
    try:
        if not lip_sync_client:
            return jsonify({"status": "error", "message": "对口型服务客户端未初始化"}), 503
            
        if 'audio' not in request.files:
            return jsonify({"status": "error", "message": "请上传音频文件"}), 400
        
        # 保存上传的音频到临时文件
        audio_file = request.files['audio']
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file)
            temp_file_path = temp_file.name
        
        # 调用API
        result = lip_sync_client.predict(
            video=handle_file(temp_file_path),
            api_name="/display_audio_path"
        )
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
        return jsonify({
            "status": "success",
            "audio_path": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"调用/display_audio_path接口失败: {str(e)}"
        }), 500

@app.route('/lip_sync/add_box', methods=['POST'])
def lip_sync_add_box():
    """转发到/add_box接口"""
    try:
        if not lip_sync_client:
            return jsonify({"status": "error", "message": "对口型服务客户端未初始化"}), 503
            
        result = lip_sync_client.predict(
            api_name="/add_box"
        )
        
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"调用/add_box接口失败: {str(e)}"
        }), 500
# 配置
GRADIO_TEMP_DIR = "D:\\Temp\\gradio"
# 允许的文件类型
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wav', 'mp3'}

def allowed_file(filename):
    """检查文件是否为允许的类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_recent_files(since_timestamp, max_files=10):
    """获取指定时间戳之后修改的文件"""
    recent_files = []
    
    # 转换为datetime对象
    since_time = datetime.fromtimestamp(since_timestamp)
    
    # 遍历目录查找文件
    for root, dirs, files in os.walk(GRADIO_TEMP_DIR):
        for file in files:
            if allowed_file(file):
                file_path = os.path.join(root, file)
                try:
                    # 获取文件修改时间
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 检查是否在指定时间之后
                    if modified_time >= since_time:
                        # 计算相对路径（相对于GRADIO_TEMP_DIR）
                        relative_path = os.path.relpath(file_path, GRADIO_TEMP_DIR)
                        recent_files.append({
                            'path': relative_path,
                            'modified_time': modified_time.timestamp(),
                            'name': file,
                            'size': os.path.getsize(file_path)
                        })
                except Exception as e:
                    app.logger.warning(f"检查文件 {file_path} 时出错: {str(e)}")
    
    # 按修改时间排序（最新的在前）
    recent_files.sort(key=lambda x: x['modified_time'], reverse=True)
    
    # 返回前max_files个文件
    return recent_files[:max_files]


@app.route('/proxy_gradio_file/<path:encoded_path>')
def proxy_gradio_file(encoded_path):
    try:
        # 检查是否是查询最近文件的请求
        # 通过特殊路径标识或查询参数来判断
        if encoded_path == 'recent' or request.args.get('action') == 'recent':
            # 获取查询参数，默认为10分钟前
            since = request.args.get('since', default=int((datetime.now() - timedelta(minutes=10)).timestamp()), type=int)
            max_files = request.args.get('max', default=10, type=int)
            
            # 获取最近的文件
            recent_files = get_recent_files(since, max_files)
            
            return jsonify({
                'status': 'success',
                'since': since,
                'count': len(recent_files),
                'files': recent_files
            })
        
        # 正常的文件代理请求
        # 解码路径
        file_path = unquote(encoded_path)
        
        # 构建完整路径
        full_path = os.path.join(GRADIO_TEMP_DIR, file_path)
        
        # 安全检查：只允许访问Gradio的临时目录
        # 处理Windows系统的路径问题
        if sys.platform.startswith('win32'):
            # 统一转换为小写进行比较（Windows路径不区分大小写）
            normalized_path = os.path.normpath(full_path).lower()
            normalized_allowed_dir = os.path.normpath(GRADIO_TEMP_DIR).lower()
        else:
            normalized_path = os.path.normpath(full_path)
            normalized_allowed_dir = os.path.normpath(GRADIO_TEMP_DIR)
        
        # 检查路径是否在允许的目录下
        if not normalized_path.startswith(normalized_allowed_dir):
            app.logger.warning(f"访问被拒绝：路径不在允许范围内 - {normalized_path}")
            return f"访问被拒绝：路径不在允许范围内", 403
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            app.logger.warning(f"文件不存在：{full_path}")
            return f"文件不存在", 404
        
        # 检查是否是文件（不是目录）
        if not os.path.isfile(full_path):
            app.logger.warning(f"请求的路径不是文件：{full_path}")
            return f"请求的路径不是文件", 400
        
        # 检查文件是否可读
        if not os.access(full_path, os.R_OK):
            app.logger.warning(f"没有文件读取权限：{full_path}")
            return f"没有文件读取权限", 403
        
        # 自动检测MIME类型
        filename = os.path.basename(full_path)
        if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            mimetype = 'video/' + filename.rsplit('.', 1)[1].lower()
        elif filename.lower().endswith(('.mp3', '.wav')):
            mimetype = 'audio/' + filename.rsplit('.', 1)[1].lower()
        elif filename.lower().endswith('.txt'):  # 处理TXT文件
            mimetype = 'text/plain'
        else:
            mimetype = 'application/octet-stream'
        
        # 发送文件给前端
        return send_file(
            full_path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        app.logger.error(f"服务器错误：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
@app.route('/lip_sync/process_video', methods=['POST'])
def lip_sync_process_video():
    """转发到/process_video接口 - 处理视频生成对口型效果，自动查找最新音频音频文件，使用固定视频路径"""
    try:
        import os
        import glob
        import time
        import shutil
        import traceback
        
        # 使用绝对路径定位目标目录
        target_dir = "E:\\kuakewangpanxiazai\\heygem\\heygem-win-50\\save\\123"
        print(f"准备处理目标目录: {target_dir}")
        
        # 仅保留清理逻辑，不主动创建目录（由源代码负责创建）
        try:
            # 检查目录是否存在，存在则清理
            if os.path.exists(target_dir):
                print(f"检测到目标目录已存在，开始清理: {target_dir}")
                
                # 处理可能的只读文件或目录
                def handle_remove_readonly(func, path, exc_info):
                    """处理只读文件的删除"""
                    os.chmod(path, 0o777)  # 修改权限为可写
                    func(path)  # 重新尝试删除
                
                # 强制删除目录及内容（为源代码创建目录扫清障碍）
                shutil.rmtree(target_dir, onerror=handle_remove_readonly)
                print(f"成功删除旧目录: {target_dir}")
            
            # 不主动创建目录，由源代码负责创建
            print(f"已清理旧目录，将由源代码创建新目录: {target_dir}")
                
        except Exception as e:
            print(f"处理目录时发生错误: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                "status": "error",
                "message": f"处理目标目录失败: {str(e)}"
            }), 500
        
        if not lip_sync_client:
            return jsonify({"status": "error", "message": "对口型服务客户端未初始化"}), 503
            
        data = request.json
        # 不再检查video_file，而是使用固定视频路径
        # 但仍可检查其他必要参数（如果需要）
        # if not data:
        #     return jsonify({
        #         "status": "error", 
        #         "message": "请求数据不能为空"
        #     }), 400
        
        # 固定视频路径
        video_file = "E:\\juli6seconds.mp4"
        # 检查固定视频文件是否存在
        if not os.path.exists(video_file):
            return jsonify({
                "status": "error", 
                "message": f"固定视频文件不存在: {video_file}"
            }), 400
        print(f"使用固定视频文件: {video_file}")
        
        # 自动查找D:\Temp\中最新产生的文件夹里的音频wav
        temp_dir = "D:\\Temp\\"
        
        # 检查目录是否存在
        if not os.path.exists(temp_dir):
            return jsonify({
                "status": "error", 
                "message": f"目录不存在: {temp_dir}"
            }), 400
        
        # 获取所有子文件夹并按创建时间排序（最新的在前面）
        subfolders = [f.path for f in os.scandir(temp_dir) if f.is_dir()]
        if not subfolders:
            return jsonify({
                "status": "error", 
                "message": f"未找到子文件夹: {temp_dir}"
            }), 400
            
        # 按文件夹创建时间排序（最新的在前）
        subfolders.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # 在最新的文件夹中查找WAV文件
        latest_folder = subfolders[0]
        wav_files = glob.glob(os.path.join(latest_folder, "*.wav"))
        
        if not wav_files:
            return jsonify({
                "status": "error", 
                "message": f"在最新文件夹中未找到WAV文件: {latest_folder}"
            }), 400
            
        # 按创建时间排序WAV文件，取最新的一个
        wav_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        audio_file = wav_files[0]
        
        # 输出调试信息
        print(f"使用最新音频文件: {audio_file}")
        print(f"来自文件夹: {latest_folder}")
        print(f"文件创建时间: {time.ctime(os.path.getctime(audio_file))}")
        
        # 调用API处理视频（由源代码创建目录）
        result = lip_sync_client.predict(
            audio_file=audio_file,
            video_file=video_file,  # 使用固定视频路径
            min_resolution=data.get('min_resolution', 2) if data else 2,
            if_res=data.get('if_res', False) if data else False,
            steps=data.get('steps', 4) if data else 4,
            api_name="/process_video"
        )
        
        # 解析结果
        generated_video, process_time, download_path = result
        
        return jsonify({
            "status": "success",
            "used_audio_file": audio_file,
            "used_video_file": video_file,  # 返回使用的固定视频路径
            "generated_video": generated_video,
            "process_time": process_time,
            "download_path": download_path
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"调用/process_video接口失败: {str(e)}"
        }), 500




BASE_DIR = "D:\\Temp"
@app.route('/proxy_files')  # 修改路径为/proxy_files
def proxy_file():
    try:
        # 从查询参数获取路径，而不是路径参数
        encoded_path = request.args.get('path')
        if not encoded_path:
            abort(400, description="缺少path参数")
            
        # 解码URL中的文件路径
        decoded_path = urllib.parse.unquote(encoded_path)
        
        # 构建完整的文件路径
        full_path = os.path.abspath(decoded_path)
        
        # 安全检查：确保文件在允许的目录内
        if not full_path.startswith(BASE_DIR):
            app.logger.warning(f"安全检查失败：{full_path} 不在允许的目录内")
            abort(403, description="禁止访问：只能访问D:\\Temp目录下的文件")
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            app.logger.warning(f"文件不存在：{full_path}")
            abort(404, description=f"文件不存在：{full_path}")
        
        # 检查是否为文件（不是目录）
        if not os.path.isfile(full_path):
            app.logger.warning(f"不是文件：{full_path}")
            abort(400, description=f"不是文件：{full_path}")
        
        # 根据文件扩展名设置MIME类型
        file_ext = pathlib.Path(full_path).suffix.lower()
        mime_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain'
        }
        mimetype = mime_types.get(file_ext, 'application/octet-stream')
        
        # 发送文件
        app.logger.info(f"成功代理文件：{full_path}")
        return send_file(full_path, mimetype=mimetype)
        
    except Exception as e:
        app.logger.error(f"代理文件出错：{str(e)}")
        abort(500, description=f"服务器错误：{str(e)}")
def analyze_frame(frame_base64, history, gradio_url):
    """分析单帧图像（局部变量：gradio客户端）"""
    try:
        # 局部创建Gradio客户端
        client = Client(gradio_url)
        
        prompt = (
            "请分析图像中人物的："
            "1. 表情（如开心、生气、中性等，包含置信度）；"
            "2. 动作姿态（如坐姿、手势、身体朝向等）；"
            "3. 整体情绪状态判断。"
        )
        
        result = client.predict(
            history=history,
            text=f"[图像数据]: {frame_base64}\n{prompt}",
            api_name="/add_text"
        )
        
        return {
            "success": True,
            "result": result,
            "history": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def process_video_frames(video_data, task_id, gradio_url, temp_dir):
    """处理视频帧（局部变量：路径、配置）"""
    try:
        # 局部定义临时文件路径
        video_path = os.path.join(temp_dir, f"{task_id}.mp4")
        with open(video_path, "wb") as f:
            f.write(video_data)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * 5)
        frames = []
        history = []
        
        count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if count % frame_interval == 0:
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                frames.append(frame_base64)
            count += 1
        cap.release()
        
        analysis_results = []
        for i, frame in enumerate(frames):
            # 传入局部gradio_url参数
            frame_result = analyze_frame(frame, history, gradio_url)
            if frame_result["success"]:
                analysis_results.append({
                    "frame_index": i,
                    "timestamp": f"{i*5}s-{i*5+5}s",
                    "analysis": frame_result["result"]
                })
                history = frame_result["history"]
            else:
                analysis_results.append({
                    "frame_index": i,
                    "error": frame_result["error"]
                })
        
        summary = {
            "total_frames": len(frames),
            "dominant_emotion": "中性",
            "common_poses": ["坐姿"],
            "frame_details": analysis_results
        }
        
        result_path = os.path.join(temp_dir, f"{task_id}_analysis.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary
        
    except Exception as e:
        error_msg = f"视频处理失败：{str(e)}\n{traceback.format_exc()}"
        with open(os.path.join(temp_dir, f"{task_id}_error.txt"), "w", encoding="utf-8") as f:
            f.write(error_msg)
        return {"status": "error", "message": error_msg}

@app.route('/api/analyze_video', methods=['POST'])
def analyze_video():
    """主接口（局部变量：配置参数）"""
    try:
        # 局部定义核心配置
        gradio_url = "http://127.0.0.1:7860"
        temp_dir = "D:/Temp/video_frames"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 获取视频数据（局部变量）
        video_data = None
        if 'video' in request.files:
            video_file = request.files['video']
            video_data = video_file.read()
        elif 'video_base64' in request.json:
            video_base64 = request.json['video_base64']
            video_data = base64.b64decode(video_base64)
        else:
            return jsonify({
                "status": "error",
                "message": "请提供video文件或video_base64字段"
            }), 400
        
        task_id = str(uuid.uuid4())
        
        # 线程参数传递局部变量
        threading.Thread(
            target=process_video_frames,
            args=(video_data, task_id, gradio_url, temp_dir)
        ).start()
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "message": "视频已接收，正在分析表情和动作..."
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"请求处理失败：{str(e)}"
        }), 500

@app.route('/api/get_result/<task_id>', methods=['GET'])
def get_result(task_id):
    """查询结果接口（局部变量：路径）"""
    temp_dir = "D:/Temp/video_frames"  # 局部定义路径
    result_path = os.path.join(temp_dir, f"{task_id}_analysis.json")
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        return jsonify({"status": "completed", "result": result})
    elif os.path.exists(os.path.join(temp_dir, f"{task_id}_error.txt")):
        with open(os.path.join(temp_dir, f"{task_id}_error.txt"), "r", encoding="utf-8") as f:
            error = f.read()
        return jsonify({"status": "error", "message": error})
    else:
        return jsonify({"status": "processing", "message": "分析中，请稍后查询"})


@app.route('/api/analyze_frame', methods=['POST'])
def analyze_frame():
    """分析单帧图片中的表情和动作（严格遵循Gradio API文档）"""
    try:
        # 局部配置参数
        max_content_length = 16 * 1024 * 1024  # 16MB
        gradio_url = "http://127.0.0.1:7860"
        max_retries = 5
        retry_delay = 2
        
        # 检查请求大小
        if request.content_length and request.content_length > max_content_length:
            return jsonify({
                "status": "error", 
                "message": f"请求大小超过限制（最大{max_content_length//1024//1024}MB）"
            }), 413
        
        # 获取请求数据
        data = request.json
        image_base64 = data.get('image_base64')
        frame_index = data.get('frame_index', 0)
        
        if not image_base64:
            return jsonify({"status": "error", "message": "缺少图片数据"}), 400
        
        # 定义单帧分析函数
        def analyze_single_frame(local_image_base64, local_gradio_url):
            """完全按照Gradio API文档要求实现接口调用"""
            try:
                import tempfile
                import base64
                import os
                import traceback
                import time
                from gradio_client import Client, handle_file
                
                # 创建Gradio客户端
                local_client = Client(local_gradio_url)
                
                # 处理base64图片数据为临时文件
                try:
                    # 解码base64
                    image_data = base64.b64decode(local_image_base64)
                    
                    # 简单验证图片数据
                    if len(image_data) < 100:
                        raise ValueError("无效的图片数据，可能是错误的base64编码")
                    
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_file.write(image_data)
                        temp_file_path = temp_file.name
                    
                    if not os.path.exists(temp_file_path):
                        raise Exception("临时文件创建失败")
                    
                except Exception as e:
                    error_msg = f"图片处理错误: {str(e)}"
                    print(f"{error_msg}\n{traceback.format_exc()}")
                    return {
                        "emotion": "图片处理错误",
                        "poses": [error_msg],
                        "confidence": 0
                    }
                
                # 定义分析提示词
                prompt = "分析图片中人物的表情和动作，详细描述人物的情绪状态和肢体动作"
                
                try:
                    # 第一步：使用/add_file端点上传图片并发送提示
                    # 完全按照API文档示例，使用handle_file处理文件路径
                    result = local_client.predict(
                        history=[(None, prompt)],  # 历史消息列表，包含提示词
                        file=handle_file(temp_file_path),  # 使用API文档推荐的handle_file函数
                        api_name="/add_file"  # 明确指定API端点
                    )
                    
                    # 第二步：使用重试机制和/predict端点获取完整结果
                    retry_count = 0
                    response_text = ""
                    
                    while retry_count < max_retries:
                        print(f"重试 {retry_count + 1}/{max_retries} - 当前结果: {str(result)[:200]}")
                        
                        # 检查是否获得有效响应
                        if isinstance(result, list) and len(result) > 0:
                            last_entry = result[-1]
                            if isinstance(last_entry, tuple) and len(last_entry) > 1 and last_entry[1]:
                                response_text = last_entry[1]
                                break
                        
                        # 等待并重试获取结果
                        time.sleep(retry_delay)
                        retry_count += 1
                        
                        # 调用/predict端点获取更新，完全符合API文档参数要求
                        result = local_client.predict(
                            _chatbot=result,  # 传递当前对话历史
                            api_name="/predict"
                        )
                    
                    # 处理未获取到结果的情况
                    if not response_text:
                        response_text = "未获取到有效分析结果"
                        if isinstance(result, list) and len(result) > 0:
                            response_text = str(result[-1])
                    
                except Exception as e:
                    error_msg = f"Gradio API调用错误: {str(e)}"
                    print(f"{error_msg}\n{traceback.format_exc()}")
                    return {
                        "emotion": "API调用错误",
                        "poses": [error_msg],
                        "confidence": 0
                    }
                finally:
                    # 确保临时文件被清理
                    if os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except Exception as e:
                            print(f"清理临时文件失败: {str(e)}")
                
                # 解析结果
                print(f"Gradio原始响应: {str(result)[:500]}")
                
                # 提取表情和动作信息
                emotion = "未知"
                poses = []
                
                # 表情识别
                emotion_keywords = {
                    "惊讶": "惊讶",
                    "开心": "开心",
                    "生气": "生气",
                    "害怕": "害怕",
                    "困惑": "困惑",
                    "中性": "中性",
                    "悲伤": "悲伤"
                }
                for keyword, emotion_name in emotion_keywords.items():
                    if keyword in response_text:
                        emotion = emotion_name
                        break
                
                # 动作识别
                pose_keywords = {
                    "双手捂住脸": "双手捂脸",
                    "站立": "站立",
                    "坐姿": "坐姿",
                    "挥手": "挥手",
                    "点头": "点头",
                    "摇头": "摇头"
                }
                for keyword, pose_name in pose_keywords.items():
                    if keyword in response_text:
                        poses.append(pose_name)
                
                # 如果没有识别到动作，使用原始描述片段
                if not poses and response_text:
                    poses.append(response_text[:50] + "...")
                
                return {
                    "emotion": emotion,
                    "poses": poses,
                    "confidence": 70,
                    "raw_description": response_text
                }
                
            except Exception as e:
                error_detail = f"单帧分析出错: {str(e)}\n{traceback.format_exc()}"
                print(error_detail)
                return {
                    "emotion": "分析错误",
                    "poses": [str(e)],
                    "confidence": 0
                }
        
        # 执行分析并返回结果
        analysis_result = analyze_single_frame(image_base64, gradio_url)
        
        return jsonify({
            "status": "success",
            "result": {
                "frame_index": frame_index,
                "dominant_emotion": analysis_result.get("emotion", "未知"),
                "common_poses": analysis_result.get("poses", []),
                "confidence": analysis_result.get("confidence", 0),
                "raw_description": analysis_result.get("raw_description", "")
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
    

# 添加一个测试页面
@app.route('/lip_sync')
def lip_sync_page():
    return '''
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lip Sync Video Generation Test</title>
    <style>
        /* 保持原有样式不变 */
        .container {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h1, h2, h3 {
            color: #333;
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }

        input, select, textarea {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        button:hover {
            background-color: #45a049;
        }

        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }

        .result {
            margin-top: 20px;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 4px;
            overflow-x: auto;
        }

        .file-info {
            margin-top: 10px;
            color: #666;
            font-size: 0.9em;
        }

        .preview {
            margin-top: 15px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }

        video, audio {
            max-width: 100%;
            margin-top: 10px;
            border-radius: 4px;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(76, 175, 80, 0.3);
            border-radius: 50%;
            border-top-color: #4CAF50;
            animation: spin 1s ease-in-out infinite;
            margin-left: 10px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .progress-container {
            margin-top: 15px;
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }

        .progress-bar {
            height: 20px;
            background-color: #4CAF50;
            width: 0%;
            transition: width 0.3s ease;
        }

        .debug-info {
            margin-top: 20px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }

        .api-response {
            margin-top: 15px;
            padding: 10px;
            background-color: #f0f7ff;
            border-radius: 4px;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }

        .optional-preview {
            margin-top: 20px;
            padding: 15px;
            border: 1px dashed #ccc;
            border-radius: 4px;
        }

        .optional-preview h3 {
            margin-top: 0;
            color: #666;
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Lip Sync Video Generation Test</h1>

        <!-- Audio Generation Section -->
        <div class="section">
            <h2>1. Generate Audio</h2>
            <form id="audioGenerateForm" class="generate-form">
                <div class="form-group">
                    <label for="promptText">Input Text (for voice generation)</label>
                    <textarea id="promptText" placeholder="Enter text to be converted to speech, e.g., Explain the concept of neural networks" required></textarea>
                </div>
                <button type="submit" id="audioGenerateButton">Generate Audio</button>
                <span id="audioLoading" class="loading" style="display: none;"></span>
            </form>
            <div id="chatResponse" class="api-response" style="display: none;">
                <strong>AI Interviewer Response:</strong>
                <div id="chatResponseContent"></div>
            </div>
            <div id="audioResult" class="result" style="display: none;"></div>
            <div class="preview" id="audioPreview"></div>
        </div>

        <!-- Video Processing Section -->
        <div class="section">
            <h2>2. Process Video</h2>
            <form id="processForm">
                <div class="form-group">
                    <label for="minResolution">Minimum Resolution</label>
                    <select id="minResolution">
                        <option value="2">2 (Default)</option>
                        <option value="1">1</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="ifRes">Maintain Resolution</label>
                    <select id="ifRes">
                        <option value="false">No (Default)</option>
                        <option value="true">Yes</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="steps">Processing Steps</label>
                    <select id="steps">
                        <option value="4">4 (Default)</option>
                        <option value="2">2</option>
                        <option value="6">6</option>
                        <option value="8">8</option>
                    </select>
                </div>
                <button type="submit" id="processButton" disabled>Start Processing</button>
                <button type="button" id="cancelButton" disabled>Cancel Processing</button>
                <span id="processLoading" class="loading" style="display: none;"></span>
            </form>
            
            <div id="processStatus" class="result" style="display: none;"></div>
            
            <div class="progress-container">
                <div id="progressBar" class="progress-bar"></div>
            </div>
            
            <!-- Optional Video Preview Section -->
            <div class="optional-preview">
                <h3>Video to Watch While Waiting</h3>
                <p>While waiting for processing, you can watch this video:</p>
                <button id="showPreviewVideo" type="button">Show Preview Video</button>
                <div id="previewVideoContainer" style="display: none; margin-top: 10px;">
                    <video controls src="https://123.56.203.202/proxy_files?path=D%3A%5CTemp%5Cjulibzhan.mp4">
                        Your browser does not support video playback
                    </video>
                    <div class="file-info">
                        Video file: julibzhan.mp4
                    </div>
                </div>
            </div>
            
            <div class="preview" id="outputVideoPreview"></div>
        </div>

        <!-- Debug Information Section -->
        <div class="section">
            <h2>Debug Information</h2>
            <div id="debugInfo" class="debug-info"></div>
        </div>
    </div>

    <script>
        // Configuration - 调整视频处理超时为30分钟
        const HTTPS_BASE_URL = 'https://123.56.203.202'; // Base URL
        const PROXY_FILE_PATH = '/proxy_gradio_file/'; // File proxy path
        const RECENT_FILES_PATH = '/proxy_gradio_file/recent'; // Recent files query path
        const PROCESS_VIDEO_PATH = '/lip_sync/process_video'; // Video processing API path
        const CHAT_API_PATH = '/api/chat'; // Chat API path
        const CHAT_RESULT_PATH = '/api/chat/result'; // Chat result API path for polling
        const TTS_API_PATH = '/gpt-sovites/tts_english'; // Text-to-speech API path
        const GET_LATEST_AUDIO_URL = '/gpt-sovites/get_latest_audio_url'; // Get latest audio URL API
        const POLL_INTERVAL = 3000; // 视频轮询间隔保持3秒
        const MAX_POLL_ATTEMPTS = 600; // 最大视频轮询次数改为600次 (3秒 × 600 = 1800秒 = 30分钟)
        const AUDIO_POLL_INTERVAL = 2000; // Audio polling interval (milliseconds)
        const MAX_AUDIO_ATTEMPTS = 180; // Maximum audio polling attempts (~360 seconds)
        const CHAT_POLL_INTERVAL = 2000; // Chat result polling interval
        const MAX_CHAT_ATTEMPTS = 120; // Maximum chat result polling attempts (~4 minutes)
        const OPTIONAL_VIDEO_URL = 'https://123.56.203.202/proxy_files?path=D%3A%5CTemp%5Cjulibzhan.mp4'; // Optional video URL

        // Get DOM elements
        const elements = {
            promptText: document.getElementById('promptText'),
            audioGenerateForm: document.getElementById('audioGenerateForm'),
            audioGenerateButton: document.getElementById('audioGenerateButton'),
            audioLoading: document.getElementById('audioLoading'),
            audioResult: document.getElementById('audioResult'),
            audioPreview: document.getElementById('audioPreview'),
            chatResponse: document.getElementById('chatResponse'),
            chatResponseContent: document.getElementById('chatResponseContent'),
            
            processForm: document.getElementById('processForm'),
            processButton: document.getElementById('processButton'),
            cancelButton: document.getElementById('cancelButton'),
            processLoading: document.getElementById('processLoading'),
            processStatus: document.getElementById('processStatus'),
            progressBar: document.getElementById('progressBar'),
            outputVideoPreview: document.getElementById('outputVideoPreview'),
            minResolution: document.getElementById('minResolution'),
            ifRes: document.getElementById('ifRes'),
            steps: document.getElementById('steps'),
            showPreviewVideo: document.getElementById('showPreviewVideo'),
            previewVideoContainer: document.getElementById('previewVideoContainer'),
            
            debugInfo: document.getElementById('debugInfo')
        };

        // Application state
        const state = {
            promptText: '',
            chatResponseText: '',
            audioUrl: null,
            audioPreviewUrl: null,
            isAudioGenerating: false,
            audioFolderPrefix: null, // For verifying audio folder
            currentTaskId: null, // Store current chat task ID
            
            isProcessing: false,
            processStartTime: null, // Record processing start timestamp
            pollAttempts: 0, // Polling attempt count
            pollTimer: null, // Polling timer
            abortController: null
        };

        // Show debug information
        function showDebugInfo(message) {
            const timestamp = new Date().toISOString();
            elements.debugInfo.innerHTML += `[${timestamp}] ${message}\n`;
            elements.debugInfo.scrollTop = elements.debugInfo.scrollHeight;
        }

        // Fetch with timeout
        function fetchWithTimeout(url, options = {}, timeout = 500000) {
            return Promise.race([
                fetch(url, options),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Request timed out')), timeout)
                )
            ]);
        }

        // Update process button state (only depends on whether audio is generated)
        function updateProcessButtonState() {
            elements.processButton.disabled = 
                state.isAudioGenerating || 
                !state.audioUrl || 
                state.isProcessing;
                
            elements.cancelButton.disabled = !state.isProcessing;
        }

        // Function to poll for audio URL
        function startAudioPolling(folderPrefix) {
            let attempts = 0;
            
            const pollTimer = setInterval(async () => {
                attempts++;
                showDebugInfo(`Polling for audio, attempt ${attempts}`);
                
                try {
                    // Call API to get latest audio URL
                    const url = new URL(GET_LATEST_AUDIO_URL, HTTPS_BASE_URL).href;
                    const response = await fetchWithTimeout(url, { method: 'GET' });
                    
                    const result = await response.json();
                    showDebugInfo(`Polling result: ${JSON.stringify(result)}`);
                    
                    // Process polling result
                    if (result.status === 'success') {
                        // Verify if it's the folder generated by current request
                        if (result.folder_path.includes(folderPrefix)) {
                            clearInterval(pollTimer);
                            state.audioUrl = result.audio_url; // Save HTTPS link
                            
                            // Display audio preview
                            elements.audioPreview.innerHTML = `
                                <p>Audio preview:</p>
                                <audio controls src="${state.audioUrl}"></audio>
                                <div class="file-info">
                                    Generation time: ${result.created_time}<br>
                                    <a href="${state.audioUrl}" download="generated_audio.wav">Download audio</a>
                                </div>
                            `;
                            
                            // Try to get audio duration
                            const audioElement = elements.audioPreview.querySelector('audio');
                            audioElement.onloadedmetadata = function() {
                                const duration = audioElement.duration.toFixed(2);
                                const fileInfo = elements.audioPreview.querySelector('.file-info');
                                fileInfo.innerHTML = `
                                    Generation time: ${result.created_time}<br>
                                    Audio length: ${duration} seconds<br>
                                    <a href="${state.audioUrl}" download="generated_audio.wav">Download audio</a>
                                `;
                            };
                            
                            elements.audioResult.textContent = 'Audio generated successfully';
                            state.isAudioGenerating = false;
                            elements.audioGenerateButton.disabled = false;
                            elements.audioLoading.style.display = 'none';
                            updateProcessButtonState();
                        } else {
                            showDebugInfo(`Waiting for target folder ${folderPrefix}...`);
                        }
                        
                    } else if (result.status === 'pending') {
                        // Audio not generated yet, continue polling
                        elements.audioResult.textContent = `Generating audio (${attempts}/${MAX_AUDIO_ATTEMPTS})...`;
                        
                    } else {
                        // Error occurred
                        clearInterval(pollTimer);
                        elements.audioResult.textContent = `Polling error: ${result.message}`;
                        state.isAudioGenerating = false;
                        elements.audioGenerateButton.disabled = false;
                        elements.audioLoading.style.display = 'none';
                        updateProcessButtonState();
                    }
                    
                    // Reached maximum attempts
                    if (attempts >= MAX_AUDIO_ATTEMPTS) {
                        clearInterval(pollTimer);
                        elements.audioResult.textContent = 'Audio generation timed out, please try again';
                        state.isAudioGenerating = false;
                        elements.audioGenerateButton.disabled = false;
                        elements.audioLoading.style.display = 'none';
                        updateProcessButtonState();
                    }
                    
                } catch (error) {
                    showDebugInfo(`Polling error: ${error.message}`);
                    if (attempts >= MAX_AUDIO_ATTEMPTS) {
                        clearInterval(pollTimer);
                        elements.audioResult.textContent = `Polling failed: ${error.message}`;
                        state.isAudioGenerating = false;
                        elements.audioGenerateButton.disabled = false;
                        elements.audioLoading.style.display = 'none';
                        updateProcessButtonState();
                    }
                }
            }, AUDIO_POLL_INTERVAL);
        }

        // Function to poll for chat result from TXT file
        function pollForChatResult(taskId) {
            return new Promise((resolve, reject) => {
                let attempts = 0;
                
                const poll = async () => {
                    attempts++;
                    showDebugInfo(`Polling for chat result (task ID: ${taskId}), attempt ${attempts}`);
                    
                    try {
                        // Call the result API to get content from TXT file
                        const resultUrl = new URL(`${CHAT_RESULT_PATH}/${taskId}`, HTTPS_BASE_URL).href;
                        const response = await fetchWithTimeout(resultUrl, { method: 'GET' }, 10000);
                        
                        if (!response.ok) {
                            throw new Error(`Result API error: ${response.status} ${response.statusText}`);
                        }
                        
                        const resultData = await response.json();
                        showDebugInfo(`Chat result response: ${JSON.stringify(resultData)}`);
                        
                        // Check different statuses
                        if (resultData.status === 'processing') {
                            // Still processing, continue polling
                            elements.audioResult.textContent = `Waiting for AI response (${attempts}/${MAX_CHAT_ATTEMPTS})...`;
                            
                            if (attempts >= MAX_CHAT_ATTEMPTS) {
                                reject(new Error('Timeout waiting for chat response'));
                                return;
                            }
                            
                            setTimeout(poll, CHAT_POLL_INTERVAL);
                            
                        } else if (resultData.status === 'success') {
                            // Successfully got result from TXT file
                            resolve(resultData.result);
                            
                        } else if (resultData.status === 'error') {
                            // Error occurred in processing
                            reject(new Error(`Processing error: ${resultData.result}`));
                            
                        } else {
                            // Unknown status
                            reject(new Error(`Unknown status: ${resultData.status}`));
                        }
                        
                    } catch (error) {
                        showDebugInfo(`Chat result polling error: ${error.message}`);
                        
                        if (attempts >= MAX_CHAT_ATTEMPTS) {
                            reject(new Error(`Polling failed after ${MAX_CHAT_ATTEMPTS} attempts: ${error.message}`));
                        } else {
                            // Retry on error
                            setTimeout(poll, CHAT_POLL_INTERVAL);
                        }
                    }
                };
                
                // Start first poll
                poll();
            });
        }

        // Generate audio (via API)
        elements.audioGenerateForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const userInput = elements.promptText.value.trim();
            if (!userInput) return;
            
            // Construct prompt to ensure AI responds as a technical interviewer in English
            const interviewerPrompt = `You are a senior AI technical interviewer conducting a technical interview with a candidate. Based on the following input, provide a professional technical response in ENGLISH ONLY. Focus on areas related to artificial intelligence, machine learning, deep learning, and maintain professional and targeted interview tone: ${userInput}`;
            
            state.promptText = interviewerPrompt;
            state.isAudioGenerating = true;
            state.currentTaskId = null;
            elements.audioGenerateButton.disabled = true;
            elements.audioLoading.style.display = 'inline-block';
            elements.audioResult.textContent = 'Sending request to AI...';
            elements.audioResult.style.display = 'block';
            elements.chatResponse.style.display = 'none';
            elements.audioPreview.innerHTML = '';
            
            try {
                // Step 1: Call chat API to get task ID (will store result in TXT file)
                showDebugInfo(`Calling Chat API as AI technical interviewer: ${CHAT_API_PATH}`);
                const chatUrl = new URL(CHAT_API_PATH, HTTPS_BASE_URL).href;
                
                const chatResponse = await fetchWithTimeout(
                    chatUrl,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ prompt: interviewerPrompt })
                    },
                    30000 // Timeout for getting task ID
                );
                
                if (!chatResponse.ok) {
                    throw new Error(`Chat API error: ${chatResponse.status} ${chatResponse.statusText}`);
                }
                
                const chatResult = await chatResponse.json();
                showDebugInfo(`Chat API returned: ${JSON.stringify(chatResult)}`);
                
                if (chatResult.status !== 'success' || !chatResult.task_id) {
                    throw new Error(`Chat API returned invalid result: ${JSON.stringify(chatResult)}`);
                }
                
                // Store task ID for reference
                state.currentTaskId = chatResult.task_id;
                elements.audioResult.textContent = `Received task ID: ${state.currentTaskId}, waiting for response...`;
                
                // Step 2: Poll for chat result (which comes from TXT file on server)
                const aiResponse = await pollForChatResult(state.currentTaskId);
                
                // Display AI interviewer response from TXT file
                state.chatResponseText = aiResponse;
                elements.chatResponseContent.textContent = state.chatResponseText;
                elements.chatResponse.style.display = 'block';
                
                // Step 3: Call TTS API to generate audio
                showDebugInfo(`Calling TTS API: ${TTS_API_PATH}`);
                const ttsUrl = new URL(TTS_API_PATH, HTTPS_BASE_URL).href;
                
                // Prepare TTS request data
                const ttsData = {
                    text: state.chatResponseText,
                    reference_text: state.chatResponseText
                };
                
                const ttsResponse = await fetchWithTimeout(
                    ttsUrl,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(ttsData)
                    },
                    600000 // Timeout set to 600 seconds
                );
                
                if (!ttsResponse.ok) {
                    throw new Error(`TTS API error: ${ttsResponse.status} ${ttsResponse.statusText}`);
                }
                
                // Get TTS result
                const ttsResult = await ttsResponse.json();
                showDebugInfo(`TTS API returned: ${JSON.stringify(ttsResult)}`);
                
                if (ttsResult.status !== 'success') {
                    throw new Error(`Audio synthesis failed: ${ttsResult.message}`);
                }
                
                // Step 4: Start polling for latest audio URL
                elements.audioResult.textContent = 'Audio synthesis in progress, waiting for result...';
                state.audioFolderPrefix = ttsResult.folder_prefix;
                startAudioPolling(ttsResult.folder_prefix);
                
            } catch (error) {
                elements.audioResult.textContent = `Error: ${error.message}`;
                showDebugInfo(`Audio generation failed: ${error.message}`);
                // Reset state on error
                state.isAudioGenerating = false;
                state.currentTaskId = null;
                elements.audioGenerateButton.disabled = false;
                elements.audioLoading.style.display = 'none';
                updateProcessButtonState();
            }
        });

        // Poll for recent files
        function pollForRecentFiles() {
            // Check if maximum attempts reached
            if (state.pollAttempts >= MAX_POLL_ATTEMPTS) {
                elements.processStatus.textContent = `Processing timed out, could not generate video within ${(MAX_POLL_ATTEMPTS * POLL_INTERVAL / 1000).toFixed(0)} seconds`;
                showDebugInfo(`Polling timed out, attempted ${state.pollAttempts} times`);
                resetProcessingState();
                return;
            }

            // Increment poll count
            state.pollAttempts++;
            showDebugInfo(`Polling for recent files, attempt ${state.pollAttempts}`);

            // Build query URL
            const recentFilesUrl = new URL(RECENT_FILES_PATH, HTTPS_BASE_URL);

            // Check if processStartTime is valid
            if (state.processStartTime == null) {
                // Handle null case: set default or log error
                showDebugInfo("Warning: processStartTime not set, using current time as default");
                state.processStartTime = Math.floor(Date.now() / 1000); // Set to current timestamp
            }

            // Safely add parameters
            recentFilesUrl.searchParams.append('since', state.processStartTime.toString());
            recentFilesUrl.searchParams.append('max', '10');


            // Send request to query recent files
            fetchWithTimeout(recentFilesUrl.toString(), { method: 'GET' }, 1000000)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`File query failed: ${response.status} ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    showDebugInfo(`Found ${data.count} new files`);
                    
                    if (data.status === 'success' && data.count > 0) {
                        // Assume latest video file is our result
                        const latestFile = data.files[0];
                        const videoUrl = `${HTTPS_BASE_URL}${PROXY_FILE_PATH}${encodeURIComponent(latestFile.path)}`;
                        
                        showDebugInfo(`Found latest file: ${videoUrl}`);
                        elements.processStatus.textContent = 'Video processing complete, loading preview...';
                        elements.progressBar.style.width = '100%';
                        
                        // Display video preview
                        elements.outputVideoPreview.innerHTML = `
                            <p>Processed video:</p>
                            <video controls src="${videoUrl}"></video>
                            <div class="file-info">
                                Name: ${latestFile.name}<br>
                                Size: ${(latestFile.size / (1024 * 1024)).toFixed(2)} MB<br>
                                <a href="${videoUrl}" download="${latestFile.name}">Download video</a>
                            </div>
                        `;
                        
                        resetProcessingState();
                    } else {
                        // No files found, continue polling
                        // 更新状态显示，显示当前已等待时间和总超时时间
                        const elapsedMinutes = Math.floor((state.pollAttempts * POLL_INTERVAL) / 60000);
                        const totalMinutes = Math.floor((MAX_POLL_ATTEMPTS * POLL_INTERVAL) / 60000);
                        elements.processStatus.textContent = `Processing... Waiting for ${elapsedMinutes} minutes (of maximum ${totalMinutes} minutes)`;
                        
                        // Update progress bar
                        const progress = Math.min(90, (state.pollAttempts / MAX_POLL_ATTEMPTS) * 100);
                        elements.progressBar.style.width = `${progress}%`;
                        
                        // Continue polling
                        state.pollTimer = setTimeout(pollForRecentFiles, POLL_INTERVAL);
                    }
                })
                .catch(error => {
                    showDebugInfo(`Polling error: ${error.message}`);
                    elements.processStatus.textContent = `Polling error: ${error.message}, will continue retrying...`;
                    
                    // Continue polling even if there's an error
                    state.pollTimer = setTimeout(pollForRecentFiles, POLL_INTERVAL);
                });
        }

        // Reset processing state
        function resetProcessingState() {
            state.isProcessing = false;
            state.processStartTime = null;
            state.pollAttempts = 0;
            
            if (state.pollTimer) {
                clearTimeout(state.pollTimer);
                state.pollTimer = null;
            }
            
            elements.processLoading.style.display = 'none';
            elements.processButton.disabled = false;
            elements.cancelButton.disabled = true;
            updateProcessButtonState();
        }

        // Process video
        async function processVideo() {
            state.isProcessing = true;
            state.processStartTime = Math.floor(Date.now() / 1000); // Record start timestamp (seconds)
            state.pollAttempts = 0;
            
            elements.processButton.disabled = true;
            elements.cancelButton.disabled = false;
            elements.processLoading.style.display = 'inline-block';
            elements.processStatus.textContent = 'Submitting processing request...';
            elements.processStatus.style.display = 'block';
            
            elements.progressBar.style.width = '0%';
            elements.outputVideoPreview.innerHTML = '';
            
            // Create AbortController for request cancellation
            state.abortController = new AbortController();
            
            try {
                // Submit processing request (no need to pass video_file, fixed on backend)
                const processUrl = new URL(PROCESS_VIDEO_PATH, HTTPS_BASE_URL).href;
                showDebugInfo(`Submitting video processing request to: ${processUrl}`);
                
                // Build request body (remove video_file parameter)
                const requestData = {
                    min_resolution: parseInt(elements.minResolution.value),
                    if_res: elements.ifRes.value === 'true',
                    steps: parseInt(elements.steps.value)
                };
                
                // 延长视频处理请求超时时间至30分钟
                const response = await fetchWithTimeout(
                    processUrl,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(requestData),  // Does not include video_file
                        signal: state.abortController.signal
                    },
                    1800000 // 视频处理请求超时设置为30分钟(1800000毫秒)
                );
                
                // Process response (continue polling regardless of success)
                if (!response.ok) {
                    showDebugInfo(`Processing request returned non-success status: ${response.status} ${response.statusText}`);
                    // Try to read error content
                    let errorText = await response.text().catch(() => 'Could not get error details');
                    showDebugInfo(`Error content: ${errorText}`);
                    elements.processStatus.textContent = `Processing request returned error, but will continue waiting for results...`;
                } else {
                    try {
                        const result = await response.json();
                        showDebugInfo(`Processing request response: ${JSON.stringify(result)}`);
                        // Show fixed video path used by backend
                        if (result.used_video_file) {
                            showDebugInfo(`Fixed video path used by backend: ${result.used_video_file}`);
                        }
                        elements.processStatus.textContent = 'Processing request submitted, waiting for video generation...';
                    } catch (e) {
                        showDebugInfo(`Failed to parse processing response: ${e.message}`);
                        elements.processStatus.textContent = 'Processing request submitted, waiting for video generation...';
                    }
                }
            } catch (error) {
                if (error.name !== 'AbortError') {
                    showDebugInfo(`Error in processing request: ${error.message}`);
                    elements.processStatus.textContent = `Error in processing request, but will continue waiting for results...`;
                } else {
                    // User actively cancelled
                    elements.processStatus.textContent = 'Processing cancelled';
                    resetProcessingState();
                    return;
                }
            }
            
            // Start polling
            elements.progressBar.style.width = '10%';
            pollForRecentFiles();
        }

        // Handle video processing form submission
        elements.processForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            showDebugInfo('Processing video form submitted');
            
            if (!state.audioUrl) {
                elements.processStatus.textContent = 'Please generate audio first';
                elements.processStatus.style.display = 'block';
                showDebugInfo('No audio generated, terminating processing');
                return;
            }
            
            // Call processing function
            await processVideo();
        });

        // Cancel processing
        elements.cancelButton.addEventListener('click', () => {
            showDebugInfo('User clicked to cancel processing');
            if (state.isProcessing && state.abortController) {
                state.abortController.abort();
                elements.processStatus.textContent = 'Processing cancelled';
                elements.progressBar.style.width = '0%';
                resetProcessingState();
            }
        });

        // Show/hide optional preview video
        elements.showPreviewVideo.addEventListener('click', () => {
            const container = elements.previewVideoContainer;
            if (container.style.display === 'none') {
                container.style.display = 'block';
                elements.showPreviewVideo.textContent = 'Hide Preview Video';
                showDebugInfo('Showing optional preview video');
            } else {
                container.style.display = 'none';
                elements.showPreviewVideo.textContent = 'Show Preview Video';
                showDebugInfo('Hiding optional preview video');
            }
        });

        // Cleanup on page unload
        window.addEventListener('unload', () => {
            if (state.audioPreviewUrl) {
                URL.revokeObjectURL(state.audioPreviewUrl);
            }
            
            // Clean up timers
            if (state.pollTimer) {
                clearTimeout(state.pollTimer);
            }
        });

        // Initialization
        showDebugInfo('Page loaded completely, ready');
        // Set default prompt text to technical interview question
        elements.promptText.value = 'Explain the difference between supervised and unsupervised learning, and provide examples of each';
    </script>
</body>
</html>
    
    
    
    

    


    



    '''
def save_state(process_id, state_data):
    """保存处理状态到文件"""
    with state_lock:
        # 更新内存状态
        processing_states[process_id] = state_data
        
        # 保存到文件，用于持久化
        state_path = os.path.join(STATE_FOLDER, f"{process_id}.json")
        with open(state_path, 'w') as f:
            json.dump(state_data, f, indent=2)

def load_state(process_id):
    """从文件加载处理状态"""
    with state_lock:
        # 先检查内存中是否有
        if process_id in processing_states:
            return processing_states[process_id]
            
        # 从文件加载
        state_path = os.path.join(STATE_FOLDER, f"{process_id}.json")
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
                processing_states[process_id] = state
                return state
                
        return None

def delete_state(process_id):
    """删除处理状态"""
    with state_lock:
        if process_id in processing_states:
            del processing_states[process_id]
            
        state_path = os.path.join(STATE_FOLDER, f"{process_id}.json")
        if os.path.exists(state_path):
            os.remove(state_path)

def process_phase_task(process_id, phase, total_phases, params):
    """实际处理任务的函数，在后台线程中运行"""
    try:
        # 获取当前状态
        state = load_state(process_id)
        if not state:
            return
            
        # 更新状态为处理中
        state['status'] = 'processing'
        state['current_phase'] = phase
        save_state(process_id, state)
        
        # 模拟视频处理 - 实际应用中替换为真实的处理逻辑
        # 这里根据阶段不同模拟不同的处理时间
        processing_time = 5 + (phase * 2)  # 每个阶段处理时间递增
        if processing_time > MAX_PROCESS_TIME:
            processing_time = MAX_PROCESS_TIME
            
        # 模拟处理进度更新
        for i in range(10):
            time.sleep(processing_time / 10)
            state['progress'] = phase / total_phases + (i/10) * (1/total_phases)
            save_state(process_id, state)
        
        # 检查是否是最后一个阶段
        if phase >= total_phases:
            # 处理完成，生成结果文件路径
            output_filename = f"result_{process_id}.mp4"
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            
            # 实际应用中这里应该是真实的输出文件
            # 这里我们简单复制视频文件作为示例
            if os.path.exists(state['video_path']):
                shutil.copy2(state['video_path'], output_path)
            
            # 更新状态为完成
            state['status'] = 'completed'
            state['progress'] = 1.0
            state['generated_video'] = output_filename
            state['end_time'] = datetime.now().isoformat()
        else:
            # 准备下一阶段
            state['status'] = 'pending'
            state['next_phase'] = phase + 1
            
        save_state(process_id, state)
        
    except Exception as e:
        # 处理出错
        state = load_state(process_id)
        if state:
            state['status'] = 'failed'
            state['error'] = str(e)
            save_state(process_id, state)

@app.route('/get_task_file_url', methods=['POST'])
def get_task_file_url():
    try:
        data = request.get_json()
        if not data or 'task_id' not in data:
            return jsonify({'status': 'error', 'message': '缺少task_id参数'}), 400
        
        task_id = data['task_id']
        temp_dir = 'D:\\Temp\\gradio'  # 保持原目录路径
        
        if not os.path.exists(temp_dir) or not os.path.isdir(temp_dir):
            return jsonify({'status': 'error', 'message': f'目录不存在：{temp_dir}'}), 500
        
        # 查找包含task_id的TXT和Markdown文件
        txt_files = []
        md_files = []
        
        for filename in os.listdir(temp_dir):
            # 检查文件名是否包含当前task_id
            if task_id in filename:
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    # 区分文件格式
                    if filename.lower().endswith('.txt'):
                        txt_files.append(file_path)
                    elif filename.lower().endswith('.md'):  # 新增Markdown文件检查
                        md_files.append(file_path)
        
        # 准备返回结果
        result = {
            'status': 'success',
            'task_id': task_id,
            'txt': None,
            'markdown': None
        }
        
        # 处理TXT文件（取最新的）
        if txt_files:
            txt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            txt_file = txt_files[0]
            txt_filename = os.path.basename(txt_file)
            encoded_txt = quote(txt_filename)
            base_url = "https://123.56.203.202"
            result['txt'] = {
                'file_name': txt_filename,
                'file_url': f"{base_url}/proxy_gradio_file/{encoded_txt}",
                'count': len(txt_files)
            }
        
        # 处理Markdown文件（取最新的）
        if md_files:
            md_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            md_file = md_files[0]
            md_filename = os.path.basename(md_file)
            encoded_md = quote(md_filename)
            result['markdown'] = {
                'file_name': md_filename,
                'file_url': f"{base_url}/proxy_gradio_file/{encoded_md}",
                'count': len(md_files)
            }
        
        # 如果两种文件都没找到
        if not result['txt'] and not result['markdown']:
            return jsonify({'status': 'error', 'message': f'未找到匹配文件：{task_id}'}), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/lip_sync/init_process', methods=['POST'])
def init_process():
    """初始化处理流程"""
    try:
        data = request.json
        
        # 验证必要参数
        required_fields = ['audio_file', 'video_file', 'min_resolution', 'if_res', 'total_steps']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'缺少参数: {field}'}), 400
        
        # 生成唯一处理ID
        process_id = f"proc_{uuid.uuid4().hex[:12]}"
        
        # 创建初始状态
        state = {
            'process_id': process_id,
            'status': 'initialized',
            'audio_path': data['audio_file'],
            'video_path': data['video_file'],
            'min_resolution': data['min_resolution'],
            'if_res': data['if_res'],
            'total_phases': data['total_steps'],
            'current_phase': 0,
            'next_phase': 1,
            'progress': 0.0,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'generated_video': None,
            'error': None
        }
        
        # 保存状态
        save_state(process_id, state)
        
        return jsonify({
            'status': 'initialized',
            'process_id': process_id,
            'message': '处理已初始化'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/lip_sync/process_phase', methods=['POST'])
def process_phase():
    """处理单个阶段"""
    try:
        data = request.json
        
        # 验证必要参数
        if 'process_id' not in data or 'phase' not in data:
            return jsonify({'status': 'error', 'message': '缺少process_id或phase参数'}), 400
        
        process_id = data['process_id']
        phase = int(data['phase'])
        
        # 加载状态
        state = load_state(process_id)
        if not state:
            return jsonify({'status': 'error', 'message': f'未找到处理ID: {process_id}'}), 404
        
        # 检查状态是否合法
        if state['status'] in ['completed', 'failed']:
            return jsonify({
                'status': state['status'],
                'message': f'处理已{state["status"]}'
            })
        
        # 启动后台处理线程
        thread = threading.Thread(
            target=process_phase_task,
            args=(process_id, phase, state['total_phases'], data),
            daemon=True
        )
        thread.start()
        
        # 等待一小段时间，确保线程已启动
        time.sleep(0.1)
        
        # 返回当前状态
        updated_state = load_state(process_id)
        return jsonify({
            'status': updated_state['status'],
            'process_id': process_id,
            'current_phase': updated_state['current_phase'],
            'next_phase': updated_state.get('next_phase'),
            'total_phases': updated_state['total_phases'],
            'progress': updated_state['progress']
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/lip_sync/check_status', methods=['POST'])
def check_status():
    """检查处理状态"""
    try:
        data = request.json
        
        if 'process_id' not in data:
            return jsonify({'status': 'error', 'message': '缺少process_id参数'}), 400
        
        process_id = data['process_id']
        state = load_state(process_id)
        
        if not state:
            return jsonify({'status': 'error', 'message': f'未找到处理ID: {process_id}'}), 404
        
        return jsonify({
            'status': state['status'],
            'process_id': process_id,
            'current_phase': state['current_phase'],
            'total_phases': state['total_phases'],
            'progress': state['progress'],
            'generated_video': state['generated_video'],
            'error': state['error']
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/lip_sync/cancel_process', methods=['POST'])
def cancel_process():
    """取消处理"""
    try:
        data = request.json
        
        if 'process_id' not in data:
            return jsonify({'status': 'error', 'message': '缺少process_id参数'}), 400
        
        process_id = data['process_id']
        state = load_state(process_id)
        
        if not state:
            return jsonify({'status': 'error', 'message': f'未找到处理ID: {process_id}'}), 404
        
        # 更新状态为已取消
        state['status'] = 'cancelled'
        state['end_time'] = datetime.now().isoformat()
        save_state(process_id, state)
        
        return jsonify({
            'status': 'cancelled',
            'process_id': process_id,
            'message': '处理已取消'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 辅助接口：提供生成的视频文件访问
@app.route('/proxy_gradio_file/<path:filename>')
def serve_processed_file(filename):
    """提供处理后的文件访问"""
    from flask import send_from_directory
    try:
        return send_from_directory(PROCESSED_FOLDER, filename)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 404
@app.route('/extract_tone', methods=['POST'])
def extract_tone():
    """语调提取API接口"""
    try:
        if 'audio' not in request.files:
            return jsonify({"status": "error", "message": "请上传音频文件"}), 400
            
        audio_data = request.files['audio'].read()
        y, sample_rate = sf.read(io.BytesIO(audio_data))
        result = extract_f0(y, sample_rate)
        return jsonify({"status": "success", "data": convert_to_serializable(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# RVC服务配置
RVC_API_URL = "http://localhost:7897"

# 全局变量存储音色和索引信息（避免频繁刷新）
rvc_voices = []
rvc_indexes = []

def convert_to_standard_wav(audio_bytes):
    try:
        # 首先尝试使用pydub处理
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # 转换为单声道，16000Hz采样率，16位深度
        audio = audio.set_channels(1) \
                     .set_frame_rate(16000) \
                     .set_sample_width(2)  # 16位
        
        # 导出为WAV
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav", codec="pcm_s16le")
        return wav_io.getvalue()
        
    except Exception as e:
        app.logger.error(f"pydub转换失败，尝试备用方法: {str(e)}")
        
        # 备用方法：直接使用wave模块创建WAV
        try:
            # 尝试将原始音频转换为numpy数组
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            samples = np.array(audio.get_array_of_samples())
            
            # 确保是单声道
            if audio.channels > 1:
                samples = samples[::audio.channels]  # 取左声道
            
            # 重采样到16000Hz
            if audio.frame_rate != 16000:
                ratio = 16000 / audio.frame_rate
                new_length = int(len(samples) * ratio)
                samples = np.interp(
                    np.linspace(0, len(samples), new_length, endpoint=False),
                    np.arange(len(samples)),
                    samples
                ).astype(np.int16)
            
            # 确保是16位
            if samples.dtype != np.int16:
                samples = (samples / np.max(np.abs(samples)) * 32767).astype(np.int16)
            
            # 创建WAV文件
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(samples.tobytes())
            
            return wav_io.getvalue()
            
        except Exception as e:
            app.logger.error(f"备用转换方法也失败: {str(e)}")
            raise

@app.route('/rvc/process', methods=['POST'])
def rvc_process():
    """整合RVC相关的所有操作的统一接口"""
    global rvc_voices, rvc_indexes
    
    try:
        data = request.json
        app.logger.info(f"收到请求: {data.get('action')}")
        
        if not data or 'action' not in data:
            return jsonify({
                "status": "error",
                "message": "请提供操作类型(action)"
            }), 400
        
        action = data['action']
        
        # 刷新音色列表
        if action == 'refresh_voices':
            try:
                app.logger.info("刷新音色列表...")
                response = requests.post(
                    f"{RVC_API_URL}/run/infer_refresh", 
                    json={"data": []},
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                app.logger.info(f"RVC返回的音色数据: {result}")
                
                if "data" in result and len(result["data"]) >= 1:
                    rvc_voices = result["data"][0]
                    rvc_indexes = result["data"][1] if len(result["data"]) > 1 else []
                    
                    return jsonify({
                        "status": "success",
                        "voices": rvc_voices,
                        "indexes": rvc_indexes
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "未能获取音色列表，RVC返回格式异常"
                    })
            except Exception as e:
                app.logger.error(f"刷新音色失败: {str(e)}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": f"刷新音色失败: {str(e)}"
                }), 500
        
        # 处理语音转换
        elif action == 'convert':
            if 'audio' not in data:
                return jsonify({
                    "status": "error",
                    "message": "请提供音频数据"
                }), 400
            
            try:
                # 解码base64音频
                audio_base64 = data['audio']
                if ',' in audio_base64:
                    audio_base64 = audio_base64.split(',')[1]
                
                audio_bytes = base64.b64decode(audio_base64)
                app.logger.info(f"收到音频数据，大小: {len(audio_bytes)} bytes")
                
                # 转换为标准WAV格式
                wav_data = convert_to_standard_wav(audio_bytes)
                app.logger.info(f"转换后WAV大小: {len(wav_data)} bytes")
                
                # 再次验证WAV文件
                try:
                    with wave.open(io.BytesIO(wav_data), 'rb') as wf:
                        app.logger.info(f"WAV验证: 声道={wf.getnchannels()}, 采样率={wf.getframerate()}, "
                                     f"位深度={wf.getsampwidth()*8}, 帧数={wf.getnframes()}")
                        
                        # 检查是否有有效数据
                        if wf.getnframes() < 1000:  # 少于1000帧可能是无效音频
                            return jsonify({
                                "status": "error",
                                "message": "音频太短，请录制更长的音频（至少1秒）"
                            }), 400
                except Exception as e:
                    app.logger.error(f"WAV文件验证失败: {str(e)}")
                    return jsonify({
                        "status": "error",
                        "message": "生成的音频无效，请重试"
                    }), 500
                
                wav_base64 = base64.b64encode(wav_data).decode('utf-8')
                
                # 构建RVC API请求数据
                rvc_data = {
                    "data": [
                        data.get('speaker_id', 0),
                        "",
                        data.get('pitch', 0),
                        {
                            "name": "input.wav",
                            "data": f"data:@file/octet-stream;base64,{wav_base64}"
                        },
                        data.get('pitch_extraction', 'rmvpe'),
                        "",
                        data.get('index_path', ""),
                        0.75,  # feature_ratio
                        3,     # filter_radius
                        0,     # resample
                        0.25,  # volume_envelope
                        0.33   # protection
                    ]
                }
                
                app.logger.info(f"发送转换请求到RVC: speaker_id={data.get('speaker_id')}")
                response = requests.post(
                    f"{RVC_API_URL}/run/infer_convert",
                    json=rvc_data,
                    timeout=120
                )
                
                if response.status_code != 200:
                    app.logger.error(f"RVC返回错误状态码: {response.status_code}, 内容: {response.text}")
                    return jsonify({
                        "status": "error",
                        "message": f"RVC服务错误: {response.status_code} {response.reason}"
                    }), 500
                
                rvc_result = response.json()
                app.logger.info(f"RVC转换结果: {rvc_result}")
                
                if "data" in rvc_result and len(rvc_result["data"]) >= 2:
                    return jsonify({
                        "status": "success",
                        "message": rvc_result["data"][0],
                        "audio": rvc_result["data"][1]["data"]
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "RVC返回格式不正确，无法解析结果"
                    })
                    
            except Exception as e:
                app.logger.error(f"音频处理失败: {str(e)}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": f"音频处理失败: {str(e)}"
                }), 500
        
        else:
            return jsonify({
                "status": "error",
                "message": f"未知的操作类型: {action}"
            }), 400
            
    except requests.exceptions.Timeout:
        app.logger.error("RVC请求超时")
        return jsonify({
            "status": "error",
            "message": "语音转换超时，请重试"
        }), 504
    except Exception as e:
        app.logger.error(f"服务器内部错误: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"服务器内部错误: {str(e)}"
        }), 500
# ====================== 姿态检测功能 ======================
def paint_chinese_opencv(im, chinese, pos, color):
    """在OpenCV图像上绘制中文"""
    img_PIL = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    try:
        # 适配不同系统字体
        if os.name == 'nt':  # Windows
            font = ImageFont.truetype('C:\\Windows\\Fonts\\msyh.ttc', 25, encoding="utf-8")
        else:  # Linux/Mac
            font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 25)
    except:
        font = ImageFont.load_default()
    fillColor = color
    position = pos
    draw = ImageDraw.Draw(img_PIL)
    draw.text(position, chinese, fillColor, font)
    img = cv2.cvtColor(np.asarray(img_PIL), cv2.COLOR_RGB2BGR)
    return img

def get_angle(v1, v2):
    """计算两个向量的夹角"""
    denominator = (np.sqrt(np.sum(v1*v1)) * np.sqrt(np.sum(v2*v2))) + 1e-8
    angle = np.dot(v1, v2) / denominator
    angle = np.arccos(np.clip(angle, -1.0, 1.0)) / np.pi * 180
    cross = v2[0] * v1[1] - v2[1] * v1[0]
    if cross < 0:
        angle = -angle
    return float(angle)  # 确保返回Python float而非numpy float

def get_pos(keypoints):
    """根据关键点判断姿态"""
    keypoints = np.array(keypoints)
    if len(keypoints) < 17:
        return "检测点不足"
    try:
        v1 = keypoints[5] - keypoints[6]
        v2 = keypoints[8] - keypoints[6]
        angle_right_arm = get_angle(v1, v2)
        
        v1 = keypoints[7] - keypoints[5]
        v2 = keypoints[6] - keypoints[5]
        angle_left_arm = get_angle(v1, v2)
        
        v1 = keypoints[6] - keypoints[8]
        v2 = keypoints[10] - keypoints[8]
        angle_right_elbow = get_angle(v1, v2)
        
        v1 = keypoints[5] - keypoints[7]
        v2 = keypoints[9] - keypoints[7]
        angle_left_elbow = get_angle(v1, v2)
        
        str_pos = ""
        if angle_right_arm < 0 and angle_left_arm < 0:
            str_pos = "正常"
            if abs(angle_left_elbow) < 120 and abs(angle_right_elbow) < 120:
                str_pos = "叉腰"
        elif angle_right_arm < 0 and angle_left_arm > 0:
            str_pos = "抬左手"
        elif angle_right_arm > 0 and angle_left_arm < 0:
            str_pos = "抬右手"
        elif angle_right_arm > 0 and angle_left_arm > 0:
            str_pos = "抬双手"
            if abs(angle_left_elbow) < 120 and abs(angle_right_elbow) < 120:
                str_pos = "三角形"
        return str_pos
    except IndexError:
        return "关键点异常"
    except Exception as e:
        return f"计算错误: {str(e)[:5]}"

# 加载姿态检测模型
pose_interpreter = None
pose_input_details = None
pose_output_details = None
pose_height, pose_width = 0, 0

try:
    file_model = "posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite"
    if os.path.exists(file_model):
        pose_interpreter = tflite.Interpreter(model_path=file_model)
        pose_interpreter.allocate_tensors()
        pose_input_details = pose_interpreter.get_input_details()
        pose_output_details = pose_interpreter.get_output_details()
        pose_height = pose_input_details[0]['shape'][1]
        pose_width = pose_input_details[0]['shape'][2]
        print(f"✅ 姿态检测模型加载成功: {file_model}")
    else:
        print(f"❌ 姿态检测模型文件不存在: {file_model}")
except Exception as e:
    print(f"❌ 姿态检测模型加载失败: {str(e)}")

def process_pose_frame(img):
    """处理单帧图像，进行姿态检测"""
    global latest_pose_detection
    
    # 图像处理
    imH, imW, _ = np.shape(img)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (pose_width, pose_height))
    input_data = np.expand_dims(img_resized, axis=0)
    input_data = (np.float32(input_data) - 128.0) / 128.0  # 归一化

    # 模型推理
    str_pos = "未检测到人体"
    score = 0.0  # 初始化为Python float
    if pose_interpreter:
        pose_interpreter.set_tensor(pose_input_details[0]['index'], input_data)
        pose_interpreter.invoke()

        # 获取输出
        hotmaps = pose_interpreter.get_tensor(pose_output_details[0]['index'])[0]
        offsets = pose_interpreter.get_tensor(pose_output_details[1]['index'])[0]
        h_output, w_output, n_KeyPoints = np.shape(hotmaps)

        # 解析关键点
        keypoints = []
        score = 0.0  # 确保是Python float
        for i in range(n_KeyPoints):
            hotmap = hotmaps[:, :, i]
            max_index = np.where(hotmap == np.max(hotmap))
            max_val = np.max(hotmap)
            try:
                offset_y = offsets[max_index[0], max_index[1], i]
                offset_x = offsets[max_index[0], max_index[1], i + n_KeyPoints]
            except IndexError:
                offset_y, offset_x = 0, 0

            # 计算坐标并转换为Python float
            pos_y = float(max_index[0] / (h_output - 1) * pose_height + offset_y)
            pos_x = float(max_index[1] / (w_output - 1) * pose_width + offset_x)
            pos_y = float(pos_y / (pose_height - 1) * imH)
            pos_x = float(pos_x / (pose_width - 1) * imW)
            keypoints.append([int(round(pos_x)), int(round(pos_y))])
            
            # 计算置信度并转换为Python float
            score += float(1.0 / (1.0 + np.exp(-max_val)))

        # 平均置信度（确保是Python float）
        score = float(score / n_KeyPoints) if n_KeyPoints > 0 else 0.0

        # 绘制关键点和连接线（当置信度足够时）
        if score > 0.5:
            # 绘制关键点
            for point in keypoints:
                cv2.circle(img, (point[0], point[1]), 5, (255, 255, 0), 5)

            # 绘制骨架
            if len(keypoints) >= 10:
                # 左臂
                cv2.polylines(img, [np.array([keypoints[5], keypoints[7], keypoints[9]])], False, (0, 255, 0), 3)
                # 右臂
                cv2.polylines(img, [np.array([keypoints[6], keypoints[8], keypoints[10]])], False, (0, 0, 255), 3)
            if len(keypoints) >= 16:
                # 左腿
                cv2.polylines(img, [np.array([keypoints[11], keypoints[13], keypoints[15]])], False, (0, 255, 0), 3)
                # 右腿
                cv2.polylines(img, [np.array([keypoints[12], keypoints[14], keypoints[16]])], False, (0, 255, 255), 3)
                # 身体
                cv2.polylines(img, [np.array([keypoints[5], keypoints[6], keypoints[12], keypoints[11], keypoints[5]])], False, (255, 255, 0), 3)

            # 动作识别
            str_pos = get_pos(keypoints)
        
        # 更新全局检测结果，确保所有值都是JSON可序列化的
        latest_pose_detection = convert_to_serializable({
            "pose": str_pos,
            "score": round(score, 2)
        })

        # 添加文字信息
        img = paint_chinese_opencv(img, str_pos, (0, 5), (255, 0, 0))
        cv2.putText(img, f'score: {score:.2f}',
                   (imW - 200, imH - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)

    return img, latest_pose_detection

@app.route('/process_pose_frame', methods=['POST'])
def process_pose_frame_api():
    """处理客户端发送的视频帧，进行姿态检测"""
    try:
        if 'base64' not in request.json:
            return jsonify({"error": "请提供base64格式的视频帧"}), 400
        
        # 解码base64帧
        base64_str = request.json['base64']
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        img_bytes = base64.b64decode(base64_str)
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"error": "无法解码图像"}), 400
        
        # 处理帧
        processed_img, result = process_pose_frame(img)
        
        # 编码处理后的图像
        ret, buffer = cv2.imencode('.jpg', processed_img)
        if not ret:
            return jsonify({"error": "无法编码处理后的图像"}), 500
        
        frame_bytes = buffer.tobytes()
        base64_result = base64.b64encode(frame_bytes).decode('utf-8')
        
        # 使用安全转换确保所有数据可序列化
        response_data = convert_to_serializable({
            "status": "success",
            "result": result,
            "processed_frame": base64_result
        })
        
        return jsonify(response_data)
        
    except Exception as e:
        # 捕获并处理所有异常，返回友好信息
        error_msg = str(e)
        # 特别处理float32相关错误
        if "float32" in error_msg or "numpy" in error_msg:
            error_msg = "数据格式错误: 请确保所有数值都是标准类型"
        return jsonify({"error": error_msg}), 500

@app.route('/detection_data')
def get_detection_data():
    """获取姿态检测数据"""
    # 确保返回的数据可序列化
    return jsonify(convert_to_serializable(latest_pose_detection))

# ====================== 语音识别功能 ======================
# 配置ffmpeg路径（根据实际情况修改）
ffmpeg_bin_path = r"E:\ffmpegkezhixing\ffmpeg-2025-05-01-git-707c04fe06-full_build\bin"
ffprobe_path = os.path.join(ffmpeg_bin_path, "ffprobe.exe")
ffmpeg_path = os.path.join(ffmpeg_bin_path, "ffmpeg.exe")

# 检查并设置ffprobe路径
if PYDUB_AVAILABLE and os.path.exists(ffprobe_path):
    utils.ffprobe = ffprobe_path
    print(f"✅ 已设置ffprobe路径: {ffprobe_path}")
elif PYDUB_AVAILABLE:
    print(f"❌ 指定的ffprobe路径不存在: {ffprobe_path}")

# 将ffmpeg路径添加到系统环境变量
if os.path.exists(ffmpeg_bin_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_bin_path
    print(f"✅ 已将ffmpeg路径添加到环境变量: {ffmpeg_bin_path}")

# 显式设置pydub的ffmpeg路径
if PYDUB_AVAILABLE:
    AudioSegment.converter = ffmpeg_path

def convert_to_wav(input_path, output_path):
    """转换音频为Vosk兼容格式"""
    if not PYDUB_AVAILABLE:
        print("❌ pydub库未安装，无法转换音频")
        return False
        
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)  # 单声道+16kHz
        audio.export(output_path, format="wav", codec="pcm_s16le")
        print(f"✅ 音频转换成功")
        return True
    except Exception as e:
        print(f"❌ 音频转换失败: {str(e)}")
        return False




@app.route('/recognize_speech', methods=['POST'])
def recognize_speech():
    """语音识别API接口"""
    if not VOSK_AVAILABLE:
        return jsonify({"status": "error", "message": "vosk库未安装，无法使用语音识别功能"}), 500
        
    try:
        if 'audio' not in request.files:
            return jsonify({"status": "error", "message": "请上传音频文件"}), 400
        
        # 获取模型路径（默认同目录下的vosk-model-small-cn-0.22）
        model_path = request.form.get('model_path', os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model-small-cn-0.22"))
        
        # 保存上传的音频文件到临时位置
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
            audio_data = request.files['audio'].read()
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # 检查模型路径
        if not os.path.exists(model_path):
            os.unlink(temp_file_path)  # 清理临时文件
            return jsonify({"status": "error", "message": f"模型路径不存在: {model_path}"}), 400
        
        # 转换音频格式
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_temp_file:
            wav_temp_path = wav_temp_file.name
        
        file_ext = os.path.splitext(request.files['audio'].filename)[1].lower()
        if file_ext != ".wav" and not convert_to_wav(temp_file_path, wav_temp_path):
            os.unlink(temp_file_path)
            os.unlink(wav_temp_path)
            return jsonify({"status": "error", "message": "音频转换失败"}), 500
        
        audio_path = wav_temp_path if file_ext != ".wav" else temp_file_path
        
        # 执行语音识别
        results = []
        try:
            with wave.open(audio_path, "rb") as wf:
                # 检查WAV格式
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    return jsonify({"status": "error", "message": "音频格式不符合要求（需单声道、16位、PCM WAV）"}), 400
                
                model = Model(model_path)
                recognizer = KaldiRecognizer(model, wf.getframerate())
                
                # 识别音频
                while True:
                    data = wf.readframes(4000)
                    if not data:
                        break
                    if recognizer.AcceptWaveform(data):
                        partial = json.loads(recognizer.Result())
                        results.append(partial["text"])
                
                # 最终结果
                final = json.loads(recognizer.FinalResult())
                results.append(final["text"])
        
        except wave.Error as e:
            return jsonify({"status": "error", "message": f"音频文件处理错误: {str(e)}"}), 500
        
        # 清理临时文件
        os.unlink(temp_file_path)
        if file_ext != ".wav" and os.path.exists(wav_temp_path):
            os.unlink(wav_temp_path)
        
        # 合并结果
        full_text = " ".join(results).strip()
        return jsonify({"status": "success", "text": full_text})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ====================== 表情识别功能 ======================
def load_emotion_model():
    """加载表情识别模型"""
    global emotion_model
    if emotion_model is None and EMOTION_AVAILABLE:
        emotion_model = CNN3()
        model_path = './models/cnn3_best_weights.h5'
        if os.path.exists(model_path):
            emotion_model.load_weights(model_path)
        else:
            print(f"❌ 表情识别模型文件不存在: {model_path}")
            return None
    return emotion_model

def generate_faces(face_img, img_size=48):
    """将探测到的人脸进行增广"""
    face_img = face_img / 255.
    face_img = cv2.resize(face_img, (img_size, img_size), interpolation=cv2.INTER_LINEAR)
    resized_images = list()
    resized_images.append(face_img)
    resized_images.append(face_img[2:45, :])
    resized_images.append(face_img[1:47, :])
    resized_images.append(cv2.flip(face_img[:, :], 1))

    for i in range(len(resized_images)):
        resized_images[i] = cv2.resize(resized_images[i], (img_size, img_size))
        resized_images[i] = np.expand_dims(resized_images[i], axis=-1)
    resized_images = np.array(resized_images)
    return resized_images

def process_emotion_frame(frame):
    """处理单帧图像，进行表情识别"""
    global emotion_model
    if not EMOTION_AVAILABLE:
        return [], frame
    
    if emotion_model is None:
        emotion_model = load_emotion_model()
        if emotion_model is None:
            return [], frame
    
    # 预处理
    frame = cv2.resize(frame, (800, 600))
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    
    # 人脸检测
    faces = blaze_detect(frame)
    results = []
    
    # 处理检测到的人脸
    if faces is not None and len(faces) > 0:
        for (x, y, w, h) in faces:
            # 提取人脸区域
            face = frame_gray[y: y + h, x: x + w]
            # 生成增广人脸
            faces_augmented = generate_faces(face)
            # 预测表情
            predictions = emotion_model.predict(faces_augmented)
            result_sum = np.sum(predictions, axis=0).reshape(-1)
            label_index = np.argmax(result_sum, axis=0)
            emotion = index2emotion(label_index)
            # 转换为Python float
            confidence = float(np.max(result_sum) / len(faces_augmented))
            
            # 记录结果
            results.append({
                "bounding_box": [int(x), int(y), int(w), int(h)],
                "emotion": emotion,
                "confidence": confidence
            })
            
            # 绘制边框和标签
            cv2.rectangle(frame, (x - 10, y - 10), (x + w + 10, y + h + 10), (0, 0, 0), thickness=2)
            cv2.putText(frame, f"{emotion} ({confidence:.2f})", 
                       (x + 30, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (255, 255, 255), 4)
    
    # 安全转换结果
    return convert_to_serializable(results), frame

def detection_worker():
    """后台处理线程，处理视频流帧"""
    global is_processing
    is_processing = True
    
    while is_processing:
        if not frame_queue.empty():
            frame = frame_queue.get()
            results, processed_frame = process_emotion_frame(frame)
            
            # 编码为JPEG
            ret, buffer = cv2.imencode('.jpg', cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR))
            if ret:
                frame_bytes = buffer.tobytes()
                detection_queue.put((results, frame_bytes))
            
            frame_queue.task_done()
        else:
            time.sleep(0.01)

@app.route('/predict/image', methods=['POST'])
def predict_image():
    """处理单张图片的表情识别请求"""
    if not EMOTION_AVAILABLE:
        return jsonify({"status": "error", "message": "表情识别模块不可用"}), 500
        
    try:
        # 接收图片数据
        if 'image' in request.files:
            # 从文件上传获取
            file = request.files['image']
            img_bytes = file.read()
            img = Image.open(io.BytesIO(img_bytes))
            frame = np.array(img.convert('RGB'))
        elif 'base64' in request.json:
            # 从base64获取
            base64_str = request.json['base64']
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            img_bytes = base64.b64decode(base64_str)
            img = Image.open(io.BytesIO(img_bytes))
            frame = np.array(img.convert('RGB'))
        else:
            return jsonify({"error": "请提供image文件或base64数据"}), 400
        
        # 处理图片
        results, _ = process_emotion_frame(frame)
        
        return jsonify({
            "status": "success",
            "predictions": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict/video/frame', methods=['POST'])
def predict_video_frame():
    """处理视频流的单帧，用于实时识别"""
    if not EMOTION_AVAILABLE:
        return jsonify({"status": "error", "message": "表情识别模块不可用"}), 500
        
    try:
        if 'base64' not in request.json:
            return jsonify({"error": "请提供base64格式的视频帧"}), 400
        
        # 解码base64帧
        base64_str = request.json['base64']
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        img_bytes = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(img_bytes))
        frame = np.array(img.convert('RGB'))
        
        # 将帧放入队列
        if not frame_queue.full():
            frame_queue.put(frame)
        
        # 等待处理结果
        start_time = time.time()
        results = None
        frame_bytes = None
        
        while time.time() - start_time < 1.0:  # 1秒超时
            if not detection_queue.empty():
                results, frame_bytes = detection_queue.get()
                detection_queue.task_done()
                break
            time.sleep(0.01)
        
        if results is None:
            return jsonify({"error": "处理超时"}), 504
        
        # 返回结果
        return jsonify({
            "status": "success",
            "predictions": results,
            "frame": base64.b64encode(frame_bytes).decode('utf-8') if frame_bytes else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================== 对话功能 ======================
# ====================== 对话功能 ======================
# ====================== 对话功能 ======================
@app.route('/api/chat', methods=['POST'])
def chat():
    """处理对话请求，支持带图片或纯文本，返回任务ID，后台异步处理并存储结果"""
    try:
        # 定义存储目录
        temp_dir = "D:/Temp/gradio"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 获取前端请求
        request_data = request.json
        prompt = request_data.get('prompt', '')
        # 获取图片相关参数（可选）
        image_url = request_data.get('image_url')  # 图片URL
        image_base64 = request_data.get('image_base64')  # 图片Base64编码
        
        if not prompt:
            return jsonify({"status": "error", "result": "请输入问题内容"}), 400

        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 定义两种格式的文件路径
        txt_file = os.path.join(temp_dir, f"chat_result_{task_id}.txt")
        md_file = os.path.join(temp_dir, f"chat_result_{task_id}.md")
        
        # 创建初始文件标记任务状态
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("processing")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("processing")
        
        # 启动线程异步处理，传入所有必要参数
        threading.Thread(
            target=process_chat_request, 
            args=(prompt, txt_file, md_file, image_url, image_base64)
        ).start()
        
        # 返回任务ID
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "message": "请求已接收，正在处理中"
        })

    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({
            "status": "error",
            "result": f"处理失败：{str(e)}\n{error_details}"
        }), 500


from openai import OpenAI
import base64
import re
import os

def process_chat_request(prompt, txt_file, md_file, image_url=None, image_base64=None):
    """处理聊天请求的函数，使用标准OpenAI客户端和Base64处理"""
    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        
        # 构建消息内容
        message_content = [{"type": "text", "text": prompt}]
        
        # 处理Base64图片（使用标准处理方式）
        if image_base64:
            try:
                # 提取纯Base64数据（移除前缀）
                prefix_pattern = r'^data:image/[a-zA-Z0-9]+;base64,'
                cleaned_base64 = re.sub(prefix_pattern, '', image_base64, flags=re.IGNORECASE)
                
                # 验证Base64数据
                try:
                    base64.b64decode(cleaned_base64, validate=True)
                except (base64.binascii.Error, ValueError) as e:
                    raise Exception(f"无效的Base64数据: {str(e)}")
                
                # 添加图片内容
                message_content.append({
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{cleaned_base64}"}
                })
                
            except Exception as e:
                raise Exception(f"图片处理错误: {str(e)}")
        
        # 调用API
        try:
            response = client.chat.completions.create(
                model="qwen2.5vl:7b",
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                max_tokens=500
            )
            
            # 提取结果
            result = response.choices[0].message.content
            
            # 保存结果
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            # 同时保存为MD格式
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(result)
                
            return result
            
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")
        
    except Exception as e:
        error_msg = f"处理失败：{str(e)}"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(error_msg)
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return error_msg
    
    



    

@app.route('/api/chat/result/<task_id>', methods=['GET'])
def get_chat_result(task_id):
    """获取聊天结果的接口，供前端轮询"""
    try:
        # 构建结果文件路径
        result_file = os.path.join(TEMP_DIR, f"chat_result_{task_id}.txt")
        
        # 检查文件是否存在
        if not os.path.exists(result_file):
            return jsonify({
                "status": "pending",
                "message": "任务不存在或已过期"
            })
        
        # 读取文件内容
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 判断处理状态
        if content == "processing":
            return jsonify({
                "status": "processing",
                "message": "正在处理中，请稍后"
            })
        elif content.startswith("error:"):
            return jsonify({
                "status": "error",
                "result": content[6:].strip()  # 移除"error:"前缀
            })
        else:
            # 处理完成，返回结果
            return jsonify({
                "status": "success",
                "result": content
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "result": f"获取结果失败：{str(e)}"
        }), 500

# ====================== 数据库功能 ======================
def is_valid_email(email):
    """验证邮箱格式"""
    email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    return email_regex.match(email) is not None

# 用户登录接口
@app.route('/sqlLogin', methods=['POST'])
def sql_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "请输入用户名和密码"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "数据库连接失败"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        # 查询用户
        cursor.execute("SELECT * FROM sqlusers WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        
        if user:
            # 生成JWT
            expiration = datetime.utcnow() + timedelta(hours=1)
            token =jwt.encode(
                {
                    "userId": user['id'],
                    "exp": expiration  # 在payload中直接指定过期时间
                },
                'your_secret_key',
                algorithm="HS256"
            )        
            # 设置session
            session['userId'] = user['id']
            session['username'] = user['username']
            session['isLoggedIn'] = True
            
            user_data = {
                "username": username,
                "loggedIn": True
            }
            
            return jsonify({
                "success": True,
                "message": "SQL 数据库登录成功",
                "token": token,
                "a": user_data,
                "username": username,
                "id": user['id'],
                "b": session['isLoggedIn']
            })
        else:
            return jsonify({"success": False, "message": "SQL 数据库用户名或密码错误"})
            
    except Error as e:
        print(f"数据库错误: {e}")
        return jsonify({"success": False, "message": "数据库错误"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 用户注册接口
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    # 基本验证
    if not username or not password or not email:
        return jsonify({"success": False, "message": "请填写完整信息"}), 400
    
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "请输入有效的邮箱地址"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "数据库连接失败"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 检查用户名是否存在
        cursor.execute("SELECT * FROM sqlusers WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "该用户名已被使用，请选择其他用户名"}), 400
        
        # 检查邮箱是否存在
        cursor.execute("SELECT * FROM sqlusers WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "该邮箱已被注册，请使用其他邮箱"}), 400
        
        # 创建新用户
        cursor.execute(
            "INSERT INTO sqlusers (username, password, email) VALUES (%s, %s, %s)",
            (username, password, email)
        )
        connection.commit()
        
        return jsonify({"success": True, "message": "注册成功"})
        
    except Error as e:
        print(f"数据库错误: {e}")
        connection.rollback()
        return jsonify({"success": False, "message": "注册失败，请稍后重试"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 获取所有博客接口
@app.route('/getBlogs', methods=['GET'])
def get_blogs():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "数据库连接失败"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT username, blogs FROM sqlusers")
        rows = cursor.fetchall()
        
        all_blogs = []
        for row in rows:
            username = row['username']
            blogs = row['blogs']
            
            if blogs:
                try:
                    # 解析博客数据
                    blogs_list = json.loads(blogs) if isinstance(blogs, str) else blogs
                    
                    # 为每个博客添加用户名
                    for blog in blogs_list:
                        blog['username'] = username
                        all_blogs.append(blog)
                except json.JSONDecodeError:
                    print(f"解析博客数据失败: {blogs}")
        
        # 按日期排序
        all_blogs.sort(
            key=lambda x: datetime.fromisoformat(x['date'].replace('Z', '')), 
            reverse=True
        )
        return jsonify(all_blogs)
        
    except Error as e:
        print(f"数据库错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 获取评论接口
@app.route('/getComments', methods=['GET'])
def get_comments():
    connection = get_db_connection()
    if not connection:
        return jsonify({"message": "数据库连接失败"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT username, comments FROM sqlusers")
        rows = cursor.fetchall()
        
        all_comments = []
        for row in rows:
            username = row['username']
            comments_str = row['comments']
            
            if comments_str:
                try:
                    comments = json.loads(comments_str)
                    for comment in comments:
                        comment['username'] = comment.get('username', username)
                        all_comments.append(comment)
                except json.JSONDecodeError:
                    print(f"解析评论失败: {comments_str}")
        
        return jsonify(all_comments)
        
    except Error as e:
        print(f"数据库错误: {e}")
        return jsonify({"message": "服务器错误"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ====================== 通用接口 ======================
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        db_connected = False
        connection = get_db_connection()
        if connection and connection.is_connected():
            db_connected = True
            connection.close()
        
        # 检查各模块状态
        status = {
            "status": "healthy" if db_connected else "unhealthy",
            "database_connection": db_connected,
            "tone_extraction": True,
            "pose_detection": pose_interpreter is not None,
            "speech_recognition": VOSK_AVAILABLE,
            "emotion_recognition": EMOTION_AVAILABLE and (load_emotion_model() is not None),
            "chat_function": True
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/')
def index():
    """主页接口，返回服务信息"""
    return jsonify({
        "message": "综合识别服务运行中",
        "available_endpoints": {
            # 原有功能接口
            "/extract_tone": "POST - 语调提取",
            "/process_pose_frame": "POST - 处理客户端姿态检测帧",
            "/detection_data": "GET - 姿态检测数据",
            "/recognize_speech": "POST - 语音识别",
            "/predict/image": "POST - 表情识别（图片）",
            "/predict/video/frame": "POST - 表情识别（视频帧）",
            "/api/chat": "POST - 对话功能",
            
            # 数据库功能接口
            "/sqlLogin": "POST - 用户登录",
            "/register": "POST - 用户注册",
            "/getBlogs": "GET - 获取所有博客",
            "/personBlogs/<username>": "GET - 获取指定用户博客",
            "/submitBlogs/<username>": "POST - 提交博客",
            "/deleteBlogsByTime": "DELETE - 按日期删除博客",
            "/addComment/<blogOwnerUsername>/<blogDate>": "POST - 添加评论",
            "/getComments": "GET - 获取所有评论",
            "/getTotalLikes/<username>/<date>": "GET - 获取总点赞数",
            "/addLike/<blogUsername>/<blogDate>": "POST - 添加点赞",
            "/search": "GET - 搜索博客",
            "/getFriends": "POST - 获取好友列表",
            "/getUserBlogs/<username>": "GET - 获取用户博客列表",
            "/addFriend": "POST - 添加好友",
            "/getApplys/<username>": "GET - 获取好友申请",
            "/updateFriendApply": "POST - 更新好友申请状态",
            "/getMessage/<username>": "GET - 获取消息",
            "/health": "GET - 健康检查",
            
            "/gpt-sovites/tts": "POST - 转发文本到语音合成请求到GPT Sovites服务"
        },
        "port": 3000
    })

# ====================== 前端页面（用于测试客户端摄像头） ======================
@app.route('/pose_detection')
def pose_detection_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>客户端摄像头姿态检测</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; }
            .container { display: flex; justify-content: center; gap: 20px; margin-top: 20px; }
            .video-container { border: 2px solid #333; border-radius: 5px; }
            #status { font-size: 1.2em; margin: 20px 0; padding: 10px; background-color: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>客户端摄像头姿态检测</h1>
        <div class="container">
            <div class="video-container">
                <h3>原始视频</h3>
                <video id="video" width="640" height="480" autoplay playsinline></video>
            </div>
            <div class="video-container">
                <h3>处理结果</h3>
                <canvas id="processedCanvas" width="640" height="480"></canvas>
            </div>
        </div>
        <div id="status">等待开始检测...</div>
        
        <script>
            // 获取DOM元素
            const video = document.getElementById('video');
            const processedCanvas = document.getElementById('processedCanvas');
            const processedCtx = processedCanvas.getContext('2d');
            const statusDiv = document.getElementById('status');
            
            // 配置
            const FPS = 15; // 每秒发送15帧，平衡性能和流畅度
            let isProcessing = false;
            
            // 初始化摄像头
            async function initCamera() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { 
                            width: { ideal: 640 },
                            height: { ideal: 480 },
                            facingMode: { ideal: 'environment' } // 优先使用后置摄像头
                        },
                        audio: false
                    });
                    video.srcObject = stream;
                    return stream;
                } catch (err) {
                    console.error('获取摄像头失败:', err);
                    statusDiv.textContent = '获取摄像头失败: ' + err.message;
                    statusDiv.style.backgroundColor = '#ffeeee';
                    return null;
                }
            }
            
            // 发送帧到服务器处理
            async function processFrame() {
                if (!isProcessing) return;
                
                // 创建临时画布绘制当前视频帧
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = video.videoWidth;
                tempCanvas.height = video.videoHeight;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
                
                // 转换为base64
                const base64Frame = tempCanvas.toDataURL('image/jpeg');
                
                try {
                    // 发送到后端处理
                    const response = await fetch('/process_pose_frame', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ base64: base64Frame })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP错误: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        // 更新状态信息
                        statusDiv.textContent = `姿态: ${result.result.pose}, 置信度: ${result.result.score}`;
                        statusDiv.style.backgroundColor = '#eeffee';
                        
                        // 显示处理后的帧
                        const img = new Image();
                        img.onload = () => {
                            processedCtx.drawImage(img, 0, 0, processedCanvas.width, processedCanvas.height);
                        };
                        img.src = `data:image/jpeg;base64,${result.processed_frame}`;
                    } else {
                        statusDiv.textContent = `处理错误: ${result.error}`;
                        statusDiv.style.backgroundColor = '#ffeeee';
                    }
                } catch (err) {
                    console.error('处理帧失败:', err);
                    statusDiv.textContent = '处理帧失败: ' + err.message;
                    statusDiv.style.backgroundColor = '#ffeeee';
                }
                
                // 定时处理下一帧
                setTimeout(processFrame, 1000 / FPS);
            }
            
            // 开始检测
            async function startDetection() {
                isProcessing = true;
                const stream = await initCamera();
                if (stream) {
                    statusDiv.textContent = '开始检测...';
                    processFrame();
                }
            }
            
            // 停止检测
            function stopDetection() {
                isProcessing = false;
                if (video.srcObject) {
                    video.srcObject.getTracks().forEach(track => track.stop());
                    video.srcObject = null;
                }
                statusDiv.textContent = '已停止检测';
                statusDiv.style.backgroundColor = '#f0f0f0';
                processedCtx.clearRect(0, 0, processedCanvas.width, processedCanvas.height);
            }
            
            // 页面加载完成后自动开始
            window.onload = startDetection;
        </script>
    </body>
    </html>
    '''



@app.route('/gpt-sovites/tts', methods=['POST'])
def gpt_sovites_tts():
    """优化的语音合成实现，增加文本长度检查以避免模型错误，合成完成后返回轮询标识"""
    print("===== 进入语音合成接口 =====")
    try:
        # 导入必要模块
        import os
        import re
        import uuid
        import tempfile
        import time
        import json
        import urllib.parse
        import requests
        from flask import jsonify, request, Response
        
        # 1. 获取前端输入的文本和参数
        data = request.json
        if not data or 'text' not in data:
            print("错误：未收到文本数据")
            return jsonify({"status": "error", "message": "请提供需要合成的文本内容"}), 400
        print("收到前端数据：", data)
        
        # 生成唯一请求标识，用于跟踪不同请求
        request_id = str(uuid.uuid4())[:8]
        print(f"当前请求ID: {request_id}")
        
        # 2. 文本处理流程
        target_text = data['text']
        print(f"[{request_id}] 原始文本: {target_text}")
        
        # 步骤1：移除干扰标记
        cleaned_text = re.sub(r'<think>[\s\S]*?</think>', '', target_text)
        cleaned_text = re.sub(r'\s*think\/think\s*', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\\boxed\{(\d+)\}', r'\1', cleaned_text)
        cleaned_text = re.sub(r'\*\*', '', cleaned_text)
        cleaned_text = re.sub(r'<think>|<|FunctionCallEnd|>', '', cleaned_text)
        
        # 步骤2：数字转换逻辑
        NUM_MAP = {
            '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'
        }
        TEN_MAP = {
            '10': '十', '11': '十一', '12': '十二', '13': '十三', '14': '十四',
            '15': '十五', '16': '十六', '17': '十七', '18': '十八', '19': '十九',
            '20': '二十', '30': '三十', '40': '四十', '50': '五十', '60': '六十',
            '70': '七十', '80': '八十', '90': '九十'
        }
        
        def replace_numbers(match):
            num_str = match.group(0)
            if num_str in TEN_MAP:
                return TEN_MAP[num_str]
            if len(num_str) == 2 and num_str.isdigit():
                tens = num_str[0]
                units = num_str[1]
                if tens == '0':
                    return NUM_MAP[units]
                if units == '0':
                    return NUM_MAP[tens] + '十'
                return NUM_MAP[tens] + '十' + NUM_MAP[units]
            return ''.join([NUM_MAP[char] for char in num_str if char in NUM_MAP])
        
        cleaned_text = re.sub(r'\d+', replace_numbers, cleaned_text)
        
        # 步骤3：保留所有原始标点
        cleaned_text = re.sub(r'[^\u4e00-\u9fa50-9,.，。:：;；、？！]', '', cleaned_text)
        print(f"[{request_id}] 处理后文本: {cleaned_text}")
        
        if not cleaned_text:
            return jsonify({"status": "error", "message": "过滤后无有效合成内容"}), 400
        
        # 检查文本长度，BERT模型通常有512token限制
        MAX_TEXT_LENGTH = 170  # 留一些余量
        if len(cleaned_text) > MAX_TEXT_LENGTH:
            cleaned_text = cleaned_text[:MAX_TEXT_LENGTH]
            print(f"[{request_id}] 文本过长，已截断至{MAX_TEXT_LENGTH}字符")
        
        # 3. 初始化临时目录（确保在D:\Temp下）
        temp_dir = os.path.join("D:\\Temp", f"tts_single_{request_id}_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"[{request_id}] 临时目录: {temp_dir}")
        
        # 4. 单次合成音频
        api_base_url = "http://localhost:9872"
        ref_wav_path = r"E:\GPT-SoVITS-v3lora-20250228\GPT-SoVITS-v3lora-20250228\TEMP\gradio\1.wav"
        
        # 准备参考音频信息
        file_name = os.path.basename(ref_wav_path)
        file_size = os.path.getsize(ref_wav_path)
        encoded_path = urllib.parse.quote(ref_wav_path)
        reference_url = f"{api_base_url}/file={encoded_path}"
        
        # 重置模型状态
        def reset_model_state():
            try:
                requests.post(
                    f"{api_base_url}/change_sovits_weights",
                    json={
                        "sovits_path": "GPT_SoVITS/pretrained_models/s2G488k.pth",
                        "prompt_language": "中文",
                        "text_language": "中文"
                    },
                    timeout=10
                )
                print(f"[{request_id}] 模型状态已重置")
                return True
            except Exception as e:
                print(f"[{request_id}] 重置模型状态失败: {str(e)}")
                return False
        
        # 重置模型状态
        reset_model_state()
        
        # 使用更长的session_hash，确保唯一性
        session_hash = f"{request_id}_{uuid.uuid4().hex[:12]}"
        
        # 构建请求体
        payload = {
            "data": [
                {
                    "meta": {"_type": "gradio.FileData"},
                    "path": ref_wav_path,
                    "url": reference_url,
                    "orig_name": file_name,
                    "size": file_size,
                    "mime_type": "audio/wav"
                },
                "",  # prompt_text
                "中文",  # prompt_language
                cleaned_text,  # 完整文本（不分段）
                "中文",  # text_language
                "不切",  # how_to_cut
                15,  # top_k
                1.0,  # top_p
                0.7,  # temperature
                False,  # ref_free
                1.0,  # speed
                False,  # if_freeze
                None,  # inp_refs
                "32",  # sample_steps
                False,  # if_sr
                0.3   # pause_second
            ],
            "event_data": None,
            "fn_index": 1,
            "trigger_id": 47,
            "session_hash": session_hash
        }
        
        # 发送请求到/queue/join
        join_url = f"{api_base_url}/queue/join"
        try:
            join_response = requests.post(
                join_url,
                json=payload,
                timeout=60  # 延长超时时间
            )
            
            if join_response.status_code != 200:
                error_msg = f"[{request_id}] 请求失败: {join_response.status_code}, 详情: {join_response.text}"
                print(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 500
            
            event_id = join_response.json()["event_id"]
            print(f"[{request_id}] 获取到event_id: {event_id}")
            
            # 轮询/queue/data获取结果
            data_url = f"{api_base_url}/queue/data?session_hash={session_hash}&event_id={event_id}"
            audio_url = None
            max_retries = 120  # 增加重试次数
            retry_count = 0
            
            while retry_count < max_retries:
                retry_count += 1
                time.sleep(1)
                
                try:
                    data_response = requests.get(
                        data_url,
                        timeout=20,
                        stream=True
                    )
                    
                    if data_response.status_code != 200:
                        print(f"[{request_id}] 轮询第{retry_count}次失败, 状态码: {data_response.status_code}")
                        continue
                    
                    # 处理event-stream格式
                    for line in data_response.iter_lines():
                        if not line:
                            continue
                        
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            line_str = line_str[6:]
                        
                        try:
                            msg_data = json.loads(line_str)
                        except json.JSONDecodeError as e:
                            print(f"[{request_id}] 解析消息失败: {e}, 原始消息: {line_str}")
                            continue
                        
                        if msg_data.get("msg") == "process_completed":
                            if msg_data.get("success") is False:
                                error_msg = f"[{request_id}] 合成失败: {msg_data.get('output', {}).get('error')}"
                                print(error_msg)
                                return jsonify({"status": "error", "message": error_msg}), 500
                            
                            # 提取音频URL
                            audio_path_info = msg_data["output"]["data"][0]
                            audio_url = audio_path_info["url"]
                            break
                        elif msg_data.get("msg") == "process_generating":
                            print(f"[{request_id}] 合成中... 进度: {msg_data.get('output', {}).get('duration', 0)}s")
                        elif msg_data.get("msg") == "estimation":
                            print(f"[{request_id}] 排队中... 预计等待: {msg_data.get('rank_eta', 0)}s")
                    
                    if audio_url:
                        break
                        
                except requests.exceptions.Timeout:
                    print(f"[{request_id}] 轮询第{retry_count}次超时，继续重试")
                    continue
                except Exception as e:
                    print(f"[{request_id}] 轮询出错: {str(e)}")
                    continue
            
            if not audio_url:
                error_msg = f"[{request_id}] 合成超时"
                print(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 504
            
            # 下载音频文件到临时目录
            output_path = os.path.join(temp_dir, "final.wav")
            audio_response = requests.get(audio_url, timeout=30)
            
            if audio_response.status_code != 200:
                error_msg = f"[{request_id}] 下载音频失败，状态码: {audio_response.status_code}"
                print(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 500
            
            with open(output_path, 'wb') as f:
                f.write(audio_response.content)
            
            print(f"[{request_id}] 合成完成: {output_path}")
            print(f"[{request_id}] 临时文件保留路径: {temp_dir}")
            
            # 合成完成后返回轮询标识，不直接返回音频二进制
            return jsonify({
                "status": "success",
                "message": "音频合成已完成，可开始轮询获取最新音频",
                "request_id": request_id,
                "folder_prefix": f"tts_single_{request_id}"  # 用于前端验证文件夹
            })
            
        except Exception as e:
            error_msg = f"服务错误: {str(e)}"
            print(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
    except Exception as e:
        error_msg = f"服务错误: {str(e)}"
        print(error_msg)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500
    
    
@app.route('/gpt-sovites/get_latest_audio_url', methods=['GET'])
def get_latest_audio_url():
    """获取D:\Temp下最新文件夹中WAV文件的HTTPS链接"""
    try:
        import os
        import glob
        import urllib.parse
        from datetime import datetime
        
        # 配置：替换为你的HTTPS域名和文件访问路径
        # 需确保后端有静态文件映射，能通过此URL访问D:\Temp下的文件
        HTTPS_DOMAIN = "https://123.56.203.202"  # 你的服务器HTTPS域名
        FILE_PROXY_PATH = "/proxy_files"  # 后端文件代理路径（需提前配置）
        TEMP_ROOT = "D:\\Temp"
        
        # 检查目录是否存在
        if not os.path.exists(TEMP_ROOT):
            return jsonify({
                "status": "error",
                "message": f"目录不存在: {TEMP_ROOT}"
            }), 404
        
        # 获取所有子文件夹并按创建时间排序（最新的在前）
        subfolders = [f.path for f in os.scandir(TEMP_ROOT) if f.is_dir()]
        if not subfolders:
            return jsonify({
                "status": "error",
                "message": f"未找到子文件夹: {TEMP_ROOT}"
            }), 404
        
        # 按创建时间倒序排序（最新的文件夹优先）
        subfolders.sort(key=lambda x: os.path.getctime(x), reverse=True)
        latest_folder = subfolders[0]
        
        # 在最新文件夹中查找WAV文件
        wav_files = glob.glob(os.path.join(latest_folder, "*.wav"))
        if not wav_files:
            return jsonify({
                "status": "pending",  # 表示还未生成音频
                "message": f"最新文件夹中未找到WAV文件: {latest_folder}",
                "latest_folder": latest_folder
            }), 202  # 202表示请求已接受但未完成
        
        # 按创建时间排序WAV文件，取最新的一个
        wav_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        latest_wav = wav_files[0]
        
        # 生成HTTPS链接（通过后端文件代理）
        # 例如：将D:\Temp\folder\file.wav转换为https://domain/proxy_files?path=D:\Temp\folder\file.wav
        encoded_path = urllib.parse.quote(latest_wav)
        https_url = f"{HTTPS_DOMAIN}{FILE_PROXY_PATH}?path={encoded_path}"
        
        return jsonify({
            "status": "success",
            "audio_url": https_url,
            "file_path": latest_wav,
            "folder_path": latest_folder,
            "created_time": datetime.fromtimestamp(os.path.getctime(latest_wav)).strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取最新音频失败: {str(e)}"
        }), 500
    
    
    
    
@app.route('/gpt-sovites/tts_english', methods=['POST'])
def gpt_sovites_tts_english():
    """英文语音合成接口，优化处理流程，增加文本验证，返回轮询标识"""
    print("===== 进入英文语音合成接口 =====")
    try:
        # 导入必要模块
        import os
        import re
        import uuid
        import tempfile
        import time
        import json
        import urllib.parse
        import requests
        from flask import jsonify, request, Response
        
        # 1. 获取前端输入的文本和参数
        data = request.json
        if not data or 'text' not in data:
            print("错误：未收到文本数据")
            return jsonify({"status": "error", "message": "请提供需要合成的文本内容"}), 400
        print("收到前端数据：", data)
        
        # 生成唯一请求标识，用于跟踪不同请求
        request_id = str(uuid.uuid4())[:8]
        print(f"当前请求ID: {request_id}")
        
        # 2. 文本处理流程（针对英文优化）
        target_text = data['text']
        print(f"[{request_id}] 原始文本: {target_text}")
        
        # 步骤1：移除干扰标记
        cleaned_text = re.sub(r'<|FunctionCallBegin|>[\s\S]*?<|FunctionCallEnd|>', '', target_text)
        cleaned_text = re.sub(r'\s*think\/think\s*', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\\boxed\{(\d+)\}', r'\1', cleaned_text)
        cleaned_text = re.sub(r'\*\*', '', cleaned_text)
        cleaned_text = re.sub(r'superscript:|<|FunctionCallEnd|>', '', cleaned_text)
        
        # 步骤2：保留英文相关字符和标点
        # 允许英文、数字、常见标点和空格
        cleaned_text = re.sub(r'[^\u0041-\u005A\u0061-\u007A0-9,.!?\'\"()\s]', '', cleaned_text)
        
        # 步骤3：去除多余空格
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        print(f"[{request_id}] 处理后文本: {cleaned_text}")
        
        if not cleaned_text:
            return jsonify({"status": "error", "message": "过滤后无有效合成内容"}), 400
        
        # 检查文本长度，英文token通常比中文长，适当调整限制
        MAX_TEXT_LENGTH = 300  # 英文可容纳更多字符
        if len(cleaned_text) > MAX_TEXT_LENGTH:
            cleaned_text = cleaned_text[:MAX_TEXT_LENGTH]
            print(f"[{request_id}] 文本过长，已截断至{MAX_TEXT_LENGTH}字符")
        
        # 3. 初始化临时目录（确保在D:\Temp下，使用英文标识）
        temp_dir = os.path.join("D:\\Temp", f"tts_english_{request_id}_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"[{request_id}] 临时目录: {temp_dir}")
        
        # 4. 单次合成音频（使用英文参考音频和模型设置）
        api_base_url = "http://localhost:9872"
        # 使用英文参考音频
        ref_wav_path = r"E:\GPT-SoVITS-v3lora-20250228\GPT-SoVITS-v3lora-20250228\TEMP\gradio\1.wav"
        
        # 验证英文参考音频是否存在
        if not os.path.exists(ref_wav_path):
            error_msg = f"[{request_id}] 英文参考音频不存在: {ref_wav_path}"
            print(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 500
        
        # 准备参考音频信息
        file_name = os.path.basename(ref_wav_path)
        file_size = os.path.getsize(ref_wav_path)
        encoded_path = urllib.parse.quote(ref_wav_path)
        reference_url = f"{api_base_url}/file={encoded_path}"
        
        # 重置模型状态（针对英文设置）
        def reset_model_state():
            try:
                requests.post(
                    f"{api_base_url}/change_sovits_weights",
                    json={
                        "sovits_path": "GPT_SoVITS/pretrained_models/s2G488k_en.pth",  # 英文模型
                        "prompt_language": "英文",
                        "text_language": "英文"
                    },
                    timeout=10
                )
                print(f"[{request_id}] 英文模型状态已重置")
                return True
            except Exception as e:
                print(f"[{request_id}] 重置英文模型状态失败: {str(e)}")
                return False
        
        # 重置模型状态
        reset_model_state()
        
        # 使用更长的session_hash，确保唯一性
        session_hash = f"en_{request_id}_{uuid.uuid4().hex[:12]}"
        
        # 构建请求体（针对英文优化参数）
        payload = {
            "data": [
                {
                    "meta": {"_type": "gradio.FileData"},
                    "path": ref_wav_path,
                    "url": reference_url,
                    "orig_name": file_name,
                    "size": file_size,
                    "mime_type": "audio/wav"
                },
                "",  # prompt_text（英文通常不需要提示文本）
                "英文",  # prompt_language
                cleaned_text,  # 完整文本（不分段）
                "英文",  # text_language
                "不切",  # how_to_cut
                15,  # top_k（英文合成推荐值）
                0.9,  # top_p（英文合成适当提高）
                0.8,  # temperature（英文合成适当提高）
                False,  # ref_free
                1.0,  # speed（英文语速通常保持默认）
                False,  # if_freeze
                None,  # inp_refs
                "32",  # sample_steps
                False,  # if_sr
                0.2   # pause_second（英文停顿稍短）
            ],
            "event_data": None,
            "fn_index": 1,
            "trigger_id": 47,
            "session_hash": session_hash
        }
        
        # 发送请求到/queue/join
        join_url = f"{api_base_url}/queue/join"
        try:
            join_response = requests.post(
                join_url,
                json=payload,
                timeout=60  # 延长超时时间
            )
            
            if join_response.status_code != 200:
                error_msg = f"[{request_id}] 请求失败: {join_response.status_code}, 详情: {join_response.text}"
                print(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 500
            
            event_id = join_response.json()["event_id"]
            print(f"[{request_id}] 获取到event_id: {event_id}")
            
            # 轮询/queue/data获取结果
            data_url = f"{api_base_url}/queue/data?session_hash={session_hash}&event_id={event_id}"
            audio_url = None
            max_retries = 120  # 增加重试次数
            retry_count = 0
            
            while retry_count < max_retries:
                retry_count += 1
                time.sleep(1)
                
                try:
                    data_response = requests.get(
                        data_url,
                        timeout=20,
                        stream=True
                    )
                    
                    if data_response.status_code != 200:
                        print(f"[{request_id}] 轮询第{retry_count}次失败, 状态码: {data_response.status_code}")
                        continue
                    
                    # 处理event-stream格式
                    for line in data_response.iter_lines():
                        if not line:
                            continue
                        
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            line_str = line_str[6:]
                        
                        try:
                            msg_data = json.loads(line_str)
                        except json.JSONDecodeError as e:
                            print(f"[{request_id}] 解析消息失败: {e}, 原始消息: {line_str}")
                            continue
                        
                        if msg_data.get("msg") == "process_completed":
                            if msg_data.get("success") is False:
                                error_msg = f"[{request_id}] 合成失败: {msg_data.get('output', {}).get('error')}"
                                print(error_msg)
                                return jsonify({"status": "error", "message": error_msg}), 500
                            
                            # 提取音频URL
                            audio_path_info = msg_data["output"]["data"][0]
                            audio_url = audio_path_info["url"]
                            break
                        elif msg_data.get("msg") == "process_generating":
                            print(f"[{request_id}] 合成中... 进度: {msg_data.get('output', {}).get('duration', 0)}s")
                        elif msg_data.get("msg") == "estimation":
                            print(f"[{request_id}] 排队中... 预计等待: {msg_data.get('rank_eta', 0)}s")
                    
                    if audio_url:
                        break
                        
                except requests.exceptions.Timeout:
                    print(f"[{request_id}] 轮询第{retry_count}次超时，继续重试")
                    continue
                except Exception as e:
                    print(f"[{request_id}] 轮询出错: {str(e)}")
                    continue
            
            if not audio_url:
                error_msg = f"[{request_id}] 合成超时"
                print(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 504
            
            # 下载音频文件到临时目录
            output_path = os.path.join(temp_dir, "final_english.wav")
            audio_response = requests.get(audio_url, timeout=30)
            
            if audio_response.status_code != 200:
                error_msg = f"[{request_id}] 下载音频失败，状态码: {audio_response.status_code}"
                print(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 500
            
            with open(output_path, 'wb') as f:
                f.write(audio_response.content)
            
            print(f"[{request_id}] 英文合成完成: {output_path}")
            print(f"[{request_id}] 临时文件保留路径: {temp_dir}")
            
            # 合成完成后返回轮询标识，不直接返回音频二进制
            return jsonify({
                "status": "success",
                "message": "英文音频合成已完成，可开始轮询获取最新音频",
                "request_id": request_id,
                "folder_prefix": f"tts_english_{request_id}"  # 用于前端验证文件夹
            })
            
        except Exception as e:
            error_msg = f"服务错误: {str(e)}"
            print(error_msg)
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
    except Exception as e:
        error_msg = f"服务错误: {str(e)}"
        print(error_msg)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500


@app.route('/gpt-sovites/get_latest_english_audio_url', methods=['GET'])
def get_latest_english_audio_url():
    """获取D:\Temp下最新英文音频文件夹中WAV文件的HTTPS链接"""
    try:
        import os
        import glob
        import urllib.parse
        from datetime import datetime
        
        # 配置：替换为你的HTTPS域名和文件访问路径
        HTTPS_DOMAIN = "https://123.56.203.202"  # 你的服务器HTTPS域名
        FILE_PROXY_PATH = "/proxy_files"  # 后端文件代理路径（需提前配置）
        TEMP_ROOT = "D:\\Temp"
        
        # 检查目录是否存在
        if not os.path.exists(TEMP_ROOT):
            return jsonify({
                "status": "error",
                "message": f"目录不存在: {TEMP_ROOT}"
            }), 404
        
        # 获取所有英文音频子文件夹并按创建时间排序（最新的在前）
        # 只筛选以tts_english_开头的文件夹
        subfolders = [
            f.path for f in os.scandir(TEMP_ROOT) 
            if f.is_dir() and f.name.startswith("tts_english_")
        ]
        
        if not subfolders:
            return jsonify({
                "status": "error",
                "message": f"未找到英文音频子文件夹: {TEMP_ROOT}"
            }), 404
        
        # 按创建时间倒序排序（最新的文件夹优先）
        subfolders.sort(key=lambda x: os.path.getctime(x), reverse=True)
        latest_folder = subfolders[0]
        
        # 在最新文件夹中查找WAV文件
        wav_files = glob.glob(os.path.join(latest_folder, "*.wav"))
        if not wav_files:
            return jsonify({
                "status": "pending",  # 表示还未生成音频
                "message": f"最新英文音频文件夹中未找到WAV文件: {latest_folder}",
                "latest_folder": latest_folder
            }), 202  # 202表示请求已接受但未完成
        
        # 按创建时间排序WAV文件，取最新的一个
        wav_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        latest_wav = wav_files[0]
        
        # 生成HTTPS链接（通过后端文件代理）
        encoded_path = urllib.parse.quote(latest_wav)
        https_url = f"{HTTPS_DOMAIN}{FILE_PROXY_PATH}?path={encoded_path}"
        
        return jsonify({
            "status": "success",
            "audio_url": https_url,
            "file_path": latest_wav,
            "folder_path": latest_folder,
            "created_time": datetime.fromtimestamp(os.path.getctime(latest_wav)).strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取最新英文音频失败: {str(e)}"
        }), 500
   

# 虚拟人配置
VIRTUAL_CHARACTER_CONFIG = {
    "default_avatar": "female_avatar",  # 默认虚拟人形象
    "animation_speed": 1.0,             # 动画播放速度
    "emotion_intensity": 0.8,           # 情感表现强度
    "voice_pitch": 1.0,                 # 语音音调
    "default_language": "zh-CN"         # 默认语言
}

# 虚拟人动画库 - 存储基础动作与表情映射
ANIMATION_LIBRARY = {
    "idle": "idle_animation.json",              # 空闲状态
    "talking": "talking_animation.json",        # 说话状态
    "happy": "happy_animation.json",            # 开心表情
    "sad": "sad_animation.json",                # 悲伤表情
    "angry": "angry_animation.json",            # 愤怒表情
    "surprised": "surprised_animation.json",    # 惊讶表情
    "thinking": "thinking_animation.json"       # 思考状态
}

# WebSocket连接管理
websocket_connections = set()

async def websocket_proxy_handler(request):
    """将3000端口的WebSocket请求转发到8765端口"""
    # 建立到8765端口的WebSocket连接
    ws_8765 = await websockets.connect('ws://localhost:8765')
    
    # 为客户端创建响应WebSocket
    ws_response = web.WebSocketResponse()
    await ws_response.prepare(request)
    
    async def forward(src, dst):
        """双向转发消息"""
        try:
            async for msg in src:
                if isinstance(msg, str):
                    await dst.send(msg)
                else:
                    await dst.send(msg.data)
        except websockets.exceptions.ConnectionClosed:
            pass
    
    # 启动双向转发
    await asyncio.gather(
        forward(ws_8765, ws_response),
        forward(ws_response, ws_8765)
    )
    
    return ws_response

def start_websocket_server():
    """启动WebSocket服务，适配旧版本websockets库（仅需websocket参数）"""
    # 处理函数只接收websocket参数（适配旧版本库）
    async def websocket_handler(websocket):
        print("新的WebSocket连接加入")
        websocket_connections.add(websocket)
        try:
            async for message in websocket:
                data = json_lib.loads(message)
                print(f"收到客户端消息: {data}")
                # 消息处理逻辑...
        except Exception as e:
            print(f"WebSocket消息处理错误: {e}")
        finally:
            if websocket in websocket_connections:
                websocket_connections.remove(websocket)
            print("WebSocket连接已关闭")
    
    async def run_server():
        # 启动服务
        start_server = await websockets.serve(
            websocket_handler,  # 现在处理函数只有一个参数
            "0.0.0.0", 
            8765
        )
        print("WebSocket服务已启动，端口: 8765")
        await start_server.wait_closed()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_server())
    except Exception as e:
        print(f"WebSocket服务启动失败: {str(e)}")
        traceback.print_exc()
    finally:
        loop.close()


# 发送消息给所有连接的客户端
async def broadcast_message(message):
    if websocket_connections:
        await asyncio.gather(
            *[connection.send(json_lib.dumps(message)) for connection in websocket_connections]
        )

# 虚拟人情感分析模块
def analyze_text_emotion(text):
    """分析文本情感倾向"""
    # 实际项目中可替换为更复杂的NLP模型
    # 这里使用简单关键词匹配作为示例
    
    # 情感词库
    positive_words = ["好", "开心", "高兴", "棒", "成功", "喜欢", "满意", "优秀"]
    negative_words = ["坏", "难过", "生气", "糟糕", "失败", "讨厌", "不满", "差"]
    surprised_words = ["惊讶", "居然", "没想到", "突然", "哇"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    surprised_count = sum(1 for word in surprised_words if word in text_lower)
    
    # 确定主要情感
    if surprised_count > 0:
        return {
            "emotion": "surprised",
            "confidence": min(0.5 + surprised_count * 0.1, 1.0)
        }
    elif positive_count > negative_count:
        return {
            "emotion": "happy",
            "confidence": min(0.5 + positive_count * 0.1, 1.0)
        }
    elif negative_count > positive_count:
        return {
            "emotion": "angry" if negative_count > 1 else "sad",
            "confidence": min(0.5 + negative_count * 0.1, 1.0)
        }
    else:
        return {
            "emotion": "neutral",
            "confidence": 1.0
        }

def map_emotion_to_animation(emotion_result, current_action="idle"):
    """将情感结果映射为虚拟人动画"""
    emotion = emotion_result["emotion"]
    confidence = emotion_result["confidence"]
    
    # 情感强度足够时才切换表情
    if confidence > 0.6:
        if emotion in ANIMATION_LIBRARY:
            return {
                "primary_animation": ANIMATION_LIBRARY[emotion],
                "secondary_animation": ANIMATION_LIBRARY["talking"],
                "blend_weight": min(confidence, 1.0),
                "duration": 3.0  # 情感动画持续时间
            }
    
    # 默认返回当前动作
    return {
        "primary_animation": ANIMATION_LIBRARY[current_action],
        "secondary_animation": None,
        "blend_weight": 1.0,
        "duration": 0
    }

def generate_visemes(text):
    """生成与文本同步的唇形数据（Viseme）"""
    # 简单的音节到唇形映射示例
    viseme_map = {
        'a': 1, 'i': 2, 'u': 3, 'e': 4, 'o': 5,
        'b': 6, 'p': 6, 'm': 6,
        'f': 7, 'v': 7,
        'd': 8, 't': 8, 'n': 8,
        'l': 9,
        'g': 10, 'k': 10, 'h': 10,
        'j': 11, 'q': 11, 'x': 11,
        'zh': 12, 'ch': 12, 'sh': 12, 'r': 12,
        'z': 13, 'c': 13, 's': 13,
        'sil': 0  # 静音
    }
    
    # 简单分词（实际项目中应使用专业分词库）
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', text)
    visemes = []
    timestamp = 0.0
    interval = 0.15  # 每个音节持续时间
    
    for word in words:
        # 对于中文，每个字一个音节
        if re.match(r'^[\u4e00-\u9fa5]+$', word):
            for char in word:
                # 这里简化处理，实际应根据拼音确定
                viseme = viseme_map.get('a', 0)  # 默认值
                visemes.append({
                    "timestamp": round(timestamp, 2),
                    "viseme_id": viseme,
                    "duration": interval
                })
                timestamp += interval
        else:
            # 处理英文
            for char in word.lower():
                viseme = viseme_map.get(char, 0)
                visemes.append({
                    "timestamp": round(timestamp, 2),
                    "viseme_id": viseme,
                    "duration": interval
                })
                timestamp += interval
    
    return visemes

# ====================== 虚拟人驱动接口 ======================
@app.route('/virtual_character/drive', methods=['POST'])
def drive_virtual_character():
    """驱动虚拟人，整合语音、表情、动作数据"""
    try:
        data = request.json
        
        # 1. 验证输入
        input_text = data.get('text', '')
        input_audio = data.get('audio', None)
        
        if not input_text and not input_audio:
            return jsonify({
                "status": "error", 
                "message": "请提供文本或音频输入"
            }), 400
        
        # 2. 处理语音输入（如果提供）
        recognized_text = input_text
        if input_audio:
            # 调用现有语音识别接口
            audio_response = recognize_speech_from_base64(input_audio)
            if audio_response.get('status') == 'success':
                recognized_text = audio_response.get('text', input_text)
        
        # 3. 获取对话回应
        chat_response = requests.post(
            "http://localhost:3000/api/chat",
            json={"prompt": recognized_text}
        ).json()
        
        if chat_response.get('status') != 'success':
            return jsonify({
                "status": "error",
                "message": f"对话处理失败: {chat_response.get('result')}"
            }), 500
        
        reply_text = chat_response.get('result', '')
        
        # 4. 分析情感
        emotion_result = analyze_text_emotion(reply_text)
        
        # 5. 生成语音
        tts_response = requests.post(
            "http://localhost:3000/gpt-sovites/tts",
            json={"text": reply_text}
        )
        
        if tts_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"语音合成失败: {tts_response.text}"
            }), tts_response.status_code
        
        # 保存音频到临时文件
        audio_filename = f"virtual_character_{uuid.uuid4()}.wav"
        audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
        
        with open(audio_path, 'wb') as f:
            f.write(tts_response.content)
        
        # 6. 生成唇形同步数据
        visemes = generate_visemes(reply_text)
        
        # 7. 生成动画指令
        animation = map_emotion_to_animation(emotion_result)
        
        # 8. 生成语调分析
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        y, sample_rate = sf.read(io.BytesIO(audio_data))
        tone_result = extract_f0(y, sample_rate)
        
        # 9. 准备响应数据
        response_data = {
            "status": "success",
            "text": reply_text,
            "recognized_text": recognized_text,
            "emotion": emotion_result,
            "animation": animation,
            "visemes": visemes,
            "tone": tone_result,
            "audio_url": f"/temp_audio/{audio_filename}",
            "timestamp": datetime.now().isoformat()
        }
        
        # 10. 通过WebSocket广播更新
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(broadcast_message({
            "type": "character_update",
            "data": response_data
        }))
        loop.close()
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"虚拟人驱动失败: {str(e)}"
        print(error_msg)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500

# 辅助函数：从base64处理语音识别
def recognize_speech_from_base64(base64_audio):
    try:
        # 解码base64音频
        audio_bytes = base64.b64decode(base64_audio)
        
        # 保存为临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        # 调用现有语音识别逻辑
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model-small-cn-0.22")
        
        if not os.path.exists(model_path):
            os.unlink(temp_file_path)
            return {"status": "error", "message": f"模型路径不存在: {model_path}"}
        
        # 转换音频格式（如果需要）
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_temp_file:
            wav_temp_path = wav_temp_file.name
        
        if not convert_to_wav(temp_file_path, wav_temp_path):
            os.unlink(temp_file_path)
            os.unlink(wav_temp_path)
            return {"status": "error", "message": "音频转换失败"}
        
        audio_path = wav_temp_path
        
        # 执行语音识别
        results = []
        with wave.open(audio_path, "rb") as wf:
            model = Model(model_path)
            recognizer = KaldiRecognizer(model, wf.getframerate())
            
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    partial = json_lib.loads(recognizer.Result())
                    results.append(partial["text"])
            
            final = json_lib.loads(recognizer.FinalResult())
            results.append(final["text"])
        
        # 清理临时文件
        os.unlink(temp_file_path)
        os.unlink(wav_temp_path)
        
        full_text = " ".join(results).strip()
        return {"status": "success", "text": full_text}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 提供临时音频文件访问
@app.route('/temp_audio/<filename>')
def get_temp_audio(filename):
    audio_path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(audio_path):
        return jsonify({"status": "error", "message": "音频文件不存在"}), 404
    
    return Response(
        open(audio_path, 'rb').read(),
        mimetype="audio/wav",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

# ====================== 虚拟人管理接口 ======================
@app.route('/virtual_character/set_avatar', methods=['POST'])
def set_virtual_avatar():
    """设置虚拟人形象"""
    try:
        data = request.json
        avatar_name = data.get('avatar_name')
        
        if not avatar_name:
            return jsonify({
                "status": "error",
                "message": "请提供虚拟人形象名称"
            }), 400
        
        # 实际项目中应验证形象是否存在
        VIRTUAL_CHARACTER_CONFIG["default_avatar"] = avatar_name
        
        # 广播形象变更
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(broadcast_message({
            "type": "avatar_changed",
            "data": {
                "avatar_name": avatar_name
            }
        }))
        loop.close()
        
        return jsonify({
            "status": "success",
            "message": f"已切换虚拟人形象为: {avatar_name}",
            "current_avatar": avatar_name
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"设置虚拟人形象失败: {str(e)}"
        }), 500

@app.route('/virtual_character/get_config', methods=['GET'])
def get_virtual_character_config():
    """获取当前虚拟人配置"""
    return jsonify({
        "status": "success",
        "config": VIRTUAL_CHARACTER_CONFIG,
        "available_animations": list(ANIMATION_LIBRARY.keys()),
        "current_avatar": VIRTUAL_CHARACTER_CONFIG["default_avatar"]
    })

@app.route('/virtual_character/update_config', methods=['POST'])
def update_virtual_character_config():
    """更新虚拟人配置参数"""
    try:
        data = request.json
        valid_keys = ["animation_speed", "emotion_intensity", "voice_pitch", "default_language"]
        
        # 更新配置
        for key in valid_keys:
            if key in data:
                VIRTUAL_CHARACTER_CONFIG[key] = data[key]
        
        # 广播配置变更
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(broadcast_message({
            "type": "config_updated",
            "data": VIRTUAL_CHARACTER_CONFIG
        }))
        loop.close()
        
        return jsonify({
            "status": "success",
            "message": "虚拟人配置已更新",
            "config": VIRTUAL_CHARACTER_CONFIG
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"更新虚拟人配置失败: {str(e)}"
        }), 500

@app.route('/virtual_character')
def virtual_character_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>虚拟人交互界面</title>
        <style>
            body { 
                font-family: 'Microsoft YaHei', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .character-container {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            #character-view {
                width: 800px;
                height: 600px;
                background-color: #f0f8ff;
                border-radius: 8px;
                overflow: hidden;
                position: relative;
                margin-bottom: 20px;
            }
            #character-placeholder {
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 24px;
                color: #666;
            }
            .controls {
                width: 800px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                min-height: 100px;
                font-size: 16px;
            }
            .button-group {
                display: flex;
                gap: 10px;
            }
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                background-color: #4285f4;
                color: white;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #3367d6;
            }
            .status-panel {
                background-color: #e8f4fd;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
                width: 800px;
            }
            .status-item {
                margin-bottom: 8px;
                font-size: 14px;
            }
            .avatar-selector {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            }
            .avatar-option {
                width: 80px;
                height: 80px;
                border-radius: 8px;
                cursor: pointer;
                overflow: hidden;
                border: 2px solid transparent;
            }
            .avatar-option.selected {
                border-color: #4285f4;
            }
            .avatar-option img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>虚拟人交互演示</h1>
            
            <div class="character-container">
                <div id="character-view">
                    <div id="character-placeholder">
                        虚拟人将在这里显示
                    </div>
                </div>
                
                <div class="avatar-selector">
                    <div class="avatar-option selected" data-avatar="female_avatar">
                        <img src="https://picsum.photos/id/64/200/200" alt="女性虚拟人">
                    </div>
                    <div class="avatar-option" data-avatar="male_avatar">
                        <img src="https://picsum.photos/id/91/200/200" alt="男性虚拟人">
                    </div>
                    <div class="avatar-option" data-avatar="cartoon_avatar">
                        <img src="https://picsum.photos/id/237/200/200" alt="卡通虚拟人">
                    </div>
                </div>
                
                <div class="controls">
                    <textarea id="input-text" placeholder="请输入你想对虚拟人说的话..."></textarea>
                    <div class="button-group">
                        <button id="send-btn">发送消息</button>
                        <button id="voice-btn">语音输入</button>
                        <button id="reset-btn">重置虚拟人</button>
                    </div>
                </div>
                
                <div class="status-panel">
                    <h3>状态信息</h3>
                    <div class="status-item">
                        <strong>当前情感:</strong> <span id="emotion-status">中性</span>
                    </div>
                    <div class="status-item">
                        <strong>当前动作:</strong> <span id="action-status">空闲</span>
                    </div>
                    <div class="status-item">
                        <strong>语音状态:</strong> <span id="voice-status">未播放</span>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // WebSocket连接
            let websocket;
            let audioElement = null;
            
            // 初始化WebSocket
            function initWebSocket() {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUri = `${wsProtocol}//${window.location.hostname}:8765/`;
                
                websocket = new WebSocket(wsUri);
                
                websocket.onopen = function(evt) {
                    console.log('WebSocket连接已打开');
                };
                
                websocket.onclose = function(evt) {
                    console.log('WebSocket连接已关闭，将在5秒后重连');
                    setTimeout(initWebSocket, 5000);
                };
                
                websocket.onmessage = function(evt) {
                    handleWebSocketMessage(evt);
                };
                
                websocket.onerror = function(evt) {
                    console.error('WebSocket错误:', evt);
                };
            }
            
            // 处理WebSocket消息
            function handleWebSocketMessage(evt) {
                try {
                    const message = JSON.parse(evt.data);
                    console.log('收到消息:', message);
                    
                    switch(message.type) {
                        case 'character_update':
                            updateCharacter(message.data);
                            break;
                        case 'avatar_changed':
                            updateAvatarDisplay(message.data.avatar_name);
                            break;
                        case 'config_updated':
                            console.log('配置已更新:', message.data);
                            break;
                    }
                } catch (e) {
                    console.error('解析WebSocket消息失败:', e);
                }
            }
            
            // 更新虚拟人状态
            function updateCharacter(data) {
                // 更新状态面板
                document.getElementById('emotion-status').textContent = 
                    data.emotion.emotion + ' (' + (data.emotion.confidence * 100).toFixed(0) + '%)';
                document.getElementById('action-status').textContent = 
                    data.animation.primary_animation.replace('_animation.json', '');
                
                // 播放语音
                if (data.audio_url) {
                    playAudio(data.audio_url);
                }
                
                // 显示回应文本（可以在这里添加气泡对话效果）
                console.log('虚拟人回应:', data.text);
                
                // 模拟动画效果（实际项目中应驱动3D/2D模型）
                animateCharacter(data.animation, data.visemes);
            }
            
            // 播放音频
            function playAudio(audioUrl) {
                if (audioElement) {
                    audioElement.pause();
                }
                
                audioElement = new Audio(audioUrl);
                document.getElementById('voice-status').textContent = '播放中...';
                
                audioElement.onplay = function() {
                    document.getElementById('voice-status').textContent = '播放中...';
                };
                
                audioElement.onended = function() {
                    document.getElementById('voice-status').textContent = '播放完成';
                };
                
                audioElement.onerror = function() {
                    document.getElementById('voice-status').textContent = '播放失败';
                };
                
                audioElement.play();
            }
            
            // 模拟虚拟人动画
            function animateCharacter(animation, visemes) {
                const placeholder = document.getElementById('character-placeholder');
                
                // 简单动画效果
                placeholder.style.transition = 'all 0.3s ease';
                
                // 根据情感改变背景色
                switch(animation.primary_animation) {
                    case 'happy_animation.json':
                        document.getElementById('character-view').style.backgroundColor = '#fff0f3';
                        break;
                    case 'angry_animation.json':
                        document.getElementById('character-view').style.backgroundColor = '#fff0f0';
                        break;
                    case 'sad_animation.json':
                        document.getElementById('character-view').style.backgroundColor = '#f0f4ff';
                        break;
                    default:
                        document.getElementById('character-view').style.backgroundColor = '#f0f8ff';
                }
                
                // 模拟说话动作
                let scale = 1.0;
                const interval = setInterval(() => {
                    scale = 1.0 + (Math.sin(Date.now() * 0.005) * 0.02);
                    placeholder.style.transform = `scale(${scale})`;
                }, 100);
                
                // 一段时间后停止动画
                setTimeout(() => {
                    clearInterval(interval);
                    placeholder.style.transform = 'scale(1.0)';
                }, animation.duration * 1000);
            }
            
            // 更新虚拟人形象显示
            function updateAvatarDisplay(avatarName) {
                console.log('切换到虚拟人形象:', avatarName);
                // 实际项目中应加载对应的3D/2D模型
            }
            
            // 发送消息给虚拟人
            function sendMessageToCharacter() {
                const inputText = document.getElementById('input-text').value.trim();
                if (!inputText) return;
                
                fetch('/virtual_character/drive', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: inputText })
                })
                .then(response => response.json())
                .then(data => {
                    console.log('发送成功:', data);
                    if (data.status === 'success') {
                        document.getElementById('input-text').value = '';
                    }
                })
                .catch(error => {
                    console.error('发送失败:', error);
                });
            }
            
            // 初始化页面事件
            function initEvents() {
                // 发送按钮点击事件
                document.getElementById('send-btn').addEventListener('click', sendMessageToCharacter);
                
                // 回车键发送消息
                document.getElementById('input-text').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessageToCharacter();
                    }
                });
                
                // 重置按钮
                document.getElementById('reset-btn').addEventListener('click', function() {
                    fetch('/virtual_character/update_config', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({})
                    });
                    
                    if (audioElement) {
                        audioElement.pause();
                    }
                    
                    document.getElementById('voice-status').textContent = '未播放';
                    document.getElementById('emotion-status').textContent = '中性';
                    document.getElementById('action-status').textContent = '空闲';
                    document.getElementById('character-view').style.backgroundColor = '#f0f8ff';
                });
                
                // 语音输入按钮
                document.getElementById('voice-btn').addEventListener('click', function() {
                    alert('语音输入功能将在这里实现');
                    // 实际项目中应实现语音录制和上传
                });
                
                // 虚拟人形象选择
                document.querySelectorAll('.avatar-option').forEach(option => {
                    option.addEventListener('click', function() {
                        // 移除其他选中状态
                        document.querySelectorAll('.avatar-option').forEach(o => {
                            o.classList.remove('selected');
                        });
                        // 添加当前选中状态
                        this.classList.add('selected');
                        
                        // 发送请求切换虚拟人
                        const avatarName = this.getAttribute('data-avatar');
                        fetch('/virtual_character/set_avatar', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ avatar_name: avatarName })
                        });
                    });
                });
            }
            
            // 页面加载完成后初始化
            window.onload = function() {
                initWebSocket();
                initEvents();
                
                // 获取初始配置
                fetch('/virtual_character/get_config')
                    .then(response => response.json())
                    .then(data => {
                        console.log('初始配置:', data);
                    });
            };
        </script>
    </body>
    </html>
    '''

# 2. 添加Flask路由（确保这些路由能被3000端口访问）
@app.route('/home')
def home_page():
    """根路径页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>虚拟人交互系统</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #333; }
            .link { color: #007bff; text-decoration: none; font-size: 1.2em; }
            .link:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>虚拟人交互系统已启动</h1>
        <p>点击进入：<a href="/virtual_character" class="link">虚拟人交互页面</a></p>
    </body>
    </html>
    '''

def start_combined_server():
    """在3000端口同时启动Flask和WebSocket代理（彻底修复属性错误）"""
    # 将Flask应用转换为aiohttp可处理的应用
    wsgi_handler = aiohttp_wsgi.WSGIHandler(app)
    
    # 创建aiohttp应用
    aio_app = web.Application()
    
    
    # 配置路由映射
    aio_app.router.add_route('GET', '/ws', websocket_proxy_handler)
    aio_app.router.add_route('*', '/{path_info:.*}', wsgi_handler)
    
    # 注册启动钩子
    aio_app.on_startup.append(on_startup)
    
    # 实际启动服务器
    web.run_app(
        aio_app,
        host='0.0.0.0',
        port=3000,
        access_log=None  # 可选：禁用访问日志
    )
    

# 启动时的日志函数（独立定义）
async def on_startup(aio_app):
    print("3000端口服务已启动，路由映射:")
    print("  - WebSocket: /ws -> 转发到8765端口")
    print("  - HTTP请求: 所有路径 -> 由Flask处理")
    

from flask import Flask, request, Response
import requests
import mimetypes
import threading
import time
import queue
from flask_sock import Sock
import websocket
import re
import subprocess
import sys
# 添加路由检查（放在所有路由定义之后）
print("Flask应用注册的路由:")
for rule in app.url_map.iter_rules():
    print(f"  - {rule.rule} -> {rule.endpoint}")

sock = Sock(app)

# 配置参数
PUBLIC_DOMAIN = "http://123.56.203.202"  # 改为HTTP协议，匹配FRP配置
LOCAL_HOST = "localhost"
LOCAL_PORT = 8282  # 本地服务端口
PROXY_PORT = 3000  # 代理服务端口

# 提取公网域名和端口
public_parts = PUBLIC_DOMAIN.split('://')[1].split(':')
PUBLIC_DOMAIN_HOST = public_parts[0]
PUBLIC_DOMAIN_PORT = public_parts[1] if len(public_parts) > 1 else "80"

# 信任的外部资源域名
TRUSTED_DOMAINS = [
    "https://cdnjs.cloudflare.com",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com"
]

# 通用CSP策略生成函数 - 移除不支持的指令
def get_csp_headers():
    return {
        'default-src': f"'self' blob: http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}",
        'connect-src': f"'self' blob: ws://{PUBLIC_DOMAIN_HOST}:{PUBLIC_DOMAIN_PORT} http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}",
        'style-src': f"'self' 'unsafe-inline' http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}",
        'script-src': f"'self' 'unsafe-inline' 'unsafe-eval' blob: http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}",
        'font-src': f"'self' blob: data: http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}",
        'img-src': f"'self' blob: data: http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}",
        'worker-src': f"'self' blob: http://{LOCAL_HOST}:{LOCAL_PORT}",
        'script-src-elem': f"'self' 'unsafe-inline' 'unsafe-eval' blob: http://{LOCAL_HOST}:{LOCAL_PORT} {' '.join(TRUSTED_DOMAINS)}"
    }

# 构建CSP头部字符串
def build_csp_header():
    csp = get_csp_headers()
    return '; '.join([f"{key} {value}" for key, value in csp.items()])

# 1. 静态资源转发
@app.route('/assets/<path:filename>', methods=['GET', 'OPTIONS'])
def proxy_assets(filename):
    local_asset_prefix = f"http://{LOCAL_HOST}:{LOCAL_PORT}/ui/assets"
    target_url = f"{local_asset_prefix}/{filename}"
    query_params = request.query_string.decode()
    if query_params:
        target_url += f"?{query_params}"
    
    headers = {
        'Host': f"{LOCAL_HOST}:{LOCAL_PORT}",
        'User-Agent': request.headers.get('User-Agent'),
        'Accept': request.headers.get('Accept'),
        'Cookie': request.headers.get('Cookie', '')
    }
    
    try:
        with requests.get(
            url=target_url,
            headers=headers,
            stream=True,
            verify=False
        ) as local_response:
            if local_response.status_code == 404:
                return f"本地资源不存在: {target_url}", 404
            
            mime_type, _ = mimetypes.guess_type(filename)
            content_type = local_response.headers.get('Content-Type', mime_type)
            
            if filename.endswith('.js') and 'javascript' not in str(content_type).lower():
                content_type = 'text/javascript'
            
            response_headers = {
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Set-Cookie': local_response.headers.get('Set-Cookie', ''),
                'Content-Security-Policy': build_csp_header()
            }
            
            return Response(
                local_response.content,
                status=local_response.status_code,
                headers=response_headers
            )
    except Exception as e:
        return f"资源转发失败: {str(e)}", 500

# 2. UI页面转发
@app.route('/ui', defaults={'subpath': ''}, methods=['GET', 'POST', 'OPTIONS'])
@app.route('/ui/<path:subpath>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_ui(subpath):    
    target_url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/ui/{subpath}" if subpath else f"http://{LOCAL_HOST}:{LOCAL_PORT}/ui/"
    query_params = request.query_string.decode()
    if query_params:
        target_url += f"?{query_params}"
    
    headers = {
        'Host': f"{LOCAL_HOST}:{LOCAL_PORT}",
        'Cookie': request.headers.get('Cookie', '')
    }
    
    try:
        with requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            verify=False
        ) as resp:
            content = resp.content.decode('utf-8')
            
            # 替换WebSocket地址为ws协议（匹配FRP配置）
            content = re.sub(
                rf'ws://(localhost|127\.0\.0\.1):{LOCAL_PORT}/ws/lam_data_stream/',
                f'ws://{PUBLIC_DOMAIN_HOST}:{PUBLIC_DOMAIN_PORT}/ws/lam_data_stream/',
                content
            )
            
            # 替换本地HTTP资源地址
            content = re.sub(
                rf'http://(localhost|127\.0\.0\.1):{LOCAL_PORT}/',
                f'{PUBLIC_DOMAIN}/',
                content
            )
            
            response_headers = {
                'Content-Type': 'text/html; charset=utf-8',
                'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
                'Access-Control-Allow-Credentials': 'true',
                'Set-Cookie': resp.headers.get('Set-Cookie', ''),
                'Content-Security-Policy': build_csp_header()
            }
            
            return Response(
                content.encode('utf-8'),
                status=resp.status_code,
                headers=response_headers
            )
    except Exception as e:
        return f"UI转发失败: {str(e)}", 500

# 3. Gradio组件接口转发
@app.route('/ui/gradio_api/<path:subpath>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_gradio_components(subpath):
    target_url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/ui/gradio_api/{subpath}"
    query_params = request.query_string.decode()
    if query_params:
        target_url += f"?{query_params}"
    
    try:
        with requests.request(
            method=request.method,
            url=target_url,
            headers={'Host': f"{LOCAL_HOST}:{LOCAL_PORT}"},
            data=request.get_data(),
            stream=True,
            verify=False
        ) as local_response:
            if local_response.status_code == 404:
                return f"组件资源不存在: {target_url}", 404
            
            mime_type, _ = mimetypes.guess_type(subpath)
            content_type = local_response.headers.get('Content-Type', mime_type)
            
            if subpath.endswith('.js'):
                content_type = 'text/javascript'
            elif subpath.endswith('.css'):
                content_type = 'text/css'
            
            response_headers = {
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
                'Set-Cookie': local_response.headers.get('Set-Cookie', ''),
                'Content-Security-Policy': build_csp_header()
            }
            
            return Response(
                local_response.content,
                status=local_response.status_code,
                headers=response_headers
            )
    except Exception as e:
        return f"组件资源转发失败: {str(e)}", 500

# 4. 下载资源转发
@app.route('/download/<path:subpath>', methods=['GET', 'OPTIONS'])
def proxy_downloads(subpath):
    target_url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/download/{subpath}"
    query_params = request.query_string.decode()
    if query_params:
        target_url += f"?{query_params}"
    
    try:
        with requests.get(
            url=target_url,
            headers={'Host': f"{LOCAL_HOST}:{LOCAL_PORT}"},
            stream=True,
            verify=False
        ) as local_response:
            if local_response.status_code == 404:
                return f"下载资源不存在: {target_url}", 404
            
            filename = subpath.split('/')[-1]
            mime_type, _ = mimetypes.guess_type(filename)
            
            response_headers = {
                'Content-Type': mime_type or 'application/octet-stream',
                'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Set-Cookie': local_response.headers.get('Set-Cookie', '')
            }
            
            return Response(
                local_response.content,
                status=local_response.status_code,
                headers=response_headers
            )
    except Exception as e:
        return f"下载资源转发失败: {str(e)}", 500

# 5. 网站图标处理
@app.route('/favicon.ico', methods=['GET'])
def favicon():
    target_url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/favicon.ico"
    
    try:
        response = requests.get(
            target_url, 
            verify=False,
            headers={'Cookie': request.headers.get('Cookie', '')}
        )
        if response.status_code == 200:
            return Response(
                response.content,
                status=200,
                headers={'Content-Type': 'image/x-icon'}
            )
    except:
        pass
    return Response(status=204)

# 6. WebSocket代理（终极修复）
@sock.route('/ws/lam_data_stream/<path:subpath>', endpoint='proxy_lam_websocket')
def proxy_lam_websocket(ws, subpath):
    local_ws_url = f"ws://{LOCAL_HOST}:{LOCAL_PORT}/ws/lam_data_stream/{subpath}"
    public_ws_url = f"wss://{PUBLIC_DOMAIN_HOST}/ws/lam_data_stream/{subpath}"
    
    print(f"转发LAM数据流WebSocket: {public_ws_url} → {local_ws_url}")
    
    message_queue = queue.Queue()
    is_running = [True]
    
    # 核心修复：仅保留Host和Cookie，其他头部完全透传原始请求
    headers = []
    
    # 仅添加Host头部（必须项）
    headers.append(f"Host: {LOCAL_HOST}:{LOCAL_PORT}")
    
    # 透传原始Cookie（如果存在）
    if 'Cookie' in request.headers:
        headers.append(f"Cookie: {request.headers['Cookie']}")
    
    # 关键：仅透传WebSocket必需的原始头部，不做任何重复添加
    # 使用集合确保每个头部只出现一次
    ws_headers = {'Upgrade', 'Connection', 'Sec-WebSocket-Key', 
                 'Sec-WebSocket-Version', 'Sec-WebSocket-Extensions', 'Origin'}
    passed_headers = set()
    
    for header in request.headers:
        if header in ws_headers and header not in passed_headers:
            headers.append(f"{header}: {request.headers[header]}")
            passed_headers.add(header)
    
    def on_message(ws_local, message):
        try:
            if is_running[0]:
                message_queue.put(message)
        except Exception as e:
            print(f"LAM消息错误: {str(e)}")
            is_running[0] = False
    
    def on_error(ws_local, error):
        print(f"LAM WebSocket错误: {str(error)}")
        is_running[0] = False
    
    def on_close(ws_local, close_status_code, close_msg):
        print(f"LAM WebSocket关闭: {close_status_code} - {close_msg}")
        is_running[0] = False
    
    def on_open(ws_local):
        print(f"成功连接到本地LAM WebSocket: {local_ws_url}")
    
    ws_local = websocket.WebSocketApp(
        local_ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header=headers
    )
    
    local_thread = threading.Thread(target=lambda: ws_local.run_forever(ping_interval=30), daemon=True)
    local_thread.start()
    
    try:
        while is_running[0]:
            while not message_queue.empty():
                message = message_queue.get()
                ws.send(message)
                message_queue.task_done()
            
            try:
                client_msg = ws.receive(timeout=0.1)
                if client_msg and is_running[0]:
                    ws_local.send(client_msg)
            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"LAM接收错误: {str(e)}")
            
            time.sleep(0.01)
    except Exception as e:
        print(f"LAM转发异常: {str(e)}")
    finally:
        is_running[0] = False
        ws_local.close()
        local_thread.join(timeout=1.0)


# 6.1 其他WebSocket路径的处理
@sock.route('/ws/<path:subpath>', endpoint='proxy_other_websocket')
def proxy_other_websocket(ws, subpath):
    print(f"处理其他WebSocket路径: /ws/{subpath}")
    try:
        local_ws_url = f"ws://{LOCAL_HOST}:{LOCAL_PORT}/ws/{subpath}"
        print(f"尝试连接到本地WebSocket: {local_ws_url}")
        
        message_queue = queue.Queue()
        is_running = [True]
        
        headers = []
        for header in ['Upgrade', 'Connection', 'Sec-WebSocket-Key', 
                      'Sec-WebSocket-Version', 'Sec-WebSocket-Extensions', 'Origin']:
            if header in request.headers:
                headers.append(f"{header}: {request.headers[header]}")
        headers.append(f"Host: {LOCAL_HOST}:{LOCAL_PORT}")
        
        def on_message(ws_local, message):
            try:
                if is_running[0]:
                    message_queue.put(message)
            except Exception as e:
                print(f"其他WebSocket消息错误: {str(e)}")
                is_running[0] = False
        
        def on_error(ws_local, error):
            print(f"其他WebSocket错误: {str(error)}")
            is_running[0] = False
        
        def on_close(ws_local, close_status_code, close_msg):
            print(f"其他WebSocket关闭: {close_status_code} - {close_msg}")
            is_running[0] = False
        
        def on_open(ws_local):
            print(f"成功连接到本地其他WebSocket: {local_ws_url}")
        
        ws_local = websocket.WebSocketApp(
            local_ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header=headers
        )
        
        local_thread = threading.Thread(target=lambda: ws_local.run_forever(ping_interval=30), daemon=True)
        local_thread.start()
        
        while is_running[0]:
            while not message_queue.empty():
                message = message_queue.get()
                ws.send(message)
                message_queue.task_done()
            
            try:
                client_msg = ws.receive(timeout=0.1)
                if client_msg and is_running[0]:
                    ws_local.send(client_msg)
            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"其他WebSocket接收错误: {str(e)}")
            
            time.sleep(0.01)
    except Exception as e:
        print(f"其他WebSocket处理异常: {str(e)}")
        ws.close(code=1008, reason="Unsupported WebSocket path")
    finally:
        try:
            ws_local.close()
            local_thread.join(timeout=1.0)
        except:
            pass

# 7. WebSocket OPTIONS处理
@app.route('/ws/lam_data_stream/<path:subpath>', methods=['OPTIONS'], endpoint='ws_lam_options')
def handle_ws_lam_options(subpath):
    return Response(
        status=200,
        headers={
            'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Upgrade, Connection, Sec-WebSocket-Key, Sec-WebSocket-Version, Sec-WebSocket-Extensions, Sec-WebSocket-Protocol',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Upgrades': 'websocket',
            'Connection': 'Upgrade',
            'Upgrade': 'websocket'
        }
    )

# 7.1 通用WebSocket OPTIONS处理
@app.route('/ws/<path:subpath>', methods=['OPTIONS'], endpoint='ws_general_options')
def handle_ws_general_options(subpath):
    return Response(
        status=200,
        headers={
            'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Upgrade, Connection, Sec-WebSocket-Key, Sec-WebSocket-Version, Sec-WebSocket-Extensions, Sec-WebSocket-Protocol',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Upgrades': 'websocket',
            'Connection': 'Upgrade',
            'Upgrade': 'websocket'
        }
    )

# 8. 通用跨域预检处理
@app.route('/<path:any>', methods=['OPTIONS'])
def handle_general_options(any):
    return Response(
        status=200,
        headers={
            'Access-Control-Allow-Origin': PUBLIC_DOMAIN,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Cookie, Upgrade, Connection, Sec-WebSocket-Key, Sec-WebSocket-Version',
            'Access-Control-Allow-Credentials': 'true'
        }
    )
@app.route('/submitBlogs/<username>', methods=['POST'])
def submit_blogs(username):
    try:
        # 获取请求数据
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return jsonify({"message": "标题和内容不能为空"}), 400
        
        # 创建新文章对象
        new_article = {
            "title": title,
            "content": content,
            "date": datetime.now().isoformat()  # 转换为ISO字符串格式
        }
        
        # 处理JSON字符串
        a = json.dumps(new_article)
        b = [json.dumps(a)]
        c = b
        
        # 处理转义字符
        d = [item.replace("\\", "") for item in c]
        
        # 处理数组元素
        processed_array = []
        for item in d:
            # 去除首尾空格和引号
            trimmed = item.strip()[1:-1]
            # 移除转义字符
            processed = trimmed.replace("\\", "")
            processed_array.append(processed)
        
        # 构建JSON数组字符串
        json_array_string = f"[ {', '.join(processed_array)} ]"
        final_string = f"'{json_array_string}'"
        new_string = final_string.strip().replace(r'\s*(\[|\])\s*', r'\1', 0)
        e = new_string[1:-1]
        
        # 连接数据库并执行更新
        connection = get_db_connection()
        if not connection:
            return jsonify({"message": "数据库连接失败"}), 500
            
        cursor = connection.cursor()
        query = """
        UPDATE sqlUsers
        SET blogs = IF(
            blogs IS NULL,
            %s,
            JSON_MERGE_PRESERVE(blogs, %s)
        )
        WHERE username = %s
        """
        
        cursor.execute(query, (e, e, username))
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"message": "未找到对应的用户或更新失败"}), 404
        
        return jsonify({
            "message": "文章提交成功",
            "article": new_article
        }), 200
        
    except Exception as error:
        print(f"数据库操作出错: {error}")
        return jsonify({"message": "文章提交失败，请稍后重试"}), 500
        
    finally:
        # 确保数据库连接关闭
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
if __name__ == '__main__':
    # 创建必要的临时目录
    temp_audio_dir = os.path.join(tempfile.gettempdir(), 'virtual_character_audio')
    os.makedirs(temp_audio_dir, exist_ok=True)
    print(f"临时音频目录已创建: {temp_audio_dir}")
    
    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
    print("数据库表已初始化")
    
    # 加载表情识别模型
    if EMOTION_AVAILABLE:
        load_emotion_model()
        # 启动表情识别工作线程
        threading.Thread(target=detection_worker, daemon=True).start()
        print("表情识别服务已启动")
    else:
        print("表情识别服务不可用")
    
    # 启动8765端口的WebSocket服务
    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    print("WebSocket服务线程已启动")
    
    # 等待WebSocket服务初始化
    import time
    time.sleep(2)  # 给予2秒初始化时间
    
    # 路由检查（确认Flask路由已正确注册）
    print("\nFlask应用注册的路由:")
    for rule in app.url_map.iter_rules():
        print(f"  - {rule.rule} -> {rule.endpoint}")
    
    # 启动3000端口的整合服务
    print("\n===== 虚拟人服务启动信息 =====")
    print(f"主服务地址: http://0.0.0.0:3000")
    print(f"虚拟人交互页面: http://0.0.0.0:3000/virtual_character")
    print(f"WebSocket代理: ws://0.0.0.0:3000/ws (转发到8765)")
    print("==============================\n")
    required_libraries = ['websocket-client>=1.8.0', 'flask-sock>=0.6.0', 'requests>=2.31.0']
    for lib in required_libraries:
        try:
            lib_name = lib.split('>=')[0].split('-')[0]
            __import__(lib_name)
        except ImportError:
            print(f"正在安装{lib}库...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
    
    print(f"代理服务启动: http://localhost:{PROXY_PORT}")
    print(f"公网WebSocket地址: ws://{PUBLIC_DOMAIN_HOST}:{PUBLIC_DOMAIN_PORT}/ws/lam_data_stream/")
    print(f"本地服务映射: http://{LOCAL_HOST}:{LOCAL_PORT}")
    app.run(
        host="0.0.0.0",
        port=PROXY_PORT,
        debug=True,
        threaded=True,
        use_reloader=False
    )
    
    # 启动整合服务（会阻塞当前线程）
    start_combined_server()
