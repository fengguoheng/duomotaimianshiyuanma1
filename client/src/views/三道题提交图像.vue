<template>
  <div class="nav-container">
    <div class="container">
      <div class="button-group">
        <button @click="jumpToHome" class="custom-btn">返回首页</button>
      </div>
      
      <div class="exam-container">
        <h1>笔试答案分析</h1>
        
        <!-- 题目与答案区域 -->
        <div ref="examContent" class="exam-content">
          <div v-if="isLoading" class="loading">
            <p>正在加载笔试内容...</p>
          </div>
          
          <div v-else class="question-container">
            <div v-for="(questionItem, index) in questions" :key="index" class="question">
              <h3>问题 {{ index + 1 }}</h3>
              <div class="question-content">
                {{ questionItem.question }}
              </div>
              <div class="options">
                <label class="option" v-for="(option, optIndex) in questionItem.options" :key="optIndex">
                  <input 
                    type="radio" 
                    :name="'q' + (index + 1)" 
                    :value="option.value" 
                    v-model="answers[index]"
                  >
                  {{ option.label }}. {{ option.content }}
                </label>
              </div>
              <div class="user-answer">
                <p><strong>你的答案：</strong>{{ answers[index] || '未选择' }}</p>
                <p v-if="showAnswers"><strong>正确答案：</strong>{{ questionItem.answer }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 提交区域 -->
        <div class="submit-area">
          <button @click="handleUpload" id="submitBtn" :disabled="isUploading">
            {{ isUploading ? '分析中...' : '分析答案' }}
          </button>
          <button @click="showAnswers = !showAnswers" class="show-answer-btn">
            {{ showAnswers ? '隐藏答案' : '显示答案' }}
          </button>
        </div>
        
        <!-- 进度显示 -->
        <div v-show="showProgress" class="progress">{{ progressText }}</div>
        
        <!-- 结果展示区域 -->
        <div v-show="showResult" class="result-container">
          <div v-if="isLoadingResult" class="loading">
            <p>正在生成分析报告...</p>
          </div>
          
          <div v-else class="analysis-result">
            <h2>笔试答案分析报告</h2>
            <div class="visualization-container">
              <div class="chart-wrapper">
                <canvas ref="resultChart" width="400" height="300"></canvas>
              </div>
            </div>
            <div v-html="answerHtml" class="analysis-content"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import html2canvas from 'html2canvas';
import { Chart } from 'chart.js';

export default {
  data() {
    return {
      questions: [],        // 题目数据
      answers: [],          // 用户答案
      isLoading: true,      // 加载题目状态
      isUploading: false,   // 上传状态
      showProgress: false,  // 显示进度
      showResult: false,    // 显示结果
      isLoadingResult: false, // 加载结果状态
      progressText: '',     // 进度文本
      answerContent: '',    // 分析结果内容
      answerHtml: '',       // 分析结果HTML
      showAnswers: false,   // 显示正确答案
      requestId: null,      // 请求ID
      apiBaseUrl: 'https://117.72.49.76:443', // API基础URL
      chart: null,          // 图表实例
      analysisData: {}      // 分析数据
    };
  },
  mounted() {
    this.loadQuestions();
  },
  methods: {
    jumpToHome() {
      this.$router.push('/home');
    },
    
    // 加载题目
    loadQuestions() {
      try {
        const questionData = localStorage.getItem('question');
        if (questionData) {
          this.parseQuestions(questionData);
        } else {
          this.isLoading = false;
          this.questions = this.generateSampleQuestions(); // 生成示例题目
        }
      } catch (error) {
        console.error('加载题目失败:', error);
        this.questions = this.generateSampleQuestions(); // 生成示例题目
      } finally {
        this.isLoading = false;
        this.answers = new Array(this.questions.length).fill(''); // 初始化答案数组
      }
    },
    
    // 生成示例题目（带分类）
    generateSampleQuestions() {
      return [
        {
          id: 1,
          question: "1. 下列哪个不是人工智能的主要研究领域？",
          options: [
            { label: 'A', content: '机器学习', value: 'A' },
            { label: 'B', content: '自然语言处理', value: 'B' },
            { label: 'C', content: '量子计算', value: 'C' },
            { label: 'D', content: '计算机视觉', value: 'D' }
          ],
          answer: 'C',
          category: 'AI基础' // 题目分类
        },
        {
          id: 2,
          question: "2. 下列哪个算法属于监督学习？",
          options: [
            { label: 'A', content: 'K-means', value: 'A' },
            { label: 'B', content: '决策树', value: 'B' },
            { label: 'C', content: 'PCA', value: 'C' },
            { label: 'D', content: 'LDA', value: 'D' }
          ],
          answer: 'B',
          category: '机器学习' // 题目分类
        },
        {
          id: 3,
          question: "3. 卷积神经网络(CNN)主要用于什么领域？",
          options: [
            { label: 'A', content: '自然语言处理', value: 'A' },
            { label: 'B', content: '计算机视觉', value: 'B' },
            { label: 'C', content: '语音识别', value: 'C' },
            { label: 'D', content: '强化学习', value: 'D' }
          ],
          answer: 'B',
          category: '深度学习' // 题目分类
        }
      ];
    },
    
    // 解析题目（支持分类）
    parseQuestions(questionData) {
      const questions = [];
      const lines = questionData.split('\n');
      let currentQuestion = null;
      let currentOptions = [];
      
      lines.forEach(line => {
        const lineTrimmed = line.trim();
        const qMatch = lineTrimmed.match(/^Q(\d+):$/);
        
        if (qMatch) {
          const qNum = parseInt(qMatch[1], 10);
          if (currentQuestion) {
            currentQuestion.options = currentOptions;
            questions.push(currentQuestion);
            currentOptions = [];
          }
          
          currentQuestion = {
            id: qNum,
            question: '',
            options: [],
            answer: '',
            category: '未知' // 题目分类，默认为未知
          };
        } 
        // 解析题目分类（格式：#分类: 深度学习）
        else if (lineTrimmed.startsWith('#分类:')) {
          if (currentQuestion) {
            currentQuestion.category = lineTrimmed.slice(4).trim();
          }
        }
        else if (lineTrimmed.startsWith('A.') || lineTrimmed.startsWith('B.') || 
                 lineTrimmed.startsWith('C.') || lineTrimmed.startsWith('D.')) {
          const label = lineTrimmed.charAt(0);
          const content = lineTrimmed.slice(2).trim();
          currentOptions.push({ label, content, value: label });
        } 
        else if (currentQuestion) {
          currentQuestion.question += lineTrimmed + '\n';
        }
      });
      
      if (currentQuestion) {
        currentQuestion.options = currentOptions;
        questions.push(currentQuestion);
      }
      
      this.questions = questions;
    },
    
    // 处理提交
    async handleUpload() {
      if (this.answers.some(answer => !answer)) {
        alert('请回答所有问题');
        return;
      }
      
      this.isUploading = true;
      this.showProgress = true;
      this.progressText = '正在分析答案，请稍候...';
      this.showResult = false;
      this.isLoadingResult = false;
      
      try {
        // 生成截图
        const canvas = await html2canvas(this.$refs.examContent, {
          useCORS: true,
          logging: false,
          scale: 2,
          scrollX: 0,
          scrollY: 0
        });
        const imageBase64 = canvas.toDataURL('image/png').split(',')[1];
        
        // 构建优化后的提示词（要求生成可视化评测报告）
        let question = '生成结构化的笔试答案分析报告，要求包含以下可视化数据：\n\n';
        question += '1. 整体正确率统计（百分比）\n';
        question += '2. 按知识点分类的掌握情况（如AI基础、机器学习等），需提供分类名称和掌握分数\n';
        question += '3. 错误题目的详细解析（包含错误原因和知识点补充）\n';
        question += '4. 针对性的学习建议\n';
        question += '5. 结构化数据输出（JSON格式），包含以上所有内容\n\n';
        question += '以下是笔试题目、用户答案和正确答案：\n\n';
        
        this.questions.forEach((q, index) => {
          question += `Q${index+1}: ${q.question}\n`;
          question += `用户答案: ${this.answers[index] || '未选择'}\n`;
          question += `正确答案: ${q.answer}\n`;
          question += `题目分类: ${q.category}\n\n`;
        });
        
        // 发送分析请求
        const analysisResponse = await fetch(`${this.apiBaseUrl}/image-understanding`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': '69420'
          },
          body: JSON.stringify({ image_base64: imageBase64, question: question })
        });
        
        const data = await analysisResponse.json();
        
        if (data.status === 'processing') {
          this.requestId = data.request_id;
          await this.pollResult();
        } else {
          this.handleAnalysisResult(data);
        }
      } catch (error) {
        console.error('分析失败:', error);
        this.answerContent = `网络错误：${error.message}`;
        this.answerHtml = this.parseMarkdownToHtml(this.answerContent);
        this.showResult = true;
      } finally {
        this.isUploading = false;
        this.showProgress = false;
      }
    },
    
    // 处理分析结果
    handleAnalysisResult(data) {
      if (data.status === 'failed') {
        this.answerContent = '分析失败：' + (data.error || '未知错误');
        this.answerHtml = this.parseMarkdownToHtml(this.answerContent);
        this.showResult = true;
        return;
      }
      
      this.answerContent = data.content || '暂无分析结果';
      
      // 尝试解析JSON数据用于可视化
      try {
        const jsonStart = this.answerContent.indexOf('{');
        const jsonEnd = this.answerContent.lastIndexOf('}') + 1;
        if (jsonStart > 0 && jsonEnd > jsonStart) {
          const jsonContent = this.answerContent.substring(jsonStart, jsonEnd);
          this.analysisData = JSON.parse(jsonContent);
          this.renderVisualization();
        }
      } catch (error) {
        console.error('解析分析结果失败:', error);
        this.analysisData = {};
      }
      
      this.answerHtml = this.parseMarkdownToHtml(this.answerContent);
      this.showResult = true;
    },
    
    // 轮询获取结果
    async pollResult() {
      try {
        while (true) {
          const resultResponse = await fetch(`${this.apiBaseUrl}/get-result/${this.requestId}`);
          const result = await resultResponse.json();
          
          if (result.status === 'completed') {
            this.handleAnalysisResult(result);
            return;
          } else if (result.status === 'failed') {
            this.answerContent = '分析失败：' + (result.error || '未知错误');
            this.answerHtml = this.parseMarkdownToHtml(this.answerContent);
            this.showResult = true;
            return;
          }
          
          await new Promise(resolve => setTimeout(resolve, 3000));
          this.progressText = '分析中，请稍候...';
        }
      } catch (error) {
        console.error('轮询失败:', error);
        this.answerContent = `轮询错误：${error.message}`;
        this.answerHtml = this.parseMarkdownToHtml(this.answerContent);
        this.showResult = true;
      }
    },
    
    // 渲染可视化图表
    renderVisualization() {
      if (!this.analysisData || !this.analysisData.categoryMastery) {
        return;
      }
      
      const ctx = this.$refs.resultChart.getContext('2d');
      if (this.chart) {
        this.chart.destroy();
      }
      
      // 准备图表数据
      const categories = Object.keys(this.analysisData.categoryMastery);
      const scores = categories.map(category => this.analysisData.categoryMastery[category].score);
      const backgroundColors = [
        'rgba(59, 130, 246, 0.7)',
        'rgba(16, 185, 129, 0.7)',
        'rgba(243, 156, 18, 0.7)',
        'rgba(230, 126, 34, 0.7)',
        'rgba(220, 38, 38, 0.7)'
      ];
      
      this.chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: categories,
          datasets: [{
            label: '知识点掌握情况 (%)',
            data: scores,
            backgroundColor: backgroundColors,
            borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              title: {
                display: true,
                text: '掌握度'
              }
            }
          },
          plugins: {
            title: {
              display: true,
              text: '各知识点掌握情况'
            },
            legend: {
              display: false
            }
          }
        }
      });
    },
    
    // 转换Markdown到HTML
    parseMarkdownToHtml(markdown) {
      if (!markdown) return '<p>暂无分析结果</p>';
      
      let html = markdown
        .replace(/\*\*(.*?)\*\*/g, '<h3>$1</h3>')
        .replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>')
        .replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>')
        .replace(/\n{3,}/g, '\n\n') // 合并多余空行
        .split('\n\n').map(paragraph => {
          if (paragraph.trim().startsWith('<h3>') || paragraph.trim().startsWith('<ul>')) {
            return paragraph;
          }
          return `<p>${paragraph.trim()}</p>`;
        }).join('');
        
      return `<div class="answer-content">${html}</div>`;
    }
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.destroy();
    }
  }
};
</script>

<style scoped>
/* 其他样式保持不变，新增图表容器样式 */
.visualization-container {
  display: flex;
  justify-content: center;
  margin: 30px 0;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
}

.chart-wrapper {
  width: 100%;
  max-width: 600px;
}

@media (max-width: 768px) {
  .visualization-container {
    padding: 15px;
  }
  
  .chart-wrapper {
    max-width: 100%;
  }
}
</style>