<template>
  <div class="audio-analyzer">
    <div class="header">
      <h1>语音分析工具</h1>
      <button 
        class="record-btn" 
        :class="{ 'recording': isRecording }"
        @click="toggleRecording"
      >
        {{ isRecording ? '停止录音' : '开始录音' }}
      </button>
    </div>
    
    <div class="metrics">
      <div class="metric-card">
        <div class="metric-title">音量</div>
        <div class="metric-value">{{ volume.toFixed(1) }} dB</div>
        <div class="volume-graph">
          <div class="volume-bar" :style="{ width: volumePercent + '%' }"></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-title">语速</div>
        <div class="metric-value">{{ speechRate.toFixed(1) }} 词/分钟</div>
        <div class="metric-progress">
          <div class="progress-bar" :style="{ width: speechRatePercent + '%' }"></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-title">音调稳定度</div>
        <div class="metric-value">{{ pitchStability.toFixed(1) }}%</div>
        <div class="metric-progress">
          <div class="progress-bar" :style="{ width: pitchStability + '%' }"></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-title">音调</div>
        <div class="metric-value">{{ pitch.toFixed(1) }} Hz</div>
        <div class="pitch-graph">
          <div class="pitch-point" :style="{ left: pitchPosition + '%' }"></div>
        </div>
      </div>
    </div>
    
    <div class="frequency-chart">
      <h3>频率分布</h3>
      <canvas ref="frequencyCanvas"></canvas>
    </div>
    
    <div class="transcript">
      <h3>语音转文字</h3>
      <div class="transcript-text">{{ transcript }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AudioAnalyzer',
  data() {
    return {
      isRecording: false,
      audioContext: null,
      analyser: null,
      microphone: null,
      scriptProcessor: null,
      animationFrameId: null,
      volume: 0,
      pitch: 0,
      pitchStability: 50,
      speechRate: 0,
      transcript: '',
      pitchHistory: [],
      wordCount: 0,
      lastSpeechTime: 0,
      canvas: null,
      canvasCtx: null,
      // 修改：使用Float32Array存储浮点频率数据
      frequencyData: new Float32Array(1024),
      // 新增：用于绘制频谱图的Uint8Array
      byteFrequencyData: new Uint8Array(1024)
    };
  },
  computed: {
    volumePercent() {
      return Math.min(100, Math.max(0, this.volume + 100));
    },
    speechRatePercent() {
      const maxRate = 200; // 最大语速词/分钟
      return Math.min(100, (this.speechRate / maxRate) * 100);
    },
    pitchPosition() {
      // 将音高映射到图表上 (80-500Hz范围)
      const minPitch = 80;
      const maxPitch = 500;
      return Math.min(100, Math.max(0, ((this.pitch - minPitch) / (maxPitch - minPitch)) * 100));
    }
  },
  methods: {
    async toggleRecording() {
      if (this.isRecording) {
        this.stopRecording();
      } else {
        await this.startRecording();
      }
    },
    
    async startRecording() {
      try {
        // 创建音频上下文
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // 获取麦克风权限
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        
        // 创建音频节点
        this.microphone = this.audioContext.createMediaStreamSource(stream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 2048;
        this.analyser.smoothingTimeConstant = 0.8;
        
        // 创建脚本处理器 (用于自定义音频处理)
        this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        // 连接音频节点
        this.microphone.connect(this.analyser);
        this.analyser.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.audioContext.destination);
        
        // 设置音频处理回调
        this.scriptProcessor.onaudioprocess = (event) => {
          this.processAudio(event);
        };
        
        // 初始化频率图表
        this.initFrequencyChart();
        
        // 开始动画循环
        this.startAnimation();
        
        // 初始化语音识别
        this.initSpeechRecognition();
        
        this.isRecording = true;
      } catch (error) {
        console.error('录音启动失败:', error);
        alert('录音启动失败，请确保您已授予麦克风权限。');
      }
    },
    
    stopRecording() {
      this.isRecording = false;
      
      // 停止动画
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
      }
      
      // 断开音频节点连接
      if (this.microphone) {
        this.microphone.disconnect();
      }
      if (this.analyser) {
        this.analyser.disconnect();
      }
      if (this.scriptProcessor) {
        this.scriptProcessor.disconnect();
        this.scriptProcessor.onaudioprocess = null;
      }
      
      // 停止语音识别
      if (this.recognition) {
        this.recognition.stop();
      }
      
      // 关闭音频上下文
      if (this.audioContext) {
        this.audioContext.close();
        this.audioContext = null;
      }
    },
    
    processAudio(event) {
      // 获取音频数据
      const inputBuffer = event.inputBuffer.getChannelData(0);
      
      // 计算音量 (RMS)
      let sum = 0;
      for (let i = 0; i < inputBuffer.length; i++) {
        sum += inputBuffer[i] * inputBuffer[i];
      }
      const rms = Math.sqrt(sum / inputBuffer.length);
      this.volume = 20 * Math.log10(rms) || -100; // dB
      
      // 检测语音活动
      const isSpeaking = this.volume > -40; // 阈值可调整
      
      // 更新语速
      if (isSpeaking) {
        if (!this.lastSpeechTime) {
          this.lastSpeechTime = Date.now();
        }
        
        // 模拟单词计数 (实际应用中应使用语音识别)
        if (Math.random() < 0.05) { // 模拟每20帧增加一个词
          this.wordCount++;
        }
        
        const duration = (Date.now() - this.lastSpeechTime) / 1000 / 60; // 分钟
        if (duration > 0) {
          this.speechRate = this.wordCount / duration;
        }
      } else {
        this.lastSpeechTime = 0;
      }
      
      // 修改：获取浮点频率数据
      this.analyser.getFloatFrequencyData(this.frequencyData);
      
      // 计算音高
      let maxAmp = -Infinity;
      let maxFreq = 0;
      
      // 修改：处理浮点频率数据
      for (let i = 0; i < this.frequencyData.length; i++) {
        if (this.frequencyData[i] > maxAmp) {
          maxAmp = this.frequencyData[i];
          maxFreq = i * (this.audioContext.sampleRate / 2) / this.frequencyData.length;
        }
      }
      
      // 过滤低振幅噪声
      if (maxAmp > -90) {
        this.pitch = maxFreq;
        
        // 更新音调历史，用于计算稳定性
        this.pitchHistory.push(maxFreq);
        if (this.pitchHistory.length > 20) {
          this.pitchHistory.shift();
        }
        
        // 计算音调稳定性
        if (this.pitchHistory.length > 5) {
          const avgPitch = this.pitchHistory.reduce((a, b) => a + b, 0) / this.pitchHistory.length;
          let variance = 0;
          
          this.pitchHistory.forEach(freq => {
            variance += Math.pow(freq - avgPitch, 2);
          });
          
          const stdDev = Math.sqrt(variance / this.pitchHistory.length);
          // 将标准差转换为0-100的稳定性分数
          this.pitchStability = Math.max(0, Math.min(100, 100 - (stdDev / 50) * 100));
        }
      }
       this.saveVoiceAnalysisToLocalStorage();
    },
    
    startAnimation() {
      const animate = () => {
        this.updateFrequencyChart();
        this.animationFrameId = requestAnimationFrame(animate);
      };
      
      animate();
    },
    
    initFrequencyChart() {
      this.canvas = this.$refs.frequencyCanvas;
      this.canvasCtx = this.canvas.getContext('2d');
      
      // 设置canvas尺寸
      const resizeCanvas = () => {
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
      };
      
      resizeCanvas();
      window.addEventListener('resize', resizeCanvas);
    },
    
    updateFrequencyChart() {
      if (!this.canvasCtx) return;
      
      const canvas = this.canvas;
      const ctx = this.canvasCtx;
      const width = canvas.width;
      const height = canvas.height;
      
      // 清除画布
      ctx.clearRect(0, 0, width, height);
      
      // 修改：获取字节频率数据用于绘制频谱图
      this.analyser.getByteFrequencyData(this.byteFrequencyData);
      
      // 绘制频谱图
      const barWidth = width / this.byteFrequencyData.length * 2.5;
      let x = 0;
      
      for (let i = 0; i < this.byteFrequencyData.length; i++) {
        const barHeight = (this.byteFrequencyData[i] / 255) * height;
        
        // 渐变颜色
        const hue = (i / this.byteFrequencyData.length) * 240;
        ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
        
        ctx.fillRect(x, height - barHeight / 2, barWidth, barHeight / 2);
        
        x += barWidth + 1;
      }
    },
    
    initSpeechRecognition() {
      // 检查浏览器支持
      if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
        console.warn('语音识别不支持此浏览器');
        this.transcript = '语音识别不支持此浏览器';
        return;
      }
      
      // 创建识别对象
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      
      // 配置识别选项
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'zh-CN';
      
      // 设置结果回调
      this.recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        
        this.transcript = transcript;
      };
      
      // 错误处理
      this.recognition.onerror = (event) => {
        console.error('语音识别错误:', event.error);
      };
      
      // 开始识别
      this.recognition.start();
    }
  },
  beforeDestroy() {
    this.stopRecording();
  }
};
</script>

<style scoped>
/* 样式部分保持不变 */
.audio-analyzer {
  font-family: 'Arial', sans-serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h1 {
  color: #333;
}

.record-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.record-btn.recording {
  background-color: #f44336;
}

.record-btn:hover {
  opacity: 0.9;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.metric-card {
  background-color: #f9f9f9;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.metric-title {
  font-size: 16px;
  color: #666;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.volume-graph, .pitch-graph {
  height: 20px;
  background-color: #eee;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}

.volume-bar {
  height: 100%;
  background: linear-gradient(to right, #f44336, #ffeb3b, #4CAF50);
  transition: width 0.1s;
}

.pitch-graph .pitch-point {
  position: absolute;
  top: 0;
  width: 10px;
  height: 100%;
  background-color: #2196F3;
  border-radius: 50%;
  transform: translateX(-50%);
}

.metric-progress {
  height: 20px;
  background-color: #eee;
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: #2196F3;
  transition: width 0.3s;
}

.frequency-chart {
  margin-bottom: 20px;
}

canvas {
  width: 100%;
  height: 200px;
  background-color: #f5f5f5;
  border-radius: 10px;
}

.transcript {
  background-color: #f9f9f9;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.transcript-text {
  min-height: 60px;
  padding: 10px;
  background-color: white;
  border-radius: 5px;
  line-height: 1.5;
}
</style>