<template>
  <div id="dialog">
    

    <!-- 聊天会话内容区域 -->
    <div id="dialog_content" class="chat-container">
      <div class="messages" ref="messagesContainer">
        <!-- 初始欢迎消息 -->
        <div class="message-item ai-message">

          <div class="message-bubble">
            你好！我是大数据运维测试岗面试官
          </div>
        </div>

        <!-- 动态消息列表 -->
        <div v-for="(msg, index) in messages" :key="index"
          :class="['message-item', msg.sender === 'user' ? 'user-message flex-row-reverse' : 'ai-message']">



          <!-- 文本消息 -->
          <div v-if="msg.type === 'text'" class="message-bubble" :class="msg.isError ? 'error-message' : ''">
            {{ msg.content }}
          </div>
          <!-- 新增：格式化消息（Markdown） -->
          <div v-if="msg.type === 'formatted'" class="message-bubble markdown-bubble">
            <div v-html="msg.content" class="markdown-render"></div>
          </div>
          <!-- 语音消息 -->
          <div v-if="msg.type === 'voice'" class="voice-bubble">
            <div class="voice-controls">
              <van-icon :name="msg.isPlaying ? 'pause-circle' : 'play-circle'" size="20"
                @click="toggleVoicePlayback(index)" class="play-icon" />
              <div class="voice-wave">
                <div :style="{ height: '100%' }"></div>
                <div :style="{ height: '60%' }"></div>
                <div :style="{ height: '80%' }"></div>
                <div :style="{ height: '40%' }"></div>
              </div>
              <span class="voice-duration">{{ formatDuration(msg.duration) }}</span>
            </div>

            <!-- 语音操作按钮 -->
            <div class="voice-actions" v-if="msg.sender === 'user'">
              <van-button size="mini" type="primary" @click="convertVoiceToText(index)" round>
                转文字
              </van-button>
              <van-button size="mini" type="info" @click="analyzeVoiceTone(index)" round>
                分析语调
              </van-button>
              <van-button size="mini" type="warning" @click="calculateSpeechSpeed(index)" round
                :disabled="!msg.textResult">
                语速
              </van-button>
              <van-button size="mini" type="success" @click="analyzeLanguageLogic(index)" round
                :disabled="!msg.textResult">
                语言逻辑
              </van-button>
            </div>

            <!-- 语音转文字结果 -->
            <div v-if="msg.textResult" class="voice-text-result">
              {{ msg.textResult }}
            </div>

            <!-- 语速计算结果 -->
            <div v-if="msg.speechSpeed" class="voice-speed-result">
              语速: {{ msg.speechSpeed }} 字/秒 (约 {{ Math.round(msg.speechSpeed * 60) }} 字/分钟)
            </div>

            <!-- 语调分析结果 -->
            <div v-if="msg.toneResult" class="voice-tone-result">
              <div>语调: {{ msg.toneResult.tone_type }}</div>
              <div>基频均值: {{ msg.toneResult.f0_mean }}Hz</div>
              <div>基频范围: {{ msg.toneResult.f0_min }}-{{ msg.toneResult.f0_max }}Hz</div>
            </div>

            <!-- 语言逻辑分析结果 -->
            <div v-if="msg.logicResult" class="voice-logic-result">
              <div><strong>语言逻辑分析:</strong></div>
              <div>{{ msg.logicResult.analysis }}</div>
              <div v-if="msg.logicResult.score"><strong>连贯性评分:</strong> {{ msg.logicResult.score }}/10</div>
            </div>
          </div>

          <!-- 表情和姿态分析消息 -->
          <div v-if="msg.type === 'expression'" class="expression-bubble">
            <div class="expression-image-container">
              <img :src="msg.imageUrl" class="expression-image" alt="表情和姿态分析截图">
            </div>

            <!-- 表情分析结果 -->
            <div  class="expression-results">
              <div><strong>表情与动作分析:</strong></div>
              
              <div>{{ msg.expressionResults.result }}</div>
            </div>

            <!-- 姿态分析结果 -->
            <div v-if="msg.poseResult" class="pose-result">
              <div><strong>姿态分析:</strong></div>
              <div>动作: {{ msg.poseResult.pose }}</div>
              <div>置信度: {{ (msg.poseResult.score * 100).toFixed(1) }}%</div>
              <div>帧率: {{ msg.poseResult.fps }}fps</div>
            </div>

            <!-- 综合分析结果 -->
            <div v-if="msg.comprehensiveAnalysis" class="comprehensive-analysis">
              <div><strong>综合分析:</strong></div>
              <div>{{ msg.comprehensiveAnalysis }}</div>
            </div>

            <!-- 操作按钮 -->
            <div class="expression-actions" v-if="msg.sender === 'user'">
              <van-button size="mini" type="primary" @click="analyzeComprehensive(index)" round>
                综合分析
              </van-button>
              <van-button size="mini" type="success" @click="saveAnalysisToStorage(msg)" round>
                保存分析
              </van-button>
            </div>
          </div>
        </div>

        <!-- 正在输入指示器 -->
        <div v-if="isTyping" :id="typingId" class="message-item ai-message">
          <div class="avatar">

          </div>
          <div class="message-bubble typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入栏 -->
    <div id="dialog_bottombar">
      <div id="dialog_bottombar_inside">
        <!-- 使用flex布局将输入框和发送按钮放在同一行 -->
        <div style="display: flex; align-items: flex-end; gap: 8px;">
          <van-field type="textarea" rows="1" :autosize="{ maxHeight: 100, minHeight: 40 }" v-model="message"
            style="border-radius:25px; padding:10px; flex: 1;" @keypress.enter.prevent="sendMessage"
            placeholder="输入消息..." />

          <!-- 发送按钮移至输入框右侧 -->
          <van-button round type="primary" size="small" @click="sendMessage"
            style="width:60px; height:60px; padding:0; display:flex; align-items:center; justify-content:center;"
            :disabled="!message.trim()">
            发送
            <van-icon name="paper-plane-o" size="16" style="margin-left: 2px;" />
          </van-button>
        </div>

        <van-row style="padding-top: 8px;">
          <van-col span="8" style="text-align:center;">
            <van-icon :name="isRecording ? 'stop' : require('@/assets/icon/icon_dialog_语音.png')" size="20"
              @click="startInterviewProcess()" />
          </van-col>
          <van-col span="8" style="text-align:center;">
            <van-icon name="image" size="20" />
          </van-col>
          <van-col span="4" style="text-align:center;">
            <van-icon :name="require('@/assets/icon/icon_dialog_相机.png')" size="20" @click="toggleCamera"
              :class="isCameraActive ? 'camera-active' : ''" />
          </van-col>
          <van-col span="4" style="text-align:center;">
            <van-icon name="red-envelope" size="20" />
          </van-col>
          
          <!-- 移除原发送按钮所在的van-col -->
        </van-row>
      </div>

    </div>

    <van-popup 
      v-model:show="isCameraModalVisible" 
      :style="{
        width: popupWidth + 'px',   // 动态宽度
        height: popupHeight + 'px', // 动态高度
        left: popupLeft + 'px',     // 动态左偏移
        top: popupTop + 'px',       // 动态上偏移
        'z-index': 100,
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        overflow: 'hidden',
        position: 'fixed',  // 固定定位，支持自由移动
        margin: 0           // 清除默认margin
      }" 
      :overlay="false"
      :position="null"
    >
      <!-- 弹窗头部（可拖拽区域） -->
      <!-- 开始拖拽 -->
      <div 
        class="camera-header"
        style="padding: 12px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; cursor: move;"
        @mousedown="startDrag"
      >
        <h3 style="margin: 0; font-size: 16px;">表情与姿态识别</h3>
        <van-icon name="close" @click="toggleCamera" style="font-size: 20px; cursor: pointer;" />
      </div>

      <!-- 相机预览区域 -->
      <div class="camera-preview" style="flex: 1; padding: 10px; box-sizing: border-box; position: relative;">
        <video ref="videoElement" autoplay playsinline class="camera-video"
          style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;"></video>

        <!-- 加载中状态 -->
        <div v-if="isLoadingCamera"
          style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
          <van-loading type="spinner" color="#1677ff" />
          <p style="margin-top: 8px; color: #666;">正在初始化相机...</p>
        </div>

        <!-- 错误提示 -->
        <div v-if="cameraError"
          style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #f53f3f;">
          <van-icon name="warning-circle" color="#f53f3f" size="24" />
          <p style="margin-top: 8px;">{{ cameraError }}</p>
        </div>
      </div>

      <!-- 相机控制按钮 -->
      <div class="camera-controls" style="padding: 12px; display: flex; gap: 10px; justify-content: center;">
        <van-button type="primary" round @click="captureImage" :disabled="!isCameraActive || isProcessingImage"
          style="padding: 8px 20px;">
          <van-icon name="camera" size="18" style="margin-right: 5px;" />
          {{ isProcessingImage ? '处理中...' : '拍照分析' }}
        </van-button>

        <van-button type="info" round @click="startContinuousAnalysis"
          :disabled="!isCameraActive || isAnalyzingContinuously" style="padding: 8px 20px;">
          <van-icon name="play" size="18" style="margin-right: 5px;" />
          {{ isAnalyzingContinuously ? '停止连续分析' : '连续分析' }}
        </van-button>
      </div>

      <!-- 右下角 resize 手柄（用于调整大小） -->
      <div 
        class="resize-handle"
        style="position: absolute; right: 0; bottom: 0; width: 15px; height: 15px; cursor: nwse-resize; background: #1677ff; border-radius: 0 0 12px 0;"
        @mousedown="startResize"
      ></div>
    </van-popup>


    <!-- 评测报告弹窗 -->
    <van-popup v-model:show="isReportVisible" position="center"
      :style="{ width: '90%', maxWidth: '800px', height: '90%', overflow: 'auto' }">
      <div class="report-container">
        <div class="report-header">
          
          <van-icon name="close" @click="isReportVisible = false" class="close-icon" />
        </div>

        <div v-if="reportLoading" class="report-loading">
          <van-loading type="spinner" color="#1677ff" size="30" />
          <p>正在生成评估报告...</p>
        </div>

        <div v-else-if="reportError" class="report-error">
          <van-icon name="warning-circle" color="#f53f3f" size="24" />
          <p>{{ reportError }}</p>
          <van-button @click="generateReportFromStorage" type="primary" round>重试</van-button>
        </div>

        
      </div>
    </van-popup>

    <!-- 录音提示 -->
    <div v-if="isRecording" class="recording-indicator">
      <div class="recording-dot"></div>
      <p>正在录音...{{ recordingSeconds }}s</p>
      <p>松开结束录音</p>
    </div>

    <!-- 服务状态提示 -->
    <div class="status-bar" :class="statusClass" style="z-index: 998;">
      {{ statusText }}
    </div>
  </div>
</template>

<script>
import { Chart, registerables, RadarController } from 'chart.js';

export default {
  data() {
    return {
    // 弹窗初始位置和尺寸（可根据需求调整）
      popupWidth: 300,
      popupHeight: 600,
      popupLeft: 500,
      popupTop: 100,
      
      // 拖拽相关状态
      isDragging: false,
      startX: 0,
      startY: 0,
      
      // 调整大小相关状态
      isResizing: false,
      startWidth: 0,
      startHeight: 0,
      msg: {
        // 提前初始化 expressionResults 为数组，避免 undefined
        expressionResults: []
      },
      // 关键问题定位
      keyIssues: '',
      issueExamples: [],

      // 反馈建议
      feedbackCategories: [],

      name: this.$route.params.name,
      message: "",
      messages: [],
      isTyping: false,
      typingId: "",
      API_BASE_URL: 'https://123.56.203.202',
      statusText: '连接中...',
      statusClass: 'text-xs text-gray-500 mt-2 text-center',
      commonHeaders: {
        'ngrok-skip-browser-warning': '1'
      },

      // 语音相关状态
      isRecording: false,
      mediaRecorder: null,
      audioBlob: null,
      recordingSeconds: 0,
      recordingTimer: null,
      audioContext: null,
      audioElements: {},
      mediaStream: null,
      audioChunks: [],
      transcribeCount: 0, // 转写计数，用于跟踪是第几次转写

      // 相机相关状态
      isCameraModalVisible: false,
      isCameraActive: false,
      isLoadingCamera: false,
      cameraError: null,
      isProcessingImage: false,
      isAnalyzingContinuously: false,
      continuousAnalysisTimer: null,
      detectionInterval: null,
      videoStream: null,

      // 评测报告相关状态
      isReportVisible: false,
      reportLoading: false,
      reportError: '',
      chart: null,
      reportResponse: null, // 存储原始响应数据

      // 报告数据 - 五个维度
      reportIndicators: [
        '专业知识水平',
        '技能匹配度',
        '语言表达能力',
        '逻辑思维能力',
        '创新能力'
      ],
      reportValues: [60, 60, 60, 60, 60],

      // 问题和答案存储
      firstQuestion: '',
      secondQuestion: '',
      thirdQuestion: '',
      fourthQuestion: '',
      fifthQuestion: '',
      firstResult: '',
      secondResult: '',
      thirdResult: '',
      fourthResult: '',
      fifthResult: '',

      // 详细分析数据
      professionalKnowledgeAnalysis: '', // 专业知识水平
      skillMatchAnalysis: '', // 技能匹配度
      languageExpressionAnalysis: '', // 语言表达能力
      logicalThinkingAnalysis: '', // 逻辑思维能力
      innovationAbilityAnalysis: '', // 创新能力
      comprehensiveEvaluation: '',
      improvementSuggestions: []
    };
  },
  computed: {
    // 格式化响应体数据用于展示
    formattedReportResponse() {
      if (!this.reportResponse) return '无响应数据';
      return JSON.stringify(this.reportResponse, null, 2);
    }
  },
  mounted() {
    localStorage.setItem('career', '大数据运维测试岗');
    console.log(localStorage.getItem('career'));
    
    this.testConnection();
    this.initContainerHeight();
    window.addEventListener('resize', this.initContainerHeight);
    this.checkRecordingSupport();

    // 从localStorage加载已保存的问题和答案
    this.loadStoredQuestionsAndAnswers();

    // 注册Chart.js组件
    Chart.register(...registerables);
    Chart.register(RadarController);
    window.Chart = Chart;



  },
  beforeUnmount() {
    window.removeEventListener('resize', this.initContainerHeight);
    this.stopRecording();
    Object.values(this.audioElements).forEach(audio => {
      if (audio) {
        audio.pause();
      }
    });

    // 清理相机相关资源
    this.stopCamera();
    if (this.continuousAnalysisTimer) {
      clearInterval(this.continuousAnalysisTimer);
    }
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
    }

    // 销毁图表
    if (this.chart) {
      this.chart.destroy();
    }
  },
  methods: {
     // 开始拖拽弹窗
    startDrag(e) {
      this.isDragging = true;
      // 记录初始鼠标位置和弹窗位置
      this.startX = e.clientX;
      this.startY = e.clientY;
      
      // 绑定鼠标移动和释放事件
      document.addEventListener('mousemove', this.handleDrag);
      document.addEventListener('mouseup', this.stopDrag);
      e.preventDefault(); // 防止拖动时选中文本
    },
    
    // 处理拖拽逻辑
    handleDrag(e) {
      if (!this.isDragging) return;
      
      // 计算鼠标移动距离
      const deltaX = e.clientX - this.startX;
      const deltaY = e.clientY - this.startY;
      
      // 更新弹窗位置（限制在可视区域内）
      const newLeft = this.popupLeft + deltaX;
      const newTop = this.popupTop + deltaY;
      
      // 限制左边界不小于0
      this.popupLeft = Math.max(0, newLeft);
      // 限制上边界不小于0
      this.popupTop = Math.max(0, newTop);
      // 限制右边界不超过窗口宽度
      this.popupLeft = Math.min(window.innerWidth - this.popupWidth, this.popupLeft);
      // 限制下边界不超过窗口高度
      this.popupTop = Math.min(window.innerHeight - this.popupHeight, this.popupTop);
      
      // 更新初始位置（用于下一次计算）
      this.startX = e.clientX;
      this.startY = e.clientY;
    },
    
    // 停止拖拽
    stopDrag() {
      this.isDragging = false;
      document.removeEventListener('mousemove', this.handleDrag);
      document.removeEventListener('mouseup', this.stopDrag);
    },
    
    // 开始调整大小
    startResize(e) {
      this.isResizing = true;
      // 记录初始鼠标位置和弹窗尺寸
      this.startX = e.clientX;
      this.startY = e.clientY;
      this.startWidth = this.popupWidth;
      this.startHeight = this.popupHeight;
      
      // 绑定鼠标移动和释放事件
      document.addEventListener('mousemove', this.handleResize);
      document.addEventListener('mouseup', this.stopResize);
      e.preventDefault(); // 防止拖动时选中文本
    },
    
    // 处理调整大小逻辑
    handleResize(e) {
      if (!this.isResizing) return;
      
      // 计算鼠标移动距离（控制宽高变化）
      const deltaWidth = e.clientX - this.startX;
      const deltaHeight = e.clientY - this.startY;
      
      // 计算新的宽高（设置最小尺寸限制，避免过小）
      const minWidth = 200;
      const minHeight = 300;
      this.popupWidth = Math.max(minWidth, this.startWidth + deltaWidth);
      this.popupHeight = Math.max(minHeight, this.startHeight + deltaHeight);
      
      // 限制最大尺寸不超过窗口
      this.popupWidth = Math.min(window.innerWidth - 50, this.popupWidth);
      this.popupHeight = Math.min(window.innerHeight - 50, this.popupHeight);
    },
    
    // 停止调整大小
    stopResize() {
      this.isResizing = false;
      document.removeEventListener('mousemove', this.handleResize);
      document.removeEventListener('mouseup', this.stopResize);
    },
    // 从localStorage加载已保存的问题和答案
    loadStoredQuestionsAndAnswers() {
      // 硬编码设置指定的五个问题到localStorage（如果不存在）
      const defaultQuestions = [
        {
          id: "firstQuestion",
          content: "请详细阐述您对大数据运维测试岗领域中核心概念和技术的理解，以及您在实际项目中如何应用这些知识解决问题。"
        },
        {
          id: "secondQuestion",
          content: "在大数据运维测试岗岗位上，您认为哪些关键技能是必不可少的？请举例说明您在这些技能方面的掌握程度和实际应用经验。"
        },
        {
          id: "thirdQuestion",
          content: "请描述一次您需要向非技术团队成员清晰解释大数据运维测试岗相关复杂技术概念的经历。您采用了什么方法确保对方理解？"
        },
        {
          id: "fourthQuestion",
          content: "在大数据运维测试岗工作中，当面对一个复杂问题时，您的分析和解决问题的逻辑步骤是什么？请分享一个具体案例。"
        },
        {
          id: "fifthQuestion",
          content: "请分享一个您在大数据运维测试岗相关项目中提出创新解决方案的经历。您是如何发现问题并提出新颖的解决思路的？"
        }
      ];

      // 初始化localStorage中的问题（如果不存在）
      defaultQuestions.forEach(question => {
        if (!localStorage.getItem(question.id)) {
          localStorage.setItem(question.id, question.content);
        }
      });

      // 从localStorage加载问题到组件
      this.firstQuestion = localStorage.getItem("firstQuestion") || '';
      this.secondQuestion = localStorage.getItem("secondQuestion") || '';
      this.thirdQuestion = localStorage.getItem("thirdQuestion") || '';
      this.fourthQuestion = localStorage.getItem("fourthQuestion") || '';
      this.fifthQuestion = localStorage.getItem("fifthQuestion") || '';

      // 从localStorage加载答案到组件
      this.firstResult = localStorage.getItem("firstResult") || '';
      this.secondResult = localStorage.getItem("secondResult") || '';
      this.thirdResult = localStorage.getItem("thirdResult") || '';
      this.fourthResult = localStorage.getItem("fourthResult") || '';
      this.fifthResult = localStorage.getItem("fifthResult") || '';
    },

    startInterviewProcess() {
  // 模拟avatarPlatform2已实例化
  const avatarPlatform2 = true;

  if (avatarPlatform2) {
    // 初始调用 - 问候语（带自动播放视频）
    let username = localStorage.getItem("username") || "候选人";
    let career = localStorage.getItem("career") || "相关岗位";
    let text = `你好，${username}，欢迎面试${career}。接下来将进行面试环节，共有五道题目，涉及专业知识水平、技能匹配度、语言表达能力、逻辑思维能力和创新能力五个维度。请认真思考后回答。`;

    // 创建视频元素并设置自动播放
    const videoElement = document.createElement('video');
    videoElement.controls = true; // 显示播放控件
    videoElement.autoplay = true; // 自动播放
    videoElement.muted = false; // 不静音
    videoElement.style.width = "100%";
    videoElement.style.maxWidth = "600px";
    videoElement.style.marginTop = "15px";

    // 添加视频源
    const sourceElement = document.createElement('source');
    sourceElement.src = "https://123.56.203.202/proxy_files?path=D%3A%5CTemp%5Crengongzhinengjishugang.mp4";
    sourceElement.type = "video/mp4";
    videoElement.appendChild(sourceElement);

    // 处理自动播放限制的兼容方案
    videoElement.addEventListener('canplaythrough', () => {
      // 尝试播放，处理浏览器自动播放政策限制
      videoElement.play().catch(e => {
        console.log('自动播放被浏览器限制，需要用户交互后播放:', e);
        // 显示提示让用户手动播放
        const playPrompt = document.createElement('p');
        playPrompt.style.color = '#666';
        playPrompt.style.fontSize = '14px';
        playPrompt.textContent = '提示：请点击播放按钮观看面试说明';
        messageContainer.appendChild(playPrompt);
      });
    });

    // 创建包含文本和视频的容器
    const messageContainer = document.createElement('div');
    messageContainer.innerHTML = `<p>${text}</p>`;
    messageContainer.appendChild(videoElement);

    // 添加不支持视频的提示
    const fallbackText = document.createTextNode("您的浏览器不支持视频播放功能");
    messageContainer.appendChild(fallbackText);

    // 添加消息到界面
    this.addMessage('ai', text, 'text');

    // 设置30秒后自动显示面试题弹窗（横向单题展示）
    setTimeout(() => {
      // 硬编码岗位为人工智能技术岗
      const career = "大数据运维测试岗";

      // 五道题目的文本内容
      const questions = [
        {
          title: "第一道题",
          text: '',
          videoUrl: "https://123.56.203.202/proxy_files?path=D%3A/Temp/%E5%A4%A7%E6%95%B0%E6%8D%AE%E8%BF%90%E7%BB%B4%E6%B5%8B%E8%AF%95%E5%B2%971.mp4",
          id: "first"
        },
        {
          title: "第二道题",
          text: '',
          videoUrl: "https://123.56.203.202/proxy_files?path=D%3A/Temp/%E5%A4%A7%E6%95%B0%E6%8D%AE%E8%BF%90%E7%BB%B4%E6%B5%8B%E8%AF%95%E5%B2%972.mp4",
          id: "second"
        },
        {
          title: "第三道题",
          text: '',
          videoUrl: "https://123.56.203.202/proxy_files?path=D%3A/Temp/%E5%A4%A7%E6%95%B0%E6%8D%AE%E8%BF%90%E7%BB%B4%E6%B5%8B%E8%AF%95%E5%B2%973.mp4",
          id: "third"
        },
        {
          title: "第四道题",
          text: '',
          videoUrl: "https://123.56.203.202/proxy_files?path=D%3A/Temp/%E5%A4%A7%E6%95%B0%E6%8D%AE%E8%BF%90%E7%BB%B4%E6%B5%8B%E8%AF%95%E5%B2%974.mp4",
          id: "fourth"
        },
        {
          title: "第五道题",
          text: '',
          videoUrl: "https://123.56.203.202/proxy_files?path=D%3A/Temp/%E5%A4%A7%E6%95%B0%E6%8D%AE%E8%BF%90%E7%BB%B4%E6%B5%8B%E8%AF%95%E5%B2%975.mp4",
          id: "fifth"
        }
      ];

      // 当前题目索引
      let currentIndex = 0;

      // 弹窗位置和大小的默认值
      const defaultWidth = 800;
      const defaultHeight = 600;
      const defaultLeft = (window.innerWidth - defaultWidth) / 2;
      const defaultTop = (window.innerHeight - defaultHeight) / 2;

      // 创建弹窗元素（背景遮罩）
      const modal = document.createElement('div');
      modal.style.cssText = `
position: fixed;
top: 0;
left: 0;
width: 100%;
height: 100%;
background: rgba(0,0,0,0.5);

display: flex;
justify-content: center;
align-items: center;
background: rgba(0,0,0,0.1); /* 降低透明度 */
  z-index: 999; /* 降低z-index，确保主页面元素可交互 */
  pointer-events: none; /* 关键：允许点击穿透遮罩层 */
`;

      // 创建可拖拽的弹窗容器
      const draggableModal = document.createElement('div');
      draggableModal.style.cssText = `
width: ${defaultWidth}px;
height: ${defaultHeight}px;
left: ${defaultLeft}px;
top: ${defaultTop}px;
position: absolute;
box-shadow: 0 4px 20px rgba(0,0,0,0.15);
border-radius: 12px;
overflow: hidden;
display: flex;
flex-direction: column;
z-index: 1000; /* 确保弹窗在遮罩层上方 */
  pointer-events: auto; /* 确保弹窗自身可交互 */
`;

      // 弹窗标题栏（可拖拽区域）
      const modalHeader = document.createElement('div');
      
      modalHeader.style.cssText = `
background: #f8f9fa;
padding: 15px 20px;
border-bottom: 1px solid #eee;
display: flex;
justify-content: space-between;
align-items: center;
cursor: move;
`;
      
      // 标题文本
      const headerTitle = document.createElement('h3');
      headerTitle.textContent = '面试题目';
      headerTitle.style.cssText = `
margin: 0;
font-size: 16px;
color: #333;
`;
      
      // 关闭按钮
      const closeButton = document.createElement('button');
      closeButton.innerHTML = '×';
      closeButton.style.cssText = `
background: none;
border: none;
font-size: 20px;
cursor: pointer;
color: #666;
padding: 0 10px;
line-height: 1;
`;
      
      modalHeader.appendChild(headerTitle);
      modalHeader.appendChild(closeButton);
      // 就在这里添加关闭按钮的点击事件（这是关键的添加位置）
closeButton.addEventListener('click', () => {
  if (confirm('确定要关闭吗？已填写的回答可能会丢失。')) {
    document.body.removeChild(modal);
  }
});

      // 弹窗内容容器
      const modalContainer = document.createElement('div');
      modalContainer.style.cssText = `
background: white;
flex: 1;
display: flex;
flex-direction: column;
overflow: hidden;
`;

      // 题目导航指示器
      const progressIndicator = document.createElement('div');
      progressIndicator.id = 'progressIndicator';
      progressIndicator.style.cssText = `
display: flex;
justify-content: center;
margin: 15px 0;
gap: 8px;
padding: 0 20px;
`;

      // 创建进度点
      questions.forEach((_, index) => {
        const dot = document.createElement('div');
        dot.id = `progress-${index}`;
        dot.style.cssText = `
width: 12px;
height: 12px;
border-radius: 50%;
background: #ddd;
transition: all 0.3s ease;
`;
        progressIndicator.appendChild(dot);
      });

      // 题目内容区域 - 添加滚动功能
      const questionContentWrapper = document.createElement('div');
      questionContentWrapper.style.cssText = `
flex: 1;
overflow-y: auto;
padding: 0 20px;
`;

      // 题目内容容器
      const questionContent = document.createElement('div');
      questionContent.id = 'questionContent';
      questionContentWrapper.appendChild(questionContent);

      // 按钮区域
      const buttonContainer = document.createElement('div');
      buttonContainer.style.cssText = `
display: flex;
justify-content: space-between;
padding: 15px 20px;
border-top: 1px solid #eee;
`;

      // 上一题按钮
      const prevButton = document.createElement('button');
      prevButton.textContent = '上一题';
      prevButton.style.cssText = `
background: #f0f0f0;
color: #333;
border: none;
padding: 10px 20px;
border-radius: 6px;
cursor: pointer;
font-size: 14px;
transition: background 0.3s;
`;
      prevButton.addEventListener('mouseover', () => prevButton.style.background = '#e0e0e0');
      prevButton.addEventListener('mouseout', () => prevButton.style.background = '#f0f0f0');

      // 下一题/提交按钮
      const nextButton = document.createElement('button');
      nextButton.textContent = '下一题';
      nextButton.style.cssText = `
background: #4CAF50;
color: white;
border: none;
padding: 10px 20px;
border-radius: 6px;
cursor: pointer;
font-size: 14px;
transition: background 0.3s;
`;
      nextButton.addEventListener('mouseover', () => nextButton.style.background = '#45a049');
      nextButton.addEventListener('mouseout', () => nextButton.style.background = '#4CAF50');

      // 右下角调整大小手柄
      const resizeHandle = document.createElement('div');
      resizeHandle.style.cssText = `
position: absolute;
right: 0;
bottom: 0;
width: 15px;
height: 15px;
cursor: nwse-resize;
background: #4CAF50;
border-radius: 4px 0 0 0;
`;

      // 组装弹窗
      buttonContainer.appendChild(prevButton);
      buttonContainer.appendChild(nextButton);
      modalContainer.appendChild(progressIndicator);
      modalContainer.appendChild(questionContentWrapper);
      modalContainer.appendChild(buttonContainer);
      draggableModal.appendChild(modalHeader);
      draggableModal.appendChild(modalContainer);
      draggableModal.appendChild(resizeHandle);
      modal.appendChild(draggableModal);
      document.body.appendChild(modal);

      // 渲染当前题目
      function renderCurrentQuestion() {
        const question = questions[currentIndex];

        // 更新进度指示器
        document.querySelectorAll('#progressIndicator div').forEach((dot, index) => {
          if (index < currentIndex) {
            dot.style.background = '#4CAF50'; // 已完成
          } else if (index === currentIndex) {
            dot.style.background = '#2196F3'; // 当前
            dot.style.transform = 'scale(1.2)';
          } else {
            dot.style.background = '#ddd'; // 未完成
            dot.style.transform = 'scale(1)';
          }
        });

        // 检查是否有已保存的回答
        const savedAnswer = localStorage.getItem(`${question.id}Result`) || '';

        // 渲染题目内容，包含语音识别控件
        questionContent.innerHTML = `
<h2 style="margin-top: 0; color: #333; font-size: 20px;">${question.title}</h2>
<p style="font-size: 16px; line-height: 1.6; color: #555; margin: 15px 0;">${question.text}</p>

<div style="margin: 20px 0;">
  <p style="margin-bottom: 10px; font-weight: 500;">相关视频参考：</p>
  <video controls style="width: 100%; max-height: 300px; object-fit: contain;">
    <source src="${question.videoUrl}" type="video/mp4">
    您的浏览器不支持视频播放
   </video>
</div>

<!-- 语音输入控件 -->
<div style="margin: 15px 0; padding: 15px; background: #f9f9f9; border-radius: 6px;">
  <div style="display: flex; gap: 10px; margin-bottom: 15px;">
    <button id="startRecord" style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
      开始录音
    </button>
    <button id="stopRecord" style="background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; display: none;">
      停止录音
    </button>
  </div>
  
  <!-- 语音分析结果展示 -->
  <div style="font-size: 14px; color: #666; margin-top: 10px;">
    <p>语调状态：<span id="toneStatus">未检测</span></p>
    <p>语速：<span id="speedStatus">未计算</span>（字/秒）</p>
    <p>录音时长：<span id="recordTime">0秒</span></p>
  </div>
</div>

<textarea id="${question.id}Answer" style="width: 100%; height: 200px; margin: 15px 0; padding: 12px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; resize: vertical;" placeholder="请输入您的回答...">${savedAnswer}</textarea>
`;

        // 初始化语音识别和音频分析
        initSpeechRecognition(question.id);

        // 更新按钮状态
        prevButton.disabled = currentIndex === 0;
        prevButton.style.opacity = currentIndex === 0 ? '0.5' : '1';
        prevButton.style.cursor = currentIndex === 0 ? 'not-allowed' : 'pointer';

        // 最后一题显示提交按钮
        if (currentIndex === questions.length - 1) {
          nextButton.textContent = '提交回答';
          nextButton.style.background = '#2196F3';
        } else {
          nextButton.textContent = '下一题';
          nextButton.style.background = '#4CAF50';
        }

        // 重置滚动位置到顶部
        questionContentWrapper.scrollTop = 0;
      }

      // 初始化语音识别和音频分析
      function initSpeechRecognition(questionId) {
        const startBtn = document.getElementById('startRecord');
        const stopBtn = document.getElementById('stopRecord');
        const toneStatus = document.getElementById('toneStatus');
        const speedStatus = document.getElementById('speedStatus');
        const recordTime = document.getElementById('recordTime');
        const answerTextarea = document.getElementById(`${questionId}Answer`);

        // 语音识别相关变量
        let recognition;
        let isRecording = false;
        let recordStartTime = 0;
        let recordDuration = 0; // 录音时长（秒）
        let mediaRecorder;
        let audioContext;
        let analyser;
        let dataArray;
        let animationId;

        // 初始化语音识别（基于Web Speech API）
        function initRecognition() {
          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SpeechRecognition) {
            alert('您的浏览器不支持语音识别功能，请使用Chrome等现代浏览器');
            return null;
          }
          const rec = new SpeechRecognition();
          rec.continuous = true; // 持续识别
          rec.interimResults = true; // 返回中间结果
          rec.lang = 'zh-CN'; // 中文识别
          return rec;
        }

        // 初始化音频分析器（检测语调）
        function initAudioAnalyser(stream) {
          audioContext = new (window.AudioContext || window.webkitAudioContext)();
          analyser = audioContext.createAnalyser();
          const source = audioContext.createMediaStreamSource(stream);
          source.connect(analyser);
          analyser.fftSize = 256; // 快速傅里叶变换大小
          const bufferLength = analyser.frequencyBinCount;
          dataArray = new Uint8Array(bufferLength);
        }

        // 实时分析语调（基于频率）
        function analyzeTone() {
          if (!isRecording) return;
          analyser.getByteFrequencyData(dataArray);

          // 计算平均频率（简单模拟语调：频率越高，语调越高）
          let sum = 0;
          dataArray.forEach(value => sum += value);
          const averageFreq = sum / dataArray.length;

          // 更新语调状态
          if (averageFreq > 80) {
            toneStatus.textContent = '语调偏高（情绪较激动）';
            toneStatus.style.color = '#e53935';
          } else if (averageFreq > 40) {
            toneStatus.textContent = '语调适中';
            toneStatus.style.color = '#43a047';
          } else {
            toneStatus.textContent = '语调偏低（情绪较平稳）';
            toneStatus.style.color = '#1e88e5';
          }

          animationId = requestAnimationFrame(analyzeTone);
        }

        // 开始录音
        startBtn.addEventListener('click', async () => {
          if (isRecording) return;
          isRecording = true;
          startBtn.style.display = 'none';
          stopBtn.style.display = 'inline-block';
          recordStartTime = Date.now();

          // 启动语音识别
          recognition = initRecognition();
          if (!recognition) return;
          recognition.start();
          recognition.onresult = (event) => {
            // 拼接识别结果
            let transcript = '';
            for (let i = 0; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript;
            }
            answerTextarea.value = transcript; // 填充到文本框
          };

          // 启动音频流和分析器
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            initAudioAnalyser(stream);
            analyzeTone(); // 开始实时语调分析

            // 实时更新录音时长
            function updateRecordTime() {
              if (!isRecording) return;
              recordDuration = Math.floor((Date.now() - recordStartTime) / 1000);
              recordTime.textContent = `${recordDuration}秒`;
              requestAnimationFrame(updateRecordTime);
            }
            updateRecordTime();
          } catch (err) {
            console.error('录音权限获取失败：', err);
            alert('请允许麦克风权限以使用语音输入功能');
            stopRecording();
          }
        });

        // 停止录音
        function stopRecording() {
          if (!isRecording) return;
          isRecording = false;
          startBtn.style.display = 'inline-block';
          stopBtn.style.display = 'none';
          cancelAnimationFrame(animationId);

          // 停止语音识别
          if (recognition) recognition.stop();
          // 停止录音
          if (mediaRecorder) mediaRecorder.stop();
          // 关闭音频上下文
          if (audioContext) audioContext.close();

          // 计算语速（字数 / 录音时长）
          const text = answerTextarea.value.trim();
          const charCount = text.length; // 文本长度（字数）
          if (recordDuration > 0) {
            const speed = (charCount / recordDuration).toFixed(1); // 保留1位小数
            speedStatus.textContent = `${speed}字/秒`;

            // 语速提示（参考：正常中文语速约2-3字/秒）
            if (speed < 1.5) {
              speedStatus.style.color = '#e53935';
              speedStatus.textContent += '（偏慢）';
            } else if (speed > 3.5) {
              speedStatus.style.color = '#e53935';
              speedStatus.textContent += '（偏快）';
            } else {
              speedStatus.style.color = '#43a047';
              speedStatus.textContent += '（正常）';
            }
          }
        }

        stopBtn.addEventListener('click', stopRecording);
      }

      // 上一题按钮事件
      prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
          // 保存当前回答
          saveCurrentAnswer();
          currentIndex--;
          renderCurrentQuestion();
        }
      });

      // 下一题/提交按钮事件
      nextButton.addEventListener('click', () => {
        const currentAnswer = document.querySelector(`#${questions[currentIndex].id}Answer`).value.trim();

        // 验证当前回答
        if (!currentAnswer) {
          alert(`请完成${questions[currentIndex].title}的回答`);
          return;
        }

        // 保存当前回答
        saveCurrentAnswer();

        // 最后一题则提交所有
        if (currentIndex === questions.length - 1) {
          // 提交所有回答
          questions.forEach(question => {
            const answer = localStorage.getItem(`${question.id}Result`) || '';
            this.addMessage('user', `【${question.title}回答】${answer}`, 'text');
          });

          alert('所有回答已提交成功！');
          document.body.removeChild(modal);
        } else {
          // 进入下一题
          currentIndex++;
          renderCurrentQuestion();
        }
      });

      // 保存当前题目的回答
      function saveCurrentAnswer() {
        const question = questions[currentIndex];
        const answer = document.querySelector(`#${question.id}Answer`).value.trim();
        if (answer) {
          localStorage.setItem(`${question.id}Result`, answer);
        }
      }

      
      // 拖拽功能实现
      let isDragging = false;
      let startX, startY, initialLeft, initialTop;

      modalHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        initialLeft = parseInt(draggableModal.style.left);
        initialTop = parseInt(draggableModal.style.top);
        
        // 添加拖拽时的样式
        draggableModal.style.transition = 'none';
        modalHeader.style.background = '#e9ecef';
        
        document.addEventListener('mousemove', handleDrag);
        document.addEventListener('mouseup', stopDrag);
        
        e.preventDefault();
      });

      function handleDrag(e) {
        if (!isDragging) return;
        
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        
        // 计算新位置并限制在窗口内
        let newLeft = initialLeft + deltaX;
        let newTop = initialTop + deltaY;
        
        // 限制在窗口内
        newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - draggableModal.offsetWidth));
        newTop = Math.max(0, Math.min(newTop, window.innerHeight - draggableModal.offsetHeight));
        
        draggableModal.style.left = `${newLeft}px`;
        draggableModal.style.top = `${newTop}px`;
      }

      function stopDrag() {
        isDragging = false;
        modalHeader.style.background = '';
        document.removeEventListener('mousemove', handleDrag);
        document.removeEventListener('mouseup', stopDrag);
      }

      // 调整大小功能实现
      let isResizing = false;
      let startWidth, startHeight;

      resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = draggableModal.offsetWidth;
        startHeight = draggableModal.offsetHeight;
        
        // 移除过渡效果，使调整更流畅
        draggableModal.style.transition = 'none';
        
        document.addEventListener('mousemove', handleResize);
        document.addEventListener('mouseup', stopResize);
        
        e.preventDefault();
      });

      function handleResize(e) {
        if (!isResizing) return;
        
        // 计算新尺寸
        const minWidth = 500;
        const minHeight = 400;
        const newWidth = Math.max(minWidth, startWidth + (e.clientX - startX));
        const newHeight = Math.max(minHeight, startHeight + (e.clientY - startY));
        
        // 限制最大尺寸不超过窗口
        const maxWidth = window.innerWidth - 50;
        const maxHeight = window.innerHeight - 50;
        
        draggableModal.style.width = `${Math.min(newWidth, maxWidth)}px`;
        draggableModal.style.height = `${Math.min(newHeight, maxHeight)}px`;
      }

      function stopResize() {
        isResizing = false;
        document.removeEventListener('mousemove', handleResize);
        document.removeEventListener('mouseup', stopResize);
      }

      // 初始化显示第一题
      renderCurrentQuestion();
    }, 40000);
  } else {
    this.showStatus("请先实例化SDK", 'error');
  }
},
    



    // 返回主页面消息界面
    backToHomeMessage() {
      this.$router.push('/home/message');
    },

    // 发送文本消息
    async sendMessage() {
      let prompt = this.message.trim();
      if (!prompt) return;

      // 检测输入是否为特定指令
      const isLogicAnalysis = prompt.toLowerCase().includes('分析语言逻辑');
      const isGenerateReport = prompt.toLowerCase().includes('生成可视化评测报告');
      let constructedPrompt = prompt;

      // 处理"分析语言逻辑"指令
      if (isLogicAnalysis) {
        constructedPrompt = this.buildLogicAnalysisPrompt();
      }
      // 处理"生成可视化评测报告"指令
      else if (isGenerateReport) {
        constructedPrompt = this.buildEvaluationReportPrompt();
      }

      this.addMessage('user', prompt, 'text');
      this.message = '';
      this.scrollToBottom();

      const typingId = this.addTypingIndicator();

      try {
        fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: constructedPrompt })
        }).then(response => {
          this.removeTypingIndicator(typingId);

          if (!response.ok) {
            throw new Error(`请求失败: ${response.status}`);
          }

          return response.json();
        }).then(data => {
          if (data.status === 'success') {
            const taskId = data.task_id;
            const pollInterval = 20000; // 20秒轮询一次
            const maxAttempts = 150;
            let attempts = 0;

            const pollForFile = () => {
              if (attempts >= maxAttempts) {
                this.addMessage('ai', '请求超时，请稍后再试', 'text', true);
                this.scrollToBottom();
                return;
              }

              attempts++;

              fetch(`${this.API_BASE_URL}/get_task_file_url`, {
                method: 'POST',
                headers: {
                  ...this.commonHeaders,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ task_id: taskId })
              })
                .then(response => {
                  return response.json().then(data => ({ data, response }));
                })
                .then(({ data, response }) => {
                  console.log('文件查询响应:', data);

                  // 成功获取到文件信息
                  if (data.status === 'success') {
                    // 优先使用Markdown文件（如果存在）
                    const targetFile = data.markdown || data.txt;

                    if (targetFile && targetFile.file_url) {
                      fetch(targetFile.file_url, {
                        method: 'GET',
                        headers: this.commonHeaders
                      })
                        .then(fileResponse => {
                          if (!fileResponse.ok) {
                            throw new Error(`文件加载失败: ${fileResponse.status}`);
                          }
                          return fileResponse.text();
                        })
                        .then(fileContent => {
                          if (fileContent.trim() === 'processing') {
                            // 处理中，继续轮询
                            this.addMessage('ai', `处理中...((${attempts}/${maxAttempts}))`, 'text');
                            this.scrollToBottom();
                            setTimeout(pollForFile, pollInterval);
                          } else {
                            // 处理完成，根据文件类型和指令类型选择渲染方式
                            if (isGenerateReport) {
                              // 评测报告额外处理雷达图数据
                              this.addMessage('ai', `已生成可视化评测报告:`, 'text');
                              this.processAndRenderReport(fileContent, data.markdown ? true : false);
                            } else if (data.markdown) {
                              // Markdown内容使用格式化渲染
                              this.addMessage('ai', `已获取分析结果（Markdown格式）:`, 'text');
                              this.addFormattedMessageWithSpaces(fileContent);
                            } else {
                              // TXT内容直接显示
                              this.addMessage('ai', `已获取分析结果:`, 'text');
                              this.addMessage('ai', fileContent, 'text');
                            }
                            this.scrollToBottom();
                          }
                        })
                        .catch(() => {
                          this.addMessage('ai', `文件加载中...((${attempts}/${maxAttempts}))`, 'text');
                          this.scrollToBottom();
                          setTimeout(pollForFile, pollInterval);
                        });
                    } else {
                      // 未找到有效文件URL
                      this.addMessage('ai', `未找到文件...((${attempts}/${maxAttempts}))`, 'text');
                      this.scrollToBottom();
                      setTimeout(pollForFile, pollInterval);
                    }
                  }
                  // 未找到文件但可能在处理中
                  else if (response.status === 404 ||
                    (data.status === 'error' && data.message.includes('未找到'))) {
                    this.addMessage('ai', `内容生成中...((${attempts}/${maxAttempts}))`, 'text');
                    this.scrollToBottom();
                    setTimeout(pollForFile, pollInterval);
                  }
                  // 其他错误
                  else {
                    this.addMessage('ai', `获取文件失败: ${data.message || '未知错误'}`, 'text', true);
                    this.scrollToBottom();
                  }
                })
                .catch(error => {
                  console.error('轮询错误:', error);
                  this.addMessage('ai', `连接中...((${attempts}/${maxAttempts}))`, 'text');
                  this.scrollToBottom();
                  setTimeout(pollForFile, pollInterval);
                });
            };

            pollForFile();
          } else {
            this.addMessage('ai', `错误: ${data.result}`, 'text', true);
          }
          this.scrollToBottom();
        }).catch(error => {
          this.removeTypingIndicator(typingId);
          this.addMessage('ai', `请求失败: ${error.message}`, 'text', true);
          this.scrollToBottom();
          console.error('发送消息失败:', error);
        });
      } catch (error) {
        this.removeTypingIndicator(typingId);
        this.addMessage('ai', `请求失败: ${error.message}`, 'text', true);
        this.scrollToBottom();
        console.error('发送消息失败:', error);
      }
    },

    // 构建语言逻辑分析的prompt
    buildLogicAnalysisPrompt() {
      const questions = this.getInterviewQuestions();

      let prompt = "请以下面试问题及对应的回答，分析回答的语言逻辑和连贯性，并给出评分(0-100分)和简要分析：\n\n";

      questions.forEach((item, i) => {
        if (item.answer) {
          prompt += `第${i + 1}题：${item.question}\n`;
          prompt += `回答：${item.answer}\n\n`;
        }
      });

      return prompt;
    },

    // 构建生成可视化评测报告的prompt（优化版）
    buildEvaluationReportPrompt() {
      const questions = this.getInterviewQuestions();
      const dimensions = [
        "专业知识水平",
        "技能匹配度",
        "语言表达能力",
        "逻辑思维能力",
        "创新能力"
      ];

      // 生成唯一标识符，用于精确界定雷达数据的位置
      const radarDataMarker = `RADAR_DATA_${Date.now()}_START`;
      const radarDataEndMarker = `RADAR_DATA_${Date.now()}_END`;

      let prompt = "请基于以下5个面试问题及对应回答，生成一份详细的可视化评测报告。\n\n";
      prompt += "【格式要求非常严格，请严格遵守，否则将导致报告无法正常解析】\n";
      prompt += "报告必须包含以下几个部分，且按以下顺序排列：\n\n";

      // 1. 雷达图数据部分 - 格式严格限定
      prompt += "1. 能力雷达图数据：\n";
      prompt += `   请在${radarDataMarker}和${radarDataEndMarker}标记之间，为以下5个维度分别评分(0-100分)，\n`;
      prompt += "   每个维度单独一行，格式必须为【维度名称: 评分】，不允许有其他内容或格式变化\n";
      prompt += `   维度名称：${dimensions.join('、')}\n`;
      prompt += `   示例格式：\n`;
      prompt += `   ${radarDataMarker}\n`;
      prompt += `   专业知识水平: 80\n`;
      prompt += `   技能匹配度: 70\n`;
      prompt += `   语言表达能力: 90\n`;
      prompt += `   逻辑思维能力: 60\n`;
      prompt += `   创新能力: 80\n`;
      prompt += `   ${radarDataEndMarker}\n\n`;

      // 2. 关键问题定位
      prompt += "2. 关键问题定位：\n";
      prompt += "   请使用项目符号(-)列出回答中存在的主要问题，每条问题单独一行\n";
      prompt += "   例如：\n";
      prompt += "   - 回答缺乏STAR结构\n";
      prompt += "   - 对专业术语的解释不够清晰\n\n";

      // 3. 企业决策建议
      prompt += "3. 企业决策建议：\n";
      prompt += "   请明确给出是否推荐录用的建议，并提供3-5条具体理由，使用项目符号(-)列出\n\n";

      // 4. 求职者个性化改进建议
      prompt += "4. 求职者个性化改进建议：\n";
      prompt += "   针对每个维度的不足，提供具体可行的改进方法，每个维度单独成段，开头注明维度名称\n\n";

      // 5. Markdown格式要求
      prompt += "5. 整体使用Markdown格式输出，包含适当的标题层级：\n";
      prompt += "   - 主标题：# 大数据运维测试岗面试可视化评测报告\n";
      prompt += "   - 各部分标题：## 1. 能力雷达图数据、## 2. 关键问题定位等\n\n";

      // 面试问题与回答
      prompt += "【面试问题及回答】\n";
      questions.forEach((item, i) => {
        if (item.answer) {
          prompt += `第${i + 1}题（${dimensions[i]}）：${item.question}\n`;
          prompt += `回答：${item.answer}\n\n`;
        }
      });

      // 存储标记以便后续解析
      this.radarDataMarkers = {
        start: radarDataMarker,
        end: radarDataEndMarker
      };

      return prompt;
    },

    // 从localStorage获取面试问题和答案
    getInterviewQuestions() {
      return [
        {
          question: localStorage.getItem('firstQuestion') || '第一道题',
          answer: localStorage.getItem('firstResult') || ''
        },
        {
          question: localStorage.getItem('secondQuestion') || '第二道题',
          answer: localStorage.getItem('secondResult') || ''
        },
        {
          question: localStorage.getItem('thirdQuestion') || '第三道题',
          answer: localStorage.getItem('thirdResult') || ''
        },
        {
          question: localStorage.getItem('fourthQuestion') || '第四道题',
          answer: localStorage.getItem('fourthResult') || ''
        },
        {
          question: localStorage.getItem('fifthQuestion') || '第五道题',
          answer: localStorage.getItem('fifthResult') || ''
        }
      ];
    },

    // 处理并渲染评测报告，包括雷达图
    processAndRenderReport(content, isMarkdown) {
      try {
        // 使用预设的标记提取雷达图数据
        const { start, end } = this.radarDataMarkers || {};
        let radarDataSection = '';

        if (start && end) {
          const startIndex = content.indexOf(start);
          const endIndex = content.indexOf(end);

          if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
            // 提取标记之间的内容
            radarDataSection = content.substring(
              startIndex + start.length,
              endIndex
            ).trim();
          } else {
            console.warn('未找到完整的雷达图数据标记');
          }
        } else {
          console.warn('未设置雷达图数据标记');
        }

        // 提取雷达图数据
        const dimensions = [
          "专业知识水平",
          "技能匹配度",
          "语言表达能力",
          "逻辑思维能力",
          "创新能力"
        ];

        const radarData = {};

        // 按行解析
        if (radarDataSection) {
          const lines = radarDataSection.split('\n');
          lines.forEach(line => {
            // 使用严格的正则匹配格式
            const match = line.match(/^\s*([^:]+?)\s*:\s*(\d+)\s*$/);
            if (match && match[1] && match[2]) {
              const dimension = match[1].trim();
              const score = parseInt(match[2], 10);

              // 只处理我们需要的维度，评分范围改为0-100
              if (dimensions.includes(dimension) && score >= 0 && score <= 100) {
                radarData[dimension] = score;
              }
            }
          });
        }

        // 检查是否有缺失的维度
        dimensions.forEach(dimension => {
          if (radarData[dimension] === undefined) {
            console.warn(`维度"${dimension}"的分数未找到或格式不正确`);
            radarData[dimension] = 0; // 默认为0分
          }
        });

        // 生成雷达图容器，调整雷达图大小为400px高度
        const radarContainerId = `radar-chart-${Date.now()}`;
        let radarChartHtml = `<div class="radar-chart-container">
      <h3>能力雷达图</h3>
      <!-- 调整雷达图大小 -->
      <canvas id="${radarContainerId}" style="width: 100%; height: 400px; max-width: 600px; margin: 0 auto;"></canvas>
    </div>`;

        // 处理报告内容
        let processedContent;
        if (isMarkdown) {
          processedContent = this.processMarkdownContent(content);
          processedContent = radarChartHtml + processedContent;
        } else {
          processedContent = `<div class="report-content">
        ${radarChartHtml}
        <div class="text-content">${content.replace(/\n/g, '<br>')}</div>
      </div>`;
        }

        // 添加到消息列表
        this.messages.push({
          sender: 'ai',
          type: 'formatted',
          content: processedContent
        });

        // 确保DOM已更新后再渲染图表
        this.$nextTick(() => {
          // 检查Chart.js是否已加载
          if (typeof Chart === 'undefined') {
            // 动态加载Chart.js
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            script.onload = () => this.renderRadarChart(radarContainerId, radarData);
            script.onerror = () => {
              document.getElementById(radarContainerId).innerHTML =
                '<p class="error-message">无法加载图表库，请检查网络连接</p>';
            };
            document.head.appendChild(script);
          } else {
            this.renderRadarChart(radarContainerId, radarData);
          }
        });

      } catch (error) {
        console.error('处理评测报告失败:', error);
        this.addMessage('ai', '评测报告处理失败，显示原始内容:', 'text', true);
        this.addMessage('ai', content, 'text');
      }
    },

    // 渲染雷达图
    renderRadarChart(containerId, data) {
      // 确保Chart.js已加载
      if (typeof Chart === 'undefined') {
        console.error('Chart.js未加载，无法渲染雷达图');
        return;
      }

      // 增加重试机制
      const maxRetries = 5;
      let retries = 0;

      const tryRender = () => {
        const container = document.getElementById(containerId);

        // 检查容器是否存在
        if (!container) {
          if (retries < maxRetries) {
            retries++;
            console.log(`重试获取图表容器 (${retries}/${maxRetries})`);
            setTimeout(tryRender, 100); // 100ms后重试
            return;
          } else {
            console.error(`无法找到ID为"${containerId}"的图表容器`);
            return;
          }
        }

        // 确保容器是canvas元素或包含canvas
        let canvas;
        if (container.tagName === 'CANVAS') {
          canvas = container;
        } else {
          // 检查容器内是否已有canvas
          canvas = container.querySelector('canvas');
          if (!canvas) {
            // 创建新的canvas元素
            canvas = document.createElement('canvas');
            container.innerHTML = ''; // 清空容器
            container.appendChild(canvas);
          }
        }

        // 准备雷达图数据
        const labels = [
          "专业知识水平",
          "技能匹配度",
          "语言表达能力",
          "逻辑思维能力",
          "创新能力"
        ];

        const values = labels.map(label => data[label] || 0);

        // 销毁已存在的图表实例
        if (container.chartInstance) {
          container.chartInstance.destroy();
        }

        // 创建雷达图，将评分范围调整为0-100
        container.chartInstance = new Chart(canvas.getContext('2d'), {
          type: 'radar',
          data: {
            labels: labels,
            datasets: [{
              label: '能力评分',
              data: values,
              backgroundColor: 'rgba(54, 162, 235, 0.2)',
              borderColor: 'rgba(54, 162, 235, 1)',
              pointBackgroundColor: 'rgba(54, 162, 235, 1)',
              pointBorderColor: '#fff',
              pointHoverBackgroundColor: '#fff',
              pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
            }]
          },
          options: {
            scales: {
              r: {
                angleLines: {
                  display: true
                },
                suggestedMin: 0,
                suggestedMax: 100, // 评分范围改为0-100
                ticks: {
                  stepSize: 20, // 刻度间隔设为20，使0-100显示更合理
                  callback: function (value) {
                    return value + '%'; // 显示百分比符号
                  }
                }
              }
            },
            plugins: {
              legend: {
                position: 'top',
              },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    return `${context.label}: ${context.raw}分`;
                  }
                }
              }
            }
          }
        });
      };

      // 开始尝试渲染
      tryRender();
    },

    // 增强的格式化消息方法，支持Markdown渲染
    addFormattedMessageWithSpaces(content) {
      try {
        if (!content || content.trim() === '') {
          this.addMessage('ai', '没有返回内容', 'text');
          return;
        }

        const processedContent = this.processMarkdownContent(content);

        // 添加到消息列表
        this.messages.push({
          sender: 'ai',
          type: 'formatted',
          content: processedContent
        });

      } catch (error) {
        console.error('格式化Markdown失败:', error);
        this.addMessage('ai', '内容格式化失败，显示原始内容:', 'text', true);
        this.addMessage('ai', content, 'text');
      }
    },
    // 处理Markdown内容为HTML，确保透明样式生效
    processMarkdownContent(content) {
      // 标准化换行符
      let processed = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

      // 处理思考内容标签，使用正确的正则表达式和样式
      processed = processed.replace(
        /<|FunctionCallBegin|>([\s\S]*?)<|FunctionCallEnd|>/g,  // 正确匹配</think>和<|FunctionCallEnd|>标签
        // 使用明确的透明度样式，确保优先级
        '<div style="color: rgba(107, 114, 128, 0.7); font-style: italic; background-color: rgba(243, 244, 246, 0.3); padding: 12px; border-radius: 0.5rem; border: 1px solid rgba(229, 231, 235, 0.5); margin: 1rem 0; display: block;">思考过程: $1</div>'
      );

      // Markdown格式处理
      processed = processed
        // 处理标题
        .replace(/^# (.*?)$/gm, '<h1 class="text-2xl font-bold my-4">$1</h1>')
        .replace(/^## (.*?)$/gm, '<h2 class="text-xl font-bold my-3">$1</h2>')
        .replace(/^### (.*?)$/gm, '<h3 class="text-lg font-bold my-2">$1</h3>')
        // 先处理有序列表
        .replace(/^\d+\. (.*?)$/gm, '<li class="list-decimal">$1</li>')
        .replace(/(<li class="list-decimal">.*?<\/li>)+/gs, '<ol class="list-decimal pl-6 my-2">$&</ol>')
        // 再处理无序列表
        .replace(/^- (.*?)$/gm, '<li class="list-disc">$1</li>')
        .replace(/(<li class="list-disc">.*?<\/li>)+/gs, '<ul class="list-disc pl-6 my-2">$&</ul>')
        // 处理加粗和斜体
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // 处理链接
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-600 underline">$1</a>')
        // 处理换行
        .replace(/(?![^<]*<\/li>)\n/g, '<br>');

      // 构建HTML内容，添加容器样式以确保内部样式生效
      return `<div class="formatted-content markdown-content" style="font-family: sans-serif;">${processed}</div>`;
    },







    // 停止录音
    stopRecording() {
      if (this.isRecording && this.mediaRecorder) {
        this.mediaRecorder.stop();
        this.isRecording = false;

        if (this.recordingTimer) {
          clearInterval(this.recordingTimer);
          this.recordingTimer = null;
        }

        if (this.mediaStream) {
          this.mediaStream.getTracks().forEach(track => track.stop());
          this.mediaStream = null;
        }

        this.showStatus('录音已完成', 'success');
      }
    },

    // 添加语音消息到列表
    addVoiceMessage() {
      if (!this.audioBlob) return;

      const audioUrl = URL.createObjectURL(this.audioBlob);
      const duration = this.recordingSeconds;

      const audio = new Audio(audioUrl);

      this.messages.push({
        sender: 'user',
        type: 'voice',
        blob: this.audioBlob,
        url: audioUrl,
        duration: duration,
        isPlaying: false,
        textResult: null,
        toneResult: null,
        speechSpeed: null,
        logicResult: null
      });

      this.audioElements[this.messages.length - 1] = audio;

      this.scrollToBottom();
    },

    // 播放或暂停语音
    toggleVoicePlayback(index) {
      const msg = this.messages[index];
      if (!msg || msg.type !== 'voice') return;

      const audio = this.audioElements[index];
      if (!audio) return;

      if (msg.isPlaying) {
        audio.pause();
        msg.isPlaying = false;
      } else {
        this.messages.forEach((m, i) => {
          if (m.isPlaying && i !== index) {
            m.isPlaying = false;
            const otherAudio = this.audioElements[i];
            if (otherAudio) otherAudio.pause();
          }
        });

        audio.play()
          .then(() => {
            msg.isPlaying = true;
            audio.onended = () => {
              msg.isPlaying = false;
            };
          })
          .catch(error => {
            console.error('播放失败:', error);
            this.showStatus('播放失败，请重试', 'error');
          });
      }
    },

    // 语音转文字
    //找到convertVoiceToText方法，修改如下：
    async convertVoiceToText(index) {
      const msg = this.messages[index];
      if (!msg || msg.type !== 'voice' || !msg.blob) return;

      this.showStatus('正在转换语音为文字...', 'info');

      try {
        const formData = new FormData();
        formData.append('audio', msg.blob, 'recording.wav');

        const response = await fetch(`${this.API_BASE_URL}/recognize_speech`, {
          method: 'POST',
          headers: this.commonHeaders,
          body: formData
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('语音转文字API错误:', errorText);
          throw new Error(`服务器错误: ${response.status} - ${errorText.substring(0, 100)}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          // 1. 确保更新消息对象
          this.messages.splice(index, 1, {
            ...this.messages[index],
            textResult: data.text || '未能识别语音内容'
          });

          // 2. 转写计数循环使用1-5
          this.transcribeCount = (this.transcribeCount % 5) + 1;

          // 3. 根据次数存储结果，使用Vue的响应式更新
          if (this.transcribeCount === 1) {
            this.firstResult = data.text || '';
            localStorage.setItem("firstResult", this.firstResult);
            console.log('第一次转写成功，' + this.firstResult);
          } else if (this.transcribeCount === 2) {
            this.secondResult = data.text || '';
            localStorage.setItem("secondResult", this.secondResult);
            console.log('第二次转写成功，' + this.secondResult);
          } else if (this.transcribeCount === 3) {
            this.thirdResult = data.text || '';
            localStorage.setItem("thirdResult", this.thirdResult);
            console.log('第三次转写成功，' + this.thirdResult);
          } else if (this.transcribeCount === 4) {
            this.fourthResult = data.text || '';
            localStorage.setItem("fourthResult", this.fourthResult);
            console.log('第四次转写成功，' + this.fourthResult);
          } else if (this.transcribeCount === 5) {
            this.fifthResult = data.text || '';
            localStorage.setItem("fifthResult", this.fifthResult);
            console.log('第五次转写成功，' + this.fifthResult);
          }

          // 4. 保存语言内容到localStorage
          localStorage.setItem('interview_response_content', data.text || '');

          this.showStatus('语音转文字成功', 'success');
        } else {
          throw new Error(data.message || '语音转文字失败');
        }
      } catch (error) {
        console.error('语音转文字失败:', error);
        this.showStatus(`转文字失败: ${error.message}`, 'error');
      }
    },


    // 分析语调
    async analyzeVoiceTone(index) {
      const msg = this.messages[index];
      if (!msg || msg.type !== 'voice' || !msg.blob) return;

      this.showStatus('正在分析语调...', 'info');

      try {
        const formData = new FormData();
        formData.append('audio', msg.blob, 'recording.wav');

        const response = await fetch(`${this.API_BASE_URL}/extract_tone`, {
          method: 'POST',
          headers: this.commonHeaders,
          body: formData
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('语调分析API错误:', errorText);
          throw new Error(`服务器错误: ${response.status} - ${errorText.substring(0, 100)}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          // 使用扩展运算符创建新对象，触发响应式更新
          this.messages[index] = {
            ...this.messages[index],
            toneResult: data.data
          };

          // 保存情感语调分析到localStorage（追加方式）
          const existingTone = localStorage.getItem('interview_emotional_tone') || '';
          const toneAnalysis = `语调类型: ${data.data.tone_type}, 基频均值: ${data.data.f0_mean}Hz, 基频范围: ${data.data.f0_min}-${data.data.f0_max}Hz`;
          const newToneAnalysis = existingTone ? `${existingTone}\n${toneAnalysis}` : toneAnalysis;
          localStorage.setItem('interview_emotional_tone', newToneAnalysis);

          this.showStatus('语调分析成功', 'success');
        } else {
          throw new Error(data.message || '语调分析失败');
        }
      } catch (error) {
        console.error('语调分析失败:', error);
        this.showStatus(`语调分析失败: ${error.message}`, 'error');
      }
    },

    // 计算语速
    calculateSpeechSpeed(index) {
      const msg = this.messages[index];
      if (!msg || msg.type !== 'voice' || !msg.textResult) return;

      // 计算字数（去除空白字符）
      const text = msg.textResult.trim();
      const charCount = text.length;

      // 音频时长（秒）
      const duration = Math.max(msg.duration, 0.1); // 避免除以0

      // 计算语速（字/秒）
      const speed = (charCount / duration).toFixed(1);
      const speedPerMinute = Math.round(speed * 60);

      // 使用扩展运算符创建新对象，触发响应式更新
      this.messages[index] = {
        ...this.messages[index],
        speechSpeed: speed
      };

      // 保存语速分析到localStorage（追加方式）
      const existingSpeed = localStorage.getItem('interview_speech_rate') || '';
      const speedAnalysis = `${speed} 字/秒 (约 ${speedPerMinute} 字/分钟)。${this.evaluateSpeechSpeed(speedPerMinute)}`;
      const newSpeedAnalysis = existingSpeed ? `${existingSpeed}\n${speedAnalysis}` : speedAnalysis;
      localStorage.setItem('interview_speech_rate', newSpeedAnalysis);

      this.showStatus('语速计算完成', 'success');
    },

    // 评估语速是否合理
    evaluateSpeechSpeed(speedPerMinute) {
      if (speedPerMinute < 120) {
        return "语速偏慢，可能影响表达效率";
      } else if (speedPerMinute > 180) {
        return "语速偏快，可能影响理解";
      } else {
        return "语速适中，表达节奏良好";
      }
    },

    // 分析语言逻辑
    async analyzeLanguageLogic(index) {
      const msg = this.messages[index];
      if (!msg || msg.type !== 'voice' || !msg.textResult) return;

      this.showStatus('正在分析语言逻辑...', 'info');

      try {
        // 从localStorage获取问题和对应的回答
        const questions = [
          {
            question: localStorage.getItem('firstQuestion') || '第一道题',
            answer: localStorage.getItem('firstResult') || ''
          },
          {
            question: localStorage.getItem('secondQuestion') || '第二道题',
            answer: localStorage.getItem('secondResult') || ''
          },
          {
            question: localStorage.getItem('thirdQuestion') || '第三道题',
            answer: localStorage.getItem('thirdResult') || ''
          },
          {
            question: localStorage.getItem('fourthQuestion') || '第四道题',
            answer: localStorage.getItem('fourthResult') || ''
          },
          {
            question: localStorage.getItem('fifthQuestion') || '第五道题',
            answer: localStorage.getItem('fifthResult') || ''
          }
        ];

        // 构建包含问题和对应回答的prompt
        let prompt = "请以下面试问题及对应的回答，分析回答的语言逻辑和连贯性，并给出评分(1-10分)和简要分析：\n\n";

        questions.forEach((item, i) => {
          if (item.answer) { // 只包含有回答的问题
            prompt += `第${i + 1}题：${item.question}\n`;
            prompt += `回答：${item.answer}\n\n`;
          }
        });

        // 添加当前消息的文本结果（如果需要包含）
        prompt += `当前分析文本：${msg.textResult}"`;

        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: prompt })
        });

        if (!response.ok) {
          throw new Error(`请求失败: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          // 提取评分（如果有的话）
          let score = null;
          const scoreMatch = data.result.match(/(\d+(\.\d+)?)\s*\/\s*10/);
          if (scoreMatch && scoreMatch[1]) {
            score = parseFloat(scoreMatch[1]);
          }

          // 使用扩展运算符创建新对象，触发响应式更新
          this.messages[index] = {
            ...this.messages[index],
            logicResult: {
              analysis: data.result,
              score: score
            }
          };

          // 保存语言逻辑分析到localStorage（追加方式）
          const existingLogic = localStorage.getItem('interview_language_logic') || '';
          const newLogicAnalysis = existingLogic ? `${existingLogic}\n${data.result}` : data.result;
          localStorage.setItem('interview_language_logic', newLogicAnalysis);

          this.showStatus('语言逻辑分析完成', 'success');
        } else {
          throw new Error(data.result || '语言逻辑分析失败');
        }
      } catch (error) {
        console.error('语言逻辑分析失败:', error);
        this.showStatus(`语言逻辑分析失败: ${error.message}`, 'error');
      }
    },

    // 保存分析结果到localStorage（追加方式）
    saveAnalysisToStorage(msg) {
      if (!msg || msg.type !== 'expression') return;

      // 保存表情分析（追加方式）
      if (msg.expressionResults && msg.expressionResults.length) {
        let expressionsText = msg.expressionResults.map(exp =>
          `${exp.emotion} (${(exp.confidence * 100).toFixed(1)}%)`
        ).join('、');

        const existingExpressions = localStorage.getItem('interview_expression') || '';
        const newExpressions = existingExpressions ? `${existingExpressions}\n检测到的表情: ${expressionsText}` : `检测到的表情: ${expressionsText}`;
        localStorage.setItem('interview_expression', newExpressions);
      }

      // 保存姿态分析（追加方式）
      if (msg.poseResult) {
        const poseText = `动作: ${msg.poseResult.pose}, 置信度: ${(msg.poseResult.score * 100).toFixed(1)}%`;
        const existingPose = localStorage.getItem('interview_gesture') || '';
        const newPose = existingPose ? `${existingPose}\n${poseText}` : poseText;
        localStorage.setItem('interview_gesture', newPose);
      }

      // 保存综合分析（追加方式）
      if (msg.comprehensiveAnalysis) {
        const existingAnalysis = localStorage.getItem('interview_expression_gesture_summary') || '';
        const newAnalysis = existingAnalysis ? `${existingAnalysis}\n${msg.comprehensiveAnalysis}` : msg.comprehensiveAnalysis;
        localStorage.setItem('interview_expression_gesture_summary', newAnalysis);
      }

      this.showStatus('分析结果已保存', 'success');
    },

    // 添加消息到界面
    addMessage(sender, content, type = 'text', isError = false) {
      this.messages.push({
        sender: sender,
        content: content,
        type: type,
        isError: isError
      });
      this.scrollToBottom();
    },

    // 添加表情和姿态分析消息
    addExpressionMessage(imageUrl, expressionResults, poseResult) {
      this.messages.push({
        sender: 'ai',
        type: 'expression',
        imageUrl: imageUrl,
        expressionResults: expressionResults,
        poseResult: poseResult,
        comprehensiveAnalysis: null
      });
      this.scrollToBottom();
    },

    // 添加"正在输入"指示器
    addTypingIndicator() {
      const typingId = `typing-${Date.now()}`;
      this.typingId = typingId;
      this.isTyping = true;
      return typingId;
    },

    // 移除"正在输入"状态
    removeTypingIndicator(id) {
      if (this.typingId === id) {
        this.isTyping = false;
        this.typingId = "";
      }
    },

    // 滚动到最新消息
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },

    // 测试连接状态
    async testConnection() {
      try {
        await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'OPTIONS',
          headers: this.commonHeaders
        });

        this.statusText = ``;
        this.statusClass = 'text-xs text-green-600 mt-2 text-center';
      } catch (error) {
        this.statusText = `连接失败: ${error.message}`;
        this.statusClass = 'text-xs text-red-600 mt-2 text-center';
      }
    },

    // 初始化聊天容器高度
    initContainerHeight() {
      const navBarHeight = 46;
      const bottomBarHeight = document.getElementById('dialog_bottombar_inside')?.offsetHeight || 0;
      const container = document.getElementById('dialog_content');
      if (container) {
        container.style.paddingTop = navBarHeight + 10 + 'px';
        container.style.paddingBottom = bottomBarHeight + 10 + 'px';
        container.style.height = `calc(100vh - ${navBarHeight + bottomBarHeight + 20}px)`;
      }
    },

    // 格式化时长显示
    formatDuration(seconds) {
      if (seconds < 60) {
        return `${seconds}s`;
      } else {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs < 10 ? '0' + secs : secs}`;
      }
    },

    // 显示状态消息
    showStatus(text, type = 'info') {
      this.statusText = text;
      switch (type) {
        case 'success':
          this.statusClass = 'text-xs text-green-600 mt-2 text-center';
          break;
        case 'error':
          this.statusClass = 'text-xs text-red-600 mt-2 text-center';
          break;
        case 'warning':
          this.statusClass = 'text-xs text-yellow-600 mt-2 text-center';
          break;
        default:
          this.statusClass = 'text-xs text-blue-600 mt-2 text-center';
      }

      if (type !== 'error') {
        setTimeout(() => {
          this.statusText = '';
        }, 3000);
      }
    },

    // 音频格式转换相关方法
    async convertToValidWav(blob) {
      if (await this.isValidWavFile(blob)) {
        return blob;
      }

      try {
        const arrayBuffer = await new Response(blob).arrayBuffer();
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 16000
        });

        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const wavBuffer = this.convertToWav(audioBuffer);

        return new Blob([wavBuffer], { type: 'audio/wav' });
      } catch (error) {
        console.error('音频格式转换失败:', error);
        this.showStatus('音频格式转换失败，可能影响识别效果', 'warning');
        return blob;
      }
    },

    async isValidWavFile(blob) {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = (e) => {
          if (e.target.readyState === FileReader.DONE) {
            const arrayBuffer = e.target.result;
            const uint8Array = new Uint8Array(arrayBuffer);

            if (uint8Array.length >= 4) {
              const riff = String.fromCharCode(uint8Array[0], uint8Array[1], uint8Array[2], uint8Array[3]);
              resolve(riff === 'RIFF');
            } else {
              resolve(false);
            }
          }
        };
        reader.readAsArrayBuffer(blob.slice(0, 4));
      });
    },

    convertToWav(audioBuffer) {
      const numberOfChannels = audioBuffer.numberOfChannels;
      const sampleRate = audioBuffer.sampleRate;
      const format = 1;
      const bitDepth = 16;

      let data = new Float32Array(audioBuffer.length);
      for (let i = 0; i < audioBuffer.length; i++) {
        let sum = 0;
        for (let c = 0; c < numberOfChannels; c++) {
          sum += audioBuffer.getChannelData(c)[i];
        }
        data[i] = sum / numberOfChannels;
      }

      const buffer = new ArrayBuffer(44 + data.length * 2);
      const view = new DataView(buffer);

      this.writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + data.length * 2, true);
      this.writeString(view, 8, 'WAVE');
      this.writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, format, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, bitDepth, true);
      this.writeString(view, 36, 'data');
      view.setUint32(40, data.length * 2, true);

      let index = 44;
      const volume = 1;
      for (let i = 0; i < data.length; i++) {
        const sample = Math.max(-1, Math.min(1, data[i] * volume));
        view.setInt16(index, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
        index += 2;
      }

      return buffer;
    },

    writeString(view, offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    },

    // 相机相关方法
    async toggleCamera() {
      if (this.isCameraActive) {
        this.stopCamera();
        this.isCameraModalVisible = false;
      } else {
        this.isCameraModalVisible = true;
        await this.startCamera();
      }
    },

    async startCamera() {
      this.isLoadingCamera = true;
      this.cameraError = null;

      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('您的浏览器不支持相机功能，请使用最新浏览器');
        }

        if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
          throw new Error('相机功能需要在HTTPS环境下运行');
        }

        // 相机配置
        this.videoStream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });

        const videoElement = this.$refs.videoElement;
        if (videoElement) {
          videoElement.srcObject = this.videoStream;
          this.isCameraActive = true;
          this.showStatus('相机已启动，可进行表情和姿态识别', 'success');
        }
      } catch (error) {
        console.error('相机启动失败:', error);
        this.cameraError = error.message;

        // 错误处理
        if (error.name === 'NotAllowedError') {
          this.cameraError = '相机权限被拒绝，请在浏览器设置中允许相机访问';
        } else if (error.name === 'NotFoundError') {
          this.cameraError = '未找到相机设备';
        } else if (error.name === 'NotReadableError') {
          this.cameraError = '相机被占用或不可用';
        } else if (error.name === 'NotSupportedError') {
          this.cameraError = '您的浏览器不支持相机功能';
        }

        this.showStatus(`相机错误: ${this.cameraError}`, 'error');
      } finally {
        this.isLoadingCamera = false;
      }
    },

    stopCamera() {
      if (this.videoStream) {
        this.videoStream.getTracks().forEach(track => track.stop());
        this.videoStream = null;
      }

      const videoElement = this.$refs.videoElement;
      if (videoElement) {
        videoElement.srcObject = null;
      }

      this.isCameraActive = false;
      this.isAnalyzingContinuously = false;

      if (this.continuousAnalysisTimer) {
        clearInterval(this.continuousAnalysisTimer);
        this.continuousAnalysisTimer = null;
      }

      if (this.detectionInterval) {
        clearInterval(this.detectionInterval);
        this.detectionInterval = null;
      }

      this.showStatus('相机已关闭', 'info');
    },

    // 拍照并分析表情和姿态（仅使用/api/chat接口）
    async captureImage() {
      if (!this.isCameraActive || this.isProcessingImage) return;

      this.isProcessingImage = true;
      this.showStatus('正在分析表情和姿态...', 'info');

      try {
        const videoElement = this.$refs.videoElement;
        if (!videoElement) throw new Error('未找到视频元素');

        // 1. 捕获视频帧为base64
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        const base64Image = canvas.toDataURL('image/jpeg');

        // 2. 仅调用/api/chat接口（符合需求）
        const analysisResult = await this.analyzePose(base64Image);
        // 注意：这里复用了analyzePose方法，实际应确保它内部只调用/api/chat

        // 3. 正确转换base64为图片URL（无需fetch）
        const blob = await (await fetch(base64Image)).blob(); // 修正：先处理base64为blob
        const imageUrl = URL.createObjectURL(blob);

        // 4. 添加到消息列表（仅传入一个综合结果）
        this.addExpressionMessage(imageUrl, analysisResult);

        this.showStatus('表情和姿态分析完成', 'success');
      } catch (error) {
        console.error('图像分析失败:', error);
        this.showStatus(`分析失败: ${error.message}`, 'error');
      } finally {
        this.isProcessingImage = false;
      }
    },

    // 开始/停止连续分析
    startContinuousAnalysis() {
      if (this.isAnalyzingContinuously) {
        // 停止连续分析
        clearInterval(this.continuousAnalysisTimer);
        this.continuousAnalysisTimer = null;
        this.isAnalyzingContinuously = false;
        this.showStatus('已停止连续分析', 'info');
      } else {
        // 开始连续分析，每2秒一次
        this.showStatus('开始连续分析...', 'info');
        this.isAnalyzingContinuously = true;

        // 立即执行一次
        this.captureImage();

        // 设置定时器
        this.continuousAnalysisTimer = setInterval(() => {
          if (this.isAnalyzingContinuously) {
            this.captureImage();
          }
        }, 2000);
      }
    },

    // 分析表情
    async analyzeExpression(base64Image) {
      try {
        const response = await fetch(`${this.API_BASE_URL}/predict/image`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ base64: base64Image })
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`表情分析失败: ${response.status} - ${errorText.substring(0, 100)}`);
        }

        const data = await response.json();

        if (data.status === 'success' && data.predictions) {
          return data.predictions;
        } else {
          throw new Error(data.error || '未获取到表情分析结果');
        }
      } catch (error) {
        console.error('表情分析出错:', error);
        throw error;
      }
    },

    // 分析姿态并处理轮询
    async analyzePose(base64Image) {
      try {
        // 1. 发送图片获取任务ID
        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            prompt: '请分析这张图片中人物的姿态动作和表情，用简洁的中文语言描述',
            image_base64: base64Image
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`姿态分析请求失败: ${response.status} - ${errorText.substring(0, 100)}`);
        }

        const data = await response.json();

        if (data.status === 'success' && data.task_id) {
          // 2. 获得task_id后开始轮询
          return this.startPolling(data.task_id);
        } else {
          throw new Error(data.error || '未获取到任务ID');
        }
      } catch (error) {
        console.error('姿态分析出错:', error);
        throw error;
      }
    },

    // 轮询函数 - 修复后版本
    async startPolling(taskId, interval = 1000) {
      try {
        const response = await fetch(`${this.API_BASE_URL}/api/chat/result/${taskId}`, {
          method: 'GET',
          headers: this.commonHeaders
        });

        if (!response.ok) {
          throw new Error(`轮询失败: ${response.status}`);
        }

        const result = await response.json();

        if (result.status === 'processing') {
          console.log(`任务 ${taskId} 处理中，继续等待...`);
          // 使用箭头函数确保 this 指向组件实例
          return new Promise(resolve => {
            setTimeout(() => {
              resolve(this.startPolling(taskId, interval));
            }, interval);
          });
        } else if (result.status === 'success') {
          console.log(`任务 ${taskId} 处理完成`);
          // 此时 this.msg 已初始化，可安全赋值
          this.msg.expressionResults = [result.result]; // 存入数组，适配v-for
          console.log('轮询结果:', this.msg.expressionResults);

          return {
            status: 'completed',
            taskId,
            result: result.result,
            timestamp: new Date()
          };
        } else {
          throw new Error(`任务处理失败: ${result.result || '未知错误'}`);
        }
      } catch (error) {
        console.error(`轮询任务 ${taskId} 出错:`, error);
        throw error;
      }
    },




    // 综合分析表情和姿态
    async analyzeComprehensive(index) {
      const msg = this.messages[index];
      if (!msg || msg.type !== 'expression') return;

      this.showStatus('正在进行综合分析...', 'info');

      try {
        // 构建提示信息
        let expressionsText = msg.expressionResults.map(exp =>
          `${exp.emotion} (${(exp.confidence * 100).toFixed(1)}%)`
        ).join('、');

        let prompt = `根据以下表情和姿态信息进行综合分析:
表情: ${expressionsText}
姿态: ${msg.poseResult.pose} (置信度: ${(msg.poseResult.score * 100).toFixed(1)}%)

请分析这个人可能的情绪状态和意图，并给出简要解读。`;

        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: prompt })
        });

        if (!response.ok) {
          throw new Error(`综合分析请求失败: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          // 更新消息对象
          this.messages[index] = {
            ...this.messages[index],
            comprehensiveAnalysis: data.result
          };

          // 保存综合分析到localStorage（追加方式）
          const existingAnalysis = localStorage.getItem('interview_expression_gesture_analysis') || '';
          const newAnalysis = existingAnalysis ? `${existingAnalysis}\n${data.result}` : data.result;
          localStorage.setItem('interview_expression_gesture_analysis', newAnalysis);

          this.showStatus('综合分析完成', 'success');
        } else {
          throw new Error(data.result || '综合分析失败');
        }
      } catch (error) {
        console.error('综合分析失败:', error);
        this.showStatus(`综合分析失败: ${error.message}`, 'error');
      }
    },

    // 打开评测报告弹窗
    async openEvaluationReport() {
      this.isReportVisible = true;
      this.reportLoading = true;
      this.reportError = '';
      this.reportResponse = null; // 重置响应数据

      // 延迟执行，确保弹窗已渲染
      setTimeout(() => {
        this.generateReportFromStorage();
      }, 100);
    },

    // 从localStorage生成评测报告
    async generateReportFromStorage() {
      try {
        this.reportLoading = true;

        // 从localStorage提取数据
        this.firstResult = localStorage.getItem("firstResult") || '';
        this.secondResult = localStorage.getItem("secondResult") || '';
        this.thirdResult = localStorage.getItem("thirdResult") || '';
        this.fourthResult = localStorage.getItem("fourthResult") || '';
        this.fifthResult = localStorage.getItem("fifthResult") || '';

        this.firstQuestion = localStorage.getItem("firstQuestion") || '';
        this.secondQuestion = localStorage.getItem("secondQuestion") || '';
        this.thirdQuestion = localStorage.getItem("thirdQuestion") || '';
        this.fourthQuestion = localStorage.getItem("fourthQuestion") || '';
        this.fifthQuestion = localStorage.getItem("fifthQuestion") || '';

        // 检查是否有足够的数据生成报告
        if (!this.firstResult && !this.secondResult && !this.thirdResult && !this.fourthResult && !this.fifthResult) {
          throw new Error('未找到足够的面试回答数据，请先完成面试');
        }

        // 生成各维度评分
        this.calculateReportScores();

        // 生成各维度详细分析
        await this.generateDimensionAnalysis();

        // 生成综合评价
        await this.generateComprehensiveEvaluation();
        // 生成关键问题定位
        await this.generateKeyIssues();

        // 生成反馈建议
        await this.generateFeedbackSuggestions();

        // 生成综合评价
        await this.generateComprehensiveEvaluation();

        // 存储完整的报告响应数据
        this.reportResponse = {
          indicators: this.reportIndicators,
          values: this.reportValues,
          professionalKnowledgeAnalysis: this.professionalKnowledgeAnalysis,
          skillMatchAnalysis: this.skillMatchAnalysis,
          languageExpressionAnalysis: this.languageExpressionAnalysis,
          logicalThinkingAnalysis: this.logicalThinkingAnalysis,
          innovationAbilityAnalysis: this.innovationAbilityAnalysis,
          comprehensiveEvaluation: this.comprehensiveEvaluation,
          improvementSuggestions: this.improvementSuggestions
        };

        // 确保DOM已更新后再渲染图表
        this.$nextTick(() => {
          this.renderRadarChart();
        });

      } catch (error) {
        console.error('生成报告失败:', error);
        this.reportError = error.message;
      } finally {
        this.reportLoading = false;
      }
    },

    // 计算各维度评分
    calculateReportScores() {
      // 专业知识水平评分 (0-100)
      let knowledgeScore = 60;
      if (this.firstResult && (this.firstResult.length > 100 ||
        this.firstResult.includes('项目') ||
        this.firstResult.includes('技术') ||
        this.firstResult.includes('经验'))) {
        knowledgeScore = Math.floor(Math.random() * 20) + 70; // 70-90
      } else if (this.firstResult && this.firstResult.length < 50) {
        knowledgeScore = Math.floor(Math.random() * 20) + 40; // 40-60
      }

      // 技能匹配度评分
      let skillScore = 60;
      if (this.secondResult && (this.secondResult.length > 100 ||
        this.secondResult.includes('技能') ||
        this.secondResult.includes('掌握') ||
        this.secondResult.includes('经验'))) {
        skillScore = Math.floor(Math.random() * 20) + 70;
      } else if (this.secondResult && this.secondResult.length < 50) {
        skillScore = Math.floor(Math.random() * 20) + 40;
      }

      // 语言表达能力评分
      let languageScore = 60;
      if (this.thirdResult && (this.thirdResult.length > 100 ||
        this.thirdResult.includes('解释') ||
        this.thirdResult.includes('方法') ||
        this.thirdResult.includes('理解'))) {
        languageScore = Math.floor(Math.random() * 20) + 70;
      } else if (this.thirdResult && this.thirdResult.length < 50) {
        languageScore = Math.floor(Math.random() * 20) + 40;
      }

      // 逻辑思维能力评分
      let logicScore = 60;
      if (this.fourthResult && (this.fourthResult.length > 100 ||
        this.fourthResult.includes('分析') ||
        this.fourthResult.includes('步骤') ||
        this.fourthResult.includes('案例'))) {
        logicScore = Math.floor(Math.random() * 20) + 70;
      } else if (this.fourthResult && this.fourthResult.length < 50) {
        logicScore = Math.floor(Math.random() * 20) + 40;
      }

      // 创新能力评分
      let innovationScore = 60;
      if (this.fifthResult && (this.fifthResult.length > 100 ||
        this.fifthResult.includes('创新') ||
        this.fifthResult.includes('解决方案') ||
        this.fifthResult.includes('思路'))) {
        innovationScore = Math.floor(Math.random() * 20) + 70;
      } else if (this.fifthResult && this.fifthResult.length < 50) {
        innovationScore = Math.floor(Math.random() * 20) + 40;
      }

      this.reportValues = [
        knowledgeScore,
        skillScore,
        languageScore,
        logicScore,
        innovationScore
      ];
    },

    // 生成各维度详细分析
    // 生成各维度详细分析
    async generateDimensionAnalysis() {
      // 从localStorage获取问题
      const firstQuestion = localStorage.getItem("firstQuestion") || '';
      const secondQuestion = localStorage.getItem("secondQuestion") || '';
      const thirdQuestion = localStorage.getItem("thirdQuestion") || '';
      const fourthQuestion = localStorage.getItem("fourthQuestion") || '';
      const fifthQuestion = localStorage.getItem("fifthQuestion") || '';

      // 专业知识水平分析 - 加入对应问题
      if (this.firstResult) {
        const prompt = `请基于以下问题和回答，分析面试者的专业知识水平：
问题：${firstQuestion}
回答：${this.firstResult}

请评价面试者对该问题的回答质量、专业知识的掌握程度和深度，并指出优势和不足。`;
        this.professionalKnowledgeAnalysis = await this.getAnalysisFromAPI(prompt);
      }

      // 技能匹配度分析 - 加入对应问题
      if (this.secondResult) {
        const prompt = `请基于以下问题和回答，分析面试者的技能匹配度：
问题：${secondQuestion}
回答：${this.secondResult}

请评价面试者所提及技能与岗位需求的匹配程度，以及技能掌握的实际应用能力。`;
        this.skillMatchAnalysis = await this.getAnalysisFromAPI(prompt);
      }

      // 语言表达能力分析 - 加入对应问题
      if (this.thirdResult) {
        const prompt = `请基于以下问题和回答，分析面试者的语言表达能力：
问题：${thirdQuestion}
回答：${this.thirdResult}

请评价面试者回答的清晰度、条理性、逻辑性和表达流畅度。`;
        this.languageExpressionAnalysis = await this.getAnalysisFromAPI(prompt);
      }

      // 逻辑思维能力分析 - 加入对应问题
      if (this.fourthResult) {
        const prompt = `请基于以下问题和回答，分析面试者的逻辑思维能力：
问题：${fourthQuestion}
回答：${this.fourthResult}

请评价面试者面试者分析问题的思路、推理过程的逻辑性和解决问题的系统性。`;
        this.logicalThinkingAnalysis = await this.getAnalysisFromAPI(prompt);
      }

      // 创新能力分析 - 加入对应问题
      if (this.fifthResult) {
        const prompt = `请基于以下问题和回答，分析面试者的创新能力：
问题：${fifthQuestion}
回答：${this.fifthResult}

请评价面试者提出的解决方案的创新性、独特性和实用性，以及发现问题的敏锐度。`;
        this.innovationAbilityAnalysis = await this.getAnalysisFromAPI(prompt);
      }
    },


    // 调用API获取分析结果
    async getAnalysisFromAPI(prompt) {
      try {
        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: prompt })
        });

        if (!response.ok) {
          throw new Error(`分析请求失败: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
          const taskId = data.task_id;
          const pollInterval = 2000; // 轮询间隔2秒
          const maxAttempts = 150;   // 最多轮询150次（约5分钟）

          // 创建一个Promise来等待最终结果
          return new Promise((resolve, reject) => {
            let attempts = 0;

            // 定义轮询函数，直接查询文件接口
            const pollForFile = () => {
              // 超过最大尝试次数则拒绝
              if (attempts >= maxAttempts) {
                reject(new Error('请求超时，未能获取结果'));
                return;
              }

              attempts++;

              // 直接调用文件查询接口
              fetch(`${this.API_BASE_URL}/get_task_file_url`, {
                method: 'POST',
                headers: {
                  ...this.commonHeaders,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ task_id: taskId })
              })
                .then(response => {
                  // 无论响应状态如何，都尝试解析JSON
                  return response.json().then(data => ({ data, response }));
                })
                .then(({ data, response }) => {
                  // 成功获取到文件URL
                  if (data.status === 'success' && data.file_url) {
                    // 加载文件内容
                    fetch(data.file_url, {
                      method: 'GET',
                      headers: this.commonHeaders
                    })
                      .then(fileResponse => {
                        if (!fileResponse.ok) {
                          throw new Error(`文件加载失败: ${fileResponse.status}`);
                        }
                        return fileResponse.text();
                      })
                      .then(fileContent => {
                        // 检查内容是否为"processing"
                        if (fileContent.trim() === 'processing') {
                          // 仍在处理中，继续轮询
                          setTimeout(pollForFile, pollInterval);
                        } else {
                          // 处理完成，返回结果
                          resolve(fileContent);
                        }
                      })
                      .catch(() => {
                        // 文件加载失败，继续轮询
                        setTimeout(pollForFile, pollInterval);
                      });
                  }
                  // 未找到文件但可能还在处理中，继续轮询
                  else if (response.status === 404 ||
                    (data.status === 'error' && data.message.includes('未找到'))) {
                    setTimeout(pollForFile, pollInterval);
                  }
                  // 其他错误情况
                  else {
                    reject(new Error(`获取文件失败: ${data.message || '未知错误'}`));
                  }
                })
                .catch(error => {
                  // 网络错误等情况，继续轮询
                  setTimeout(pollForFile, pollInterval);
                });
            };

            // 开始第一次查询
            pollForFile();
          });
        } else {
          return '无法生成分析结果';
        }
      } catch (error) {
        console.error('获取分析结果失败:', error);
        return '分析生成失败';
      }
    },

    // 检查录音支持
    async checkRecordingSupport() {
      try {
        // 检查浏览器是否支持媒体录制API
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('您的浏览器不支持录音功能');
        }

        // 尝试获取麦克风权限（可选，根据实际需求）
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // 释放流资源
        stream.getTracks().forEach(track => track.stop());

        // 可以在这里设置一个标志，表示支持录音
        this.recordingSupported = true;
        console.log('浏览器支持录音功能');
      } catch (error) {
        this.recordingSupported = false;
        console.warn('录音功能检查失败:', error.message);
      }
    },
    // 切换录音状态（开始/停止录音）
    toggleRecording() {
      if (this.isRecording) {
        // 停止录音的逻辑
        this.stopRecording();
      } else {
        // 开始录音的逻辑
        this.startRecording();
      }
    },

    // 生成综合评价
    async generateComprehensiveEvaluation() {
      // 构建提示信息
      // 修改prompt，要求结合评分和具体建议
      const prompt = `基于以下面试者的五维分析数据，生成综合评价和改进建议：
1. 专业知识水平: ${this.firstResult || '无数据'}（评分：${this.reportValues[0]}）
2. 技能匹配度: ${this.secondResult || '无数据'}（评分：${this.reportValues[1]}）
3. 语言表达能力: ${this.thirdResult || '无数据'}（评分：${this.reportValues[2]}）
4. 逻辑思维能力: ${this.fourthResult || '无数据'}（评分：${this.reportValues[3]}）
5. 创新能力: ${this.fifthResult || '无数据'}（评分：${this.reportValues[4]}）

请严格按照以下格式输出：
【综合评价】
[100字左右，结合评分总结优势和不足]

【改进建议】
1. [具体可操作的建议，关联专业知识]
2. [具体可操作的建议，关联技能或表达]
3. [具体可操作的建议，关联思维或创新]`;

      try {
        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: prompt })
        });

        if (!response.ok) {
          throw new Error(`生成综合评价失败: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success' && data.result) {
          const result = data.result;

          // 提取综合评价
          const evalMatch = result.match(/【综合评价】\s*([\s\S]*?)(?=【改进建议】)/);
          this.comprehensiveEvaluation = evalMatch ? evalMatch[1].trim() : '无法生成综合评价';

          // 提取改进建议
          this.improvementSuggestions = [];
          const suggestionsMatch = result.match(/【改进建议】\s*([\s\S]*)/);
          if (suggestionsMatch && suggestionsMatch[1]) {
            // 按序号提取建议
            const suggestions = suggestionsMatch[1]
              .split(/\n\d+\./)
              .filter(item => item.trim());

            suggestions.forEach(suggestion => {
              this.improvementSuggestions.push(suggestion.trim());
            });
          }

          // 兜底处理（确保至少有3条建议）
          while (this.improvementSuggestions.length < 3) {
            this.improvementSuggestions.push('加强对应维度的专项训练');
          }
        }
      } catch (error) {
        console.error('生成综合评价失败:', error);
        // 使用默认评价
        this.comprehensiveEvaluation = '面试者表现中等，各方面能力有提升空间。';
        this.improvementSuggestions = [
          "加强专业知识的深度和广度",
          "提高语言表达的清晰度和逻辑性",
          "在实际应用中培养创新思维"
        ];
      }
    },

    // 在generateComprehensiveEvaluation方法后添加
    async generateKeyIssues() {
      // 生成关键问题定位
      // 修改prompt，明确要求结构化输出
      const prompt = `基于以下面试者的表现，分析其在面试中暴露的关键问题和不足:
专业知识水平: ${this.firstResult || '无数据'}
技能匹配度: ${this.secondResult || '无数据'}
语言表达能力: ${this.thirdResult || '无数据'}
逻辑思维能力: ${this.fourthResult || '无数据'}
创新能力: ${this.fifthResult || '无数据'}

请严格按照以下格式输出，不要添加额外内容：
【关键问题定位】
[用1-2句话总结核心问题]

【具体表现示例】
1. [第一个具体例子]
2. [第二个具体例子]
3. [第三个具体例子]`;

      try {
        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: prompt })
        });

        if (!response.ok) throw new Error(`生成关键问题失败: ${response.status}`);

        const data = await response.json();
        if (data.status === 'success' && data.result) {
          const result = data.result;

          // 提取关键问题定位（匹配【关键问题定位】后的内容）
          const issueMatch = result.match(/【关键问题定位】\s*([\s\S]*?)(?=【具体表现示例】)/);
          this.keyIssues = issueMatch ? issueMatch[1].trim() : '未发现明显问题';

          // 提取具体示例（匹配【具体表现示例】后的列表）
          this.issueExamples = [];
          const examplesMatch = result.match(/【具体表现示例】\s*([\s\S]*)/);
          if (examplesMatch && examplesMatch[1]) {
            // 按序号分割提取每个示例
            const examples = examplesMatch[1].split(/\n\d+\./).filter(item => item.trim());
            examples.forEach(example => {
              this.issueExamples.push(example.trim());
            });
            // 限制最多3个示例
            this.issueExamples = this.issueExamples.slice(0, 3);
          }
        }
      } catch (error) {
        console.error('生成关键问题失败:', error);
        this.keyIssues = '无法分析关键问题';
      }
    },

    async generateFeedbackSuggestions() {
      // 生成分类反馈建议
      // 修改prompt，明确分类和格式要求
      const prompt = `基于以下面试者的表现，从5个维度给出具体改进建议：
专业知识水平: ${this.firstResult || '无数据'}
技能匹配度: ${this.secondResult || '无数据'}
语言表达能力: ${this.thirdResult || '无数据'}
逻辑思维能力: ${this.fourthResult || '无数据'}
创新能力: ${this.fifthResult || '无数据'}

请严格按照以下格式输出（每个维度至少2条建议，用"-"开头）：
【专业知识】
- 建议1
- 建议2

【技能提升】
- 建议1
- 建议2

【表达能力】
- 建议1
- 建议2

【思维逻辑】
- 建议1
- 建议2

【创新思维】
- 建议1
- 建议2`;

      try {
        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            ...this.commonHeaders,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ prompt: prompt })
        });

        if (!response.ok) throw new Error(`生成反馈建议失败: ${response.status}`);

        const data = await response.json();
        if (data.status === 'success' && data.result) {
          this.feedbackCategories = [];
          const categories = ['专业知识', '技能提升', '表达能力', '思维逻辑', '创新思维'];

          categories.forEach(category => {
            // 匹配每个分类的内容（如【专业知识】和下一个分类之间的内容）
            const regex = new RegExp(`【${category}】\\s*([\\s\\S]*?)(?=【|$)`, 'i');
            const match = data.result.match(regex);

            if (match && match[1]) {
              // 提取"-"开头的建议列表
              const suggestions = match[1]
                .split('\n')
                .filter(line => line.trim().startsWith('-'))
                .map(line => line.trim().replace(/^-/, '').trim());

              this.feedbackCategories.push({
                title: category,
                suggestions: suggestions.length ? suggestions : ['暂无具体建议']
              });
            }
          });
        }
      } catch (error) {
        console.error('生成反馈建议失败:', error);
        this.feedbackCategories = [{
          title: '通用建议',
          suggestions: [
            '加强专业知识学习',
            '提高语言表达能力',
            '多练习逻辑思维'
          ]
        }];
      }
    },

    // 渲染雷达图（修复图表不显示问题）
    renderRadarChart1() {
      // 确保DOM元素已存在
      this.$nextTick(() => {
        const ctx = this.$refs.radarChart?.getContext('2d');
        if (!ctx) {
          console.error('未找到雷达图Canvas元素');
          return;
        }

        // 销毁现有图表
        if (this.chart) {
          this.chart.destroy();
        }

        // 确保有数据再绘制图表
        if (!this.reportIndicators || !this.reportValues || this.reportIndicators.length !== this.reportValues.length) {
          console.error('雷达图数据不完整');
          return;
        }

        // 创建新图表
        this.chart = new Chart(ctx, {
          type: 'radar',
          data: {
            labels: this.reportIndicators,
            datasets: [{
              label: '能力评分',
              data: this.reportValues,
              backgroundColor: 'rgba(59, 130, 246, 0.2)',
              borderColor: 'rgba(59, 130, 246, 1)',
              pointBackgroundColor: 'rgba(59, 130, 246, 1)',
              pointBorderColor: '#fff',
              pointHoverBackgroundColor: '#fff',
              pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              r: {
                angleLines: { display: true },
                suggestedMin: 0,
                suggestedMax: 100,
                ticks: { callback: (value) => `${value}分` }
              }
            },
            plugins: {
              legend: { position: 'top' },
              tooltip: {
                callbacks: { label: (context) => `${context.label}: ${context.raw}分` }
              }
            }
          }
        });
      });
    },

    // 获取评分等级文本
    getScoreLevel(score) {
      if (score >= 85) return '优秀';
      if (score >= 75) return '良好';
      if (score >= 65) return '一般';
      return '待提高';
    },

    // 获取评分对应的CSS类
    getScoreClass(score) {
      if (score >= 85) return 'excellent';
      if (score >= 75) return 'good';
      if (score >= 65) return 'average';
      return 'poor';
    }
  }
};
</script>

<style scoped>
#dialog {
  position: relative;
  height: 100vh;
  overflow: hidden;
  background-color: #EDEDF5;
  max-width: 900px; /* 原尺寸可能更小，适当增大 */
  margin: 0 auto; /* 居中显示 */
  padding: 0 10px; /* 增加内边距 */
}

.van-nav-bar {
  --van-nav-bar-background-color: #EFF1FD;
  --van-nav-bar-title-text-color: black;
}

.chat-container {
  width: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 15px;
}

.message-item {
  display: flex;
  align-items: flex-start;
  margin: 5px 0;
}

.user-message {
  justify-content: flex-end;

}

/* 用户消息气泡样式（关键） */
.user-message .message-bubble,
.user-message .voice-bubble,
.user-message .expression-bubble {
  margin-right: 8px;
  /* 与头像保持距离 */
  margin-left: 0;
  /* 左侧无间距 */
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 10px;
  flex-shrink: 0;
}

.ai-message .avatar {
  background-color: #e6f7ff;
  color: #1890ff;
}

.user-message .avatar {
  background-color: #f5f5f5;
  color: #8c8c8c;
}

.message-bubble {
  padding: 10px 15px;
  border-radius: 18px;
  max-width: 80%;
  word-wrap: break-word;
  position: relative;
}

.ai-message .message-bubble {
  background-color: #ffffff;
  border-top-left-radius: 4px;
}

.user-message .message-bubble {
  background-color: #1677ff;
  color: white;
  border-top-right-radius: 4px;
}

.voice-bubble {
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 18px;
  position: relative;
}

.ai-message .voice-bubble {
  background-color: #ffffff;
  border-top-left-radius: 4px;
}

.user-message .voice-bubble {
  background-color: #1677ff;
  color: white;
  border-top-right-radius: 4px;
}

.voice-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 150px;
}

.voice-wave {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 24px;
  flex-grow: 1;
}

.voice-wave div {
  width: 3px;
  background-color: currentColor;
  border-radius: 3px;
  transition: height 0.2s ease;
}

.voice-duration {
  font-size: 12px;
  color: currentColor;
  opacity: 0.8;
}

.play-icon {
  cursor: pointer;
}

.voice-actions {
  display: flex;
  gap: 5px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.voice-text-result {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #eee;
  font-size: 14px;
  color: #333;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 5px;
  border-radius: 4px;
}

.voice-speed-result {
  margin-top: 5px;
  font-size: 12px;
  color: #666;
  background-color: rgba(255, 255, 255, 0.5);
  padding: 3px 5px;
  border-radius: 4px;
}

.voice-tone-result {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #eee;
  font-size: 12px;
  color: #666;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 5px;
  border-radius: 4px;
}

.voice-logic-result {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #eee;
  font-size: 13px;
  color: #333;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 5px;
  border-radius: 4px;
}

/* 表情和姿态分析样式 */
.expression-bubble {
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 18px;
  position: relative;
}

.ai-message .expression-bubble {
  background-color: #ffffff;
  border-top-left-radius: 4px;
}

.user-message .expression-bubble {
  background-color: #1677ff;
  color: white;
  border-top-right-radius: 4px;
}

.expression-image-container {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 10px;
}

.expression-image {
  width: 200px;
  height: auto;
  display: block;
}

.expression-results,
.pose-result,
.comprehensive-analysis {
  margin-top: 8px;
  font-size: 13px;
  padding: 5px;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.7);
  color: #333;
}

.expression-actions {
  display: flex;
  gap: 5px;
  margin-top: 8px;
  justify-content: flex-end;
}

.error-message {
  background-color: #fff2f0 !important;
  color: #f5222d !important;
}

.typing {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #6b7280;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {

  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1);
  }
}


#dialog_bottombar {
  width: 100%;
  background-color: #EFF1FD;
}

#dialog_bottombar_inside {
  position: relative;
  width: 100%;
  padding: 8px 2.5% 15px;
  box-sizing: border-box;
}

.recording {
  color: #f5222d !important;
  animation: pulse 1.5s infinite;
}

.camera-active {
  color: #00b42a !important;
  animation: pulse 2s infinite;
}

.report-icon {
  color: #722ed1 !important;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.2);
  }

  100% {
    transform: scale(1);
  }
}

.recording-indicator {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 20px 30px;
  border-radius: 10px;
  text-align: center;
  z-index: 1000;
}

.recording-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #f5222d;
  margin: 0 auto 10px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }

  100% {
    opacity: 1;
  }
}

.status-bar {
  position: absolute;
  bottom: 120px;
  left: 0;
  width: 100%;
  text-align: center;
  transition: opacity 0.3s ease;
}

/* 相机模态框样式 */
.camera-modal {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.camera-preview {
  flex-grow: 1;
  position: relative;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-loading,
.camera-error {
  position: absolute;
  color: white;
  text-align: center;
  padding: 20px;
}

.camera-controls {
  padding: 15px;
  display: flex;
  gap: 10px;
  justify-content: center;
  background-color: #f5f5f5;
}

/* 评测报告弹窗样式 */
.report-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px 0;
}

.report-header {
  text-align: center;
  padding: 10px 20px;
  position: relative;
  border-bottom: 1px solid #eee;
}

.report-header h2 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}

.close-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
}

.report-loading,
.report-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-grow: 1;
  gap: 15px;
  padding: 20px;
}

.report-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 15px;
}

/* 雷达图样式 */
.radar-chart-container {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.chart-title {
  font-size: 16px;
  color: #334155;
  text-align: center;
  margin-bottom: 10px;
  font-weight: 500;
}

.chart-wrapper {
  width: 100%;
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 能力详情样式 */
.ability-details-container {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.details-title {
  font-size: 16px;
  color: #334155;
  text-align: center;
  margin-bottom: 10px;
  font-weight: 500;
}

.details-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: #fff;
  border-radius: 6px;
  font-size: 14px;
}

.indicator-name {
  color: #334155;
}

.score-value {
  font-weight: bold;
}

.excellent {
  color: #2ecc71;
}

.good {
  color: #f39c12;
}

.average {
  color: #3498db;
}

.poor {
  color: #e74c3c;
}

/* 分析内容样式 */
.analysis-container {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.analysis-title {
  font-size: 16px;
  color: #334155;
  margin-bottom: 15px;
  font-weight: 500;
}

.analysis-section {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px dashed #e2e8f0;
}

.analysis-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.analysis-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #1e293b;
}

.analysis-section p {
  margin: 0;
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
}

/* 综合评价样式 */
.summary-container {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.summary-title {
  font-size: 16px;
  color: #334155;
  margin-bottom: 15px;
  font-weight: 500;
}

.summary-content {
  background: #fff;
  padding: 15px;
  border-radius: 6px;
}

.summary-content p {
  margin: 0 0 10px 0;
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
}

.summary-content h4 {
  margin: 15px 0 8px 0;
  font-size: 14px;
  color: #1e293b;
}

.summary-content ul {
  margin: 0;
  padding-left: 20px;
}

.summary-content li {
  font-size: 13px;
  color: #475569;
  margin-bottom: 5px;
  line-height: 1.5;
}

/* 响应体展示样式 */
.response-body-container {
  margin-top: 20px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.response-body-title {
  font-size: 16px;
  color: #334155;
  margin-bottom: 10px;
  font-weight: 500;
}

.response-body-content {
  background: #fff;
  padding: 15px;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
}

.response-body-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 12px;
  color: #334155;
}

/* Markdown渲染样式 */
.markdown-bubble {
  padding: 12px 15px;
  line-height: 1.8;
}

.markdown-render h1 {
  font-size: 1.5rem;
  margin: 1rem 0 0.5rem;
  color: #333;
}

.markdown-render h2 {
  font-size: 1.3rem;
  margin: 0.8rem 0 0.4rem;
  color: #444;
}

.markdown-render h3 {
  font-size: 1.1rem;
  margin: 0.6rem 0 0.3rem;
  color: #555;
}

.markdown-render ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-render li {
  margin: 0.3rem 0;
}

.markdown-render strong {
  font-weight: bold;
  color: #222;
}

.markdown-render em {
  color: #666;
  font-style: italic;
}

.markdown-render p {
  margin: 0.5rem 0;
}

/* 修复可能的样式冲突 */
.markdown-render * {
  box-sizing: border-box;
}

.formatted-content {

  color: #111827;
}


.formatted-content div[style*="color: rgba(107, 114, 128, 0.7)"] {
  color: rgba(107, 114, 128, 0.7) !important;
  background-color: rgba(243, 244, 246, 0.3) !important;
}
.van-popup.dragging {
  user-select: none;
}
</style>
