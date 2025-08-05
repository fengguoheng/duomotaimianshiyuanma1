// vue.config.js
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false,
  publicPath: process.env.NODE_ENV === 'production' ? '/mianshi/' : '/',
  devServer: {
    
    allowedHosts: 'all',
    port: 8081,
    // 本地开发服务器仍使用HTTP（因为ngrok在前端处理HTTPS）
    https: false,
    
  }
})