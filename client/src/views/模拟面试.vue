<template>
  <div class="job-selection-page">
    <!-- 背景容器：fixed 定位覆盖全局 -->
    <div class="global-background"></div>  
    
    <div class="content-wrapper">
      <h1 class="page-title">择途问职</h1>
      
      <div class="button-container">
        <button 
          class="job-button" 
          @click="handleJobSelection('人工智能技术岗')"
        >
          人工智能技术岗
        </button>
        <button 
          class="job-button" 
          @click="handleJobSelection('大数据运维测试岗')"
        >
          大数据运维测试岗
        </button>
        <button 
          class="job-button" 
          @click="handleJobSelection('物联网产品岗')"
        >
          物联网产品岗
        </button>
      </div>
      
      
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    handleJobSelection(jobTitle) {
      localStorage.setItem('career', jobTitle);
      this.$router.push('/jianlifenxi');
    }
  }
};
</script>

<style scoped>
/* 全局背景容器：fixed 定位覆盖整个视口 */
.global-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-image: url('@/../public/back.jpg');
  background-size: cover;
  background-position: center;
  /* 让背景在内容下方 */
  z-index: -1; 
}

/* 内容容器：回到正常文档流 */
.job-selection-page {
  min-height: 100vh;
  padding: 20px;
  text-align: center;
}

.content-wrapper {
  /* 限制内容宽度，避免按钮过宽 */
  max-width: 1200px; 
  margin: 0 auto;
  /* 让内容居中，适应不同屏幕 */
  display: flex; 
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
}

.page-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 40px;
  padding-top: 30px;
}

.button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: 100%;
  max-width: 400px;
}

.job-button {
  width: 100%;
  padding: 15px 20px;
  font-size: 18px;
  border: none;
  border-radius: 8px;
  background-color: #409eff;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s ease;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.job-button:hover {
  background-color: #66b1ff;
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.back-link {
  margin-top: 40px;
}

.link-text {
  color: #409eff;
  text-decoration: none;
  font-size: 16px;
}

.link-text:hover {
  text-decoration: underline;
}
</style>