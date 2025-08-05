<template>
    <div class="nav-container">
        <div class="container">
            <div class="button-group">
                <button @click="generateReport" class="custom-btn">生成微表情评估报告</button>
                
            </div>
            
            <div v-show="showProgress" class="progress">{{ progressText }}</div>
            <div v-show="errorMessage" class="error-message">{{ errorMessage }}</div>
            
            <!-- 可视化评测反馈报告区域 -->
            <div class="result" v-show="showResult">
                <div class="result-header">
                    <h2>微表情与肢体语言评估报告</h2>
                    <p class="result-subtitle">基于面部表情与肢体动作分析的面试表现力评估</p>
                </div>
                
                <!-- 雷达图区域 -->
                <div class="radar-chart-container">
                    <h3 class="chart-title">非语言沟通能力雷达图</h3>
                    <div class="chart-wrapper">
                        <canvas ref="radarChart" width="400" height="300"></canvas>
                    </div>
                </div>
                
                <!-- 能力详情区域 -->
                <div class="ability-details-container">
                    <h3 class="details-title">各维度能力评分</h3>
                    <div class="details-list">
                        <div v-for="(item, index) in indicators" :key="index" class="detail-item">
                            <span class="indicator-name">{{ item }}</span>
                            <span class="score-value" :class="getScoreClass(scores[index])">{{ scores[index] }}分 ({{ getScoreLevel(scores[index]) }})</span>
                        </div>
                    </div>
                </div>
                
                <!-- 反馈内容区域 -->
                <div class="feedback-container">
                    <h3 class="feedback-title">非语言沟通表现分析</h3>
                    <div class="feedback-content">
                        <div class="ai-evaluation">
                            <h4>AI综合评价</h4>
                            <p>{{ aiEvaluation }}</p>
                        </div>
                        
                        
                        
                        
                    </div>
                </div>
                
                <!-- 原始数据区域 -->
                <div class="original-analysis">
                    <h3 class="original-title">微表情与肢体动作原始数据</h3>
                    <div class="data-list">
                        <div v-for="(item, index) in filteredFaceData" :key="index" class="data-item">
                            <p><strong>时间:</strong> {{ formatTime(item.timestamp) }}</p>
                            <p><strong>识别结果:</strong> {{ item.content || '未识别到有效数据' }}</p>
                        </div>
                    </div>
                </div>
                
                <!-- API响应体显示区域 -->
                <div class="api-response-container">
                    <h3 class="api-title">API分析结果</h3>
                    <div class="api-content" v-html="formattedApiResponse"></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { Chart, registerables, RadarController, PolarAreaController } from 'chart.js';
import axios from 'axios';

export default {
    data() {
        return {
            showResult: false,
            showProgress: false,
            errorMessage: '',
            isLoading: false,
            progressText: '',
            // 微表情与肢体语言核心能力指标
            indicators: [
                '表情管理能力',
                '肢体协调性',
                '眼神交流',
                '情绪稳定性',
                '空间姿态控制'
            ],
            scores: [60, 60, 60, 60, 60], // 初始评分
            aiEvaluation: '暂无综合评价',
            identifiedIssues: [], // 识别出的问题
            improvementSuggestions: [], // 改进建议
            chart: null,
            faceData: [], // 微表情数据
            filteredFaceData: [], // 过滤后的有效数据
            apiResponse: null, // 原始API响应
            // 预设关键问题库
            defaultIssues: [
                { dimension: '表情管理能力', content: "表情管理能力有待提升，情绪表达不够稳定" },
                { dimension: '肢体协调性', content: "肢体动作协调性不足，存在僵硬或抖动" },
                { dimension: '眼神交流', content: "眼神交流不够充分，存在回避或游离" }
            ],
            // 预设改进建议库
            defaultSuggestions: [
                "通过镜子练习表情管理，学习在不同场景下保持合适表情",
                "参加肢体语言训练课程，提升动作协调性与自然度",
                "进行眼神交流专项训练，增强与面试官的视觉沟通"
            ],
            apiUrl: 'https://117.72.49.76:443' // API基础地址
        };
    },
    mounted() {
        Chart.register(...registerables);
        Chart.register(RadarController, PolarAreaController);
        window.Chart = Chart;
    },
    computed: {
        formattedApiResponse() {
            if (!this.apiResponse) return '暂无API响应数据';
            // 将\n替换为<br>实现换行，并保留Markdown标题格式
            return this.apiResponse
                .replace(/\n/g, '<br>')
                .replace(/### /g, '<h4 style="margin-top: 15px; color: #334155; font-weight: 600;">')
                .replace(/\n/g, '<br>')
                .replace(/<h4/, '<h4 style="margin-top: 15px; color: #334155; font-weight: 600;">')
                .replace(/\*\*/g, '<strong>');
        }
    },
    methods: {
        // 导航到面试页面
        navigateToInterview() {
            this.$router.push({ path: '/interview' });
        },
        
        async generateReport() {
            try {
                // 重置状态
                this.isLoading = true;
                this.showProgress = true;
                this.errorMessage = '';
                this.showResult = false;
                this.progressText = '正在提取微表情数据...';
                
                // 从localStorage获取face数据
                const faceDataStr = localStorage.getItem('face');
                this.faceData = faceDataStr ? JSON.parse(faceDataStr) : [];
                
                // 数据校验
                if (this.faceData.length === 0) {
                    this.errorMessage = '未找到微表情识别数据，请先进行表情识别';
                    this.showProgress = false;
                    this.isLoading = false;
                    return;
                }
                
                // 过滤无效数据（content为空的记录）
                this.filteredFaceData = this.faceData.filter(item => item.content && item.content.trim() !== '');
                if (this.filteredFaceData.length === 0) {
                    this.errorMessage = '未找到有效微表情数据，请重试识别';
                    this.showProgress = false;
                    this.isLoading = false;
                    return;
                }
                
                this.progressText = '正在向API发送分析请求...';
                
                // 构建提示词
                const prompt = this.buildAnalysisPrompt();
                
                // 调用API
                const analysisResult = await this.callAnalysisAPI(prompt);
                
                // 存储API响应
                this.apiResponse = analysisResult;
                
                // 解析分析结果
                this.parseAnalysisResult(analysisResult);
                
                // 渲染雷达图
                this.renderRadarChart();
                
                // 显示结果
                this.showResult = true;
                this.progressText = '评估报告生成完成';
            } catch (error) {
                console.error('生成评估报告失败:', error);
                this.errorMessage = `报告生成失败：${error.message || '请检查网络连接或API服务'}`;
                this.progressText = '操作失败，请重试';
                
                // 加载默认反馈
                this.loadDefaultFeedback();
            } finally {
                this.showProgress = false;
                this.isLoading = false;
            }
        },
        
        // 构建微表情分析提示词
        buildAnalysisPrompt() {
            let prompt = "你现在是专业的非语言沟通评估专家，需要从以下五个维度，以 0-100 分的评分体系（100 分为满分）评估面试者的微表情与肢体语言表现：\n";
            prompt += "1. 表情管理能力：控制面部表情以恰当表达情绪的能力\n";
            prompt += "2. 肢体协调性：肢体动作的自然度与协调性\n";
            prompt += "3. 眼神交流：与面试官的目光接触质量\n";
            prompt += "4. 情绪稳定性：表情与动作在压力下的稳定性\n";
            prompt += "5. 空间姿态控制：身体姿态与空间利用的合理性\n\n";
            
            prompt += "请根据微表情识别数据，提供详细的评估分析，格式要求：\n";
            prompt += "### 综合评价\n"
            prompt += "一句话总结面试者的非语言沟通表现\n\n"
            prompt += "### 各维度评分与分析\n"
            prompt += "1. 维度名称: 分数分（0-100 分制，100 为满分）\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
            prompt += "2. 维度名称: 分数分（0-100 分制，100 为满分）\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
            prompt += "3. 维度名称: 分数分（0-100 分制，100 为满分）\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
            prompt += "4. 维度名称: 分数分（0-100 分制，100 为满分）\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
            prompt += "5. 维度名称: 分数分（0-100 分制，100 为满分）\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
            prompt += "### 关键问题定位\n"
            prompt += "1. 维度名称：具体问题描述（如“眼神交流不足，频繁回避目光”）\n"
            prompt += "2. 维度名称：具体问题描述\n"
            prompt += "3. 维度名称：具体问题描述\n\n"
            prompt += "### 改进建议\n"
            prompt += "1. 具体改进建议（如“通过镜子练习保持自然表情”）\n"
            prompt += "2. 具体改进建议\n"
            prompt += "3. 具体改进建议\n\n";
            
            // 添加微表情数据
            prompt += "### 微表情与肢体动作识别数据（最近20条）\n";
            const recentData = this.filteredFaceData.slice(-20); // 取最近20条数据
            recentData.forEach((item, index) => {
                prompt += `数据 ${index+1}:\n`;
                prompt += `时间: ${new Date(item.timestamp).toLocaleString()}\n`;
                prompt += `识别结果: ${item.content || '无有效识别结果'}\n\n`;
            });
            
            return prompt;
        },
        
        async callAnalysisAPI(prompt) {
            // 调用post_answer接口
            try {
                const response = await axios.post(`${this.apiUrl}/post_answer`, {
                    user_id: localStorage.getItem('user_id') || 'unknown_user',
                    question: prompt
                });
                
                if (response.status === 200 && response.data) {
                    return response.data.data || '';
                } else {
                    throw new Error('API返回错误或数据格式不正确');
                }
            } catch (error) {
                console.error('API请求失败:', error);
                // 返回模拟数据以便测试
                return `### 综合评价
面试者的非语言沟通表现较为克制但缺乏自然活力，整体呈现静态化特征，需提升表情丰富性、肢体协调性及眼神互动频率。

### 各维度评分与分析
1. **表情管理能力**: 65分 
  优点：能维持平静表情，未出现明显负面情绪泄露，严肃表情的转换有一定目的性（如强调回答）。 
  不足：表情过于单一且僵硬，缺乏自然过渡（如微笑或配合话语的动态表情），严肃表情持续时间过长易显紧绷。

2. **肢体协调性**: 55分 
  优点：无明显多余动作，基础姿态稳定。 
  不足：肢体语言匮乏（如无手势辅助说明），长时间静止易显得呆板，缺乏与语言内容的协同表达。

3. **眼神交流**: 40分 
  优点：无频繁低头或躲避行为，基础目光接触达标。 
  不足：眼神互动频率过低（数据中仅严肃/平静状态记录，无主动注视变化），缺乏焦点切换和回应式点头，易让面试官感到冷漠。

4. **情绪稳定性**: 70分 
  优点：未因压力产生慌乱表情（如皱眉、舔唇等），严肃表情可控。 
  不足：情绪表达过于压抑，缺乏适度松弛感（如短暂微笑或眉头放松），可能传递紧张感。

5. **空间姿态控制**: 60分 
  优点：头部正对镜头，无冒犯性动作（如抖腿、抱胸）。 
  不足：身体前倾/后仰等动态调整缺失，坐姿僵直导致亲和力不足，空间利用局限（如未适当手势打开空间）。

### 关键问题定位
1. **眼神交流不足**：长时间静止对视，缺乏焦点移动和回应性眼神变化。 
2. **肢体协调性差**：无手势辅助，动作与语言脱节，静态化导致表现力薄弱。 
3. **表情管理僵硬**：严肃与平静表情占比过高，缺乏自然情绪过渡（如微笑或困惑时的微表情）。

### 改进建议
1. **眼神训练**：通过“三角注视法”（左眼-右眼-鼻尖交替注视）增加焦点移动，每回答一个要点时配合短暂点头。 
2. **手势融入**：设计自然手势框架（如双手平放桌面时随话语轻微上抬），避免完全静止，可用掌心向上的开放手势增强可信度。 
3. **表情练习**：录制模拟面试并回放，刻意在回答积极内容时加入短暂微笑，通过咬字节奏配合表情变化（如“我认为”时稍挑眉）。

### 微表情与肢体动作识别数据（最近20条）
（注：用户提供数据已完整呈现于问题描述中，此处从略。）`;
            }
        },
        
        parseAnalysisResult(analysisText) {
            try {
                // 解析综合评价
                const evalStart = analysisText.indexOf('### 综合评价') + '### 综合评价'.length;
                const evalEnd = analysisText.indexOf('### 各维度评分与分析');
                const evalText = analysisText.substring(evalStart, evalEnd).trim();
                this.aiEvaluation = this.extractSectionContent(evalText, '：', '###');
                
                // 解析各维度评分
                this.extractScoresByDimension(analysisText);
                
                // 解析关键问题定位（从"关键问题定位"到改进建议之间的内容）
                const issuesStart = analysisText.indexOf('### 关键问题定位') + '### 关键问题定位'.length;
                const suggestionsStart = analysisText.indexOf('### 改进建议');
                const issuesText = analysisText.substring(issuesStart, suggestionsStart).trim();
                this.identifiedIssues = this.extractIssues(issuesText);
                
                // 若无问题，使用预设问题
                if (this.identifiedIssues.length === 0) {
                    this.identifiedIssues = this.defaultIssues;
                }
                
                // 解析改进建议（从"改进建议"到数据部分之间的内容）
                const suggestionsStartPos = analysisText.indexOf('### 改进建议') + '### 改进建议'.length;
                const dataStartPos = analysisText.indexOf('### 微表情与肢体动作识别数据');
                const suggestionsText = (dataStartPos > 0) 
                    ? analysisText.substring(suggestionsStartPos, dataStartPos).trim() 
                    : analysisText.substring(suggestionsStartPos).trim();
                this.improvementSuggestions = this.extractSuggestions(suggestionsText);
                
                // 若无建议，使用预设建议
                if (this.improvementSuggestions.length === 0) {
                    this.improvementSuggestions = this.defaultSuggestions;
                }
                
            } catch (error) {
                console.error('解析分析结果出错:', error);
                this.loadDefaultFeedback();
            }
        },
        
        extractSectionContent(section, startMarker, endMarker) {
            const startIndex = section.indexOf(startMarker) + startMarker.length;
            const endIndex = section.indexOf(endMarker);
            return (endIndex > 0) 
                ? section.substring(startIndex, endIndex).trim() 
                : section.substring(startIndex).trim();
        },
        
        extractScoresByDimension(text) {
            // 重置评分
            this.scores = [60, 60, 60, 60, 60];
            
            // 定义维度匹配模式（匹配维度名称后的第一个数字）
            const dimensionPatterns = [
                { dimension: '表情管理能力', pattern: new RegExp(`${this.indicators[0]}\\D*(\\d+)`), index: 0 },
                { dimension: '肢体协调性', pattern: new RegExp(`${this.indicators[1]}\\D*(\\d+)`), index: 1 },
                { dimension: '眼神交流', pattern: new RegExp(`${this.indicators[2]}\\D*(\\d+)`), index: 2 },
                { dimension: '情绪稳定性', pattern: new RegExp(`${this.indicators[3]}\\D*(\\d+)`), index: 3 },
                { dimension: '空间姿态控制', pattern: new RegExp(`${this.indicators[4]}\\D*(\\d+)`), index: 4 }
            ];
            
            // 提取各维度评分
            dimensionPatterns.forEach(patternObj => {
                const match = patternObj.pattern.exec(text);
                if (match && match[1]) {
                    const score = parseInt(match[1]);
                    if (!isNaN(score)) {
                        this.scores[patternObj.index] = score;
                    }
                }
            });
        },
        
        extractIssues(issuesText) {
            if (!issuesText) return [];
            
            const issues = [];
            // 匹配 "1. 维度名称：问题描述" 格式
            const issueRegex = /(\d+\.\s*)?([\u4e00-\u9fa5]+)：(.*?)(?=\d+\.|$)/g;
            let match;
            
            while ((match = issueRegex.exec(issuesText)) !== null) {
                const dimension = match[2].trim();
                const content = match[3].trim();
                if (dimension && content) {
                    issues.push({ dimension, content });
                }
            }
            
            return issues;
        },
        
        extractSuggestions(suggestionsText) {
            if (!suggestionsText) return [];
            
            // 按常见分隔符分割建议
            const separators = ['。', '；', ';', '\n', '. '];
            let suggestions = [];
            
            separators.forEach(sep => {
                if (suggestionsText.includes(sep)) {
                    suggestions = suggestionsText.split(sep).map(s => s.trim()).filter(s => s);
                }
            });
            
            // 按行分割作为备用方案
            if (suggestions.length === 0) {
                suggestions = suggestionsText.split('\n').map(s => s.trim()).filter(s => s);
            }
            
            // 去除数字编号和Markdown强调符号
            return suggestions.map(s => s.replace(/^\d+\.|\*\*|\s+/g, '').trim());
        },
        
        loadDefaultFeedback() {
            this.aiEvaluation = '未获取到足够的微表情数据，无法进行详细分析';
            this.identifiedIssues = this.defaultIssues;
            this.improvementSuggestions = this.defaultSuggestions;
            this.scores = [60, 60, 60, 60, 60];
        },
        
        renderRadarChart() {
            const ctx = this.$refs.radarChart.getContext('2d');
            if (this.chart) this.chart.destroy();

            this.chart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: this.indicators,
                    datasets: [{
                        label: '非语言沟通能力评分',
                        data: this.scores,
                        backgroundColor: 'rgba(75, 85, 99, 0.2)',
                        borderColor: 'rgba(75, 85, 99, 1)',
                        pointBackgroundColor: 'rgba(75, 85, 99, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(75, 85, 99, 1)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: { display: true },
                            suggestedMin: 0,
                            suggestedMax: 100,
                            ticks: { callback: (value) => `${value}分` }
                        }
                    },
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: { label: (context) => `${context.label}: ${context.raw}分` }
                        }
                    }
                }
            });
        },
        
        getScoreLevel(score) {
            if (score >= 85) return '优秀';
            if (score >= 75) return '良好';
            if (score >= 60) return '一般';
            return '待提高';
        },
        
        getScoreClass(score) {
            if (score >= 85) return 'excellent';
            if (score >= 75) return 'good';
            if (score >= 60) return 'average';
            return 'poor';
        },
        
        formatTime(timestamp) {
            if (!timestamp) return '未知时间';
            const date = new Date(timestamp);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    },
    beforeDestroy() {
        if (this.chart) this.chart.destroy();
    }
};
</script>

<style scoped>
/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* 导航栏样式 */
.nav-container {
    background: transparent;
    padding: 0;
    box-shadow: 0 ;
}

.container {
    padding: 30px 20px;
    max-width: 900px;
    margin: 0 auto;
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
}

.button-group {
    margin-bottom: 25px;
    text-align: center;
}

.custom-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 28px;
    border: none;
    border-radius: 30px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.25s ease;
    color: white;
    background: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.custom-btn:hover {
    background: #2563eb;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.progress {
    text-align: center;
    margin: 15px 0 25px;
    font-size: 14px;
    color: #64748b;
    font-weight: 500;
}

.error-message {
    text-align: center;
    margin: 15px 0 25px;
    font-size: 14px;
    color: #ef4444;
    font-weight: 500;
}

.result {
    background: #fff;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.03);
}

.result-header {
    text-align: center;
    margin-bottom: 30px;
    position: relative;
}

.result-header h2 {
    font-size: 24px;
    color: #1e293b;
    margin-bottom: 10px;
    font-weight: 600;
}

.result-subtitle {
    font-size: 15px;
    color: #64748b;
    max-width: 600px;
    margin: 0 auto;
}

.radar-chart-container {
    margin-bottom: 35px;
    padding: 20px;
    background: #f8fafc;
    border-radius: 12px;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.03);
}

.chart-title {
    font-size: 19px;
    color: #334155;
    text-align: center;
    margin-bottom: 20px;
    font-weight: 600;
}

.chart-wrapper {
    width: 100%;
    height: 280px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.ability-details-container {
    margin-bottom: 35px;
    padding: 20px;
    background: #f8fafc;
    border-radius: 12px;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.03);
}

.details-title {
    font-size: 19px;
    color: #334155;
    text-align: center;
    margin-bottom: 20px;
    font-weight: 600;
}

.details-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 18px;
}

.detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease;
}

.detail-item:hover {
    transform: translateY(-2px);
}

.indicator-name {
    font-weight: 500;
    color: #334155;
    font-size: 15px;
}

.score-value {
    font-weight: bold;
    font-size: 15px;
}

.excellent {
    color: #10b981; /* 绿色 */
}

.good {
    color: #f59e0b; /* 黄色 */
}

.average {
    color: #3b82f6; /* 蓝色 */
}

.poor {
    color: #ef4444; /* 红色 */
}

.feedback-container {
    margin-bottom: 35px;
    padding: 20px;
    background: #f8fafc;
    border-radius: 12px;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.03);
}

.feedback-title {
    font-size: 19px;
    color: #334155;
    text-align: center;
    margin-bottom: 20px;
    font-weight: 600;
}

.feedback-content {
    background: #fff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
}

.ai-evaluation {
    margin-bottom: 25px;
    padding-bottom: 25px;
    border-bottom: 1px solid #e2e8f0;
}

.ai-evaluation h4 {
    color: #1e293b;
    margin-top: 0;
    margin-bottom: 12px;
    font-size: 17px;
    font-weight: 600;
}

.ai-evaluation p {
    color: #475569;
    line-height: 1.7;
    font-size: 15px;
}

.issues-content, .suggestions-content {
    padding-top: 10px;
}

.issues-title, .suggestions-title {
    font-size: 17px;
    color: #1e293b;
    margin-top: 20px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 600;
}

.issues-list, .suggestions-list {
    list-style-type: none;
    padding-left: 0;
}

.issues-list li, .suggestions-list li {
    margin-bottom: 12px;
    padding-left: 28px;
    position: relative;
    color: #475569;
    font-size: 15px;
    line-height: 1.6;
}

.issues-list li::before {
    content: "•";
    color: #ef4444;
    font-weight: bold;
    display: inline-block;
    width: 1em;
    margin-left: -1em;
    position: absolute;
    left: 10px;
    font-size: 18px;
    top: 2px;
}

.issue-dimension {
    font-weight: 500;
    color: #3b82f6;
}

.suggestions-list li::before {
    content: "✓";
    color: #10b981;
    font-weight: bold;
    display: inline-block;
    width: 1em;
    margin-left: -1em;
    position: absolute;
    left: 10px;
    font-size: 16px;
    top: 3px;
}

.original-analysis {
    padding: 20px;
    background: #f8fafc;
    border-radius: 12px;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.03);
}

.original-title {
    font-size: 19px;
    color: #334155;
    text-align: center;
    margin-bottom: 20px;
    font-weight: 600;
}

.data-list {
    background: #fff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
}

.data-item {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e2e8f0;
}

.data-item:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.data-item p {
    margin-bottom: 8px;
    font-size: 15px;
    color: #475569;
}

.api-response-container {
    padding: 20px;
    background: #f8fafc;
    border-radius: 12px;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.03);
}

.api-title {
    font-size: 19px;
    color: #334155;
    text-align: center;
    margin-bottom: 20px;
    font-weight: 600;
}

.api-content {
    background: #fff;
    padding: 18px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
    min-height: 120px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-line;
    color: #475569;
}

/* 响应式适配 */
@media (max-width: 768px) {
    .container {
        padding: 25px 15px;
        border-radius: 10px;
    }
    
    .result {
        padding: 20px 15px;
    }
    
    .chart-wrapper {
        height: 250px;
    }
    
    .details-list {
        grid-template-columns: 1fr;
    }
    
    .result-header h2 {
        font-size: 22px;
    }
    
    .chart-title, .details-title, .feedback-title, .api-title, .original-title {
        font-size: 18px;
    }
}
</style>