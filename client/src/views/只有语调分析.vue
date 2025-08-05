<template>
  <div class="voice-analysis min-h-screen flex flex-col">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <span class="text-primary font-bold text-xl">
              <i class="fa fa-volume-up mr-2"></i>语音分析大师
            </span>
          </div>
          <div class="flex items-center space-x-4">
            <button id="help-btn" class="text-gray-500 hover:text-primary transition-colors" @click="openHelpModal">
              <i class="fa fa-question-circle"></i>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center mb-8">
        <h1 class="text-[clamp(1.8rem,4vw,2.5rem)] font-bold text-neutral">实时语音分析</h1>
        <p class="text-gray-500 mt-2">分析你的语调、音量、语速和频率分布</p>
      </div>

      <!-- 控制面板 -->
      <div class="flex justify-center mb-8">
        <button id="start-btn" class="gradient-bg text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-300 flex items-center"
          @click="startAnalysis">
          <i class="fa fa-microphone mr-2"></i>
          <span>开始分析</span>
        </button>
        <button id="stop-btn" class="ml-4 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg shadow hover:shadow-md transform hover:-translate-y-0.5 transition-all duration-300 flex items-center opacity-50 cursor-not-allowed"
          @click="stopAnalysis" :disabled="!isAnalyzing">
          <i class="fa fa-stop mr-2"></i>
          <span>停止</span>
        </button>
      </div>

      <!-- 状态指示器 -->
      <div id="status-indicator" class="hidden text-center mb-8">
        <div class="inline-flex items-center bg-green-100 text-green-800 px-4 py-2 rounded-full">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
          <span>正在监听...</span>
        </div>
      </div>

      <!-- 指标卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- 音量卡片 -->
        <div class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-lg font-semibold text-neutral">音量</h3>
            <div class="text-gray-400">
              <i class="fa fa-volume-up"></i>
            </div>
          </div>
          <div class="flex items-end justify-between h-24">
            <div id="volume-value" class="text-3xl font-bold text-primary">-∞ dB</div>
            <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
              <div id="volume-bar" class="h-full w-0 bg-primary transition-all duration-300"></div>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-500">
            <div class="flex justify-between">
              <span>安静</span>
              <span>适中</span>
              <span>响亮</span>
            </div>
          </div>
        </div>

        <!-- 音高卡片 -->
        <div class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-lg font-semibold text-neutral">音高</h3>
            <div class="text-gray-400">
              <i class="fa fa-music"></i>
            </div>
          </div>
          <div class="flex items-end justify-between h-24">
            <div id="pitch-value" class="text-3xl font-bold text-secondary">- Hz</div>
            <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
              <div id="pitch-bar" class="h-full w-0 bg-secondary transition-all duration-300"></div>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-500">
            <div class="flex justify-between">
              <span>低音</span>
              <span>中音</span>
              <span>高音</span>
            </div>
          </div>
        </div>

        <!-- 语速卡片 -->
        <div class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-lg font-semibold text-neutral">语速</h3>
            <div class="text-gray-400">
              <i class="fa fa-tachometer"></i>
            </div>
          </div>
          <div class="flex items-end justify-between h-24">
            <div id="wpm-value" class="text-3xl font-bold text-accent">- 词/分钟</div>
            <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
              <div id="wpm-bar" class="h-full w-0 bg-accent transition-all duration-300"></div>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-500">
            <div class="flex justify-between">
              <span>慢</span>
              <span>适中</span>
              <span>快</span>
            </div>
          </div>
        </div>

        <!-- 语调稳定性卡片 -->
        <div class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-lg font-semibold text-neutral">语调稳定性</h3>
            <div class="text-gray-400">
              <i class="fa fa-balance-scale"></i>
            </div>
          </div>
          <div class="flex items-end justify-between h-24">
            <div id="stability-value" class="text-3xl font-bold text-success">- %</div>
            <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
              <div id="stability-bar" class="h-full w-0 bg-success transition-all duration-300"></div>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-500">
            <div class="flex justify-between">
              <span>不稳定</span>
              <span>适中</span>
              <span>稳定</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 频率分布图表 -->
      <div class="bg-white rounded-xl p-6 card-shadow mb-8">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-neutral">频率分布</h3>
          <div class="text-xs text-gray-500">
            <span id="frequency-range">0 - 2500 Hz</span>
          </div>
        </div>
        <div class="h-64">
          <canvas id="frequency-chart"></canvas>
        </div>
      </div>

      <!-- 分析建议 -->
      <div id="analysis-suggestions" class="bg-white rounded-xl p-6 card-shadow hidden">
        <h3 class="text-lg font-semibold text-neutral mb-4">分析建议</h3>
        <div id="suggestions-content" class="text-gray-700">
          <!-- 建议内容将动态更新 -->
        </div>
      </div>
    </main>

    <!-- 页脚 -->
    <footer class="bg-white border-t border-gray-200 py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="text-gray-500 text-sm">
            &copy; 2023 语音分析大师 - 实时语音分析工具
          </div>
          <div class="mt-4 md:mt-0">
            <a href="#" class="text-gray-500 hover:text-primary mx-2">
              <i class="fa fa-github"></i>
            </a>
            <a href="#" class="text-gray-500 hover:text-primary mx-2">
              <i class="fa fa-twitter"></i>
            </a>
            <a href="#" class="text-gray-500 hover:text-primary mx-2">
              <i class="fa fa-linkedin"></i>
            </a>
          </div>
        </div>
      </div>
    </footer>

    <!-- 帮助模态框 -->
    <div id="help-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden">
      <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-neutral">使用帮助</h3>
          <button id="close-help" class="text-gray-400 hover:text-gray-600" @click="closeHelpModal">
            <i class="fa fa-times"></i>
          </button>
        </div>
        <div class="text-gray-700 space-y-4">
          <div>
            <h4 class="font-medium text-primary">如何使用</h4>
            <p class="text-sm mt-1">点击"开始分析"按钮，授权麦克风访问权限，然后开始说话。系统将实时分析你的语音参数。</p>
          </div>
          <div>
            <h4 class="font-medium text-primary">指标说明</h4>
            <ul class="text-sm mt-1 list-disc list-inside space-y-1">
              <li><span class="font-medium">音量：</span>语音的响亮程度，以分贝(dB)为单位</li>
              <li><span class="font-medium">音高：</span>语音的高低，以赫兹(Hz)为单位</li>
              <li><span class="font-medium">语速：</span>每分钟说的单词数</li>
              <li><span class="font-medium">语调稳定性：</span>音高变化的平稳程度</li>
            </ul>
          </div>
          <div>
            <h4 class="font-medium text-primary">最佳实践</h4>
            <p class="text-sm mt-1">在安静的环境中使用，保持麦克风距离嘴部约10-15厘米，正常语速说话以获得最准确的结果。</p>
          </div>
        </div>
        <div class="mt-6">
          <button id="close-help-btn" class="w-full bg-primary text-white py-2 rounded-lg hover:bg-primary/90 transition-colors" @click="closeHelpModal">
            我知道了
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
//import Chart from 'chart.js';
import * as Chart from 'chart.js';


import io from 'socket.io-client';

export default {
  name: 'VoiceAnalysis',
  data() {
    return {
      socket: null,
      isAnalyzing: false,
      frequencyChart: null,
      isSocketConnected: false,
      socketConnectAttempts: 0,
      maxConnectAttempts: 5
    }
  },
  mounted() {
    this.initSocket();
    this.initFrequencyChart();
    this.setupEventListeners();
  },
  beforeDestroy() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    if (this.frequencyChart) {
      this.frequencyChart.destroy();
      this.frequencyChart = null;
    }
  },
  methods: {
    initSocket() {
      this.socket = io.connect('http://127.0.0.1:3000', {
        transports: ['polling', 'websocket'],
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: this.maxConnectAttempts,
        reconnectionDelay: 1000
      });
      
      this.socket.on('connect', () => {
        this.isSocketConnected = true;
        this.socketConnectAttempts = 0;
        console.log('SocketIO连接成功');
      });
      
      this.socket.on('connect_error', (error) => {
        this.isSocketConnected = false;
        console.error('SocketIO连接错误:', error);
        alert(`SocketIO连接失败，请检查后端服务器是否运行在3000端口\n错误详情: ${error.message}`);
      });
      
      this.socket.on('connect_failed', () => {
        this.isSocketConnected = false;
        console.error('SocketIO连接失败，无法到达服务器');
        alert('无法连接到后端服务器，请确认服务器已启动且运行在3000端口');
      });
      
      this.socket.on('update_metrics', (data) => {
        this.updateVolume(data.volume);
        this.updatePitch(data.pitch);
        if (data.wpm) this.updateWpm(data.wpm);
        this.updateStability(data.stability);
        if (data.frequency_data) this.updateFrequencyChart(data.frequency_data);
        
        this.updateSuggestions({
          volume: data.volume,
          pitch: data.pitch,
          wpm: data.wpm || 0,
          stability: data.stability
        });
      });
    },
    
    initFrequencyChart() {
      const ctx = document.getElementById('frequency-chart').getContext('2d');
      
      this.frequencyChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: Array(100).fill(''),
          datasets: [{
            label: '频率分布',
            data: Array(100).fill(0),
            borderColor: '#165DFF',
            backgroundColor: 'rgba(22, 93, 255, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: {
                display: true,
                text: '频率 (Hz)'
              },
              ticks: {
                callback: function(value, index, values) {
                  const labels = ['0', '500', '1000', '1500', '2000', '2500'];
                  const positions = [0, 20, 40, 60, 80, 99];
                  if (positions.includes(index)) {
                    return labels[positions.indexOf(index)];
                  }
                  return '';
                }
              }
            },
            y: {
              title: {
                display: true,
                text: '能量'
              },
              beginAtZero: true
            }
          },
          animation: {
            duration: 0
          }
        }
      });
    },
    
    updateVolume(volume) {
      const volumeValue = document.getElementById('volume-value');
      const volumeBar = document.getElementById('volume-bar');
      
      const displayVolume = Math.max(-60, Math.min(0, volume));
      const percentage = 100 - (Math.abs(displayVolume) / 60) * 100;
      
      volumeValue.textContent = `${displayVolume.toFixed(1)} dB`;
      volumeBar.style.width = `${percentage}%`;
      
      if (displayVolume > -20) {
        volumeBar.className = 'h-full w-full bg-danger transition-all duration-300';
      } else if (displayVolume > -40) {
        volumeBar.className = 'h-full w-full bg-warning transition-all duration-300';
      } else {
        volumeBar.className = 'h-full w-full bg-primary transition-all duration-300';
      }
    },
    
    updatePitch(pitch) {
      const pitchValue = document.getElementById('pitch-value');
      const pitchBar = document.getElementById('pitch-bar');
      
      const displayPitch = Math.max(80, Math.min(500, pitch));
      const percentage = ((displayPitch - 80) / 420) * 100;
      
      pitchValue.textContent = `${Math.round(pitch)} Hz`;
      pitchBar.style.width = `${percentage}%`;
    },
    
    updateWpm(wpm) {
      const wpmValue = document.getElementById('wpm-value');
      const wpmBar = document.getElementById('wpm-bar');
      
      const displayWpm = Math.max(60, Math.min(200, wpm));
      const percentage = ((displayWpm - 60) / 140) * 100;
      
      wpmValue.textContent = `${Math.round(wpm)} 词/分钟`;
      wpmBar.style.width = `${percentage}%`;
      
      if (displayWpm > 160) {
        wpmBar.className = 'h-full w-full bg-danger transition-all duration-300';
      } else if (displayWpm > 120) {
        wpmBar.className = 'h-full w-full bg-warning transition-all duration-300';
      } else {
        wpmBar.className = 'h-full w-full bg-accent transition-all duration-300';
      }
    },
    
    updateStability(stability) {
      const stabilityValue = document.getElementById('stability-value');
      const stabilityBar = document.getElementById('stability-bar');
      
      stabilityValue.textContent = `${Math.round(stability)} %`;
      stabilityBar.style.width = `${stability}%`;
      
      if (stability < 40) {
        stabilityBar.className = 'h-full w-full bg-danger transition-all duration-300';
      } else if (stability < 70) {
        stabilityBar.className = 'h-full w-full bg-warning transition-all duration-300';
      } else {
        stabilityBar.className = 'h-full w-full bg-success transition-all duration-300';
      }
    },
    
    updateFrequencyChart(frequencyData) {
      if (!frequencyData || !frequencyData.x || !frequencyData.y) {
        console.warn("频率数据格式错误，缺少x或y属性");
        return;
      }
      
      if (!this.frequencyChart) return;
      
      const x = frequencyData.x;
      const y = frequencyData.y;
      
      if (x.length < 2 || y.length < 2) {
        console.warn("频率数据点数不足，无法绘制图表");
        return;
      }
      
      const interpolate = (xValues, yValues, targetX) => {
        const n = xValues.length;
        if (targetX <= xValues[0]) return yValues[0];
        if (targetX >= xValues[n-1]) return yValues[n-1];
        
        for (let i = 0; i < n-1; i++) {
          if (xValues[i] <= targetX && targetX <= xValues[i+1]) {
            const slope = (yValues[i+1] - yValues[i]) / (xValues[i+1] - xValues[i]);
            return yValues[i] + slope * (targetX - xValues[i]);
          }
        }
        return 0;
      };
      
      const maxFreq = 2500;
      const targetPoints = 100;
      const newX = Array(targetPoints).fill().map((_, i) => i * maxFreq / (targetPoints - 1));
      const newY = newX.map(xVal => interpolate(x, y, xVal));
      
      this.frequencyChart.data.labels = newX;
      this.frequencyChart.data.datasets[0].data = newY;
      this.frequencyChart.update('none');
    },
    
    updateSuggestions(metrics) {
      const { volume, pitch, wpm, stability } = metrics;
      let suggestions = [];
      
      if (volume < -50) {
        suggestions.push("您的音量偏低，可能需要提高说话音量以便更好地表达。");
      } else if (volume > -20) {
        suggestions.push("您的音量偏高，可能会让人感到压迫，适当降低音量可能会更舒适。");
      }
      
      if (pitch < 100 && pitch > 0) {
        suggestions.push("您的音高偏低，适当提高音调可能会让您的表达更有活力。");
      } else if (pitch > 300) {
        suggestions.push("您的音高偏高，适当降低音调可能会让您的表达更稳重。");
      }
      
      if (wpm > 160) {
        suggestions.push("您的语速偏快，可能会让听众难以跟上，请适当放慢语速。");
      } else if (wpm < 100 && wpm > 0) {
        suggestions.push("您的语速偏慢，适当加快语速可能会让您的表达更流畅。");
      }
      
      if (stability < 40) {
        suggestions.push("您的语调变化较大，适当保持稳定的语调可能会增加表达的可信度。");
      } else if (stability > 80) {
        suggestions.push("您的语调较为平稳，适当增加一些变化可能会让您的表达更生动。");
      }
      
      const suggestionsContent = document.getElementById('suggestions-content');
      const analysisSuggestions = document.getElementById('analysis-suggestions');
      
      if (suggestions.length > 0) {
        analysisSuggestions.classList.remove('hidden');
        suggestionsContent.innerHTML = suggestions.map(s => `<p class="mb-2"><i class="fa fa-lightbulb-o text-primary mr-2"></i>${s}</p>`).join('');
      } else {
        analysisSuggestions.classList.add('hidden');
      }
    },
    
    setupEventListeners() {
      const startBtn = document.getElementById('start-btn');
      const stopBtn = document.getElementById('stop-btn');
      const statusIndicator = document.getElementById('status-indicator');
      
      startBtn.addEventListener('click', () => {
        this.startAnalysis();
      });
      
      stopBtn.addEventListener('click', () => {
        this.stopAnalysis();
      });
    },
    
    startAnalysis() {
      navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(stream => {
          document.getElementById('start-btn').classList.add('opacity-50', 'cursor-not-allowed');
          document.getElementById('start-btn').disabled = true;
          document.getElementById('stop-btn').classList.remove('opacity-50', 'cursor-not-allowed');
          document.getElementById('stop-btn').disabled = false;
          document.getElementById('status-indicator').classList.remove('hidden');
          
          this.isAnalyzing = true;
          if (this.isSocketConnected) {
            this.socket.emit('start_recording');
          } else {
            console.warn('未连接到语音分析服务器，无法开始录音');
          }
          
          stream.getTracks().forEach(track => track.stop());
        })
        .catch(err => {
          alert('无法访问麦克风，请确保您已授予麦克风权限。');
          console.error('麦克风权限错误:', err);
        });
    },
    
    stopAnalysis() {
      document.getElementById('start-btn').classList.remove('opacity-50', 'cursor-not-allowed');
      document.getElementById('start-btn').disabled = false;
      document.getElementById('stop-btn').classList.add('opacity-50', 'cursor-not-allowed');
      document.getElementById('stop-btn').disabled = true;
      document.getElementById('status-indicator').classList.add('hidden');
      
      this.isAnalyzing = false;
      if (this.isSocketConnected) {
        this.socket.emit('stop_recording');
      }
    },
    
    openHelpModal() {
      document.getElementById('help-modal').classList.remove('hidden');
    },
    
    closeHelpModal() {
      document.getElementById('help-modal').classList.add('hidden');
    }
  }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary: #165DFF;
  --secondary: #36CBCB;
  --accent: #FF7D00;
  --neutral: #1D2939;
  --success: #00B42A;
  --warning: #FF7D00;
  --danger: #F53F3F;
}

.voice-analysis {
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--neutral);
}

.gradient-bg {
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
}

.card-shadow {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
}

.animate-pulse-slow {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>