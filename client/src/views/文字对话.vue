<template>
  <div class="spark-chat-container">
    <h1>
      人工智能技术岗面试官
      <button 
  id="clearBtn" 
  @click="clearChatHistory"
  style="background-color:#00c0c0;color:white;border:none;"
>
  清除历史聊天记录
</button>
    </h1>
    <!--
    <div class="model-selector">
      <label for="modelSelect">选择模型版本:</label>
      <select id="modelSelect" v-model="selectedModel" @change="changeModel">
        <option value="lite">Spark Lite</option>
        <option value="generalv3">Spark Pro</option>
        <option value="pro-128k">Spark Pro-128K</option>
        <option value="generalv3.5">Spark Max</option>
        <option value="max-32k">Spark Max-32K</option>
        <option value="4.0Ultra">Spark 4.0 Ultra</option>
        <option value="kjwx">科技文献大模型</option>
      </select>
    </div>
-->
    <div id="results">
      <div id="result">
        <div 
         v-for="(message, index) in chatMessages.filter(m => m.role !== 'system')" 
  :key="index" 
  :class="['message', `${message.role}-message`]"
        >
          <img 
            class="avatar" 
            :src="message.role === 'user' ? 'redrun.avif' : 'spark.png'"
            :alt="`${message.role} avatar`" 
          />
          <div class="content" v-html="parseContent(message.content)"></div>
        </div>
      </div>
    </div>
    
    <div id="sendVal">
      <input 
        id="question" 
        type="text" 
        placeholder="请输入信息..." 
        v-model="userInput"
        @keydown.enter="sendMessage"
        :disabled="isLoading"
      />
      <button 
        id="btn" 
        @click="sendMessage"
        :disabled="isLoading || !userInput.trim()"
      >
        {{ isLoading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SparkChat',
  data() {
    return {
      userInput: '',
      chatMessages: [],
      isLoading: false,
      currentAssistantMessage: '',
      currentAssistantDiv: null,
      selectedModel: '4.0Ultra', // 默认选择4.0 Ultra版本
      models: {
        'lite': {
          domain: 'lite',
          url: 'wss://spark-api.xf-yun.com/v1.1/chat',
          maxTokens: 4096
        },
        'generalv3': {
          domain: 'generalv3',
          url: 'wss://spark-api.xf-yun.com/v3.1/chat',
          maxTokens: 8192
        },
        'pro-128k': {
          domain: 'pro-128k',
          url: 'wss://spark-api.xf-yun.com/chat/pro-128k',
          maxTokens: 4096
        },
        'generalv3.5': {
          domain: 'generalv3.5',
          url: 'wss://spark-api.xf-yun.com/v3.5/chat',
          maxTokens: 8192
        },
        'max-32k': {
          domain: 'max-32k',
          url: 'wss://spark-api.xf-yun.com/chat/max-32k',
          maxTokens: 8192
        },
        '4.0Ultra': {
          domain: '4.0Ultra',
          url: 'wss://spark-api.xf-yun.com/v4.0/chat',
          maxTokens: 8192
        },
        'kjwx': {
          domain: 'kjwx',
          url: 'wss://spark-openapi-n.cn-huabei-1.xf-yun.com/v1.1/chat_kjwx',
          maxTokens: 8192
        }
      }
    };
  },
  mounted() {
    this.initChatHistory();
  },
  methods: {
    // 初始化聊天历史
    initChatHistory() {
      let chatHistory = localStorage.getItem('chatHistory');
      if (chatHistory) {
        this.chatMessages = JSON.parse(chatHistory).map(item => {
          if (item.content.startsWith("data:image/")) {
            item.content = "已经为您生成图片"
          }
          return item
        });
      } else {
        this.chatMessages = [
      {
  role: 'system',
  content: `你是一位经验丰富的人工智能技术岗面试官，但也可以灵活切换到其他领域的交流。
    - 主要职责：提问技术问题，评估候选人水平
    - 扩展功能：当用户明确提出其他需求时，可切换到相关话题（如行业趋势、学习资源等）
    - 回答风格：保持专业，但允许一定的灵活性和幽默感
    - 注意事项: 无论用户说什么，都要回复，不能什么都不回复`
},
      {
  role: 'assistant',
  content: `你好，${localStorage.getItem('username') || '游客'}！我是你的人工智能技术岗面试官。`
}
    ];
        // 添加欢迎消息
        
      }
      this.scrollToBottom();
    },
    
    // 清除聊天历史
    clearChatHistory() {
      const isClear = window.confirm("确定要清除所有聊天记录吗？此操作不可撤销。");
      if (isClear) {
        localStorage.removeItem('chatHistory');
        this.chatMessages = [];
        this.initChatHistory();
      }
    },
    
    // 保存聊天记录
    saveChatHistory() {
      localStorage.setItem('chatHistory', JSON.stringify(this.chatMessages));
    },
    
    // 发送消息
    async sendMessage() {
      const inputVal = this.userInput.trim();
      if (!inputVal) return;
      
      this.isLoading = true;
      
      // 保存用户消息
      const userMessage = {
        role: 'user',
        content: inputVal
      };
      
      this.chatMessages.push(userMessage);
      this.saveChatHistory();
      this.userInput = '';
      this.scrollToBottom();
      
      // 创建助手消息
      const assistantMessage = {
        role: 'assistant',
        content: '<div class="loading-dots"><div></div><div></div><div></div></div>'
      };
      
      this.chatMessages.push(assistantMessage);
      this.saveChatHistory();
      this.scrollToBottom();
      
      try {
        // 获取当前选中模型的配置
        const modelConfig = this.models[this.selectedModel];
        
        // 获取连接URL并建立WebSocket连接
        const url = await this.getWebsocketUrl(modelConfig.url);
        console.log("生成的WebSocket URL:", url);
        
        const ws = new WebSocket(url);
        
        // 等待连接建立
        await new Promise((resolve, reject) => {
          ws.addEventListener('open', (event) => {
            console.log('开启连接！！', event);
            resolve(event);
          });
          ws.addEventListener('error', (error) => {
            console.log('连接发送错误！！', error);
            reject(error);
          });
        });
        
        // 准备发送给服务器的参数
        const params = this.getParams(this.chatMessages);
        console.log("发送的参数:", params);
        let answer = "";
        
        ws.send(JSON.stringify(params));
        
        ws.addEventListener("message", async (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("收到消息:", data);
            
            if (data.header.code !== 0) {
              console.error("Error:", data.header.message);
              answer = `抱歉，出现错误: ${data.header.message}`;
              this.updateAssistantMessage(answer);
              ws.close();
              return;
            }
            
            if (data.payload.choices.text) {
              answer += data.payload.choices.text[0].content;
              // 移除加载动画并更新内容
              this.updateAssistantMessage(answer);
              this.scrollToBottom();
            }
            
            if (data.header.status === 2) {
              // 处理函数调用
              const function_call = data?.payload?.choices?.text[0]?.function_call;
              if (function_call) {
                const name = function_call.name;
                const params = JSON.parse(function_call.arguments);
                const target = this.getFunctionByName(name);
                
                if (target) {
                  // 显示正在处理函数的提示
                  this.updateAssistantMessage(`${answer}<br><br><i>正在处理 ${name} 请求...</i>`);
                  this.scrollToBottom();
                  
                  try {
                    const res = await target.handler(name, params);
                    answer = res;
                  } catch (error) {
                    answer = `处理 ${name} 请求时出错: ${error.message}`;
                  }
                }
              }
              
              // 保存最终回答
              this.chatMessages[this.chatMessages.length - 1].content = answer;
              this.saveChatHistory();
              this.updateAssistantMessage(answer);
              this.scrollToBottom();
              
              setTimeout(() => {
                ws.close();
              }, 1000);
            }
          } catch (parseError) {
            console.error("解析消息错误:", parseError);
            console.log("原始消息:", event.data);
          }
        });
        
        ws.addEventListener("close", () => {
          this.isLoading = false;
        });
        
        ws.addEventListener("error", (error) => {
          console.error("WebSocket error:", error);
          this.updateAssistantMessage("抱歉，连接出现错误，请重试。");
          this.isLoading = false;
        });
        
      } catch (error) {
        console.error("Error:", error);
        this.updateAssistantMessage("抱歉，发送消息时出现错误，请重试。");
        this.isLoading = false;
      }
    },
    
    // 更改模型版本
    changeModel() {
      console.log(`已切换到${this.getModelName(this.selectedModel)}`);
      // 可以添加切换模型时的提示或其他逻辑
    },
    
    // 获取模型名称
    getModelName(modelKey) {
      const modelNames = {
        'lite': 'Spark Lite',
        'generalv3': 'Spark Pro',
        'pro-128k': 'Spark Pro-128K',
        'generalv3.5': 'Spark Max',
        'max-32k': 'Spark Max-32K',
        '4.0Ultra': 'Spark 4.0 Ultra',
        'kjwx': '科技文献大模型'
      };
      return modelNames[modelKey] || modelKey;
    },
    
    // 更新助手消息
    updateAssistantMessage(content) {
      this.chatMessages[this.chatMessages.length - 1].content = content;
    },
    
    // 解析内容（支持代码高亮和图片显示）
    parseContent(content) {
      // 首先检查是否是Base64图片数据
      if (this.isBase64Image(content)) {
        return `<img src="${content}" alt="Generated image" style="max-width:100%;"/>`;
      }

      // 否则当作普通文本处理，解析其中的代码块
      return this.parseCodeBlocks(content);
    },
    
    // 检查是否是Base64图片
    isBase64Image(str) {
      return str.startsWith('data:image/');
    },
    
    // 解析代码块
    parseCodeBlocks(content) {
      // 匹配代码块的正则表达式
      const codeBlockRegex = /```(\w+)?\s*([\s\S]*?)```/g;
      return content.replace(codeBlockRegex, (match, lang, code) => {
        // 如果指定了语言，则使用该语言，否则默认使用 'javascript'
        const language = lang || "javascript";
        // 高亮代码
        const highlightedCode = this.highlightCode(code.trim(), language);
        // 返回包裹在 <pre> 和 <code> 标签中的代码块
        return `<pre><span>${language}<span><hr style='margin:10px 0;border-top: 1px solid blue;'/><code class="language-${language}">${highlightedCode}</code></pre>`;
      });
    },
    
    // 高亮代码
    highlightCode(code, language) {
      if (language === "javascript") {
        // 1. 匹配字符串
        code = code.replace(
          /"([^"]*)"|'([^']*)'/g,
          (match, p1, p2) => `<span class="string">"${p1 || p2}"</span>`
        );

        // 2. 匹配关键字
        code = code.replace(
          /\b(function|let|const|var|if|else|return)\b/g,
          '<span class="keyword">$&</span>'
        );

        // 3. 匹配函数名
        code = code.replace(
          /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g,
          (match, p1) => `<span class="function">${p1}</span>(`
        );

        // 4. 匹配 console.log
        code = code.replace(
          /\b(console\.log)\b/g,
          '<span class="function">$&</span>'
        );

        // 5. 匹配单行注释
        code = code.replace(
          /\/\/.*$/gm,
          '<span class="comment">$&</span>'
        );

        // 6. 匹配多行注释
        code = code.replace(
          /\/\*[\s\S]*?\*\//g,
          '<span class="comment">$&</span>'
        );

        // 7. 匹配数字
        code = code.replace(
          /\b(\d+)\b/g,
          '<span class="number">$&</span>'
        );
      }
      return code;
    },
    
    // 平滑滚动到底部
    scrollToBottom() {
      const resultsDiv = document.getElementById('results');
      if (resultsDiv) {
        resultsDiv.scrollTo({
          top: resultsDiv.scrollHeight,
          behavior: 'smooth'
        });
      }
    },
    
    // 鉴权url地址
    async getWebsocketUrl(hostUrl) {
      // 硬编码鉴权信息
      const APPID = '86f989e0';
      const APISecret = 'YjczOWNiZTYxZWNhY2M5ZjI3OTE5YTJi';
      const APIKey = '7264913c8b3035b87979668da32f762a';
      
      const host = new URL(hostUrl).host;
      const pathname = new URL(hostUrl).pathname;
      let apiKeyName = "api_key";
      let date = new Date().toGMTString();
      let algorithm = "hmac-sha256";
      let headers = "host date request-line";
      
      console.log("生成签名的原始数据:", {
        host,
        date,
        pathname
      });
      
      // 生成签名
      let signatureOrigin = `host: ${host}\ndate: ${date}\nGET ${pathname} HTTP/1.1`;
      
      try {
        let signature = await this.signatureToHmacSHA256ToBase64(signatureOrigin, APISecret);
        let authorizationOrigin = `${apiKeyName}="${APIKey}", algorithm="${algorithm}", headers="${headers}", signature="${signature}"`;
        let authorization = btoa(authorizationOrigin);
        
        // 将空格编码
        let url = `${hostUrl}?authorization=${authorization}&date=${encodeURI(date)}&host=${host}`;
        return url;
      } catch (error) {
        console.error("生成签名出错:", error);
        throw error;
      }
    },
    
    // HMAC-SHA256签名
    async signatureToHmacSHA256ToBase64(origin, secret) {
      // 使用浏览器内置的加密API替代CryptoJS
      const encoder = new TextEncoder();
      const data = encoder.encode(origin);
      const key = encoder.encode(secret);
      
      try {
        const importedKey = await window.crypto.subtle.importKey(
          "raw",
          key,
          { name: "HMAC", hash: "SHA-256" },
          false,
          ["sign"]
        );
        
        const signatureArrayBuffer = await window.crypto.subtle.sign("HMAC", importedKey, data);
        
        // 将ArrayBuffer转换为Base64
        const bytes = new Uint8Array(signatureArrayBuffer);
        let result = '';
        for (const byte of bytes) {
          result += String.fromCharCode(byte);
        }
        return btoa(result);
      } catch (error) {
        console.error("计算HMAC-SHA256签名出错:", error);
        throw error;
      }
    },
    
    // 获取请求参数
    getParams(textList) {
      let functions = this.getFunctions();
      let modelConfig = this.models[this.selectedModel];
      
      let params = {
        "header": {
          "app_id": '86f989e0',
          
          "uid": 'red润'
        },
        "parameter": {
          "chat": {
            "domain": modelConfig.domain, // 使用当前选中模型的domain
            "temperature": 0.5,
            "max_tokens": modelConfig.maxTokens, // 使用当前选中模型的max_tokens
          }
        },
        "payload": {
          "message": {
            "text": textList
          },
          "functions": {
            "text": functions
          }
        }
      };
      
      console.log("生成的请求参数:", params);
      return params;
    },
    
    // 获取所有支持的函数
    getFunctions() {
      return [
        this.weatherFunction,
        this.baiduQuestions,
        this.imgQuestions
        // 可以在这里添加其他的function
      ];
    },
    
    // 通过名称获取特定的function
    getFunctionByName(name) {
      const functions = this.getFunctions();
      return functions.find(func => func.name === name);
    },
    
    // 天气查询函数
    weatherFunction: {
      name: "天气查询",
      description: "天气插件可以提供天气相关信息。你可以提供指定的地点信息、指定的时间点或者时间段信息，来精准检索到天气信息。",
      parameters: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "地点，比如北京。"
          },
          date: {
            type: "string",
            description: "日期。"
          }
        },
        required: ["location"]
      },
      handler: async (name, params) => {
        console.log(params);
        let location = params.location;
        if (location == "北京") { window.open("https://weather.cma.cn/web/weather/54511.html") }
        else if (location == "山东") {
          window.open("https://weather.cma.cn/web/weather/013462.html")
        }
        return `已为您处理任务：${name}，参数：${JSON.stringify(params)}`
      }
    },
    
    // 百度搜索函数
    baiduQuestions: {
      name: "百度搜索",
      description: "百度可以提供需要的的相关信息。你可以提供指定的用户关键词语，来精准检索到目标。",
      parameters: {
        type: "object",
        properties: {
          username: {
            type: "string",
            description: "关键词，比如red润"
          }
        },
        required: ["username"]
      },
      handler: async (name, params) => {
        let username = params.username;
        // 构建百度搜索的 URL
        let url = 'https://www.baidu.com/s?wd=' + encodeURIComponent(username);

        // 使用 window.open 打开链接，_blank 表示在新标签页中打开
        window.open(url, '_blank');
        return `已为您处理任务：${name}，参数：${JSON.stringify(params)}`
      }
    },
    
    // 图片生成函数
    imgQuestions: {
      name: "图片生成",
      description: "根据详细描述生成图像",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": {
            "type": "string",
            "description": "图像的详细描述，需包含主体、风格、构图、色彩等关键信息。例如：'一座被云雾环绕的雪山，山脚下有清澈湖泊，采用水墨画风格，点缀少量青绿色'"
          },
          "style": {
            "type": "string",
            "enum": ["写实", "卡通", "水墨", "油画", "水彩", "数字艺术", "像素风", "动漫"],
            "description": "生成图像的艺术风格",
            "default": "写实"
          },
          "aspect_ratio": {
            "type": "string",
            "enum": ["16:9", "4:3", "1:1", "9:16", "3:4"],
            "description": "生成图像的长宽比例",
            "default": "16:9"
          },
          "color_palette": {
            "type": "string",
            "description": "可选：指定主色调或配色方案（如'冷色调，以蓝绿为主'）",
            "default": "无特定要求"
          }
        },
        "required": ["prompt"]
      },
      handler: async (name, params) => {
        console.log(params);
        let prompt = params?.prompt || params?.content[0];
        
        // 这里是模拟图片生成，实际应用中需要替换为真实的图片生成API
        // 生成一个示例图片URL
        const width = 800;
        const height = 450;
        const randomId = Math.floor(Math.random() * 1000);
        const imgUrl = `https://picsum.photos/id/${randomId}/${width}/${height}`;
        
        // 将图片转换为Base64格式（实际应用中可能需要通过API获取真实的Base64图片）
        return new Promise((resolve) => {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            const dataURL = canvas.toDataURL('image/jpeg');
            resolve(dataURL);
          };
          img.src = imgUrl;
        });
      }
    }
  }
}
</script>

<style scoped>
.spark-chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-selector {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.model-selector label {
  margin-right: 10px;
}

.model-selector select {
  padding: 5px 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

#results {
  height: 500px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 20px;
}

.message {
  display: flex;
  margin-bottom: 15px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 10px;
  object-fit: cover;
}

.content {
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 8px;
  max-width: 80%;
  white-space: pre-wrap;
}

.user-message .content {
  background-color: #e6f7ff;
}

#sendVal {
  display: flex;
}

#question {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
  outline: none;
}

#btn {
  padding: 10px 20px;
  background-color: #40a9ff;
  color: white;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
}

#btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-dots {
  display: flex;
  justify-content: center;
}

.loading-dots div {
  width: 8px;
  height: 8px;
  background-color: #40a9ff;
  border-radius: 50%;
  margin: 0 3px;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots div:nth-child(1) { animation-delay: -0.32s; }
.loading-dots div:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 10px 0;
}

code {
  font-family: Consolas, Monaco, 'Andale Mono', monospace;
  font-size: 0.9em;
}

.string { color: #d14; }
.keyword { color: #0086b3; font-weight: bold; }
.function { color: #900; font-weight: bold; }
.comment { color: #998; font-style: italic; }
.number { color: #099; }
</style>