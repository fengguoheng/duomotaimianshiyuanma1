<template>
  <div class="container">
    <h1>笔试</h1>

    <!-- 题目区域 -->
    <div v-if="isLoading" class="loading">
      <p>正在加载题目，请稍候...</p>
    </div>

    <div v-else class="question-container" ref="questionsContainer">
      <div v-for="(question, index) in parsedQuestions" :key="index" class="question">
        <h3>问题 {{ index + 1 }}</h3>
        <pre style="white-space: pre-wrap; word-break: break-all; background: #f8f9fa; padding: 15px; border-radius: 8px;">
          {{ question }}
        </pre>

        <div class="options">
          <label class="option" v-for="option in ['A', 'B', 'C', 'D']" :key="option">
            <input 
              type="radio" 
              :name="'q' + (index + 1)" 
              :value="option" 
              v-model="answers[index]"
            >
            {{ option }}
          </label>
        </div>
      </div>
    </div>

    <!-- 提交按钮 -->
    <button @click="handleSubmit" :disabled="isSubmitting || !hasAnsweredAll" class="custom-btn">
      {{ isSubmitting ? '提交中...' : '提交' }}
    </button>

    <!-- 加载状态 -->
    <div v-show="isLoading" class="loading">
      <p>{{ loadingText }}</p>
    </div>

    <!-- 结果展示 -->
    <div v-show="result" class="result">
      <p>{{ result }}</p>
    </div>
  </div>
</template>

<script>
import html2canvas from 'html2canvas';

export default {
  data() {
    return {
      rawQuestions: '',
      parsedQuestions: [],
      answers: [],
      isLoading: false,
      loadingText: '',
      isSubmitting: false,
      result: ''
    };
  },
  computed: {
    hasAnsweredAll() {
      return this.answers.every(answer => answer);
    }
  },
  mounted() {
    this.loadQuestions();
  },
  methods: {
    async loadQuestions() {
      this.isLoading = true;
      this.loadingText = '加载题目中...';

      try {
        const questionData = localStorage.getItem('question');
        if (!questionData) throw new Error('未找到题目数据');

        this.rawQuestions = questionData;
        this.parsedQuestions = questionData.split('\n\n').filter(item => item.trim());
        this.answers = new Array(this.parsedQuestions.length).fill(''); // 初始化答案数组
      } catch (error) {
        this.result = `错误：${error.message}，请先上传简历生成题目。`;
      } finally {
        this.isLoading = false;
      }
    },

    async handleSubmit() {
      if (!this.hasAnsweredAll) {
        alert('请回答所有问题');
        return;
      }

      this.isSubmitting = true;
      this.loadingText = '正在提交答案...';
      this.result = '';

      try {
        // 生成截图
        const canvas = await html2canvas(this.$refs.questionsContainer, {
          useCORS: true,
          logging: false
        });
        const imageBase64 = canvas.toDataURL('image/png').split(',')[1];

        // 构建问题描述
        const selectedAnswers = this.answers.map((ans, index) => `Q${index+1}: ${ans}`).join('\n');
        const question = `分析面试者答案：\n${selectedAnswers}`;

        // 发送请求
        const response = await fetch('https://117.72.49.76:443/image-understanding', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_base64: imageBase64, question: question })
        });

        const data = await response.json();
        if (data.status === 'processing') {
          await this.pollResult(data.request_id);
        } else {
          this.result = `处理失败：${data.error || '未知错误'}`;
        }
      } catch (error) {
        this.result = `请求失败：${error.message}`;
      } finally {
        this.isSubmitting = false;
      }
    },

    async pollResult(requestId) {
      try {
        while (true) {
          const resultResponse = await fetch(`https://117.72.49.76:443/get-result/${requestId}`);
          const resultData = await resultResponse.json();

          if (resultData.status === 'completed') {
            /*this.result = `评估结果：\n${resultData.content}`;*/
            localStorage.setItem('answer', resultData.content);
            this.$router.push({ name: 'bishileidatu' });
            return;
          } else if (resultData.status === 'processing') {
            await new Promise(resolve => setTimeout(resolve, 3000));
            this.loadingText = '分析中，请稍候...';
          } else {
            this.result = `处理失败：${resultData.error || '未知错误'}`;
            return;
          }
        }
      } catch (error) {
        this.result = `轮询失败：${error.message}`;
      }
    }
  }
};
</script>

<style>
/* 保留原样式 */
.container { 
    padding: 30px;
    max-width: 800px;
    margin: 0 auto;
    background: #f8f9fa;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.loading {
    margin: 20px 0;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
    text-align: center;
}
.question {
    margin-bottom: 30px;
    padding: 20px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.options {
    display: flex;
    gap: 15px;
    margin: 20px 0;
    font-size: 1.05em;
    color: #34495e;
}
.option input {
    margin-right: 5px;
    vertical-align: middle;
}
.custom-btn {
    padding: 10px 25px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    margin: 20px 0;
    display: block;
    width: fit-content;
    margin-left: auto;
}
.custom-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(52, 152, 219, 0.4);
}
.result {
    margin-top: 20px;
    padding: 20px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>