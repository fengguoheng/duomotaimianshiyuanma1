<template>
  <div class="container">
    <h1>虚拟人juli</h1>

    <!-- 音频生成部分 -->
    <div class="section">
      <h2>输入您想和虚拟人juli聊的内容</h2>
      <form @submit.prevent="handleAudioGenerate">
        <div class="form-group">
          <label for="promptText"></label>
          <textarea 
            id="promptText" 
            v-model="promptText"
            placeholder="输入您想和虚拟人聊的内容，例如：解释神经网络的概念" 
            required
          ></textarea>
        </div>
        <button 
          type="submit" 
          id="audioGenerateButton"
          :disabled="isAudioGenerating"
        >
          发送
        </button>
        <span id="audioLoading" class="loading" v-if="isAudioGenerating"></span>
      </form>
      <div 
        id="chatResponse" 
        class="api-response" 
        v-if="showChatResponse"
      >
        <strong>AI面试官回复：</strong>
        <div id="chatResponseContent">{{ chatResponseText }}</div>
      </div>
      <div 
        id="audioResult" 
        class="result" 
        v-if="showAudioResult"
      >
        {{ audioResultText }}
      </div>
      <div class="preview" id="audioPreview" v-html="audioPreviewHtml"></div>
    </div>

    <!-- 视频处理部分 -->
    <div class="section">
      <h2>视频回答</h2>
      <form @submit.prevent="handleProcessVideo">
        <div class="form-group">
          <label for="minResolution">最小分辨率</label>
          <select 
            id="minResolution" 
            v-model="minResolution"
          >
            <option value="2">2（默认）</option>
            <option value="1">1</option>
            <option value="3">3</option>
            <option value="4">4</option>
          </select>
        </div>
        <div class="form-group">
          <label for="ifRes">固定分辨率</label>
          <select 
            id="ifRes" 
            v-model="ifRes"
          >
            <option value="false">否（默认）</option>
            <option value="true">是</option>
          </select>
        </div>
        <div class="form-group">
          <label for="steps">思考速度</label>
          <select 
            id="steps" 
            v-model="steps"
          >
            <option value="4">4（默认）</option>
            <option value="2">2</option>
            <option value="6">6</option>
            <option value="8">8</option>
          </select>
        </div>
        <button 
          type="submit" 
          id="processButton"
          :disabled="!canProcessVideo"
        >
          开始处理
        </button>
        <button 
          type="button" 
          id="cancelButton"
          @click="handleCancelProcessing"
          :disabled="!isProcessing"
        >
          取消处理
        </button>
        <span id="processLoading" class="loading" v-if="isProcessing"></span>
      </form>
      
      <div 
        id="processStatus" 
        class="result" 
        v-if="showProcessStatus"
      >
        {{ processStatusText }}
      </div>
      
      <div class="progress-container">
        <div 
          id="progressBar" 
          class="progress-bar"
          :style="{ width: progressBarWidth + '%' }"
        ></div>
      </div>
      
      <!-- 可选视频预览部分 -->
      <div class="optional-preview">
        <h3>等待期间可观看的视频</h3>
        <p>等待处理时，您可以观看此视频：</p>
        <button 
          id="showPreviewVideo" 
          type="button"
          @click="togglePreviewVideo"
        >
          {{ showPreviewVideo ? '隐藏预览视频' : '显示预览视频' }}
        </button>
        <div 
          id="previewVideoContainer" 
          v-if="showPreviewVideo"
          style="margin-top: 10px;"
        >
          <video controls :src="optionalVideoUrl">
            您的浏览器不支持视频播放
          </video>
          <div class="file-info">
            视频文件：julibzhan.mp4
          </div>
        </div>
      </div>
      
      <div class="preview" id="outputVideoPreview" v-html="videoPreviewHtml"></div>
    </div>

    <!-- 调试信息部分 -->
    <div class="section">
      <h2>调试信息</h2>
      <div id="debugInfo" class="debug-info">{{ debugInfo }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LipSyncGenerator',
  data() {
    return {
      // 配置
      HTTPS_BASE_URL: 'https://123.56.203.202',
      PROXY_FILE_PATH: '/proxy_gradio_file/',
      RECENT_FILES_PATH: '/proxy_gradio_file/recent',
      PROCESS_VIDEO_PATH: '/lip_sync/process_video',
      CHAT_API_PATH: '/api/chat',
      CHAT_RESULT_PATH: '/api/chat/result',
      TTS_API_PATH: '/gpt-sovites/tts_english',
      GET_LATEST_AUDIO_URL: '/gpt-sovites/get_latest_audio_url',
      POLL_INTERVAL: 3000,
      MAX_POLL_ATTEMPTS: 600,
      AUDIO_POLL_INTERVAL: 2000,
      MAX_AUDIO_ATTEMPTS: 180,
      CHAT_POLL_INTERVAL: 2000,
      MAX_CHAT_ATTEMPTS: 120,
      OPTIONAL_VIDEO_URL: 'https://123.56.203.202/proxy_files?path=D%3A%5CTemp%5Cjulibzhan.mp4',

      // 表单数据
      promptText: '解释监督学习和无监督学习之间的区别，并分别提供例子',
      minResolution: '2',
      ifRes: 'false',
      steps: '4',

      // 状态
      chatResponseText: '',
      showChatResponse: false,
      audioUrl: null,
      audioPreviewHtml: '',
      isAudioGenerating: false,
      audioResultText: '',
      showAudioResult: false,
      audioFolderPrefix: null,
      currentTaskId: null,
      
      isProcessing: false,
      processStartTime: null,
      pollAttempts: 0,
      pollTimer: null,
      abortController: null,
      processStatusText: '',
      showProcessStatus: false,
      progressBarWidth: 0,
      videoPreviewHtml: '',
      showPreviewVideo: false,
      
      debugInfo: '',
      optionalVideoUrl: 'https://123.56.203.202/proxy_files?path=D%3A%5CTemp%5Cjulibzhan.mp4'
    }
  },
  computed: {
    canProcessVideo() {
      return !this.isAudioGenerating && !!this.audioUrl && !this.isProcessing
    }
  },
  methods: {
    showDebugInfo(message) {
      const timestamp = new Date().toISOString();
      this.debugInfo += `[${timestamp}] ${message}\n`;
      // 自动滚动到底部
      this.$nextTick(() => {
        const el = document.getElementById('debugInfo');
        if (el) el.scrollTop = el.scrollHeight;
      });
    },

    fetchWithTimeout(url, options = {}, timeout = 500000) {
      return Promise.race([
        fetch(url, options),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('请求超时')), timeout)
        )
      ]);
    },

    startAudioPolling(folderPrefix) {
      let attempts = 0;
      
      const pollTimer = setInterval(async () => {
        attempts++;
        this.showDebugInfo(`轮询音频，尝试 ${attempts}`);
        
        try {
          const url = new URL(this.GET_LATEST_AUDIO_URL, this.HTTPS_BASE_URL).href;
          const response = await this.fetchWithTimeout(url, { method: 'GET' });
          
          const result = await response.json();
          this.showDebugInfo(`轮询结果: ${JSON.stringify(result)}`);
          
          if (result.status === 'success') {
            if (result.folder_path.includes(folderPrefix)) {
              clearInterval(pollTimer);
              this.audioUrl = result.audio_url;
              
              this.audioPreviewHtml = `
                <p>juli的语音回答：</p>
                <audio controls src="${this.audioUrl}"></audio>
                <div class="file-info">
                    思考完成时间：${result.created_time}<br>
                    <a href="${this.audioUrl}" download="generated_audio.wav">下载</a>
                </div>
              `;
              
              // 尝试获取音频时长
              this.$nextTick(() => {
                const audioElement = document.querySelector('#audioPreview audio');
                if (audioElement) {
                  audioElement.onloadedmetadata = () => {
                    const duration = audioElement.duration.toFixed(2);
                    const fileInfo = document.querySelector('#audioPreview .file-info');
                    if (fileInfo) {
                      fileInfo.innerHTML = `
                        生成时间：${result.created_time}<br>
                        音频长度：${duration} 秒<br>
                        <a href="${this.audioUrl}" download="generated_audio.wav">下载音频</a>
                      `;
                    }
                  };
                }
              });
              
              this.audioResultText = 'juli思考成功';
              this.isAudioGenerating = false;
              this.showAudioResult = true;
            } else {
              this.showDebugInfo(`等待目标文件夹 ${folderPrefix}...`);
            }
            
          } else if (result.status === 'pending') {
            this.audioResultText = `正在生成音频（${attempts}/${this.MAX_AUDIO_ATTEMPTS}）...`;
            this.showAudioResult = true;
            
          } else {
            clearInterval(pollTimer);
            this.audioResultText = `轮询错误：${result.message}`;
            this.showAudioResult = true;
            this.isAudioGenerating = false;
          }
          
          if (attempts >= this.MAX_AUDIO_ATTEMPTS) {
            clearInterval(pollTimer);
            this.audioResultText = '音频生成超时，请重试';
            this.showAudioResult = true;
            this.isAudioGenerating = false;
          }
          
        } catch (error) {
          this.showDebugInfo(`轮询错误：${error.message}`);
          if (attempts >= this.MAX_AUDIO_ATTEMPTS) {
            clearInterval(pollTimer);
            this.audioResultText = `轮询失败：${error.message}`;
            this.showAudioResult = true;
            this.isAudioGenerating = false;
          }
        }
      }, this.AUDIO_POLL_INTERVAL);
    },

    pollForChatResult(taskId) {
      return new Promise((resolve, reject) => {
        let attempts = 0;
        
        const poll = async () => {
          attempts++;
          this.showDebugInfo(`轮询聊天结果（任务ID：${taskId}），尝试 ${attempts}`);
          
          try {
            const resultUrl = new URL(`${this.CHAT_RESULT_PATH}/${taskId}`, this.HTTPS_BASE_URL).href;
            const response = await this.fetchWithTimeout(resultUrl, { method: 'GET' }, 10000);
            
            if (!response.ok) {
              throw new Error(`结果API错误：${response.status} ${response.statusText}`);
            }
            
            const resultData = await response.json();
            this.showDebugInfo(`聊天结果响应：${JSON.stringify(resultData)}`);
            
            if (resultData.status === 'processing') {
              this.audioResultText = `juli正在思考中（${attempts}/${this.MAX_CHAT_ATTEMPTS}）...`;
              this.showAudioResult = true;
              
              if (attempts >= this.MAX_CHAT_ATTEMPTS) {
                reject(new Error('等待聊天响应超时'));
                return;
              }
              
              setTimeout(poll, this.CHAT_POLL_INTERVAL);
              
            } else if (resultData.status === 'success') {
              resolve(resultData.result);
              
            } else if (resultData.status === 'error') {
              reject(new Error(`处理错误：${resultData.result}`));
              
            } else {
              reject(new Error(`未知状态：${resultData.status}`));
            }
            
          } catch (error) {
            this.showDebugInfo(`聊天结果轮询错误：${error.message}`);
            
            if (attempts >= this.MAX_CHAT_ATTEMPTS) {
              reject(new Error(`经过 ${this.MAX_CHAT_ATTEMPTS} 次尝试后轮询失败：${error.message}`));
            } else {
              setTimeout(poll, this.CHAT_POLL_INTERVAL);
            }
          }
        };
        
        poll();
      });
    },

    async handleAudioGenerate() {
      const userInput = this.promptText.trim();
      if (!userInput) return;
      
      const interviewerPrompt = `You are a senior AI technical interviewer conducting a technical interview with a candidate. Based on the following input, provide a professional technical response in ENGLISH ONLY. Focus on areas related to artificial intelligence, machine learning, deep learning, and maintain professional and targeted interview tone: ${userInput}`;
      
      this.isAudioGenerating = true;
      this.currentTaskId = null;
      this.audioResultText = '正在向AI发送请求...';
      this.showAudioResult = true;
      this.showChatResponse = false;
      this.audioPreviewHtml = '';
      
      try {
        this.showDebugInfo(`调用聊天API作为AI技术面试官：${this.CHAT_API_PATH}`);
        const chatUrl = new URL(this.CHAT_API_PATH, this.HTTPS_BASE_URL).href;
        
        const chatResponse = await this.fetchWithTimeout(
          chatUrl,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: interviewerPrompt })
          },
          30000
        );
        
        if (!chatResponse.ok) {
          throw new Error(`聊天API错误：${chatResponse.status} ${chatResponse.statusText}`);
        }
        
        const chatResult = await chatResponse.json();
        this.showDebugInfo(`聊天API返回：${JSON.stringify(chatResult)}`);
        
        if (chatResult.status !== 'success' || !chatResult.task_id) {
          throw new Error(`聊天API返回无效结果：${JSON.stringify(chatResult)}`);
        }
        
        this.currentTaskId = chatResult.task_id;
        this.audioResultText = `收到任务ID：${this.currentTaskId}，等待响应...`;
        
        const aiResponse = await this.pollForChatResult(this.currentTaskId);
        
        this.chatResponseText = aiResponse;
        this.showChatResponse = true;
        
        this.showDebugInfo(`调用TTS API：${this.TTS_API_PATH}`);
        const ttsUrl = new URL(this.TTS_API_PATH, this.HTTPS_BASE_URL).href;
        
        const ttsData = {
          text: this.chatResponseText,
          reference_text: this.chatResponseText
        };
        
        const ttsResponse = await this.fetchWithTimeout(
          ttsUrl,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(ttsData)
          },
          600000
        );
        
        if (!ttsResponse.ok) {
          throw new Error(`TTS API错误：${ttsResponse.status} ${ttsResponse.statusText}`);
        }
        
        const ttsResult = await ttsResponse.json();
        this.showDebugInfo(`TTS API返回：${JSON.stringify(ttsResult)}`);
        
        if (ttsResult.status !== 'success') {
          throw new Error(`音频合成失败：${ttsResult.message}`);
        }
        
        this.audioResultText = '音频合成中，等待结果...';
        this.audioFolderPrefix = ttsResult.folder_prefix;
        this.startAudioPolling(ttsResult.folder_prefix);
        
      } catch (error) {
        this.audioResultText = `错误：${error.message}`;
        this.showDebugInfo(`音频生成失败：${error.message}`);
        this.isAudioGenerating = false;
        this.currentTaskId = null;
      }
    },

    pollForRecentFiles() {
      if (this.pollAttempts >= this.MAX_POLL_ATTEMPTS) {
        this.processStatusText = `处理超时，无法在 ${(this.MAX_POLL_ATTEMPTS * this.POLL_INTERVAL / 1000).toFixed(0)} 秒内生成视频`;
        this.showProcessStatus = true;
        this.showDebugInfo(`轮询超时，尝试了 ${this.pollAttempts} 次`);
        this.resetProcessingState();
        return;
      }

      this.pollAttempts++;
      this.showDebugInfo(`轮询最近文件，尝试 ${this.pollAttempts}`);

      const recentFilesUrl = new URL(this.RECENT_FILES_PATH, this.HTTPS_BASE_URL);
      
      if (!this.processStartTime) {
        this.showDebugInfo("警告：未设置processStartTime，使用当前时间作为默认值");
        this.processStartTime = Math.floor(Date.now() / 1000);
      }
      
      recentFilesUrl.searchParams.append('since', this.processStartTime.toString());
      recentFilesUrl.searchParams.append('max', '10');

      this.fetchWithTimeout(recentFilesUrl.toString(), { method: 'GET' }, 1000000)
        .then(response => {
          if (!response.ok) {
            throw new Error(`文件查询失败：${response.status} ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          this.showDebugInfo(`找到 ${data.count} 个新文件`);
          
          if (data.status === 'success' && data.count > 0) {
            const latestFile = data.files[0];
            const videoUrl = `${this.HTTPS_BASE_URL}${this.PROXY_FILE_PATH}${encodeURIComponent(latestFile.path)}`;
            
            this.showDebugInfo(`找到最新文件：${videoUrl}`);
            this.processStatusText = '视频处理完成，加载预览...';
            this.showProcessStatus = true;
            this.progressBarWidth = 100;
            
            this.videoPreviewHtml = `
              <p>处理后的视频：</p>
              <video controls src="${videoUrl}"></video>
              <div class="file-info">
                  名称：${latestFile.name}<br>
                  大小：${(latestFile.size / (1024 * 1024)).toFixed(2)} MB<br>
                  <a href="${videoUrl}" download="${latestFile.name}">下载视频</a>
              </div>
            `;
            
            this.resetProcessingState();
          } else {
            const elapsedMinutes = Math.floor((this.pollAttempts * this.POLL_INTERVAL) / 60000);
            const totalMinutes = Math.floor((this.MAX_POLL_ATTEMPTS * this.POLL_INTERVAL) / 60000);
            this.processStatusText = `处理中... 已等待 ${elapsedMinutes} 分钟（最长 ${totalMinutes} 分钟）`;
            this.showProcessStatus = true;
            
            this.progressBarWidth = Math.min(90, (this.pollAttempts / this.MAX_POLL_ATTEMPTS) * 100);
            
            this.pollTimer = setTimeout(() => this.pollForRecentFiles(), this.POLL_INTERVAL);
          }
        })
        .catch(error => {
          this.showDebugInfo(`轮询错误：${error.message}`);
          this.processStatusText = `轮询错误：${error.message}，将继续重试...`;
          this.showProcessStatus = true;
          
          this.pollTimer = setTimeout(() => this.pollForRecentFiles(), this.POLL_INTERVAL);
        });
    },

    resetProcessingState() {
      this.isProcessing = false;
      this.processStartTime = null;
      this.pollAttempts = 0;
      
      if (this.pollTimer) {
        clearTimeout(this.pollTimer);
        this.pollTimer = null;
      }
      
      this.progressBarWidth = 0;
    },

    async handleProcessVideo() {
      if (!this.audioUrl) {
        this.processStatusText = '请先生成音频';
        this.showProcessStatus = true;
        this.showDebugInfo('未生成音频，终止处理');
        return;
      }
      
      this.isProcessing = true;
      this.processStartTime = Math.floor(Date.now() / 1000);
      this.pollAttempts = 0;
      
      this.processStatusText = '提交处理请求中...';
      this.showProcessStatus = true;
      
      this.progressBarWidth = 0;
      this.videoPreviewHtml = '';
      
      this.abortController = new AbortController();
      
      try {
        const processUrl = new URL(this.PROCESS_VIDEO_PATH, this.HTTPS_BASE_URL).href;
        this.showDebugInfo(`提交视频处理请求到：${processUrl}`);
        
        const requestData = {
          min_resolution: parseInt(this.minResolution),
          if_res: this.ifRes === 'true',
          steps: parseInt(this.steps)
        };
        
        const response = await this.fetchWithTimeout(
          processUrl,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData),
            signal: this.abortController.signal
          },
          1800000
        );
        
        if (!response.ok) {
          this.showDebugInfo(`处理请求返回非成功状态：${response.status} ${response.statusText}`);
          const errorText = await response.text().catch(() => '无法获取错误详情');
          this.showDebugInfo(`错误内容：${errorText}`);
          this.processStatusText = `处理请求返回错误，但将继续等待结果...`;
          this.showProcessStatus = true;
        } else {
          try {
            const result = await response.json();
            this.showDebugInfo(`处理请求响应：${JSON.stringify(result)}`);
            if (result.used_video_file) {
              this.showDebugInfo(`后端使用的固定视频路径：${result.used_video_file}`);
            }
            this.processStatusText = '处理请求已提交，等待视频生成...';
            this.showProcessStatus = true;
          } catch (e) {
            this.showDebugInfo(`解析处理响应失败：${e.message}`);
            this.processStatusText = '处理请求已提交，等待视频生成...';
            this.showProcessStatus = true;
          }
        }
      } catch (error) {
        if (error.name !== 'AbortError') {
          this.showDebugInfo(`处理请求错误：${error.message}`);
          this.processStatusText = `处理请求错误，但将继续等待结果...`;
          this.showProcessStatus = true;
        } else {
          this.processStatusText = '处理已取消';
          this.showProcessStatus = true;
          this.resetProcessingState();
          return;
        }
      }
      
      this.progressBarWidth = 10;
      this.pollForRecentFiles();
    },

    handleCancelProcessing() {
      this.showDebugInfo('用户点击取消处理');
      if (this.isProcessing && this.abortController) {
        this.abortController.abort();
        this.processStatusText = '处理已取消';
        this.showProcessStatus = true;
        this.progressBarWidth = 0;
        this.resetProcessingState();
      }
    },

    togglePreviewVideo() {
      this.showPreviewVideo = !this.showPreviewVideo;
      this.showDebugInfo(`${this.showPreviewVideo ? '显示' : '隐藏'}可选预览视频`);
    }
  },
  mounted() {
    this.showDebugInfo('页面完全加载，准备就绪');
  },
  beforeUnmount() {
    if (this.pollTimer) {
      clearTimeout(this.pollTimer);
    }
  }
}
</script>

<style scoped>
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
    margin-right: 10px;
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
    white-space: pre-wrap;
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
