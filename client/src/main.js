import Vue from "vue";
import App from "./App.vue";
import router from "./router";
// 引入Vant UI库（用于注册van-button等组件）
import Vant from 'vant';
import 'vant/lib/index.css';
// 引入ElementUI（已有的UI库）
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';

// 导入其他SDK（按需启用）
// import AvatarPlatform from "./vm-sdk/avatar-sdk-web_3.0.3.1009/index.js";

// 导入样式（按需启用）
// import './css/main.css'
// import './css/demo.css'
// import './css/xiaxue/default.css'
// import './css/xiaxue/normalize.css'
// import './css/xiaxue/weather.css'

Vue.config.productionTip = false;

// 注册UI库
Vue.use(ElementUI);
Vue.use(Vant); // 注册Vant组件，解决van-*组件未识别问题

// 挂载SDK到Vue原型（按需启用）
// Vue.prototype.$AvatarPlatform = AvatarPlatform;

new Vue({
  router,
  el: '#app',
  render: (h) => h(App),
}).$mount("#app");
