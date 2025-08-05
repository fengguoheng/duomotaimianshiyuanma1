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
          <!-- 语音分析控制按钮 
          <el-button v-if="true" style="margin: 0px" @click="toggleVoiceAnalysis()" type="primary">
            {{ isAnalyzing ? '停止分析' : '开始语音分析' }}
          </el-button>
          -->
        </el-row>
        <!-- 转写结果显示 -->
      </el-aside>

      <el-main class="htmleaf-content" style="padding: 0px">
        <!--
        <div style="position: relative; width: 400px;height:400px;top: 80px; left: 400px; max-width: 640px; "><el-button  v-if="true"  @click="toggleVoiceAnalysis()" type="primary">
            {{ isAnalyzing ? '停止分析' : '开始语音分析' }}
          </el-button></div>
        -->
        <div class="camera-container"
          style="position: absolute; width: 400px;height:400px;top: 200px; left: 1200px; max-width: 640px; margin: 0 auto;">
          <video ref="video" autoplay muted
            style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);">
          </video>
          <div class="status" :textContent="status"
            style="position: absolute; bottom: 15px; left: 0; right: 0; text-align: center; background: rgba(0,0,0,0.5); color: white; padding: 8px 0; border-radius: 0 0 12px 12px;">
          </div>

        </div>
        <!-- 微表情和肢体语言识别结果 -->
        <div class="result" v-text="'您的微表情和肢体语言识别结果（每30秒识别一次）：' + answer"
          style="position: absolute; top: 200px; left: 750px; z-index: 1000; width: 300px; padding: 15px; border-radius: 10px; background-color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.1); transition: all 0.3s ease;">
        </div>

        <!-- 语音回答识别结果 -->
        <div v-if="true"
          style="position: absolute; top: 700px; left: 750px; z-index: 1000; width: 300px; padding: 15px; border-radius: 10px; background-color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.1); transition: all 0.3s ease;">
          <h4
            style="margin-top: 0; margin-bottom: 10px; font-weight: 600; color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px;">
            语音转写结果（转写完成后，请检查是否与您的实际回答一致）
          </h4>
          <p
            style="margin: 0; line-height: 1.6; color: #555; min-height: 40px; word-break: break-word; font-size: 15px;">
            {{ transcriptionResult || '' }}
          </p>
        </div>

        <!-- 语音分析指标显示 -->
        <div class="audio-analysis-container"
          style="position: absolute; top: 300px; left: 750px; z-index: 1000;height:350px; width: 300px; padding: 15px; border-radius: 10px; background-color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.1); transition: all 0.3s ease;">
          <h3
            style="margin-top: 0; margin-bottom: 15px; font-weight: 600; color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px;">
            语音实时分析指标（若音调异常，或者音调稳定度一直是0.0%，请保证在安静环境中面试）
          </h3>
          <div class="metrics" style="grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px;">
            <div class="metric-card" style="padding: 10px;">
              <div class="metric-title" style="font-size: 14px; margin-bottom: 5px;">音量</div>
              <div class="metric-value" style="font-size: 18px; margin-bottom: 5px;">{{ volume.toFixed(1) }} dB</div>
              <div class="volume-graph" style="height: 10px; margin-top: 5px;">
                <div class="volume-bar" :style="{ width: volumePercent + '%' }"
                  style="height: 100%; background: linear-gradient(to right, #f44336, #ffeb3b, #4CAF50); border-radius: 5px;">
                </div>
              </div>
            </div>
            <!--
            <div class="metric-card" style="padding: 10px;">
              <div class="metric-title" style="font-size: 14px; margin-bottom: 5px;">语速</div>
              <div class="metric-value" style="font-size: 18px; margin-bottom: 5px;">{{ speechRate.toFixed(1) }} 词/分钟</div>
              <div class="metric-progress" style="height: 10px; margin-top: 5px;">
                <div class="progress-bar" :style="{ width: speechRatePercent + '%' }" style="height: 100%; background-color: #2196F3; border-radius: 5px;"></div>
              </div>
            </div>
            -->
            <div class="metric-card" style="padding: 10px;">
              <div class="metric-title" style="font-size: 14px; margin-bottom: 5px;">音调稳定度</div>
              <div class="metric-value" style="font-size: 18px; margin-bottom: 5px;">{{ pitchStability.toFixed(1) }}%
              </div>
              <div class="metric-progress" style="height: 10px; margin-top: 5px;">
                <div class="progress-bar" :style="{ width: pitchStability + '%' }"
                  style="height: 100%; background-color: #4CAF50; border-radius: 5px;"></div>
              </div>
            </div>

            <div class="metric-card" style="padding: 10px;">
              <div class="metric-title" style="font-size: 14px; margin-bottom: 5px;">音调</div>
              <div class="metric-value" style="font-size: 18px; margin-bottom: 5px;">{{ pitch.toFixed(1) }} Hz</div>
              <div class="pitch-graph" style="height: 10px; margin-top: 5px; position: relative;">
                <div class="pitch-point" :style="{ left: pitchPosition + '%' }"
                  style="position: absolute; top: 0; width: 6px; height: 100%; background-color: #9C27B0; border-radius: 3px; transform: translateX(-50%);">
                </div>
              </div>
            </div>
          </div>

          <div class="frequency-chart" style="margin-top: 10px;">
            <canvas ref="frequencyCanvas"
              style="width: 100%; height: 100px; background-color: #f5f5f5; border-radius: 5px;"></canvas>
          </div>
        </div>

        <el-button @click="toggleRecording" type="primary" :class="{ 'is-recording': isRecording }"
          style="position: absolute;width:200px;height:30px; top: 650px; left: 1400px; z-index: 1000;">
          {{ isRecording ? '再次点击停止回答' : '点击开始回答' }}
        </el-button>
        <div style="position: absolute;top: 450px; left: 700px; min-height: 500px;">
          <!-- 开始面试按钮：固定在右侧区域，垂直居中偏上 -->
          <el-button v-if="isShowStartButton"
            style="position: absolute;width:200px;height: 30px; top: 150px; left: 700px;z-index: 9999;" @click="start()"
            type="primary">
            开始面试
          </el-button>
          <!-- 查看报告按钮：固定在右侧区域，垂直居中偏下 -->
          <el-button v-if="true" style="position: absolute;width:200px;height: 30px; top: 250px; left: 700px;"
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
  data() {
    return {
       pitchPosition: 0,       // 新增：音高位置，根据实际场景设置默认值
      volumePercent: 0,       // 新增：音量百分比，范围通常是 0-100
      recognitionInterval: null, // 存储表情识别定时器
    isCameraPaused: false,    // 摄像头是否暂停
       saveInterval: null,        // 存储定时器
    storageData: [],           // 存储到localStorage的数据
    storageKey: 'audioMetrics', // localStorage的键名
       analysisHistoryLimit: 1000, // 历史记录最大数量
    analysisStorageKey: 'voiceAnalysisData', // 存储键名
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

      // 语音分析相关数据
      isAnalyzing: false,
      audioContext: null,
      analyser: null,
      microphone: null,
      scriptProcessor: null,
      animationFrameId: null,
      volume: 0,
      pitch: 0,
      pitchStability: 50,
      speechRate: 0,
      pitchHistory: [],
      wordCount: 0,
      lastSpeechTime: 0,
      frequencyData: new Float32Array(1024),
      byteFrequencyData: new Uint8Array(1024),

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
      nlp: false,
      emotion: 0,
      action: "A_RH_hello_O",
    };
  },
  mounted() {
    this.initRecorder(); // 初始化录音功能
    this.initVoiceAnalysis(); // 初始化语音分析功能
    localStorage.setItem('transcribeCount', '0');
    localStorage.setItem('face', '');
     // 新增：初始化存储数据
  this.storageData = JSON.parse(localStorage.getItem(this.storageKey) || '[]');
    console.log('【面试系统】已初始化回答计数：transcribeCount = 0');
    this.initCamera();
     this.initLocalStorageStructure();
  },
  methods: {
    pauseRecognition() {
  if (!this.isProcessing) return;

  // 清除表情识别定时器
  if (this.recognitionInterval) {
    clearInterval(this.recognitionInterval);
    this.recognitionInterval = null;
  }

  // 暂停摄像头（可选）
  if (this.mediaStream && this.isCameraPaused !== false) {
    this.mediaStream.getVideoTracks().forEach(track => {
      track.enabled = false; // 禁用视频轨道
    });
    this.isCameraPaused = true;
  }

  this.isProcessing = false;
  this.status = '表情识别已暂停';
  console.log('表情识别已暂停');
},
    saveAudioMetrics() {
    const metrics = {
      timestamp: new Date().toISOString(),
      volume: this.volume,
      pitch: this.pitch,
      pitchStability: this.pitchStability
    };
    
    // 添加到临时数组
    this.storageData.push(metrics);
    
    // 合并到localStorage
    try {
      // 获取现有数据
      const existingData = JSON.parse(localStorage.getItem(this.storageKey) || '[]');
      
      // 合并数据
      const updatedData = [...existingData, metrics];
      
      // 保存到localStorage
      localStorage.setItem(this.storageKey, JSON.stringify(updatedData));
      
      console.log('已保存音频指标:', metrics);
    } catch (error) {
      console.error('保存音频指标失败:', error);
    }
  },
  
  // 开始定时保存
  startSavingMetrics() {
    if (this.saveInterval) return;
    
    // 立即保存一次
    this.saveAudioMetrics();
    
    // 设置定时器，每5秒保存一次
    this.saveInterval = setInterval(() => {
      this.saveAudioMetrics();
    }, 5000);
    
    console.log('开始每5秒保存音频指标...');
  },
  
  // 停止定时保存
  stopSavingMetrics() {
    if (this.saveInterval) {
      clearInterval(this.saveInterval);
      this.saveInterval = null;
      console.log('停止保存音频指标');
    }
  },
    initLocalStorageStructure() {
  try {
    // 获取现有存储数据
    let storageData = localStorage.getItem(this.analysisStorageKey);
    
    // 如果没有数据，初始化存储结构
    if (!storageData) {
      localStorage.setItem(this.analysisStorageKey, JSON.stringify({
        voiceAnalysisHistory: [],
        currentAnalysis: {
          volume: 0,
          pitch: 0,
          pitchStability: 0,
          updateTime: 0
        }
      }));
    }
  } catch (error) {
    console.error('初始化本地存储结构失败:', error);
  }
},
// 存储语音分析指标到localStorage
saveVoiceAnalysisToLocalStorage() {
  try {
    const now = new Date();
    const timestamp = now.getTime();
    const analysisTime = now.toISOString().slice(0, 19).replace('T', ' ');
    
    // 获取当前存储数据
    let storageData = JSON.parse(localStorage.getItem(this.analysisStorageKey) || '{}');
    
    // 更新当前分析数据
    storageData.currentAnalysis = {
      volume: this.volume,
      pitch: this.pitch,
      pitchStability: this.pitchStability,
      updateTime: timestamp
    };
    
    // 添加到历史记录
    storageData.voiceAnalysisHistory.push({
      timestamp: timestamp,
      volume: this.volume,
      pitch: this.pitch,
      pitchStability: this.pitchStability,
      analysisTime: analysisTime
    });
    
    // 限制历史记录数量
    if (storageData.voiceAnalysisHistory.length > this.analysisHistoryLimit) {
      storageData.voiceAnalysisHistory.shift(); // 移除最早的记录
    }
    
    // 保存到localStorage
    localStorage.setItem(this.analysisStorageKey, JSON.stringify(storageData));
  } catch (error) {
    console.error('保存语音分析数据到localStorage失败:', error);
  }
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
    },
    // 拍摄并发送图片
    captureAndSend() {
      const canvas = document.createElement('canvas');
      canvas.width = this.$refs.video.videoWidth;
      canvas.height = this.$refs.video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(this.$refs.video, 0, 0, canvas.width, canvas.height);
      
      // 转换为base64
      const imageBase64 = canvas.toDataURL('image/jpeg').split(',')[1];
      const question = `请严格按以下格式分析图片中人物的表情与动作："微表情：XX 肢体语言：XX"
其中：
1. XX为两个汉字，需精准描述（如"微笑""挥手"）
2. 若未检测到动作/表情，用"无"表示（如"微表情：无 肢体语言：无"）
3. 输出必须包含且仅包含"微表情："和"肢体语言："两个字段
4. 字段间用空格分隔，不允许出现任何多余文本

示例1（正确格式）：微表情：微笑 肢体语言：挥手
示例2（无动作场景）：微表情：无 肢体语言：无`;

      
      // 发送请求
      fetch('https://123.56.203.202/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_base64: imageBase64,
          prompt: question
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          this.requests.push(data.task_id);
          this.pollResult(data.task_id);
        }
      });
    },
    // 开始识别流程
    startRecognition() {
      if (!this.mediaStream) {
        alert('摄像头尚未初始化');
        return;
      }
      // 恢复摄像头（如果已暂停）
  if (this.isCameraPaused) {
    this.mediaStream.getVideoTracks().forEach(track => {
      track.enabled = true;
    });
    this.isCameraPaused = false;
  }
      this.isProcessing = true;
      this.answer = '正在分析表情...';
      this.frameCount = 0;
      this.requests = [];
      
      const interval = setInterval(() => {
        this.captureAndSend();
        this.frameCount++;
        this.status = `已拍摄 ${this.frameCount}/6 帧`;
        
        if (this.frameCount >= 6) {
          clearInterval(interval);
          this.status = '等待服务器结果...';
          setTimeout(() => {
            this.isProcessing = false;
          }, 5000);
        }
      }, 30000);
    },
    // 轮询结果
    pollResult(request_id) {
      fetch(`https://123.56.203.202/api/chat/result/${request_id}`)
        .then(response => response.json())
        .then(result => {
          if (result.status === 'success') {
            // 实时更新结果
            this.answer = '答：' + result.result;
            
            // 构建当前识别结果对象
            const currentResult = {
              content: result.result,
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
    async submitArticle1() {
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
    async submitArticle2() {
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
              title: localStorage.getItem('secondQuestion'),
              content: localStorage.getItem('secondResult')
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
    async submitArticle3() {
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
              title: localStorage.getItem('thirdQuestion'),
              content: localStorage.getItem('thirdResult')
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
    async submitArticle4() {
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
              title: localStorage.getItem('fourthQuestion'),
              content: localStorage.getItem('fourthResult')
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
    async submitArticle5() {
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
              title: localStorage.getItem('fifthQuestion'),
              content: localStorage.getItem('fifthResult')
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
    
    // 语音分析相关方法
    initVoiceAnalysis() {
      // 初始化语音分析所需的变量
      this.audioContext = null;
      this.analyser = null;
      this.microphone = null;
      this.scriptProcessor = null;
      this.animationFrameId = null;
      this.pitchHistory = [];
      this.wordCount = 0;
      this.lastSpeechTime = 0;
    },
    
    toggleVoiceAnalysis() {
      if (this.isAnalyzing) {
        this.stopVoiceAnalysis();
      } else {
        this.startVoiceAnalysis();
      }
    },
    
    async startVoiceAnalysis() {
      try {
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        
        this.microphone = this.audioContext.createMediaStreamSource(stream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 2048;
        this.analyser.smoothingTimeConstant = 0.8;
        
        this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        this.microphone.connect(this.analyser);
        this.analyser.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.audioContext.destination);
        
        this.scriptProcessor.onaudioprocess = (event) => {
          this.processAudio(event);
        };
        
        this.initFrequencyChart();
        this.startAnimation();
        
        this.isAnalyzing = true;
      } catch (error) {
        console.error('语音分析启动失败:', error);
        alert('语音分析启动失败，请确保已授予麦克风权限。');
      }
    },
    
    stopVoiceAnalysis() {
      this.isAnalyzing = false;
      
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
      }
      
      if (this.microphone) {
        this.microphone.disconnect();
      }
      if (this.analyser) {
        this.analyser.disconnect();
      }
      if (this.scriptProcessor) {
        this.scriptProcessor.disconnect();
        this.scriptProcessor.onaudioprocess = null;
      }
      
      if (this.audioContext) {
        this.audioContext.close();
        this.audioContext = null;
      }
    },
    
    processAudio(event) {
      const inputBuffer = event.inputBuffer.getChannelData(0);
      
      // 计算音量 (RMS)
      let sum = 0;
      for (let i = 0; i < inputBuffer.length; i++) {
        sum += inputBuffer[i] * inputBuffer[i];
      }
      const rms = Math.sqrt(sum / inputBuffer.length);
      this.volume = 20 * Math.log10(rms) || -100; // dB
      
      // 检测语音活动
      const isSpeaking = this.volume > -40; // 阈值可调整
      
      // 更新语速
      if (isSpeaking) {
        if (!this.lastSpeechTime) {
          this.lastSpeechTime = Date.now();
        }
        
        // 模拟单词计数 (实际应用中应使用语音识别)
        if (Math.random() < 0.05) { // 模拟每20帧增加一个词
          this.wordCount++;
        }
        
        const duration = (Date.now() - this.lastSpeechTime) / 1000 / 60; // 分钟
        if (duration > 0) {
          this.speechRate = this.wordCount / duration;
        }
      } else {
        this.lastSpeechTime = 0;
      }
      
      // 获取浮点频率数据
      this.analyser.getFloatFrequencyData(this.frequencyData);
      
      // 计算音高
      let maxAmp = -Infinity;
      let maxFreq = 0;
      
      for (let i = 0; i < this.frequencyData.length; i++) {
        if (this.frequencyData[i] > maxAmp) {
          maxAmp = this.frequencyData[i];
          maxFreq = i * (this.audioContext.sampleRate / 2) / this.frequencyData.length;
        }
      }
      
      // 过滤低振幅噪声
      if (maxAmp > -90) {
        this.pitch = maxFreq;
        
        // 更新音调历史，用于计算稳定性
        this.pitchHistory.push(maxFreq);
        if (this.pitchHistory.length > 20) {
          this.pitchHistory.shift();
        }
        
        // 计算音调稳定性
        if (this.pitchHistory.length > 5) {
          const avgPitch = this.pitchHistory.reduce((a, b) => a + b, 0) / this.pitchHistory.length;
          let variance = 0;
          
          this.pitchHistory.forEach(freq => {
            variance += Math.pow(freq - avgPitch, 2);
          });
          
          const stdDev = Math.sqrt(variance / this.pitchHistory.length);
          this.pitchStability = Math.max(0, Math.min(100, 100 - (stdDev / 50) * 100));
        }
      }
    },
    
    startAnimation() {
      const animate = () => {
        this.updateFrequencyChart();
        this.animationFrameId = requestAnimationFrame(animate);
      };
      
      animate();
    },
    
    initFrequencyChart() {
      this.canvas = this.$refs.frequencyCanvas;
      this.canvasCtx = this.canvas.getContext('2d');
      
      const resizeCanvas = () => {
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
      };
      
      resizeCanvas();
      window.addEventListener('resize', resizeCanvas);
    },
    
    updateFrequencyChart() {
      if (!this.canvasCtx) return;
      
      const canvas = this.canvas;
      const ctx = this.canvasCtx;
      const width = canvas.width;
      const height = canvas.height;
      
      ctx.clearRect(0, 0, width, height);
      
      this.analyser.getByteFrequencyData(this.byteFrequencyData);
      
      const barWidth = width / this.byteFrequencyData.length * 2.5;
      let x = 0;
      
      for (let i = 0; i < this.byteFrequencyData.length; i++) {
        const barHeight = (this.byteFrequencyData[i] / 255) * height;
        
        const hue = (i / this.byteFrequencyData.length) * 240;
        ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
        
        ctx.fillRect(x, height - barHeight / 2, barWidth, barHeight / 2);
        
        x += barWidth + 1;
      }
    },
    
    toggleRecording() {
  if (this.isRecording) {
    // 停止录音和表情识别
    this.stopRecording();
    this.pauseRecognition(); // 暂停表情识别
    this.toggleVoiceAnalysis(); // 停止语音分析
  } else {
    // 开始录音和表情识别
    this.startRecording();
    this.startRecognition(); // 启动表情识别
    this.toggleVoiceAnalysis(); // 启动语音分析
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
            this.submitArticle1();
          } else if (transcribeCount === 2) {
            localStorage.setItem("secondResult", this.transcriptionResult);
            console.log('第二次转写成功，'+localStorage.getItem("secondResult"));
            this.submitArticle2();
          }
          if(transcribeCount === 3){
            localStorage.setItem("thirdResult", this.transcriptionResult);
            console.log('3第三次转写成功，'+localStorage.getItem("thirdResult"));
            this.submitArticle3();
          }
          if(transcribeCount === 4){
            localStorage.setItem("fourthResult", this.transcriptionResult);
            console.log('4第四次转写成功，'+localStorage.getItem("fourthResult"));
            this.submitArticle4();
          }
          if(transcribeCount === 5){
            localStorage.setItem("fifthResult", this.transcriptionResult);
            console.log('5第五次转写成功，'+localStorage.getItem("fifthResult"));
            this.submitArticle5();
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
     // 新增：停止保存指标
    this.stopSavingMetrics();
    if (avatarPlatform2) {
      avatarPlatform2.stop();
    }
    this.stopVoiceAnalysis();
    if (this.isAnalyzing) {
    this.saveVoiceAnalysisToLocalStorage();
  }
  
  if (avatarPlatform2) {
    avatarPlatform2.stop();
  }
  this.stopVoiceAnalysis();
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
}

/* 语音分析样式 */
.audio-analysis-container {
  z-index: 1001;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}

.metric-card {
  background-color: #f9f9f9;
  border-radius: 5px;
  padding: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  min-height: 80px;
}

.metric-title {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.volume-graph,
.pitch-graph,
.metric-progress {
  height: 10px;
  background-color: #eee;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
  margin-top: 5px;
}

.volume-bar {
  height: 100%;
  background: linear-gradient(to right, #f44336, #ffeb3b, #4CAF50);
  transition: width 0.1s;
  border-radius: 5px;
}

.pitch-point {
  position: absolute;
  top: 0;
  width: 6px;
  height: 100%;
  background-color: #9C27B0;
  border-radius: 3px;
  transform: translateX(-50%);
}

.progress-bar {
  height: 100%;
  background-color: #2196F3;
  transition: width 0.3s;
  border-radius: 5px;
}

.frequency-chart {
  margin-top: 10px;
}

canvas {
  width: 100%;
  height: 100px !important;
  background-color: #f5f5f5;
  border-radius: 5px;
}
</style>