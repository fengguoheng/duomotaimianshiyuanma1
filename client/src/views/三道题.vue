<template>
  <div class="container">
    <h1>笔试</h1>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading">
      <p>{{ loadingText }}</p>
    </div>

    <!-- 题目区域 -->
    <div v-else>
      <!-- 有题目时显示 -->
      <div v-if="questions.length > 0" class="question-container" ref="questionsContainer">
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
          <!-- 显示答案 -->
          <div v-if="showAnswers" class="answer">
            <p><strong>正确答案：</strong>{{ questionItem.answer }}</p>
          </div>
        </div>
      </div>

      <!-- 无题目时的提示 -->
      <div v-else class="no-questions">
        <p>未加载到题目，请确认题目数据是否存在。</p>
      </div>
    </div>

    <!-- 按钮区域 -->
    <div class="button-area">
      <button @click="handleSubmit" :disabled="isSubmitting || !hasAnsweredAll" class="custom-btn">
        {{ isSubmitting ? '提交中...' : '提交答案' }}
      </button>
      <button @click="showAnswers = true" v-if="!isSubmitting && hasAnsweredAll && questions.length > 0" class="show-answer-btn">
        查看答案
      </button>
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
      questions: [],        // 解析后的题目数组
      answers: [],          // 用户选择的答案
      isLoading: false,
      loadingText: '加载题目中...',
      isSubmitting: false,
      result: '',
      showAnswers: false    // 控制是否显示答案
    };
  },
  computed: {
    hasAnsweredAll() {
      return this.questions.length > 0 && this.answers.every(answer => answer);
    }
  },
  mounted() {
    this.loadQuestions();
  },
  methods: {
    async loadQuestions() {
      this.isLoading = true;
      
      try {
        const questionData = localStorage.getItem('question');
        if (!questionData) {
          this.result = '未找到题目数据，请先上传简历生成题目。';
          
          // 开发测试用：模拟题目数据（正式环境可删除）
          this.rawQuestions = `
Q1: 下列哪个不是人工智能的核心技术？
A. 机器学习
B. 量子计算
C. 自然语言处理
D. 计算机视觉
答案：B

Q2: 深度学习属于下列哪个领域？
A. 机器学习
B. 数据结构
C. 操作系统
D. 计算机网络
答案：A
          `;
        } else {
          this.rawQuestions = questionData;
        }
        
        this.parseQuestions(this.rawQuestions);  // 解析题目数据
        this.answers = new Array(this.questions.length).fill(''); // 初始化答案数组
        
        if (this.questions.length === 0) {
          this.result = '解析题目失败，请检查题目数据格式。';
        }
      } catch (error) {
        this.result = `错误：${error.message}，请先上传简历生成题目。`;
      } finally {
        this.isLoading = false;
      }
    },

    // 优化后的题目解析方法
    parseQuestions(questionData) {
      const questions = [];
      const lines = questionData.split('\n');
      let currentQuestion = null;
      let currentOptions = [];
      let isParsingAnswers = false;

      lines.forEach((line, index) => {
        const lineTrimmed = line.trim();
        
        // 检测答案部分开始
        if (lineTrimmed.match(/^答案[:：]\s*/)) {
          isParsingAnswers = true;
          return;
        }
        
        if (isParsingAnswers) return;
        
        // 匹配题目开头
        const qMatch = lineTrimmed.match(/^(Q|第\d+题|第\d+问|问题\d+)[：:]?\s*(.*)$/);
        if (qMatch) {
          if (currentQuestion) {
            currentQuestion.options = currentOptions;
            questions.push(currentQuestion);
            currentOptions = [];
          }
          
          currentQuestion = {
            question: qMatch[2] || '',
            options: [],
            answer: ''
          };
        } 
        // 匹配选项
        else if (lineTrimmed.match(/^[A-Da-d]、?\.?\s*/)) {
          const labelMatch = lineTrimmed.match(/^([A-Da-d])[、.]?\s*/);
          if (labelMatch) {
            const label = labelMatch[1].toUpperCase();
            const content = lineTrimmed.slice(labelMatch[0].length).trim();
            currentOptions.push({ label, content, value: label });
          }
        }
        else if (currentQuestion && lineTrimmed) {
          currentQuestion.question += lineTrimmed + '\n';
        }
      });
      
      if (currentQuestion) {
        currentQuestion.options = currentOptions;
        questions.push(currentQuestion);
      }
      
      this.parseAnswers(questionData);
      this.questions = questions;
    },
    
    parseAnswers(questionData) {
      const answerMatch = questionData.match(/(答案|正确答案)[：:]\s*(.*)/);
      if (answerMatch && answerMatch[2]) {
        const answersText = answerMatch[2];
        const answerItems = answersText.split(/[，,；;]/);
        
        answerItems.forEach(ans => {
          const ansTrimmed = ans.trim();
          if (!ansTrimmed) return;
          
          const qAnswerMatch = ansTrimmed.match(/(Q\d+|第?\d+题|问题\d+)[：:]\s*([A-Da-d])/);
          if (qAnswerMatch) {
            const qNumMatch = qAnswerMatch[1].match(/\d+/);
            if (qNumMatch) {
              const qNum = parseInt(qNumMatch[0], 10);
              if (qNum > 0 && qNum <= this.questions.length) {
                this.questions[qNum - 1].answer = qAnswerMatch[2].toUpperCase();
              }
            }
          }
          else if (ansTrimmed.split(',').every(a => /[A-Da-d]/.test(a))) {
            const answers = ansTrimmed.toUpperCase().split(/[，,；;]/);
            answers.forEach((a, index) => {
              if (index < this.questions.length) {
                this.questions[index].answer = a;
              }
            });
          }
        });
      }
    },

    async handleSubmit() {
      if (this.questions.length === 0) {
        alert('没有可提交的题目');
        return;
      }
      
      if (!this.hasAnsweredAll) {
        alert('请回答所有问题');
        return;
      }

      this.isSubmitting = true;
      this.loadingText = '正在提交答案...';
      this.result = '';

      try {
        const canvas = await html2canvas(this.$refs.questionsContainer, {
          useCORS: true,
          logging: false
        });
        const imageBase64 = canvas.toDataURL('image/png').split(',')[1];

        const selectedAnswers = this.answers.map((ans, index) => `Q${index+1}: ${ans}`).join('\n');
        const question = `分析面试者答案：\n${selectedAnswers}`;

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
    const maxAttempts = 20;  // 增加最大轮询次数限制
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      attempts++;
      const resultResponse = await fetch(`https://117.72.49.76:443/get-result/${requestId}`);
      const resultData = await resultResponse.json();

      if (resultData.status === 'completed') {
        // 处理完成
        localStorage.setItem('answer', resultData.content);
        this.$router.push({ name: 'bishileidatu' });
        return;
      } else if (resultData.status === 'processing' || resultData.status === 'pending') {
        // 同时处理 processing 和 pending 状态
        if (attempts >= maxAttempts) {
          this.result = '处理超时，请稍后重试';
          return;
        }
        await new Promise(resolve => setTimeout(resolve, 3000));
        this.loadingText = `分析中，请稍候...（剩余${maxAttempts - attempts}次）`;
      } else {
        // 其他错误状态
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
.no-questions {
    margin: 20px 0;
    padding: 15px;
    background: #fff;
    border: 1px solid #e0e0e0;
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
.question-content {
    margin-bottom: 15px;
    line-height: 1.6;
}
.options {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 15px 0;
}
.option {
    display: flex;
    align-items: flex-start;
  margin-bottom: 8px;
}
.option input {
    margin-right: 10px;
    margin-top: 5px;
}
.answer {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px dashed #e0e0e0;
    color: #10b981;
    font-weight: bold;
}
.custom-btn {
    padding: 10px 25px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    margin: 20px 0 10px;
    display: inline-block;
}
.show-answer-btn {
    padding: 10px 20px;
    background: #f39c12;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
    margin: 20px 0 10px 10px;
    display: inline-block;
}
.show-answer-btn:hover {
    background: #e67e22;
}
.button-area {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 30px;
}
.result {
    margin-top: 30px;
    padding: 20px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>
