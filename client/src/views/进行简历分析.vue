<template>
  <div class="nav-container">
    
    <div class="container" style="background: transparent; box-shadow: none;">
      <!-- 按钮容器：统一垂直排列 -->
      <div class="button-container">
        <button @click="jumpToTest" class="custom-btn">笔试演练</button>
        <button @click="$router.push('/wodetiquyudiaofenxi')" class="custom-btn">面试演练</button>
        <button @click="$router.push('/jianlijieguo')" id="submitBtn" :disabled="isUploading">
          {{ isUploading ? '分析中...' : '简历分析' }}
        </button>
      </div>

      <div class="image-upload">
        <input id="customFileInput" type="file" ref="imageInput" accept="image/*" @change="previewImage">
      </div>

      <!-- 图片预览区域 -->
      <div v-if="previewUrl" class="image-preview">
        <h3 class="preview-title">简历图片预览</h3>
        <div class="preview-container">
          <img :src="previewUrl" alt="上传的简历图片" class="preview-image">
        </div>
      </div>

      <div v-show="showProgress" class="progress">{{ progressText }}</div>
      <div v-html="answerHtml" class="result" v-show="showResult"></div>
    </div>
  </div>
</template>

<script>
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
      previewUrl: '' // 存储图片预览URL
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
      if (!file) { // 修正条件判断：检查是否有文件
        alert('请选择图片');
        return;
      }

      this.isUploading = true;
      this.showProgress = true;
      this.progressText = '正在分析简历，请稍候...';

      try {
        this.$router.push('/jianlijieguo'); // 移除不必要的跳转
        const imageBase64 = await this.convertFileToBase64(file);
        const question = '生成10道人工智能技术岗面试选择题，题目不要针对简历内容，而是针对人工智能技术岗';

        // 发送分析请求
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

    jumpToTest() {
      this.$router.push('/tijiaojianlishengchengwenti');
    }
  }
}
</script>

<style scoped>
/* 导航栏样式 */
.nav-container {
  background: transparent;
  padding: 0px;
  box-shadow: 0 ;
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
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 按钮容器样式 */
.button-container {
  display: flex;
  flex-direction: column; /* 垂直排列 */
  align-items: center; /* 水平居中 */
  gap: 15px; /* 按钮间距 */
  margin-bottom: 30px; /* 容器底部间距 */
}

/* 按钮样式 */
.custom-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
  background: #3b82f6;
  width: 100%;
  max-width: 300px; /* 限制最大宽度 */
}

.custom-btn:hover {
  background: #2563eb;
  transform: translateY(-2px);
}

#submitBtn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
  background: #10b981;
  width: 100%;
  max-width: 300px; /* 限制最大宽度 */
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
  height: 300px;
  background: #f8fafc;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* 进度条 */
.progress {
  text-align: center;
  margin: 20px 0;
  font-size: 14px;
  color: #64748b;
}

/* 结果区域 */
.result {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
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
  
  /* 小屏幕下调整按钮间距 */
  .button-container {
    gap: 10px;
  }
  
  .custom-btn, #submitBtn {
    padding: 10px 15px;
    font-size: 14px;
  }
}
</style>