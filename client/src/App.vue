<template>
  <div id="app">
    <!-- 全局背景容器 -->
    <div class="global-background"></div>
    
    <!-- 导航栏 -->
    <div v-if="!$route.meta.hideNav" class="nav-container">
      <div class="header-section">
        <h1 class="title">青衿问途</h1>
        <span class="designer" style="color: black">{{ username }}兄，久仰</span>
      </div>
      <nav class="nav-menu">
        <a href="#" class="nav-item" :class="{ 'active': activeIndex === 'interview' }" @click.prevent="handleSelect('interview')">固定面试</a>
        
        <a href="#" class="nav-item" :class="{ 'active': activeIndex === 'yuyinhuida' }" @click.prevent="handleSelect('yuyinhuida')">自由面试</a>
        <a href="#" class="nav-item" :class="{ 'active': activeIndex === 'wenziwenda' }" @click.prevent="handleSelect('wenziwenda')">问途笔谈</a>
        <a href="#" class="nav-item" :class="{ 'active': activeIndex === 'xunirenduihua' }" @click.prevent="handleSelect('xunirenduihua')">问途1号虚拟人</a>
        <a 
  href="https://123.56.203.202/ui" 
  class="nav-item" 
  :class="{ 'active': activeIndex === 'personal' }"
>
  问途2号虚拟人
</a>
        <a href="#" class="nav-item" :class="{ 'active': activeIndex === 'about' }" @click.prevent="handleSelect('about')">问途虚拟人juli</a>
        <a href="#" class="nav-item" :class="{ 'active': activeIndex === 'exit' }" @click.prevent="handleSelect('exit')">雪泥收踪</a>
      </nav>
    </div>
    
    <!-- 路由视图 -->
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      activeIndex: 'home',
      username: '',
      isGlobalBackground: true
    }
  },
  computed: {
    shouldShowBackground() {
      return !this.$route.meta?.hideBackground;
    }
  },
  watch: {
    '$route'() {
      this.isGlobalBackground = this.shouldShowBackground;
    }
  },
  methods: {
    handleSelect(index) {
      this.activeIndex = index;
      console.log('当前选中：', index);
      
      // 路由跳转逻辑
      if (index === 'home') {
        this.$router.push('/home');
      } else if (index === 'interview') {
        this.$router.push('/interview');
      } else if (index === 'personal') {
        this.$router.push('/personal');
      } else if (index === 'about') {
        this.$router.push('/about');
      } else if (index === 'exit') {
        localStorage.removeItem('token');
        this.$router.push('/');
      } else if (index === 'wenziwenda') {
        this.$router.push('/wenziduihua');
      } else if (index === 'yuyinhuida') {
        this.$router.push('/yuyinhuida');
      } else if (index === 'xunirenduihua') {
        this.$router.push('/xunirenduihua');
      }
    },
    fetchUsername() {
      this.username = localStorage.getItem('username') || '用户';
    }
  },
  mounted() {
    this.fetchUsername();
    
    // 监听路由变化，更新用户名和背景状态
    this.$router.afterEach(() => {
      this.fetchUsername();
      this.isGlobalBackground = this.shouldShowBackground;
    });
  }
}
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 根容器 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* 全局背景样式 */
.global-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-image: url('@/../public/back.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  z-index: -1; /* 确保背景在内容下方 */
}

/* 导航栏样式 */
.nav-container {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 15px;
  
  
}

.header-section {
  text-align: center;
  margin-bottom: 20px;
}

.title {
  font-size: 28px;
  color: #4CAF50;
  font-weight: 600;
}

.designer {
  font-size: 14px;
  color: #6c757d;
  margin-top: 5px;
}

.nav-menu {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 10px;
}

.nav-item {
  padding: 12px 22px;
  border-radius: 8px;
  font-size: 16px;
  color: #333;
  text-decoration: none;
  transition: all 0.3s ease;
  background: rgba(245, 247, 250, 0.8); /* 半透明背景 */
}

.nav-item.active {
  background: #409eff;
  color: white;
}

.nav-item:hover:not(.active) {
  background: rgba(230, 247, 255, 0.9);
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
}
</style>