<template>
  <div class="login-page">
    <!-- 背景图片容器 -->
    <div class="bg-container">
      <!-- 动态星光背景容器 -->
      <div id="stars" class="star-background">
        <!-- 动态生成的星光将插入到这里 -->
      </div>
    </div>

    <div class="login-container">
      <h2 class="login-title">青衿问途</h2>
      <form @submit.prevent="handleSubmit">
        <!-- 用户名输入框 -->
        <div class="form-group">
          <label class="form-label">用户名</label>
          <div class="input-wrapper">
            <i class="fa fa-user input-icon"></i>
            <input type="text" id="username" name="username" v-model="username"
              :class="{ 'error-input': errors.username }" required class="form-input" />
          </div>
          <p v-if="errors.username" class="error-message">
            {{ errors.username }}
          </p>
        </div>

        <!-- 密码输入框 -->
        <div class="form-group">
          <label class="form-label">密码</label>
          <div class="input-wrapper">
            <i class="fa fa-lock input-icon"></i>
            <input type="password" id="password" name="password" v-model="password"
              :class="{ 'error-input': errors.password }" required class="form-input" />
          </div>
          <p v-if="errors.password" class="error-message">
            {{ errors.password }}
          </p>
        </div>

        <!-- 登录按钮 -->
        <button type="submit" class="login-btn" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>

        <!-- 注册链接 -->
        <div class="register-link">
          <span class="text-gray-600">没有账号？</span>
          <router-link to="/register" class="link-primary">
            现在去注册
          </router-link>
        </div>

        <!-- 消息提示 -->
        <div ref="message" class="message-box" :class="{
          'success': messageClass.includes('green'),
          'error': messageClass.includes('red')
        }" v-show="message">
          {{ message }}
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      password: '',
      message: '',
      messageClass: '',
      errors: {
        username: false,
        password: false
      },
      isLoading: false,
      starContainer: null
    };
  },
  mounted() {
    this.initStarAnimation();
  },
  beforeDestroy() {
    // 清理动态创建的元素，避免内存泄漏
    if (this.starContainer) {
      this.starContainer.innerHTML = '';
    }
  },
  methods: {
    async handleSubmit() {
      // 表单验证逻辑不变
      this.validateForm();
      if (Object.values(this.errors).some(error => error)) return;

      this.isLoading = true;
      this.message = '';

      try {
        const response = await fetch(
          'https://123.56.203.202/sqlLogin',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              username: this.username,
              password: this.password
            })
          }
        );

        const data = await response.json();

        if (data.success) {
          this.messageClass = 'bg-green-100 text-green-800';
          this.message = '登录成功！正在跳转...';
          localStorage.setItem('token', data.token);
          setTimeout(() => {
            localStorage.setItem('username', this.username);
            // 从命名路由改为路径路由
            this.$router.push('/interview');
          }, 1000);
        } else {
          this.messageClass = 'bg-red-100 text-red-800';
          this.message = data.message || '登录失败';
        }
      } catch (error) {
        this.messageClass = 'bg-red-100 text-red-800';
        this.message = '网络错误，请重试';
      } finally {
        this.isLoading = false;
      }
    },
    validateForm() {
      this.errors.username = !this.username.trim();
      this.errors.password = !this.password.trim();
    },
    initStarAnimation() {
      this.starContainer = document.getElementById('stars');
      if (!this.starContainer) return;

      // 生成20颗蓝色星光，避免遮挡背景图片
      for (let j = 0; j < 20; j++) {
        const newStar = document.createElement("div");
        newStar.className = "star";
        // 随机生成初始位置（从屏幕上方外开始）
        newStar.style.top = this.randomDistance(500, -100) + 'px';
        newStar.style.left = this.randomDistance(1300, 300) + 'px';
        this.starContainer.appendChild(newStar);
      }

      // 设置星光动画延时，使运动更自然
      const stars = document.getElementsByClassName('star');
      for (let i = 0, len = stars.length; i < len; i++) {
        stars[i].style.animationDelay = (Math.random() * 9).toFixed(1) + 's';
      }
    },
    randomDistance(max, min) {
      return Math.floor(Math.random() * (max - min + 1) + min);
    }
  }
};
</script>

<style scoped>
/* 页面基础布局 */
.login-page {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  box-sizing: border-box;
  z-index: 1;
}

/* 背景图片容器 */
.bg-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

/* 背景图片样式 */
.bg-container::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('@/../public/back.jpg');
  /* 半透明遮罩，使登录表单更清晰 */
  background-color: rgba(0, 0, 0, 0.1);
}

/* 蓝色星光背景样式 */
.star-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* 登录容器 */
.login-container {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  position: relative;
  z-index: 2;
  backdrop-filter: blur(5px);
  /* 磨砂玻璃效果 */
}

/* 标题样式 */
.login-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  text-align: center;
  padding: 24px 0;
  border-bottom: 1px solid #e3f2fd;
  margin: 0;
}

/* 表单组通用样式 */
.form-group {
  padding: 20px;
  border-bottom: 1px solid #e3f2fd;
}

/* 表单项标签 */
.form-label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

/* 输入框外层容器（配合图标） */
.input-wrapper {
  position: relative;
}

/* 输入框图标 */
.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  font-size: 16px;
}

/* 输入框样式 */
.form-input {
  width: 100%;
  padding: 12px 12px 12px 40px;
  border: 1px solid #d0efff;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
  background: rgba(255, 255, 255, 0.9);
}

/* 输入框聚焦样式 */
.form-input:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

/* 错误状态输入框 */
.error-input {
  border-color: #f56c6c !important;
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.2) !important;
}

/* 错误提示文本 */
.error-message {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
  line-height: 1.4;
}

/* 登录按钮 */
.login-btn {
  width: calc(100% - 40px);
  margin: 20px;
  padding: 12px 0;
  background: #409eff;
  color: #fff;
  font-size: 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.login-btn:hover {
  background: #66b1ff;
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.login-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  box-shadow: none;
}

/* 注册链接区域 */
.register-link {
  text-align: center;
  padding: 0 20px 24px;
  font-size: 14px;
  color: #999;
}

/* 链接样式 */
.link-primary {
  color: #409eff;
  text-decoration: none;
  margin-left: 4px;
  transition: color 0.2s ease;
}

.link-primary:hover {
  color: #66b1ff;
}

/* 消息提示框 */
.message-box {
  margin: 0 20px 20px;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
}

/* 成功消息样式 */
.message-box.success {
  background: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

/* 错误消息样式 */
.message-box.error {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}

/* 蓝色星光动画样式 */
#stars {
  width: 100%;
  height: 100vh;
  margin: 0;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 2;
}

.star {
  display: block;
  width: 1px;
  background: transparent;
  position: absolute;
  opacity: 0.8;
  /* 降低星光透明度，避免遮挡背景 */
  animation: star-fall 4.2s linear infinite;
  /* 延长动画周期，降低频率 */
}

.star:after {
  content: '';
  display: block;
  border: 0px solid #fff;
  border-width: 0px 50px 1px 50px;
  /* 缩短尾迹长度 */
  /* 浅蓝色星光尾迹，与背景协调 */
  border-color: transparent transparent transparent rgba(173, 216, 230, 0.5);
  box-shadow: 0 0 1px 0 rgba(173, 216, 230, 0.1);
  transform: rotate(-45deg) translate3d(1px, 3px, 0);
  transform-origin: 0% 100%;
}

@keyframes star-fall {
  0% {
    opacity: 0;
    transform: scale(0.5) translate3d(0, 0, 0);
  }

  50% {
    opacity: 1;
    transform: translate3d(-120px, 120px, 0);
  }

  100% {
    opacity: 0;
    transform: scale(1.1) translate3d(-220px, 220px, 0);
  }
}
</style>