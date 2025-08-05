import Vue from "vue";
import VueRouter from "vue-router";
import XrtcPlayer from "../views/XrtcPlayer.vue";
import AvatarView from "../views/avatardemo.vue";

Vue.use(VueRouter);

const routes = [
  {path : "/xunfeiyuyinhuida",
  name:"xunfeiyuyinhuida",
  component:()=>import("../views/讯飞语音回答.vue"),
  },
  {path : "/xunirenduihuapost",
  name:"xunirenduihuapost",
  component:()=>import("../views/虚拟人对话post.vue"),
  },
  {path :"/yuyinhuida",
  name:"yuyinhuida",
  component:()=>import("../views/语音回答.vue"),
  },
  {path :"/xunirenduihua",
  name:"xunirenduihua",
  component:()=>import("../views/虚拟人对话.vue"),
  },
  {path:"/wenziduihua",
  name:"wenziduihua",
  component:()=>import("../views/文字对话.vue"),
  },
  {path :"/about",
  name:"about",
  component:()=>import("../views/关于我们.vue"),
  },
  {path :"/qianduanyudiao",
    name:"qianduanyudiao",
    component:()=>import("../views/前端语调.vue"),

  },
  {path :"/wodetiquyudiaofenxi",
    name:"wodetiquyudiaofenxi",
    component:()=>import("../views/我的提取语调分析.vue"),
  },
  {path :"/zhiyouyudiaofenxi",
  name:"zhiyouyudiaofenxi",
  component:()=>import("../views/只有语调分析.vue"),
  },
  {
    path :"/tiquyudiaozhibiao",
    name:"tiquyudiaozhibiao",
    component:()=>import("../views/提取语调指标.vue"),
  },
  {
    path :"/biaoqingshibiebaogao",
    name:"biaoqingshibiebaogao",
    component:()=>import("../views/表情识别报告.vue"),
  },
  {path :"/yuyinfenxibaogao",
    name:"yuyinfenxibaogao",
    component:()=>import("../views/语音分析报告.vue"),

  },
  {path :"/tijiaotuxiang",
    name:"tijiaotuxiang",
    component:()=>import("../views/三道题提交图像.vue"),
  },
  {path :"/tijiaojianlishengchengwenti",
    name:"tijiaojianlishengchengwenti",
    component:()=>import("../views/提交简历生成问题.vue"),
  },
  {
    path: "/jianliwenbenleida",
    name:"jianliwenbenleida",
    component:()=>import("../views/无用简历分析文本和雷达显示.vue"),
  },
  {path :"/jianlijieguo",
  name:"jianlijieguo",
  component:()=>import("../views/简历分析结果展示.vue"),
  },
  {path :"/interview",
  name:"interview",
  component:()=>import("../views/模拟面试.vue"),
  },
  {
    path:"/home",
    name:"home",
    component:()=>import("../views/首页.vue"),
  },
  {
    path:"/personal",
    name:"personal",
    component:()=>import("../views/个人主页.vue"),
  },
  {path:"/register",
  name:"register",
  component:()=>import("../views/注册.vue"),
  meta: {
    hideNav: true // 标记为隐藏导航栏
  },
  },
  {
    path: "/bishileidatu",
    name: "bishileidatu",
    component: () => import("../views/笔试能力雷达图.vue"),
  },
  { 
    path: "/",
    name: "login",
    component: () => import("../views/登录.vue"),
     meta: {
      hideNav: true // 标记为隐藏导航栏
    }
  },
  {
    path: "/jianlifenxi",
    name: "进行简历分析",
    component: () => import("../views/进行简历分析.vue"),
  },
  {
    path: "/mianshi",
    name: "avatar",
    component: AvatarView,
  },
  {
    path:"/player",
    name:"xrtcplayer",
    component:XrtcPlayer,
  },
  {
    path:"/three",
    name:"question",
    component:()=>import("../views/三道题.vue"),
  }
];

const router = new VueRouter({
  routes,
});

export default router;
