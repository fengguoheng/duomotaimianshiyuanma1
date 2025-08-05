<template>
  <div class="nav-container">
    
    <div class="container">
      <div class="button-group">
        
      </div>
      
      <div class="image-upload">
        <!-- 自定义文件选择标签，显示"请从本地上传您的简历" -->
        <label for="customFileInput" class="file-label">请从本地上传您的简历</label>
        <input id="customFileInput" type="file" ref="imageInput" accept="image/*" @change="previewImage">
        <button @click="handleUpload" id="submitBtn" :disabled="isUploading">
          {{ isUploading ? '分析中...' : '进行简历分析' }}
        </button>
      </div>
      
      <!-- 图片预览区域 -->
      <div v-if="previewUrl" class="image-preview">
        <h3 class="preview-title">简历图片预览</h3>
        <div class="preview-container">
          <img :src="previewUrl" alt="上传的简历图片" class="preview-image">
        </div>
      </div>
      
      <div v-show="showProgress" class="progress">{{ progressText }}</div>
      
      <!-- 可视化评测反馈报告区域 -->
      <div class="result" v-show="showResult">
        <div class="result-header">
          <h2>面试者能力评估报告</h2>
          <p class="result-subtitle">基于简历分析生成的能力评测反馈</p>
        </div>
        
        <!-- 雷达图区域 -->
        <div class="radar-chart-container">
          <h3 class="chart-title">能力雷达图</h3>
          <div class="chart-wrapper">
            <canvas id="radarChart" width="400" height="300"></canvas>
          </div>
        </div>
        
        <!-- 关键问题与改进建议区域 -->
        <div class="feedback-container">
          <h3 class="feedback-title">关键问题与改进建议</h3>
          <div v-html="feedbackHtml" class="feedback-content"></div>
        </div>
        
        <!-- 原分析结果 -->
        <div v-html="answerHtml" class="original-analysis"></div>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  data() {
    return {
      activeIndex: 'interview',
      username: localStorage.getItem('username') || '用户',
      isUploading: false,
      showProgress: false,
      showResult: false,
      progressText: '',
      answerContent: '',
      answerHtml: '',
      feedbackHtml: '',
      previewUrl: '',
      radarChart: null,
      // 能力评估数据
      skillData: {
        专业知识水平: 0,
        技能匹配度: 0,
        语言表达能力: 0,
        逻辑思维能力: 0,
        创新能力与应变抗压能力: 0
      }
    }
  },
  methods: {
    handleSelect(index) {
      this.activeIndex = index;
      console.log('当前选中：', index);
      if (index === 'home') {
        // 跳转逻辑
      } else if (index === 'exit') {
        localStorage.removeItem('token');
        // 跳转逻辑
      }
    },
    // 图片预览函数
    previewImage(e) {
      const file = e.target.files[0];
      if (file) {
        // 检查是否为图片文件
        if (!file.type.match('image.*')) {
          alert('请选择图片文件');
          return;
        }
        
        // 创建图片预览URL
        const reader = new FileReader();
        reader.onload = (e) => {
          this.previewUrl = e.target.result;
        }
        reader.readAsDataURL(file);
      }
    },
    async handleUpload() {
      const file = this.$refs.imageInput.files[0];
      if (!file) {
        alert('请选择图片');
        return;
      }

      this.isUploading = true;
      this.showProgress = true;
      this.progressText = '正在分析简历，请稍候...';

      try {
        const imageBase64 = await this.convertFileToBase64(file);
        
        // 从localStorage获取career值
        const selectedCareer = localStorage.getItem('career') || '人工智能技术岗';
        
        
        const question = `请基于以下五个关键维度，对简历进行全面且深入的分析：

1. 专业知识水平：评估面试者在${selectedCareer}领域的理论知识储备、专业技能掌握程度及相关项目经验。
2. 技能匹配度：分析面试者的技能与${selectedCareer}岗位要求的契合度，包括硬技能（如编程语言、工具使用）和软技能（如团队协作、沟通能力）。
3. 语言表达能力：通过简历中的文字表述，评估面试者的书面表达清晰度、逻辑性及专业术语使用的准确性。
4. 逻辑思维能力：从简历内容的组织架构、项目描述的因果关系及问题解决思路，判断面试者的逻辑思维能力。
5. 创新能力与应变抗压能力：通过分析简历中体现的创新性解决方案、应对挑战的经历及成果，评估面试者的创新思维和抗压能力。

请为每个维度提供具体的分析结果，并给出综合评价和针对性的改进建议。分析结果需客观、专业且具有可操作性。面试者申请的岗位是${selectedCareer}。`;
        
        // 发送分析请求
        //const question = '提取文字';
        const analysisResponse = await fetch('https://117.72.49.76:443/image-understanding', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '69420' },
          body: JSON.stringify({ image_base64: imageBase64, question: question })
        });
        
        const data = await analysisResponse.json();
        
        if (data.status === 'processing') {
          await this.pollResult(data.request_id);
        }
      } catch (error) {
        console.error('上传失败:', error);
        this.progressText = '网络错误：' + error.message;
      } finally {
        this.isUploading = false;
        this.showProgress = false;
      }
    },

    async pollResult(requestId) {
      try {
        while (true) {
          const resultResponse = await fetch(`https://117.72.49.76:443/get-result/${requestId}`);
          const result = await resultResponse.json();

          if (result.status === 'completed') {
            this.answerContent = result.content || '暂无结果';
            this.answerHtml = this.parseMarkdownToHtml(this.answerContent);
            this.showResult = true;
            
            // 从分析结果中提取评分并生成雷达图
            this.extractSkillScores();
            this.createRadarChart();
            
            // 从分析结果中提取关键问题和改进建议
            this.generateFeedback();
            
            // 存储题目到localStorage
            localStorage.setItem('question', this.answerContent);
            this.jumpToTest();
            return;
          } else if (result.status === 'failed') {
            this.answerHtml = '分析失败：' + (result.error || '未知错误');
            this.showResult = true;
            return;
          }
          
          await new Promise(resolve => setTimeout(resolve, 3000));
          this.progressText = '分析中，请稍候...';
        }
      } catch (error) {
        console.error('轮询失败:', error);
        this.answerHtml = '网络错误：' + error.message;
        this.showResult = true;
      }
    },

    convertFileToBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result.split(',')[1]);
        reader.onerror = (error) => reject(error);
        reader.readAsDataURL(file);
      });
    },

    parseMarkdownToHtml(markdown) {
      if (!markdown) return '';
      
      let html = markdown
        .replace(/\*\*(.*?)\*\*/g, '<h3>$1</h3>')
        .replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>')
        .replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>')
        .split('\n\n').map(paragraph => {
          if (paragraph.trim().startsWith('<h3>') || paragraph.trim().startsWith('<ul>')) {
            return paragraph;
          }
          return `<p>${paragraph.trim()}</p>`;
        }).join('');
        
      return `<div class="answer-content"><h2>面试者能力评估</h2>${html}</div>`;
    },
    
    // 从分析结果中提取技能评分
    extractSkillScores() {
      try {
        // 重置评分
        for (const key in this.skillData) {
          this.skillData[key] = 0;
        }
        
        // 简单的评分提取逻辑（实际应用中可能需要更复杂的正则表达式或NLP处理）
        const content = this.answerContent.toLowerCase();
        
        // 模拟评分提取（实际项目中需要根据大模型返回的实际格式调整）
        if (content.includes('专业知识水平')) {
          this.skillData['专业知识水平'] = this.calculateScore(content, '专业知识水平');
        }
        if (content.includes('技能匹配度')) {
          this.skillData['技能匹配度'] = this.calculateScore(content, '技能匹配度');
        }
        if (content.includes('语言表达能力')) {
          this.skillData['语言表达能力'] = this.calculateScore(content, '语言表达能力');
        }
        if (content.includes('逻辑思维能力')) {
          this.skillData['逻辑思维能力'] = this.calculateScore(content, '逻辑思维能力');
        }
        if (content.includes('创新能力与应变抗压能力')) {
          this.skillData['创新能力与应变抗压能力'] = this.calculateScore(content, '创新能力与应变抗压能力');
        }
        
        console.log('提取的技能评分:', this.skillData);
      } catch (error) {
        console.error('提取技能评分时出错:', error);
      }
    },
    
    // 计算特定维度的评分（简化版）
    calculateScore(content, dimension) {
      // 简单的评分算法，实际应用中需要更复杂的逻辑
      if (content.includes(`${dimension}：优`) || content.includes(`${dimension}：优秀`)) return 85;
      if (content.includes(`${dimension}：良`) || content.includes(`${dimension}：良好`)) return 75;
      if (content.includes(`${dimension}：中`) || content.includes(`${dimension}：一般`)) return 65;
      if (content.includes(`${dimension}：差`) || content.includes(`${dimension}：较差`)) return 55;
      
      // 如果没有明确评分，根据内容长度和正面词汇出现频率估算
      const dimensionText = content.split(dimension)[1] || '';
      const positiveWords = ['强', '丰富', '扎实', '熟练', '清晰', '有条理', '优秀', '良好', '出色', '突出'];
      const negativeWords = ['不足', '欠缺', '薄弱', '不够', '有待提高', '需要加强'];
      
      let score = 50; // 基础分
      positiveWords.forEach(word => {
        if (dimensionText.includes(word)) score += 5;
      });
      negativeWords.forEach(word => {
        if (dimensionText.includes(word)) score -= 5;
      });
      
      return Math.max(0, Math.min(100, score)); // 确保分数在0-100之间
    },
    
    // 创建雷达图
    createRadarChart() {
      try {
        const ctx = document.getElementById('radarChart').getContext('2d');
        
        // 如果已有图表，先销毁
        if (this.radarChart) {
          this.radarChart.destroy();
        }
        
        // 准备数据
        const labels = Object.keys(this.skillData);
        const data = Object.values(this.skillData);
        
        // 创建图表
        this.radarChart = new Chart(ctx, {
          type: 'radar',
          data: {
            labels: labels,
            datasets: [{
              label: '能力评分',
              data: data,
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
                angleLines: {
                  display: true
                },
                suggestedMin: 0,
                suggestedMax: 100
              }
            },
            plugins: {
              legend: {
                position: 'top',
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw}分`;
                  }
                }
              }
            }
          }
        });
      } catch (error) {
        console.error('创建雷达图时出错:', error);
      }
    },
    
    // 从分析结果中提取关键问题和改进建议
    generateFeedback() {
      try {
        const content = this.answerContent;
        
        // 提取各维度分析结果
        const dimensionRegex = /(\d+)\.\s*(.*?)\s*：([\s\S]*?)(?=\d+\.\s*|综合评价|$)/g;
        const dimensions = [];
        let match;
        
        while ((match = dimensionRegex.exec(content)) !== null) {
          dimensions.push({
            title: match[2],
            analysis: match[3]
          });
        }
        
        // 提取综合评价
        const overallRegex = /综合评价[\s\S]*?：([\s\S]*?)(?=面试建议|$)/;
        const overallMatch = overallRegex.exec(content);
        const overallAnalysis = overallMatch ? overallMatch[1].trim() : '';
        
        // 提取面试建议
        const suggestionsRegex = /面试建议[\s\S]*?：([\s\S]*?)(?=$)/;
        const suggestionsMatch = suggestionsRegex.exec(content);
        const suggestions = suggestionsMatch ? suggestionsMatch[1].trim() : '';
        
        // 提取关键问题
        const keyIssues = [];
        const issueKeywords = ['不足', '欠缺', '需要改进', '有待提高', '薄弱', '不够', '缺乏'];
        
        dimensions.forEach(dimension => {
          issueKeywords.forEach(keyword => {
            const issueRegex = new RegExp(`(.*?${keyword}.*?)[。；]`, 'g');
            let issueMatch;
            
            while ((issueMatch = issueRegex.exec(dimension.analysis)) !== null) {
              keyIssues.push({
                dimension: dimension.title,
                issue: issueMatch[1].trim()
              });
            }
          });
        });
        
        // 生成HTML
        let feedbackHtml = '<div class="feedback-summary">';
        
        if (overallAnalysis) {
          feedbackHtml += `<h4 class="summary-title">综合评价</h4>`;
          feedbackHtml += `<p class="summary-content">${overallAnalysis}</p>`;
        }
        
        if (keyIssues.length > 0) {
          feedbackHtml += `<h4 class="issues-title">关键问题</h4>`;
          feedbackHtml += `<ul class="issues-list">`;
          
          keyIssues.forEach(issue => {
            feedbackHtml += `<li><span class="issue-dimension">${issue.dimension}：</span>${issue.issue}</li>`;
          });
          
          feedbackHtml += `</ul>`;
        }
        
        if (suggestions) {
          feedbackHtml += `<h4 class="suggestions-title">改进建议</h4>`;
          
          // 尝试解析为列表
          if (suggestions.includes('；') || suggestions.includes('。')) {
            const suggestionItems = suggestions.split(/[；。]/).filter(item => item.trim() !== '');
            feedbackHtml += `<ul class="suggestions-list">`;
            
            suggestionItems.forEach(item => {
              feedbackHtml += `<li>${item.trim()}</li>`;
            });
            
            feedbackHtml += `</ul>`;
          } else {
            feedbackHtml += `<p class="suggestions-content">${suggestions}</p>`;
          }
        }
        
        feedbackHtml += `</div>`;
        
        this.feedbackHtml = feedbackHtml;
        console.log('生成的反馈HTML:', this.feedbackHtml);
      } catch (error) {
        console.error('生成反馈报告时出错:', error);
        this.feedbackHtml = '<p>生成反馈报告时出错，请查看原始分析结果。</p>';
      }
    },

    jumpToTest() {
      
    }
  },
  beforeDestroy() {
    // 销毁图表以避免内存泄漏
    if (this.radarChart) {
      this.radarChart.destroy();
    }
  }
}
</script>

<style scoped>
/* 导航栏样式 */
.nav-container {
  background: #e3e9f3;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-section {
  text-align: center;
  margin-bottom: 20px;
}

.title {
  font-size: 28px;
  color: #4CAF50;
  margin: 0;
  font-weight: 600;
}

.designer {
  font-size: 14px;
  color: #6c757d;
  margin-top: 5px;
  display: block;
}

.nav-menu {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}

.nav-item {
  padding: 12px 22px;
  border-radius: 8px;
  font-size: 16px;
  color: #333;
  text-decoration: none;
  transition: all 0.3s ease;
  background: #f5f7fa;
}

.nav-item.active {
  background: #409eff;
  color: white;
}

.nav-item:hover:not(.active) {
  background: #e6f7ff;
}

/* 容器样式 */
.container {
  padding: 40px 20px;
  max-width: 800px;
  margin: 0 auto;
  background: #f8fafc;
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 按钮样式 */
.button-group {
  margin-bottom: 25px;
  text-align: center;
}

.custom-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
  background: #3b82f6;
}

.custom-btn:hover {
  background: #2563eb;
  transform: translateY(-2px);
}

#submitBtn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
  background: #10b981;
}

#submitBtn:hover {
  background: #059669;
  transform: translateY(-2px);
}

#submitBtn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 上传区域样式 */
.image-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin: 20px 0;
}

/* 自定义文件选择标签样式 */
.file-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  background: #f8fafc;
  color: #334155;
  transition: all 0.2s ease;
}

.file-label:hover {
  background: #e2e8f0;
}

/* 隐藏原生文件输入框 */
input[type="file"] {
  display: none;
}

/* 图片预览区域样式 */
.image-preview {
  margin: 30px 0;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
}

.preview-title {
  text-align: center;
  color: #334155;
  margin-bottom: 15px;
  font-size: 16px;
}

.preview-container {
  display: flex;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  max-width: 100%;
  height: 300px; /* 固定预览高度 */
  background: #f8fafc;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain; /* 保持图片比例 */
}

/* 进度条 */
.progress {
  text-align: center;
  margin: 20px 0;
  font-size: 14px;
  color: #64748b;
}

/* 结果区域样式 */
.result {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
}

.result-header {
  text-align: center;
  margin-bottom: 25px;
}

.result-header h2 {
  font-size: 22px;
  color: #1e293b;
  margin-bottom: 8px;
}

.result-subtitle {
  font-size: 14px;
  color: #64748b;
}

/* 雷达图容器样式 */
.radar-chart-container {
  margin-bottom: 30px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.chart-title {
  font-size: 18px;
  color: #334155;
  text-align: center;
  margin-bottom: 15px;
}

.chart-wrapper {
  width: 100%;
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 反馈容器样式 */
.feedback-container {
  margin-bottom: 30px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.feedback-title {
  font-size: 18px;
  color: #334155;
  text-align: center;
  margin-bottom: 15px;
}

.feedback-summary {
  background: #fff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
}

.summary-title, .issues-title, .suggestions-title {
  font-size: 16px;
  color: #1e293b;
  margin-top: 20px;
  margin-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 5px;
}

.summary-content {
  color: #334155;
  line-height: 1.6;
}

.issues-list, .suggestions-list {
  list-style-type: none;
  padding-left: 0;
}

.issues-list li {
  margin-bottom: 8px;
  padding-left: 25px;
  position: relative;
}

.issues-list li::before {
  content: "•";
  color: #ef4444;
  font-weight: bold;
  display: inline-block;
  width: 1em;
  margin-left: -1em;
  position: absolute;
  left: 10px;
}

.issue-dimension {
  font-weight: bold;
  color: #3b82f6;
}

.suggestions-list li {
  margin-bottom: 8px;
  padding-left: 25px;
  position: relative;
}

.suggestions-list li::before {
  content: "✓";
  color: #10b981;
  font-weight: bold;
  display: inline-block;
  width: 1em;
  margin-left: -1em;
  position: absolute;
  left: 10px;
}

.suggestions-content {
  color: #334155;
  line-height: 1.6;
}

/* 原始分析结果样式 */
.original-analysis {
  margin-top: 25px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.answer-content h2 {
  color: #1e293b;
  margin-bottom: 20px;
  text-align: center;
  font-size: 18px;
}

.answer-content p {
  margin-bottom: 15px;
  font-size: 15px;
  color: #334155;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-menu {
    flex-wrap: wrap;
  }
  
  .nav-item {
    padding: 8px 12px;
    font-size: 14px;
  }
  
  .container {
    padding: 25px 15px;
    border-radius: 10px;
  }
  
  .preview-container {
    height: 200px;
  }
  
  .chart-wrapper {
    height: 250px;
  }
}
</style>