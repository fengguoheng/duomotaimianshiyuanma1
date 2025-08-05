# -*- coding: utf-8 -*-
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse, urlencode
import ssl
import os
from time import mktime
import websocket
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import uuid
from collections import defaultdict
import _thread as thread
import requests
import time
import tempfile
from wsgiref.handlers import format_date_time

app = Flask(__name__, static_folder='static')
CORS(app, origins="*")

# 确保静态文件夹存在
os.makedirs('static', exist_ok=True)

# 全局变量定义区域
# 图像理解相关变量
request_map = defaultdict(dict)
request_lock = thread.allocate_lock()
image_appid = "6b6f178c"    
image_api_secret = "MjI5ZWZlMzgxMmY2MGY2YWZhNmIwNDVj"   
image_api_key ="82026fc415f3d704f372ad238ce1bb15"    
imageunderstanding_url = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"

# 文字问答相关变量
text_api_key = "Bearer qkygNBMmpKIoZKXXMRWs:YqiVWCkaWjucPjsUeXza"
text_api_url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

# 语音转文字相关变量
lfasr_host = 'https://raasr.xfyun.cn/v2/api'
api_upload = '/upload'
api_get_result = '/getResult'

# 文字转语音相关变量
tts_appid = '86f989e0'
tts_apisecret = 'YjczOWNiZTYxZWNhY2M5ZjI3OTE5YTJi'
tts_apikey = '7264913c8b3035b87979668da32f762a'
tts_url = 'wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6'


### 图像理解相关函数
class Ws_Param_Image(object):
    def __init__(self, APPID, APIKey, APISecret, imageunderstanding_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(imageunderstanding_url).netloc
        self.path = urlparse(imageunderstanding_url).path
        self.ImageUnderstanding_url = imageunderstanding_url

    def create_url(self):
        now = datetime.datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + self.host + "\n" + "date: " + date + "\n" + "GET " + self.path + " HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        url = self.ImageUnderstanding_url + '?' + urlencode(v)
        return url

# 新增getText函数定义，修复未定义错误
def getText(role, content):
    """创建符合格式的消息对象"""
    return {"role": role, "content": content}

def process_image_request(request_id, image_base64, user_question):
    global text, answer
    # 使用image_base64创建图像内容
    image_content = {"role": "user", "content": image_base64, "content_type": "image"}
    # 使用新定义的getText创建问题内容
    question_content = getText("user", user_question)
    text = [image_content, question_content]
    # 检查长度
    text = checklen(text)
    answer = ""
    main_image(image_appid, image_api_key, image_api_secret, imageunderstanding_url, text)
    with request_lock:
        request_map[request_id]["content"] = answer
        request_map[request_id]["status"] = "completed"

@app.route('/image-understanding', methods=['POST'])
def image_understanding_api():
    try:
        data = request.json
        image_base64 = data.get('image_base64')
        user_question = data.get('question')
        
        if not image_base64 or not user_question:
            return jsonify({"error": "Missing 'image_base64' or 'question'"}), 400
        
        request_id = str(uuid.uuid4())
        # 使用线程处理，避免阻塞
        thread.start_new_thread(process_image_request, (request_id, image_base64, user_question))
        
        return jsonify({
            "request_id": request_id,
            "status": "processing",
            "message": "请求已接收，正在处理..."
        }), 202
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-result/<string:request_id>', methods=['GET'])
def get_image_result(request_id):
    with request_lock:
        result = request_map.get(request_id, {
            "status": "pending",
            "content": "",
            "error": None
        })
        return jsonify({
            "status": result["status"],
            "content": result.get("content", ""),
            "error": result.get("error")
        })

def on_image_error(ws, error):
    print("### image error:", error)

def on_image_close(ws, one, two):
    print(" ")

def on_image_open(ws):
    run_image(ws)

def run_image(ws):
    data = json.dumps(gen_image_params(ws.appid, ws.question))
    ws.send(data)

def on_image_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'图像理解请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content, end="")
        global answer
        answer += content
        if status == 2:
            ws.close()

def gen_image_params(appid, question):
    return {
        "header": {"app_id": appid},
        "parameter": {"chat": {"domain": "imagev3", "temperature": 0.5, "top_k": 4, "max_tokens": 2028, "auditing": "default"}},
        "payload": {"message": {"text": question}}
    }

def main_image(appid, api_key, api_secret, imageunderstanding_url, question):
    wsParam = Ws_Param_Image(appid, api_key, api_secret, imageunderstanding_url)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_image_message, on_error=on_image_error, on_close=on_image_close, on_open=on_image_open)
    ws.appid = appid
    ws.question = question
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

def getText_image(role, content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

def getlength_image(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength_image(text[1:]) > 8000):
        del text[1]
    return text


### 文字问答相关函数
def get_answer(question):
    headers = {
        'Authorization': text_api_key,
        'content-type': "application/json"
    }
    body = {
        "model": "4.0Ultra",
        "user": "user_id",
        "messages": [question],
        "stream": True,
        "tools": [{"type": "web_search", "web_search": {"enable": True, "search_mode": "deep"}}]
    }
    full_response = ""
    isFirstContent = True

    response = requests.post(text_api_url, json=body, headers=headers, stream=True)
    for chunks in response.iter_lines():
        if chunks and '[DONE]' not in str(chunks):
            data_org = chunks[6:]
            try:
                chunk = json.loads(data_org)
                delta = chunk['choices'][0]['delta']
                if 'content' in delta and delta['content']:
                    content = delta["content"]
                    if isFirstContent:
                        isFirstContent = False
                    full_response += content
            except Exception as e:
                print(f"解析文字响应出错: {e}")
    return full_response

def getText_text(role, content):
    jsoncon = {"role": "user", "content": content}
    return jsoncon

@app.route('/post_answer', methods=['POST'])
def handle_answer():
    try:
        question = request.json.get('question', '')
        
        if not question:
            return jsonify({"code": 400, "message": "问题不能为空"}), 400
            
        response_content = get_answer(getText_text("user", question))
        
        return jsonify({"code": 200, "message": "成功", "data": response_content})
    
    except Exception as e:
        print(f"文字问答接口处理出错: {e}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


### 语音转文字相关函数
class RequestApi_ASR:
    def __init__(self, appid, secret_key):
        self.appid = appid
        self.secret_key = secret_key

    def _get_signa(self, ts):
        m2 = hashlib.md5()
        m2.update((self.appid + ts).encode('utf-8'))
        md5 = m2.hexdigest().encode('utf-8')
        signa = hmac.new(self.secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        return base64.b64encode(signa).decode('utf-8')

    def upload(self, file_path):
        ts = str(int(time.time()))
        signa = self._get_signa(ts)
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        params = {
            'appId': self.appid,
            'signa': signa,
            'ts': ts,
            'fileSize': file_size,
            'fileName': file_name,
            'duration': "200"
        }

        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{lfasr_host}{api_upload}?{urlencode(params)}",
                headers={"Content-type": "application/octet-stream"},
                data=f.read()
            )

        return response.json()

    def get_result(self, order_id):
        ts = str(int(time.time()))
        signa = self._get_signa(ts)

        params = {
            'appId': self.appid,
            'signa': signa,
            'ts': ts,
            'orderId': order_id,
            'resultType': "transfer,predict"
        }

        status = 3
        while status == 3:
            response = requests.post(
                f"{lfasr_host}{api_get_result}?{urlencode(params)}",
                headers={"Content-type": "application/json"}
            )
            result = response.json()
            status = result['content']['orderInfo']['status']
            if status == 4:
                break
            time.sleep(2)

        return result

@app.route('/api/transcribe', methods=['POST'])
def transcribe_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        # 初始化语音转文字API
        api = RequestApi_ASR(
            appid="86f989e0",
            secret_key="e46bb19717dbeb52cc5c8962815ff01c"
        )
        
        # 上传音频文件
        upload_result = api.upload(file_path)
        order_id = upload_result['content']['orderId']
        
        # 获取转写结果
        result = api.get_result(order_id)
        
        # 提取转写文本
        text = ""
        if 'content' in result and 'orderResult' in result['content']:
            try:
                order_result = json.loads(result['content']['orderResult'])
                for item in order_result.get('lattice', []):
                    json_1best = json.loads(item.get('json_1best', '{}'))
                    for rt in json_1best.get('st', {}).get('rt', []):
                        for ws in rt.get('ws', []):
                            for cw in ws.get('cw', []):
                                text += cw.get('w', '')
            except:
                text = "Failed to parse transcription result"
        
        return jsonify({
            'status': 'success',
            'text': text,
            'raw_result': result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # 清理临时文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            os.rmdir(temp_dir)


### 文字转语音相关函数
class Ws_Param_TTS(object):
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text
        self.CommonArgs = {"app_id": self.APPID, "status": 2}
        self.BusinessArgs = {
            "tts": {
                "vcn": "x4_lingxiaoxuan_oral",
                "volume": 50,
                "rhy": 0,
                "speed": 50,
                "pitch": 50,
                "bgs": 0,
                "reg": 0,
                "rdn": 0,
                "audio": {
                    "encoding": "lame",
                    "sample_rate": 24000,
                    "channels": 1,
                    "bit_depth": 16,
                    "frame_size": 0
                }
            }
        }
        self.Data = {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 2,
                "seq": 0,
                "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")
            }
        }

class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg

class Url_TTS:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema

def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest

def parse_url_tts(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url_TTS(host, path, schema)
    return u

def assemble_ws_auth_url_tts(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url_tts(requset_url)
    host = u.host
    path = u.path
    now = datetime.datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }
    return requset_url + "?" + urlencode(values)

@app.route('/tts', methods=['POST'])
def tts_api():
    text = request.json.get('text')
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    filename = f"{uuid.uuid4()}.mp3"
    audio_path = os.path.join('static', filename)
    
    wsParam = Ws_Param_TTS(APPID=tts_appid, APIKey=tts_apikey, APISecret=tts_apisecret, Text=text)
    wsUrl = assemble_ws_auth_url_tts(tts_url, "GET", tts_apikey, tts_apisecret)
    
    audio_data = []
    
    def on_message_tts(ws, message):
        try:
            message = json.loads(message)
            code = message["header"]["code"]
            if "payload" in message:
                audio = message["payload"]["audio"]["audio"]
                audio = base64.b64decode(audio)
                status = message["payload"]["audio"]["status"]
                audio_data.append(audio)
                if status == 2:
                    ws.close()
                if code != 0:
                    print(f"科大讯飞 TTS API 错误：{message['message']}, 代码：{code}")
        except Exception as e:
            print(f"解析TTS消息失败：{e}")
    
    def on_error_tts(ws, error):
        print(f"TTS WebSocket 错误：{error}")
    
    def on_close_tts(ws, close_status_code, close_msg):
        print("TTS WebSocket 连接关闭")
    
    def on_open_tts(ws):
        def run():
            d = {
                "header": wsParam.CommonArgs,
                "parameter": wsParam.BusinessArgs,
                "payload": wsParam.Data
            }
            ws.send(json.dumps(d))
        thread.start_new_thread(run, ())
    
    ws = websocket.WebSocketApp(
        wsUrl,
        on_message=on_message_tts,
        on_error=on_error_tts,
        on_close=on_close_tts
    )
    ws.on_open = on_open_tts
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    if audio_data:
        with open(audio_path, 'wb') as f:
            f.write(b''.join(audio_data))
        absolute_url = f"{request.url_root}static/{filename}"
        return jsonify({"audio_url": absolute_url})
    else:
        return jsonify({"error": "Failed to generate audio"}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/latest_audio', methods=['GET'])
def get_latest_audio():
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        return jsonify({"error": "Static directory not found"}), 404
    
    mp3_files = [f for f in os.listdir(static_dir) if f.endswith('.mp3')]
    if not mp3_files:
        return jsonify({"error": "No MP3 files found"}), 404
    
    latest_file = max(
        [os.path.join(static_dir, f) for f in mp3_files],
        key=os.path.getmtime
    )
    return jsonify({"audio_url": f"{request.url_root}static/{os.path.basename(latest_file)}"})


### HTTPS配置与启动
if __name__ == '__main__':
    import ssl
    import os
    
    # 证书路径配置：优先使用当前目录下的证书，不存在则尝试系统证书
    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/cert.pem')
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs/key.pem')
    
    # 检查证书是否存在，不存在则尝试系统证书
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        cert_path = "/etc/ssl/certs/GlobalSign_Root_CA.pem"  # 替换为实际存在的证书
        key_path = "/etc/ssl/private/server.key"  # 替换为实际私钥
        
        # 再次检查系统证书是否存在
        if not (os.path.exists(cert_path) and os.path.exists(key_path)):
            print("警告：未找到有效的证书和私钥，使用HTTP模式启动")
            app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
            exit(1)
    
    try:
        # 配置SSL上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        context.verify_mode = ssl.CERT_NONE  # 允许自签名证书
        
        print("=== HTTPS服务已启动 ===")
        print(f"* 安全连接已启用，运行在 https://0.0.0.0:443")
        print(f"* 本地测试地址: https://127.0.0.1:443")
        
        # 使用HTTPS启动服务（需sudo权限）
        app.run(
            host='0.0.0.0',
            port=443,
            debug=True,
            ssl_context=context,
            threaded=True
        )
    except ssl.SSLError as e:
        print(f"SSL配置错误: {e}")
        print("错误原因：证书和私钥不匹配或格式错误")
        print("降级为HTTP模式启动...")
        app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
    except PermissionError:
        print("错误：需要管理员权限才能监听443端口")
        print("请使用以下命令启动：")
        print("sudo python3 app.py")
