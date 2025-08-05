<template>
  <div class="avatar">

    <el-container>
      <el-aside width="200px" height="840px">
        <el-row>
          <el-button v-if="false" style="margin: 0px" @click="initSDK()" type="primary">
            实例化SDK
          </el-button>

          <el-button v-if="isShowCreateRecorderButton" style="margin: 0px" @click="createRecoder()" type="primary">
            创建录音器
          </el-button>

          <el-button v-if="isShowSetSDKEvenetButton" style="margin: 0px" @click="setSDKEvenet()" type="primary">
            设置SDK监听事件
          </el-button>

          <el-button v-if="isShowSetPlayerEvenetButton" style="margin: 0px" @click="setPlayerEvenet()" type="primary">
            设置播放器监听事件
          </el-button>

          <el-button v-if="isShowSetApiInfoButton" style="margin: 0px" @click="SetApiInfodialog = true" type="primary">
            SetApiInfo
          </el-button>

          <el-button v-if="isShowSetGlobalParamsButton" style="margin: 0px" @click="SetGlobalParamsdialog = true"
            type="primary">
            SetGlobalParams
          </el-button>

          <div style="position: relative; min-height: 500px;">
            <!-- 开始面试按钮：固定在右侧区域，垂直居中偏上 -->
            <el-button v-if="isShowStartButton" style="position: relative; top: 20px; left: 200px;z-index: 9999;"
              @click="start()" type="primary">

            </el-button>
            <!-- 查看报告按钮：固定在右侧区域，垂直居中偏下 -->

          </div>

          <div v-if="isShowNlpRadio">
            <el-radio v-model="nlp" :label="true">开启语义理解</el-radio>
            <el-radio v-model="nlp" :label="false">关闭语义理解</el-radio>
          </div>

          <el-input v-if="false" type="textarea" placeholder="请输入内容,包括符号在内，最大2000字符" v-model="textarea" maxlength="2000"
            show-word-limit :autosize="{ minRows: 5, maxRows: 10 }"></el-input>

          <el-input v-if="false" v-model="vc" placeholder="变声"></el-input>
          <el-input v-if="false" v-model.number="emotion" placeholder="情感系数"></el-input>

          <el-button v-if="false" style="margin: 0px" @click="writeText()" type="primary">
            文本驱动
          </el-button>

          <el-button v-if="isShowInterruptButton" style="margin: 0px" @click="interrupt()" type="primary">
            打断
          </el-button>


          <el-input v-if="false" v-model="action" placeholder="执行动作"></el-input>

          <el-button v-if="isShowStartRecordButton && !recorderbutton" style="margin: 0px" @click="startRecord()"
            type="primary">
            开启录音
          </el-button>

          <el-button v-if="isShowStopRecordButton && recorderbutton" style="margin: 0px" @click="stopRecord()"
            type="primary">
            关闭录音
          </el-button>

          <el-button v-if="isShowStopButton" style="margin: 0px" @click="stop()" type="primary">
            关闭连接
          </el-button>

          <el-button v-if="isShowDestroyButton" style="margin: 0px" @click="destroy()" type="primary">
            销毁SDK
          </el-button>
          <!-- 新增录音控制按钮 -->
          < </el-row>
            <!-- 转写结果显示 -->

      </el-aside>

      <el-main class="htmleaf-content" style="padding: 0px">
        <div class="voice-analysis min-h-screen flex flex-col">
          <!-- 导航栏 -->
          <nav class="bg-white shadow-sm sticky top-0 z-10">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div class="flex justify-between h-16">
                <div class="flex items-center">
                  <span class="text-primary font-bold text-xl">
                    <i class="fa fa-volume-up mr-2"></i>语音分析大师
                  </span>
                </div>
                <div class="flex items-center space-x-4">
                  <button id="help-btn" class="text-gray-500 hover:text-primary transition-colors"
                    @click="openHelpModal">
                    <i class="fa fa-question-circle"></i>
                  </button>
                </div>
              </div>
            </div>
          </nav>

          <!-- 主内容区 -->
          <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="text-center mb-8">
              <h1 class="text-[clamp(1.8rem,4vw,2.5rem)] font-bold text-neutral">实时语音分析</h1>
              <p class="text-gray-500 mt-2">分析你的语调、音量、语速和频率分布</p>
            </div>

            <!-- 控制面板 -->
            <div class="flex justify-center mb-8">
              <button id="start-btn"
                class="gradient-bg text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-300 flex items-center"
                @click="startAnalysis">
                <i class="fa fa-microphone mr-2"></i>
                <span>开始分析</span>
              </button>
              <button id="stop-btn"
                class="ml-4 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg shadow hover:shadow-md transform hover:-translate-y-0.5 transition-all duration-300 flex items-center opacity-50 cursor-not-allowed"
                @click="stopAnalysis" :disabled="!isAnalyzing">
                <i class="fa fa-stop mr-2"></i>
                <span>停止</span>
              </button>
            </div>

            <!-- 状态指示器 -->
            <div id="status-indicator" class="hidden text-center mb-8">
              <div class="inline-flex items-center bg-green-100 text-green-800 px-4 py-2 rounded-full">
                <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                <span>正在监听...</span>
              </div>
            </div>

            <!-- 指标卡片 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <!-- 音量卡片 -->
              <div
                class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                  <h3 class="text-lg font-semibold text-neutral">音量</h3>
                  <div class="text-gray-400">
                    <i class="fa fa-volume-up"></i>
                  </div>
                </div>
                <div class="flex items-end justify-between h-24">
                  <div id="volume-value" class="text-3xl font-bold text-primary">-∞ dB</div>
                  <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
                    <div id="volume-bar" class="h-full w-0 bg-primary transition-all duration-300"></div>
                  </div>
                </div>
                <div class="mt-2 text-xs text-gray-500">
                  <div class="flex justify-between">
                    <span>安静</span>
                    <span>适中</span>
                    <span>响亮</span>
                  </div>
                </div>
              </div>

              <!-- 音高卡片 -->
              <div
                class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                  <h3 class="text-lg font-semibold text-neutral">音高</h3>
                  <div class="text-gray-400">
                    <i class="fa fa-music"></i>
                  </div>
                </div>
                <div class="flex items-end justify-between h-24">
                  <div id="pitch-value" class="text-3xl font-bold text-secondary">- Hz</div>
                  <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
                    <div id="pitch-bar" class="h-full w-0 bg-secondary transition-all duration-300"></div>
                  </div>
                </div>
                <div class="mt-2 text-xs text-gray-500">
                  <div class="flex justify-between">
                    <span>低音</span>
                    <span>中音</span>
                    <span>高音</span>
                  </div>
                </div>
              </div>



              <!-- 语调稳定性卡片 -->
              <div
                class="bg-white rounded-xl p-6 card-shadow transform hover:-translate-y-1 transition-all duration-300">
                <div class="flex justify-between items-start mb-4">
                  <h3 class="text-lg font-semibold text-neutral">语调稳定性</h3>
                  <div class="text-gray-400">
                    <i class="fa fa-balance-scale"></i>
                  </div>
                </div>
                <div class="flex items-end justify-between h-24">
                  <div id="stability-value" class="text-3xl font-bold text-success">- %</div>
                  <div class="w-40 h-12 bg-gray-100 rounded-full overflow-hidden">
                    <div id="stability-bar" class="h-full w-0 bg-success transition-all duration-300"></div>
                  </div>
                </div>
                <div class="mt-2 text-xs text-gray-500">
                  <div class="flex justify-between">
                    <span>不稳定</span>
                    <span>适中</span>
                    <span>稳定</span>
                  </div>
                </div>
              </div>
            </div>



            <!-- 分析建议 -->
            <div id="analysis-suggestions" class="bg-white rounded-xl p-6 card-shadow hidden">
              <h3 class="text-lg font-semibold text-neutral mb-4">分析建议</h3>
              <div id="suggestions-content" class="text-gray-700">
                <!-- 建议内容将动态更新 -->
              </div>
            </div>
          </main>

          <!-- 页脚 -->
          <footer class="bg-white border-t border-gray-200 py-6">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div class="flex flex-col md:flex-row justify-between items-center">
                <div class="text-gray-500 text-sm">
                  &copy; 2023 语音分析大师 - 实时语音分析工具
                </div>
                <div class="mt-4 md:mt-0">
                  <a href="#" class="text-gray-500 hover:text-primary mx-2">
                    <i class="fa fa-github"></i>
                  </a>
                  <a href="#" class="text-gray-500 hover:text-primary mx-2">
                    <i class="fa fa-twitter"></i>
                  </a>
                  <a href="#" class="text-gray-500 hover:text-primary mx-2">
                    <i class="fa fa-linkedin"></i>
                  </a>
                </div>
              </div>
            </div>
          </footer>

          <!-- 帮助模态框 -->
          <div id="help-modal"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden">
            <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-neutral">使用帮助</h3>
                <button id="close-help" class="text-gray-400 hover:text-gray-600" @click="closeHelpModal">
                  <i class="fa fa-times"></i>
                </button>
              </div>
              <div class="text-gray-700 space-y-4">
                <div>
                  <h4 class="font-medium text-primary">如何使用</h4>
                  <p class="text-sm mt-1">点击"开始分析"按钮，授权麦克风访问权限，然后开始说话。系统将实时分析你的语音参数。</p>
                </div>
                <div>
                  <h4 class="font-medium text-primary">指标说明</h4>
                  <ul class="text-sm mt-1 list-disc list-inside space-y-1">
                    <li><span class="font-medium">音量：</span>语音的响亮程度，以分贝(dB)为单位</li>
                    <li><span class="font-medium">音高：</span>语音的高低，以赫兹(Hz)为单位</li>
                    <li><span class="font-medium">语速：</span>每分钟说的单词数</li>
                    <li><span class="font-medium">语调稳定性：</span>音高变化的平稳程度</li>
                  </ul>
                </div>
                <div>
                  <h4 class="font-medium text-primary">最佳实践</h4>
                  <p class="text-sm mt-1">在安静的环境中使用，保持麦克风距离嘴部约10-15厘米，正常语速说话以获得最准确的结果。</p>
                </div>
              </div>
              <div class="mt-6">
                <button id="close-help-btn"
                  class="w-full bg-primary text-white py-2 rounded-lg hover:bg-primary/90 transition-colors"
                  @click="closeHelpModal">
                  我知道了
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="camera-container"
          style="position: relative; width: 400px;height:400px;top: 80px; left: 500px; max-width: 640px; margin: 0 auto;">
          <video ref="video" autoplay muted
            style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);">
          </video>
          <div class="status" :textContent="status" style="position: absolute; bottom: 15px; left: 0; right: 0; text-align: center;
           background: rgba(0,0,0,0.5); color: white; padding: 8px 0; border-radius: 0 0 12px 12px;">
          </div>
          <button @click="startRecognition" :disabled="isProcessing" style="position: relative; top: 80px; left: 500px; transform: translateX(-50%);
           background: #4a90e2; color: white; border: none; padding: 12px 24px;
           border-radius: 30px; font-weight: bold; box-shadow: 0 4px 12px rgba(74,144,226,0.3);
           transition: transform 0.2s;">
            {{ isProcessing ? '分析中...' : '开始表情识别' }}
          </button>
          <!-- 结果显示区域，通过v-text绑定answer属性 -->

        </div>
        <!-- 微表情和肢体动作识别结果 -->
        <div class="result" v-text="'您的微表情和肢体动作识别结果（有延迟）：' + answer" style="position: absolute; top: 300px; left: 750px; z-index: 1000; 
         width: 300px; padding: 15px; border-radius: 10px; 
         background-color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.1);
         transition: all 0.3s ease;">
        </div>

        <!-- 语音回答识别结果 -->
        <div v-if="true" style="position: absolute; top: 400px; left: 750px; z-index: 1000; 
         width: 300px; padding: 15px; border-radius: 10px; 
         background-color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.1);
         transition: all 0.3s ease;">
          <h4 style="margin-top: 0; margin-bottom: 10px; font-weight: 600; color: #333; 
             border-bottom: 1px solid #eee; padding-bottom: 8px;">
            请检查语音识别的结果是否与您的实际回答相符
          </h4>
          <p style="margin: 0; line-height: 1.6; color: #555; min-height: 40px; 
           word-break: break-word; font-size: 15px;">
            {{ transcriptionResult || '等待语音输入...' }}
          </p>
        </div>
        <el-button @click="toggleRecording" type="primary" :class="{ 'is-recording': isRecording }"
          style="position: absolute; top: 800px; left: 909px; z-index: 1000;">
          {{ isRecording ? '再次点击停止回答' : '点击开始回答' }}
        </el-button>
        <div style="position: relative; min-height: 500px;">
          <!-- 开始面试按钮：固定在右侧区域，垂直居中偏上 -->
          <el-button v-if="isShowStartButton" style="position: relative; top: 150px; left: 700px;z-index: 9999;"
            @click="start()" type="primary">
            开始面试
          </el-button>
          <!-- 查看报告按钮：固定在右侧区域，垂直居中偏下 -->
          <el-button v-if="true" style="position: relative; top: 250px; left: 490px;"
            @click="$router.push('/yuyinfenxibaogao')" type="primary">
            面试结束请点击这里
          </el-button>
        </div>
        <div class="weather rain" id="wrapper"></div>
        <span>透明度</span><input type="range" id="opacityRange" min="0" max="1" step="0.1" value="1">
      </el-main>

      <!--SetApiInfo悬浮框-->
      <el-dialog title="初始化SDK" :visible.sync="SetApiInfodialog">
        <el-form :model="form">
          <span>此处参数均去交互平台-接口服务中获取</span>
          <el-form-item label="Appid" :label-width="formLabelWidth">
            <el-input class="widthclass" v-model="form.appid" autocomplete="off"></el-input>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="ApiKey" :label-width="formLabelWidth">
            <el-input class="widthclass" v-model="form.apikey" autocomplete="off"></el-input>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="ApiSecret" :label-width="formLabelWidth">
            <el-input class="widthclass" v-model="form.apisecret" autocomplete="off"></el-input>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="SceneId" :label-width="formLabelWidth">
            <el-input class="widthclass" v-model="form.sceneid" autocomplete="off"></el-input>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="ServerUrl" :label-width="formLabelWidth">
            <el-input class="widthclass" v-model="form.serverurl" autocomplete="off"></el-input>
            <span>必填</span>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click="SetApiInfodialog = false">取 消</el-button>
          <el-button type="primary" @click="(SetApiInfodialog = false), SetApiInfo2()">确 定</el-button>
        </div>
      </el-dialog>
      <!--SetGlobalParams悬浮框-->
      <el-dialog title="设置全局变量" :visible.sync="SetGlobalParamsdialog">
        <div style="text-align: center">
          <h3>打断模式全局设置</h3>
        </div>
        <el-form :model="setglobalparamsform" :label-width="formLabelWidth">
          <el-form-item label="视频协议">
            <el-tooltip class="item" effect="dark" content="支持webrtc/xrtc/rtmp(控制台打印视频流地址)" placement="right-start">
              <i class="el-icon-question"></i>
            </el-tooltip>
            <el-select v-model="setglobalparamsform.stream.protocol" placeholder="请选择视频流协议">
              <el-option label="xrtc" value="xrtc"></el-option>
              <el-option label="webrtc" value="webrtc"></el-option>
              <el-option label="rtmp" value="rtmp"></el-option>
            </el-select>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="透明背景">
            <el-tooltip class="item" effect="dark" content="仅支持xrtc协议" placement="right-start">
              <i class="el-icon-question"></i>
            </el-tooltip>
            <el-switch v-model="setglobalparamsform.stream.alpha"></el-switch>
          </el-form-item>
          <el-form-item label="全局交互模式">
            <el-radio-group v-model="setglobalparamsform.avatar_dispatch.interactive_mode">
              <el-radio :label="0">追加模式（信息依次播报）</el-radio>
              <el-radio :label="1">打断模式（直接播报最新）</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="形象ID">
            <el-input class="widthclass" v-model="setglobalparamsform.avatar.avatar_id" autocomplete="on"
              placeholder="到交互平台-接口服务-形象列表中获取id"></el-input>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="分辨率高">
            <el-input class="widthclass" v-model="setglobalparamsform.avatar.height" autocomplete="on"></el-input>
          </el-form-item>
          <el-form-item label="分辨率宽">
            <el-input class="widthclass" v-model="setglobalparamsform.avatar.width" autocomplete="on"></el-input>
          </el-form-item>
          <el-form-item label="音频采样率">
            <el-radio-group v-model="setglobalparamsform.avatar.audio_format">
              <el-radio :label="1">16K(传1)</el-radio>
              <el-radio :label="2">24K(传2，大部分情况默认24K即可)</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="形象裁剪" v-if="setglobalparamsform.avatar.mask_region != null">
            <el-input class="widthclass" v-model="setglobalparamsform.avatar.mask_region" autocomplete="on"
              placeholder="对形象进行裁剪[从左到右,从上到下,从右到左,从下到上]"></el-input>
          </el-form-item>
          <el-form-item label="发音人">
            <el-input class="widthclass" v-model="setglobalparamsform.tts.vcn" autocomplete="on"
              placeholder="到交互平台-接口服务-声音列表中获取id"></el-input>
            <span>必填</span>
          </el-form-item>
          <el-form-item label="情感">
            <el-input class="widthclass" v-model.number="setglobalparamsform.tts.emotion" autocomplete="on"
              placeholder="到交互平台-接口服务-声音列表中获取id"></el-input>
          </el-form-item>
          <el-form-item label="是否开启字幕">
            <el-radio-group v-model="setglobalparamsform.subtitle.subtitle">
              <el-radio :label="1">开启</el-radio>
              <el-radio :label="0">关闭</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="字体颜色">
            <el-color-picker v-model="setglobalparamsform.subtitle.font_color"></el-color-picker>
          </el-form-item>
          <el-form-item label="是否开启背景图">
            <el-radio-group v-model="setglobalparamsform.enable">
              <el-radio :label="true">开启</el-radio>
              <el-radio :label="false">关闭</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="背景图片">
            <el-radio-group v-model="setglobalparamsform.background.type">
              <el-radio label="url">URL</el-radio>
              <el-radio label="res_key">res_key(到交互平台-素材管理中获取)</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="背景数据">
            <el-input v-model="setglobalparamsform.background.data" autocomplete="on"></el-input>
          </el-form-item>
        </el-form>

        <el-form :model="form"> </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click="SetGlobalParamsdialog = false">取 消</el-button>
          <el-button type="primary" @click="(SetGlobalParamsdialog = false), SetGlobalParams()">确 定</el-button>
        </div>
      </el-dialog>
    </el-container>


  </div>

</template>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
//模块导入
import AvatarPlatform, {
  PlayerEvents,
  SDKEvents,
} from "../vm-sdk/avatar-sdk-web_3.1.1.1011/index.js";
import axios from "axios"; // 需安装 axios: npm install axios
import * as Chart from 'chart.js';


import io from 'socket.io-client';
//动态虚拟人调节透明度
document.addEventListener("DOMContentLoaded", function () {
  const div = document.getElementById('wrapper');
  const range = document.getElementById('opacityRange');

  range.addEventListener('input', function () {
    div.style.opacity = this.value;
  });
})

let avatarPlatform2 = null;
let recorder = null;
export default {
  name: "avatarComponent",
   name: 'VoiceAnalysis',
  data() {
    return {
        socket: null,
      isAnalyzing: false,
      frequencyChart: null,
      isSocketConnected: false,
      socketConnectAttempts: 0,
      maxConnectAttempts: 5,
       mediaStream: null,
      frameCount: 0,
      requests: [],
      answer: '',
      status: '',
      isProcessing: false,
      isShowInitButton: false,
      isShowCreateRecorderButton: false,
      isShowSetSDKEvenetButton: false,
      isShowSetPlayerEvenetButton: false,
      isShowSetApiInfoButton: false,
      isShowSetGlobalParamsButton: false,
      isShowStartButton: true,
      isShowWriteTextButton: true,
      isShowInterruptButton: false,
      isShowWriteCmdButton: false,
      isShowStartRecordButton: false,
      isShowStopRecordButton: false,
      isShowStopButton: false,
      isShowDestroyButton: false,

      // 控制输入框和其他元素
      isShowNlpRadio: false,
      isShowTextarea: true,
      isShowVcInput: false,
      isShowEmotionInput: false,
      isShowActionInput: false,

      // 录音按钮状态
      recorderbutton: false,// 控制实例化SDK按钮的显示状态（false为隐藏）
      SetApiInfodialog: false,
      SetGlobalParamsdialog: false,

      isShowInitButton: true,
      isRecording: false,
      mediaRecorder: null,
      audioChunks: [],
      transcriptionResult: null,
      avatarPlatform2: null,

      form: {
        appid: "7d2ebf7e",//到交互平台-接口服务中获取
        apikey: "f7c54ee54ab86f4dbe65d78a7770121c",//到交互平台-接口服务中获取
        apisecret: "ZjNhMjRhZmJmMTU0ZGFhN2Q4NTZlNjA1",//到交互平台-接口服务中获取
        sceneid: "184186341888757760",//到交互平台-接口服务中获取，即"接口服务ID"
        serverurl: "wss://avatar.cn-huadong-1.xf-yun.com/v1/interact",//接口地址，无需更改
      },
      setglobalparamsform: {
        stream: {
          protocol: "xrtc",//（必传）实时视频协议，支持webrtc/xrtc/rtmp，其中只有xrtc支持透明背景，需参数alpha传1
          fps: 25,//（非必传）视频刷新率,值越大，越流畅，取值范围0-25，默认25即可
          bitrate: 1000000,//（非必传）视频码率，值越大，越清晰，对网络要求越高，默认1000000即可
          alpha: false,//（非必传）是否开启透明背景，0关闭1开始，需配合protocol=xrtc使用
        },
        avatar: {
          avatar_id: "110117005",//（必传）授权的形象资源id，请到交互平台-接口服务-形象列表中获取
          width: 1080,//（非必传）视频分辨率宽（不是画布的宽，调整画布大小需调整名为wrapper的div宽）
          height: 1920,//（非必传）视频分辨率高（不是画布的高，调整画布大小需调整名为wrapper的div高）
          mask_region: "[0,0,1080,1920]",//（非必传）形象裁剪参数，[从左到右，从上到下，从右到左，从下到上]
          scale: 1,//（非必传）形象缩放比例，取值范围0.1-1
          move_h: 0,//（非必传）形象左右移动
          move_v: 0,//（非必传）形象上下移动
          audio_format: 1,//（非必传）音频采样率，传1即可
        },
        tts: {
          vcn: "x4_lingxiaoying_assist",//（必传）授权的声音资源id，请到交互平台-接口服务-声音列表中获取
          speed: 50,//（非必传）语速
          pitch: 50,//（非必传）语调
          volume: 100,//（非必传）音量
          emotion: 13,//（非必传）情感系数，仅带有情感能力的超拟人音色支持该能力，普通音色不支持
        },
        avatar_dispatch: {
          interactive_mode: 1,//（非必传）0追加模式，1打断模式
        },
        subtitle: {
          subtitle: 1,//（非必传）开启字幕，2D形象支持字幕，透明背景不支持字幕，3D形象不支持字幕（3D形象多为卡通形象，2D多为真人形象）
          font_color: "#FFFFFF",//（非必传）字体颜色
          font_name: "Sanji.Suxian.Simple",//（非必传）不支持自定义字体，若不想使用默认提供的
          //字体，那么可以设置asr和nlp监听事件，去获取语音识别和语义理解的文本，自己前端贴字体。
          //支持一下字体：'Sanji.Suxian.Simple','Honglei.Runninghand.Sim','Hunyuan.Gothic.Bold',
          //'Huayuan.Gothic.Regular','mainTitle'
          position_x: 100,//（非必传）设置字幕水平位置，必须配置width、height一起使用，否则字幕不显示
          position_y: 0,//（非必传）设置字幕竖向位置，必须配置width、height一起使用，否则字幕不显示
          font_size: 10,//（非必传）设置字幕字体大小，取值范围：1-10
          width: 100,//（非必传）设置字幕宽
          height: 100,//（非必传）设置字幕高
        },
        enable: false,//demo中用来控制是否开启背景的参数，与虚拟人参数无关
        background: {
          type: "res_key",//（非必传）上传图片的类型，支持url以及res_key。（res_key请到交互平台-素材管理-背景中上传获取)
          data: "22SLM2teIw+aqR6Xsm2JbH6Ng310kDam2NiCY/RQ9n6dw47gMO+7gGUJfWWfkqD3IxsU/HMK1uJTTxxF2llcKSM4dlSdBy0Piag/DndHocqs32kTOwXUw6lkyggYQBXF0uwTv9jVFm1ZjZgSehV3kpx5RTvizZ9MqEI8lotCRvokC9HLI0pGfKtSmlKgCKL+OUoc9QI5HW3wLtYbLersumd4UCKEPk/uWAdKEh4ntSJiW2km8waGFsg/VSNFj5vaDK3LC4PxfsRvi1a2veZW7JUs/VOleE9wwgTH+A/oqPPcyksBY7aQ4TxYjvS9Qj9LtXkvOwttQMgPGwoxlqBEBhR/xLUwmecHkHzgjACFtxE=",
          //（非必传）图片的值，当type='url'时,data='http://xxx/xxx.png'，当type='res_key'时，data='res_key值'（res_key请到交互平台-素材管理-背景中上传获取)
        }
      },
      formLabelWidth: "120px",
      textarea: "",
      vc: "",
      recorderbutton: false,
      nlp: false,
      emotion: 0,
      action: "A_RH_hello_O",
      volume: 100,
    };
  },
  mounted() {
    
    this.initRecorder(); // 初始化录音功能
    localStorage.setItem('transcribeCount', '0');
    console.log('【面试系统】已初始化回答计数：transcribeCount = 0');
    this.initCamera();
    this.initSocket();
    this.initFrequencyChart();
    this.setupEventListeners();
  },
  beforeDestroy() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    if (this.frequencyChart) {
      this.frequencyChart.destroy();
      this.frequencyChart = null;
    }
  },
  methods: {
    initSocket() {
      this.socket = io.connect('http://127.0.0.1:3000', {
        transports: ['polling', 'websocket'],
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: this.maxConnectAttempts,
        reconnectionDelay: 1000
      });
      
      this.socket.on('connect', () => {
        this.isSocketConnected = true;
        this.socketConnectAttempts = 0;
        console.log('SocketIO连接成功');
      });
      
      this.socket.on('connect_error', (error) => {
        this.isSocketConnected = false;
        console.error('SocketIO连接错误:', error);
        alert(`SocketIO连接失败，请检查后端服务器是否运行在3000端口\n错误详情: ${error.message}`);
      });
      
      this.socket.on('connect_failed', () => {
        this.isSocketConnected = false;
        console.error('SocketIO连接失败，无法到达服务器');
        alert('无法连接到后端服务器，请确认服务器已启动且运行在3000端口');
      });
      
      this.socket.on('update_metrics', (data) => {
        this.updateVolume(data.volume);
        this.updatePitch(data.pitch);
        if (data.wpm) this.updateWpm(data.wpm);
        this.updateStability(data.stability);
        if (data.frequency_data) this.updateFrequencyChart(data.frequency_data);
        
        this.updateSuggestions({
          volume: data.volume,
          pitch: data.pitch,
          wpm: data.wpm || 0,
          stability: data.stability
        });
      });
    },
    
    initFrequencyChart() {
      const ctx = document.getElementById('frequency-chart').getContext('2d');
      
      this.frequencyChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: Array(100).fill(''),
          datasets: [{
            label: '频率分布',
            data: Array(100).fill(0),
            borderColor: '#165DFF',
            backgroundColor: 'rgba(22, 93, 255, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: {
                display: true,
                text: '频率 (Hz)'
              },
              ticks: {
                callback: function(value, index, values) {
                  const labels = ['0', '500', '1000', '1500', '2000', '2500'];
                  const positions = [0, 20, 40, 60, 80, 99];
                  if (positions.includes(index)) {
                    return labels[positions.indexOf(index)];
                  }
                  return '';
                }
              }
            },
            y: {
              title: {
                display: true,
                text: '能量'
              },
              beginAtZero: true
            }
          },
          animation: {
            duration: 0
          }
        }
      });
    },
    
    updateVolume(volume) {
      const volumeValue = document.getElementById('volume-value');
      const volumeBar = document.getElementById('volume-bar');
      
      const displayVolume = Math.max(-60, Math.min(0, volume));
      const percentage = 100 - (Math.abs(displayVolume) / 60) * 100;
      
      volumeValue.textContent = `${displayVolume.toFixed(1)} dB`;
      volumeBar.style.width = `${percentage}%`;
      
      if (displayVolume > -20) {
        volumeBar.className = 'h-full w-full bg-danger transition-all duration-300';
      } else if (displayVolume > -40) {
        volumeBar.className = 'h-full w-full bg-warning transition-all duration-300';
      } else {
        volumeBar.className = 'h-full w-full bg-primary transition-all duration-300';
      }
    },
    
    updatePitch(pitch) {
      const pitchValue = document.getElementById('pitch-value');
      const pitchBar = document.getElementById('pitch-bar');
      
      const displayPitch = Math.max(80, Math.min(500, pitch));
      const percentage = ((displayPitch - 80) / 420) * 100;
      
      pitchValue.textContent = `${Math.round(pitch)} Hz`;
      pitchBar.style.width = `${percentage}%`;
    },
    
    updateWpm(wpm) {
      const wpmValue = document.getElementById('wpm-value');
      const wpmBar = document.getElementById('wpm-bar');
      
      const displayWpm = Math.max(60, Math.min(200, wpm));
      const percentage = ((displayWpm - 60) / 140) * 100;
      
      wpmValue.textContent = `${Math.round(wpm)} 词/分钟`;
      wpmBar.style.width = `${percentage}%`;
      
      if (displayWpm > 160) {
        wpmBar.className = 'h-full w-full bg-danger transition-all duration-300';
      } else if (displayWpm > 120) {
        wpmBar.className = 'h-full w-full bg-warning transition-all duration-300';
      } else {
        wpmBar.className = 'h-full w-full bg-accent transition-all duration-300';
      }
    },
    
    updateStability(stability) {
      const stabilityValue = document.getElementById('stability-value');
      const stabilityBar = document.getElementById('stability-bar');
      
      stabilityValue.textContent = `${Math.round(stability)} %`;
      stabilityBar.style.width = `${stability}%`;
      
      if (stability < 40) {
        stabilityBar.className = 'h-full w-full bg-danger transition-all duration-300';
      } else if (stability < 70) {
        stabilityBar.className = 'h-full w-full bg-warning transition-all duration-300';
      } else {
        stabilityBar.className = 'h-full w-full bg-success transition-all duration-300';
      }
    },
    
    updateFrequencyChart(frequencyData) {
      if (!frequencyData || !frequencyData.x || !frequencyData.y) {
        console.warn("频率数据格式错误，缺少x或y属性");
        return;
      }
      
      if (!this.frequencyChart) return;
      
      const x = frequencyData.x;
      const y = frequencyData.y;
      
      if (x.length < 2 || y.length < 2) {
        console.warn("频率数据点数不足，无法绘制图表");
        return;
      }
      
      const interpolate = (xValues, yValues, targetX) => {
        const n = xValues.length;
        if (targetX <= xValues[0]) return yValues[0];
        if (targetX >= xValues[n-1]) return yValues[n-1];
        
        for (let i = 0; i < n-1; i++) {
          if (xValues[i] <= targetX && targetX <= xValues[i+1]) {
            const slope = (yValues[i+1] - yValues[i]) / (xValues[i+1] - xValues[i]);
            return yValues[i] + slope * (targetX - xValues[i]);
          }
        }
        return 0;
      };
      
      const maxFreq = 2500;
      const targetPoints = 100;
      const newX = Array(targetPoints).fill().map((_, i) => i * maxFreq / (targetPoints - 1));
      const newY = newX.map(xVal => interpolate(x, y, xVal));
      
      this.frequencyChart.data.labels = newX;
      this.frequencyChart.data.datasets[0].data = newY;
      this.frequencyChart.update('none');
    },
    
    updateSuggestions(metrics) {
      const { volume, pitch, wpm, stability } = metrics;
      let suggestions = [];
      
      if (volume < -50) {
        suggestions.push("您的音量偏低，可能需要提高说话音量以便更好地表达。");
      } else if (volume > -20) {
        suggestions.push("您的音量偏高，可能会让人感到压迫，适当降低音量可能会更舒适。");
      }
      
      if (pitch < 100 && pitch > 0) {
        suggestions.push("您的音高偏低，适当提高音调可能会让您的表达更有活力。");
      } else if (pitch > 300) {
        suggestions.push("您的音高偏高，适当降低音调可能会让您的表达更稳重。");
      }
      
      if (wpm > 160) {
        suggestions.push("您的语速偏快，可能会让听众难以跟上，请适当放慢语速。");
      } else if (wpm < 100 && wpm > 0) {
        suggestions.push("您的语速偏慢，适当加快语速可能会让您的表达更流畅。");
      }
      
      if (stability < 40) {
        suggestions.push("您的语调变化较大，适当保持稳定的语调可能会增加表达的可信度。");
      } else if (stability > 80) {
        suggestions.push("您的语调较为平稳，适当增加一些变化可能会让您的表达更生动。");
      }
      
      const suggestionsContent = document.getElementById('suggestions-content');
      const analysisSuggestions = document.getElementById('analysis-suggestions');
      
      if (suggestions.length > 0) {
        analysisSuggestions.classList.remove('hidden');
        suggestionsContent.innerHTML = suggestions.map(s => `<p class="mb-2"><i class="fa fa-lightbulb-o text-primary mr-2"></i>${s}</p>`).join('');
      } else {
        analysisSuggestions.classList.add('hidden');
      }
    },
    
    setupEventListeners() {
      const startBtn = document.getElementById('start-btn');
      const stopBtn = document.getElementById('stop-btn');
      const statusIndicator = document.getElementById('status-indicator');
      
      startBtn.addEventListener('click', () => {
        this.startAnalysis();
      });
      
      stopBtn.addEventListener('click', () => {
        this.stopAnalysis();
      });
    },
    
    startAnalysis() {
      navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(stream => {
          document.getElementById('start-btn').classList.add('opacity-50', 'cursor-not-allowed');
          document.getElementById('start-btn').disabled = true;
          document.getElementById('stop-btn').classList.remove('opacity-50', 'cursor-not-allowed');
          document.getElementById('stop-btn').disabled = false;
          document.getElementById('status-indicator').classList.remove('hidden');
          
          this.isAnalyzing = true;
          if (this.isSocketConnected) {
            this.socket.emit('start_recording');
          } else {
            console.warn('未连接到语音分析服务器，无法开始录音');
          }
          
          stream.getTracks().forEach(track => track.stop());
        })
        .catch(err => {
          alert('无法访问麦克风，请确保您已授予麦克风权限。');
          console.error('麦克风权限错误:', err);
        });
    },
    
    stopAnalysis() {
      document.getElementById('start-btn').classList.remove('opacity-50', 'cursor-not-allowed');
      document.getElementById('start-btn').disabled = false;
      document.getElementById('stop-btn').classList.add('opacity-50', 'cursor-not-allowed');
      document.getElementById('stop-btn').disabled = true;
      document.getElementById('status-indicator').classList.add('hidden');
      
      this.isAnalyzing = false;
      if (this.isSocketConnected) {
        this.socket.emit('stop_recording');
      }
    },
    
    openHelpModal() {
      document.getElementById('help-modal').classList.remove('hidden');
    },
    
    closeHelpModal() {
      document.getElementById('help-modal').classList.add('hidden');
    },
    // 初始化摄像头
    async initCamera() {
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
        this.$refs.video.srcObject = this.mediaStream;
      } catch (err) {
        console.error("摄像头访问失败:", err);
        alert('无法访问摄像头，请确保已授予权限');
      }
    },// 拍摄并发送图片
    captureAndSend() {
      const canvas = document.createElement('canvas');
      canvas.width = this.$refs.video.videoWidth;
      canvas.height = this.$refs.video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(this.$refs.video, 0, 0, canvas.width, canvas.height);
      
      // 转换为base64
      const imageBase64 = canvas.toDataURL('image/jpeg').split(',')[1];
      const question = '图片中的人是什么表情，什么肢体动作。用两个字回复我表情，用两个字回复我动作';
      
      // 发送请求
      fetch('https://117.72.49.76/image-understanding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_base64: imageBase64,
          question: question
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'processing') {
          this.requests.push(data.request_id);
          this.pollResult(data.request_id);
        }
      });
    },
    // 开始识别流程
    startRecognition() {
      if (!this.mediaStream) {
        alert('摄像头尚未初始化');
        return;
      }
      
      this.isProcessing = true;
      this.answer = '正在分析表情...';
      this.frameCount = 0;
      this.requests = [];
      
      const interval = setInterval(() => {
        this.captureAndSend();
        this.frameCount++;
        this.status = `已拍摄 ${this.frameCount}/60 帧`;
        
        if (this.frameCount >= 60) {
          clearInterval(interval);
          this.status = '等待服务器结果...';
          setTimeout(() => {
            this.isProcessing = false;
          }, 5000);
        }
      }, 1000);
    },// 轮询结果
    pollResult(request_id) {
  fetch(`https://117.72.49.76/get-result/${request_id}`)
    .then(response => response.json())
    .then(result => {
      if (result.status === 'completed') {
        // 实时更新结果
        this.answer = '答：' + result.content;
        
        // 构建当前识别结果对象
        const currentResult = {
          content: result.content,
          timestamp: new Date().toISOString(),
          requestId: request_id
        };
        
        // 更新历史记录
        this.updateFaceHistory(currentResult);
        
        // 从请求列表中移除
        this.requests = this.requests.filter(id => id !== request_id);
        if (this.requests.length === 0) {
          this.status = '分析完成';
        }
      } else if (result.status === 'processing') {
        setTimeout(() => this.pollResult(request_id), 1000);
      }
    })
    .catch(error => {
      console.error('获取结果失败:', error);
    });
},

// 更新面部识别历史记录
updateFaceHistory(newResult) {
  try {
    // 获取现有历史记录
    let faceHistory = JSON.parse(localStorage.getItem('face') || '[]');
    
    // 添加新结果到历史记录
    faceHistory.push(newResult);
    
    // 限制历史记录长度（可选）
    const MAX_HISTORY_LENGTH = 50;
    if (faceHistory.length > MAX_HISTORY_LENGTH) {
      faceHistory = faceHistory.slice(-MAX_HISTORY_LENGTH);
    }
    
    // 保存更新后的历史记录
    localStorage.setItem('face', JSON.stringify(faceHistory));
    
    console.log('面部识别历史已更新:', faceHistory.length, '条记录');
  } catch (error) {
    console.error('更新面部识别历史失败:', error);
  }
},
    yuyinfenxi() {
      this.$router.push('/yuyinfenxibaogao');
    },
    async submitArticle() {
    try {
      // 从localStorage获取数据并直接发送请求
      const response = await fetch(
        `https://tender-secure-bluegill.ngrok-free.app/api/submitBlogs/${localStorage.getItem('username')}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            title: localStorage.getItem('firstQuestion'),
            content: localStorage.getItem('firstResult')
          })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        
        
        
      } else {
        
      }
    } catch (error) {
      console.error('请求出错:', error);
     
    }
  },
    toQuestion() {
      this.$router.push("/question");
    },
    initRecorder() {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error("浏览器不支持录音功能");
        return;
      }
    },

    toggleRecording() {
      this.startSavingMetrics();
      this.startRecognition();
      
      if (this.isRecording) {
        this.stopRecording();
      } else {
        this.startRecording();
      }
    },

    startRecording() {
      this.isRecording = true;
      this.audioChunks = [];
      this.transcriptionResult = null;

      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          this.mediaRecorder = new MediaRecorder(stream);
          this.mediaRecorder.ondataavailable = (e) => {
            this.audioChunks.push(e.data);
          };
          this.mediaRecorder.onstop = () => {
            const audioBlob = new Blob(this.audioChunks, { type: "audio/wav" });
            this.sendToTranscribe(audioBlob);
            stream.getTracks().forEach(track => track.stop());
          };
          this.mediaRecorder.start();
        })
        .catch(error => {
          console.error("录音失败:", error);
          this.isRecording = false;
        });
    },

    stopRecording() {
      this.isRecording = false;
      this.mediaRecorder?.stop();
      this.mediaRecorder = null;
    },

    async sendToTranscribe(audioBlob) {
      const formData = new FormData();
      const file = new File([audioBlob], "recording.wav", { type: "audio/wav" });
      formData.append("file", file);

      try {
        const response = await axios.post(
          "https://117.72.49.76:443/api/transcribe",
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );

        if (response.data.status === "success") {
          this.transcriptionResult = response.data.text;

          // 获取当前转写次数（初始为0）
          let transcribeCount = parseInt(localStorage.getItem("transcribeCount") || "0");
          transcribeCount++;

          // 根据次数存储结果
          if (transcribeCount === 1) {
            localStorage.setItem("firstResult", this.transcriptionResult);
            console.log('第一次转写成功，'+localStorage.getItem("firstResult"));
            this.submitArticle();
          } else if (transcribeCount === 2) {
            localStorage.setItem("secondResult", this.transcriptionResult);
            console.log('第二次转写成功，'+localStorage.getItem("secondResult"));
          }
          if(transcribeCount === 3){
            localStorage.setItem("thirdResult", this.transcriptionResult);
            console.log('3第三次转写成功，'+localStorage.getItem("thirdResult"));
          }
          if(transcribeCount === 4){
            localStorage.setItem("fourthResult", this.transcriptionResult);
            console.log('4第四次转写成功，'+localStorage.getItem("fourthResult"));
          }
          if(transcribeCount === 5){
            localStorage.setItem("fifthResult", this.transcriptionResult);
            console.log('5第五次转写成功，'+localStorage.getItem("fifthResult"));
          }

          // 更新计数器
          localStorage.setItem("transcribeCount", transcribeCount.toString());
          console.log(`第${transcribeCount}次转写成功`);
        } else {
          console.error("转写失败:", response.data.error);
          this.transcriptionResult = "转写失败，请重试";
        }
      } catch (error) {
        console.error("网络错误:", error);
        this.transcriptionResult = "网络请求失败";
      }
    },
    initSDK() {
      //必须先实例化SDK，再去调用其挂载的方法
      avatarPlatform2 = new AvatarPlatform();
      if (avatarPlatform2 != null) {
        this.open2("实例化SDK成功");
      }
    },
    createRecoder() {
      if (avatarPlatform2 != null) {
        recorder = avatarPlatform2.createRecorder();
        this.open2("创建录音器成功");
      } else {
        alert("请实例化SDK实例");
      }
    },
    setSDKEvenet() {
      //绑定SDK事件
      if (avatarPlatform2 != null) {
        avatarPlatform2
          .on(SDKEvents.connected, function (initResp) {
            console.log("SDKEvent.connect:initResp:", initResp);
          })
          .on(SDKEvents.stream_start, function () {
            console.log("stream_start");
          })
          .on(SDKEvents.disconnected, function (err) {
            console.log("SDKEvent.disconnected:", err);
            if (err) {
              // 因为异常 而导致的断开！ 此处可以进行 提示通知等
              console.error("ws link disconnected because of Error");
              console.error(e.code, e.message, e.name, e.stack);
            }
          })
          .on(SDKEvents.nlp, function (nlpData) {
            console.log("语义理解内容nlp:", nlpData);
          })
          .on(SDKEvents.frame_start, function (frame_start) {
            console.log(
              "推流开始（可以看作一段文本开始播报时间点）frame_start:",
              frame_start
            );
          })
          .on(SDKEvents.frame_stop, function (frame_stop) {
            console.log(
              "推流结束（可以看作一段文本结束播报时间点）frame_stop:",
              frame_stop
            );
          })
          .on(SDKEvents.error, function (error) {
            console.log("错误信息error:", error);
          })
          .on(SDKEvents.connected, function () {
            console.log("connected");
          })
          .on(SDKEvents.asr, function (asrData) {
            console.log("语音识别数据asr:", asrData);
          })
          .on(SDKEvents.tts_duration, function (ttsData) {
            console.log("语音合成用时tts：", ttsData);
          })
          .on(SDKEvents.subtitle_info, function (subtitleData) {
            console.log("subtitleData：", subtitleData);
          })
          .on(SDKEvents.action_start, function (action_start) {
            console.log(
              "动作推流开始（可以看作动作开始时间节点）action_start:",
              action_start
            );
          })
          .on(SDKEvents.action_stop, function (action_stop) {
            console.log(
              "动作推流结束（可以看作动作结束时间点）action_stop：",
              action_stop
            );
          });
        this.open2("监听SDK事件成功");
      } else {
        alert("请先实例化SDK")
      }
    },
    setPlayerEvenet() {
      if (avatarPlatform2 != null) {
        //绑定播放器事件
        const player = avatarPlatform2.createPlayer();
        player
          .on(PlayerEvents.play, function () {
            console.log("paly");
          })
          .on(PlayerEvents.playing, function () {
            console.log("playing");
          })
          .on(PlayerEvents.waiting, function () {
            console.log("waiting");
          })
          .on(PlayerEvents.stop, function () {
            console.log("stop");
          })
          .on(PlayerEvents.playNotAllowed, function () {
            console.log(
              "playNotAllowed：触发了游览器限制自动播放策略，播放前必须与游览器产生交互（例如点击页面或者dom组件），触发该事件后调用avatarPlatform2.player.resume()方法来接触限制"
            );
            player.resume();
          });
        this.open2("监听播放器事件成功");
      } else {
        alert("请先实例化SDK")
      }
    },
    SetApiInfo2() {
      if (avatarPlatform2 == null) {
        alert("请先实例化SDK");
      } else {
        console.log("设置setApiInfo");
        const params = {
          appId: this.form.appid,
          apiKey: this.form.apikey,
          apiSecret: this.form.apisecret,
          serverUrl: this.form.serverurl,
          sceneId: this.form.sceneid,
        };
        console.log("初始化SDK信息：", params);
        //初始化SDK
        avatarPlatform2.setApiInfo(params);
        this.open2("初始化SDK成功");
      }
    },
    SetGlobalParams() {
      if (avatarPlatform2 != null) {
        let params = Object.assign({}, this.setglobalparamsform);
        console.log("this.setglobalparamsform.stream.alpha", this.setglobalparamsform.stream.alpha)
        if (this.setglobalparamsform.enable == false) {
          delete params.background;
          delete params.enable;
        }
        console.log("this.setglobalparamsform", this.setglobalparamsform)
        if (this.setglobalparamsform.stream.alpha == true) {
          console.log("设置alpha=1")
          params.stream.alpha = 1
        } else {
          console.log("设置alpha=0")
          params.stream.alpha = 0
        }
        console.log("设置的全局变量为：", params);
        avatarPlatform2.setGlobalParams(params);
        this.open2("准备好了吗，马上开始面试")
      } else {
        alert("请先实例化SDK");
      }
    },
    async start() {
      console.log("1");
      this.initSDK();
      console.log("2");
      this.createRecoder();
      this.setSDKEvenet();
      this.setPlayerEvenet();
      this.SetApiInfo2();
      this.SetGlobalParams();

      // 先启动SDK连接，等待连接成功
      if (avatarPlatform2 != null) {
        try {
          await avatarPlatform2.start({ wrapper: document.querySelector("#wrapper") });
          console.log("SDK启动成功，3秒后发送问候语");

          // 3秒后执行writeText
          setTimeout(() => {
            this.writeText();
          }, 10000);

        } catch (e) {
          console.error("SDK启动失败:", e);
          alert("SDK启动失败，请检查配置");
        }
      } else {
        alert("请先实例化SDK");
      }
    },
    writeText() {
      if (avatarPlatform2 != null) {
        // 初始调用 - 问候语
        let text = `你好，${localStorage.getItem("username") || "候选人"}，欢迎面试${localStorage.getItem("career") || "相关岗位"}。接下来将进行面试环节，共有五道题目，涉及专业知识水平、技能匹配度、语言表达能力、逻辑思维能力和创新能力五个维度。每道题目间隔60秒，请认真思考后回答。`;

        this.sendTextToAvatar(text);

        // 设置30秒后自动发送第一道题
        setTimeout(() => {
          let career = localStorage.getItem("career");
          text = `请详细阐述您对${career}领域中核心概念和技术的理解，以及您在实际项目中如何应用这些知识解决问题。`;
          localStorage.setItem("firstQuestion", text);
          this.sendTextToAvatar(text);
        }, 30000);
        // 设置90秒后自动发送第二道题
        setTimeout(() => {
          let career = localStorage.getItem("career");
          text = `在${career}岗位上，您认为哪些关键技能是必不可少的？请举例说明您在这些技能方面的掌握程度和实际应用经验。`;
          localStorage.setItem("secondQuestion", text);
          this.sendTextToAvatar(text);
        }, 90000);
        // 设置150秒后自动发送第三道题
        setTimeout(() => {
          let career = localStorage.getItem("career");
          text = `请描述一次您需要向非技术团队成员清晰解释${career}相关复杂技术概念的经历。您采用了什么方法确保对方理解？`;
          localStorage.setItem("thirdQuestion", text);
          this.sendTextToAvatar(text);
        }, 150000);
        // 设置210秒后自动发送第四道题
        setTimeout(() => {
          let career = localStorage.getItem("career");
          text = `在${career}工作中，当面对一个复杂问题时，您的分析和解决问题的逻辑步骤是什么？请分享一个具体案例。`;
          localStorage.setItem("fourthQuestion", text);
          this.sendTextToAvatar(text);
        }, 210000);
        // 设置270秒后自动发送第五道题
        setTimeout(() => {
          let career = localStorage.getItem("career");
          text = `请分享一个您在${career}相关项目中提出创新解决方案的经历。您是如何发现问题并提出新颖的解决思路的？`;
          localStorage.setItem("fifthQuestion", text);
          this.sendTextToAvatar(text);
        }, 270000);
      } else {
        alert("请先实例化SDK")
      }
    },

    sendTextToAvatar(text) {
      if (text) {
        const options = {
          nlp: this.nlp,
          tts: {
            volume: 100,
            ...(this.vc ? { vcn: this.vc, emotion: this.emotion } : {})
          }
        };
        avatarPlatform2.writeText(text, options);
      } else {
        alert("内容不许为空");
      }
    },
    writeCmd() {
      avatarPlatform2.writeCmd("action", this.action);
    },
    interrupt() {
      if (avatarPlatform2 != null) {
        avatarPlatform2.interrupt();
      } else {
        alert("请先实例化SDK")
      }
    },
    startRecord() {
      if (avatarPlatform2 != null) {
        avatarPlatform2.recorder.startRecord(0, () => {
          console.warn('STOPED RECORDER')
        }, {
          nlp: true,
          avatar_dispatch: {
            interactive_mode: 0//交互模式（追加或打断）
          }
        });
        //关闭录音按钮显示
        this.recorderbutton = true;
      } else {
        alert("请先实例化SDK")
      }
    },
    stopRecord() {
      if (avatarPlatform2 != null) {
        avatarPlatform2.recorder.stopRecord();
        //开启录音按钮显示
        this.recorderbutton = false;
      } else {
        alert("请先实例化SDK")
      }
    },
    stop() {
      if (avatarPlatform2 != null) {
        avatarPlatform2.stop();
      } else {
        alert("请先实例化SDK")
      }
    },
    destroy() {
      if (avatarPlatform2 != null) {
        //销毁SDK示例，内部包含stop协议，重启需重新示例化avatarPlatform实例
        avatarPlatform2.destroy();
        avatarPlatform2 = null;
      } else {
        alert("请先实例化SDK")
      }
    },
    open2(text) {
      this.$message({
        message: text,
        type: "success",
      });
    },
  },

  beforeDestroy() {
    //关闭页面时调用stop协议，确保链接断开，释放资源
    if (avatarPlatform2) {
      avatarPlatform2.stop();
    }
  }
};
</script>

<style scoped>
* {
  margin: 0px;
  padding: 0px;
  box-sizing: border-box;
  border: none;
}

.el-button {
  width: 200px;
  margin: 0px;
}

#wrapper {
  height: 800px;
  width: 600px;
}

.error {
  border-block-color: red;
}

.widthclass {
  width: 400px;
}

span {
  color: red;
}

#wrapper {
  position: fixed;
  top: 200px;
  left: 30%;
  transform: translateX(-50%);
  z-index: 999;
}

.el-aside {
  overflow: hidden;
}

.el-aside::-webkit-scrollbar {
  display: none;
}

.htmleaf-content>span:nth-of-type(1) {
  display: none;
}

#opacityRange {
  display: none !important;
}

/* 用属性选择器定位父元素（确保唯一性） */
div[data-v-2eee1256] {
  overflow: hidden;
  /* 若需要，可加高度/宽度限制，比如 height: 100%; width: 100%; */
}
</style>