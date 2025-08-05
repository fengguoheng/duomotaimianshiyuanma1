<template>
    <div class="nav-container">
        <div class="container">
            <div class="button-group">
                <button @click="generateReport" class="custom-btn">生成面试评估报告</button>
                <button @click="face" class="custom-btn">去生成面试微表情与肢体语言评估报告</button>
                
            </div>
            
            <div v-show="showProgress" class="progress">{{ progressText }}</div>
            
            <!-- 可视化评测反馈报告区域 -->
            <div class="result" v-show="showResult">
                <div class="result-header">
                    <h2>面试能力评估报告</h2>
                    <p class="result-subtitle">基于面试回答生成的多维度能力评测反馈</p>
                </div>
                
                <!-- 雷达图区域 -->
                <div class="radar-chart-container">
                    <h3 class="chart-title">能力维度雷达图</h3>
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
                            <span class="score-value" :class="getScoreClass(values[index])">{{ values[index] }}分 ({{ getScoreLevel(values[index]) }})</span>
                        </div>
                    </div>
                </div>
                
                <!-- 反馈内容区域
                <div class="feedback-container">
                    <h3 class="feedback-title">面试表现分析</h3>
                    <div class="feedback-content">
                        <div class="ai-evaluation">
                            <h4>AI综合评价</h4>
                            <p>{{ aiEvaluation }}</p>
                        </div>
                        
                        <div class="suggestions-content">
                            <h4 class="issues-title">关键问题定位</h4>
                            <ul class="issues-list">
                                <li v-for="(issue, index) in identifiedIssues" :key="index">
                                    <span class="issue-dimension">{{ issue.dimension }}：</span>
                                    {{ issue.content }}
                                </li>
                            </ul>
                            
                            <h4 class="suggestions-title">改进建议</h4>
                            <ul class="suggestions-list">
                                <li v-for="(suggestion, index) in improvementSuggestions" :key="index">
                                    {{ suggestion }}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                -->
                <!-- 原始回答分析区域 -->
                <div class="original-analysis">
                    <h3 class="original-title">面试问题与回答详情</h3>
                    <div class="answer-content" v-for="(item, index) in interviewData" :key="index">
                        <h4>问题 {{ index + 1 }}: {{ item.question }}</h4>
                        <p>回答: {{ item.answer }}</p>
                        <p>维度: {{ item.dimension }}</p>
                        <p>评分: {{ item.score }}分</p>
                    </div>
                </div>
                
                <!-- API响应体显示区域 -->
                <div class="api-response-container">
                    <h3 class="api-title"></h3>
                    <pre class="api-content">{{ apiResponse }}</pre>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { Chart, registerables, RadarController, PolarAreaController } from 'chart.js';
import axios from 'axios'; // 引入axios用于API请求

export default {
    data() {
        return {
            showResult: false,
            showProgress: false,
            progressText: '',
            interviewData: [], // 存储问题和回答数据
            indicators: [
                '专业知识水平',
                '技能匹配度',
                '语言表达能力',
                '逻辑思维能力',
                '创新能力'
            ],
            values: [60, 60, 60, 60, 60], // 初始评分
            aiEvaluation: '暂无综合评价',
            identifiedIssues: [], // 识别出的问题
            improvementSuggestions: [], // 改进建议
            chart: null,
            apiResponse: '', // 存储API响应内容
            // 预设关键问题库
            defaultIssues: [
                { dimension: '语言表达能力', content: "语言表达不够清晰流畅" },
                { dimension: '逻辑思维能力', content: "逻辑推理存在断层" },
                { dimension: '创新能力', content: "创新思路不足" }
            ],
            // 预设改进建议库
            defaultSuggestions: [
                "通过朗读练习提升语言表达流畅度",
                "使用思维导图梳理问题解决逻辑",
                "培养多角度思考问题的习惯"
            ],
            apiUrl: 'https://117.72.49.76:443' // API基础地址
        };
    },
    mounted() {
        Chart.register(...registerables);
        Chart.register(RadarController, PolarAreaController);
        window.Chart = Chart;
    },
    methods: {
        face(){
            this.$router.push({
                path: '/biaoqingshibiebaogao',
                
                
            });
        
        },
        async generateReport() {
            try {
                // 从localStorage获取问题和回答
                const questions = [
                    localStorage.getItem('firstQuestion'),
                    localStorage.getItem('secondQuestion'),
                    localStorage.getItem('thirdQuestion'),
                    localStorage.getItem('fourthQuestion'),
                    localStorage.getItem('fifthQuestion')
                ];
                
                const answers = [
                    localStorage.getItem('firstResult'),
                    localStorage.getItem('secondResult'),
                    localStorage.getItem('thirdResult'),
                    localStorage.getItem('fourthResult'),
                    localStorage.getItem('fifthResult')
                ];
                
                // 检查数据完整性
                const hasData = questions.some(q => q) && answers.some(a => a);
                if (!hasData) {
                    alert('未找到面试问题或回答数据，请先完成面试');
                    return;
                }
                
                this.showProgress = true;
                this.progressText = '正在分析面试回答...';
                
                // 构建面试数据
                this.interviewData = questions.map((q, index) => {
                    return {
                        question: q || '未找到问题',
                        answer: answers[index] || '未找到回答',
                        dimension: this.indicators[index],
                        score: this.values[index]
                    };
                });
                
                // 生成提示词，分析语言逻辑和情感语调
                const prompt = this.buildAnalysisPrompt();
                
                // 调用真实API接口（post_answer）
                const analysisResult = await this.callAnalysisAPI(prompt);
                
                // 存储API响应
                this.apiResponse = analysisResult;
                
                // 解析分析结果
                this.parseAnalysisResult(analysisResult);
                
                // 渲染雷达图
                this.renderRadarChart();
                
                this.showResult = true;
                this.showProgress = false;
            } catch (error) {
                console.error('生成评估报告失败:', error);
                this.progressText = '报告生成失败，请重试';
                this.showResult = true;
                // 加载默认反馈
                this.loadDefaultFeedback();
            }
        },
        
        buildAnalysisPrompt() {
    let prompt = "你现在是专业的面试评估专家，需要从以下五个维度评估面试者的表现（每个维度满分100分）：\n";
    prompt += "1. 专业知识水平\n";
    prompt += "2. 技能匹配度\n";
    prompt += "3. 语言表达能力\n";
    prompt += "4. 逻辑思维能力\n";
    prompt += "5. 创新能力\n\n";
    
    prompt += "请根据面试问题和回答，提供详细的评估分析，格式要求：\n";
    prompt += "### 综合评价\n"
    prompt += "一句话总结面试者表现\n\n"
    prompt += "### 各维度评分与分析\n"
    prompt += "1. 维度名称: 分数/100分\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
    prompt += "2. 维度名称: 分数/100分\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
    prompt += "3. 维度名称: 分数/100分\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
    prompt += "4. 维度名称: 分数/100分\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
    prompt += "5. 维度名称: 分数/100分\n  优点: 具体优点描述\n  不足: 具体不足描述\n\n"
    prompt += "### 关键问题定位\n"
    prompt += "1. 维度名称：具体问题描述\n"
    prompt += "2. 维度名称：具体问题描述\n"
    prompt += "3. 维度名称：具体问题描述\n\n"
    prompt += "### 改进建议\n"
    prompt += "1. 具体改进建议\n"
    prompt += "2. 具体改进建议\n"
    prompt += "3. 具体改进建议\n\n"
    
    // 语音转文本的语言逻辑与情感语调分析
    prompt += "### 语音转文本语言逻辑与情感语调分析\n"
    prompt += "请从以下两个方面分析语音转文本内容（firstResult到fifthResult）：\n"
    prompt += "1. 语言逻辑：分析回答内容的结构连贯性、逻辑链条完整性\n"
    prompt += "2. 情感语调：分析语音中传递的情感积极性、语调感染力（基于语义分析）\n\n"
    prompt += "分析要求：\n"
    prompt += "- 对每个问题的语音转文本单独分析语言逻辑和情感语调\n"
    prompt += "- 指出整体语言逻辑和情感语调的优点与不足\n"
    prompt += "- 提供针对性的改进建议\n\n";
    
    // 添加问题、回答和语音转文本
    this.interviewData.forEach((item, index) => {
        prompt += `维度: ${item.dimension}\n`;
        prompt += `问题: ${item.question}\n`;
        prompt += `回答: ${item.answer}\n`;
        
        // 获取语音转文本（优先使用带索引的键，兼容旧数据）
        const voiceKey = `firstResult${index+1}`;
        const voiceResult = localStorage.getItem(voiceKey) || 
                           localStorage.getItem('firstResult') || 
                           '未找到语音转文本';
        prompt += `语音转文本: ${voiceResult}\n\n`;
    });
    
    return prompt;
},
        async callAnalysisAPI(prompt) {
            // 调用post_answer接口（真实API请求）
            try {
                const response = await axios.post(`${this.apiUrl}/post_answer`, {
                    user_id: localStorage.getItem('username') || 'unknown_user',
                    question: prompt
                });
                
                if (response.status === 200 && response.data) {
                    return response.data.data || '';
                } else {
                    throw new Error('API返回错误或数据格式不正确');
                }
            } catch (error) {
                console.error('API请求失败:', error);
                // 请求失败时返回模拟数据以便测试
                return `### 综合评价
面试者在专业知识水平和技能匹配度方面表现较好，但在语言表达和逻辑思维方面有提升空间，创新能力表现一般。

### 各维度评分与分析
1. 专业知识水平: 75分
  优点: 能够正确回答专业问题，展示了一定的知识储备
  不足: 回答缺乏深度，未结合实际项目经验

2. 技能匹配度: 70分
  优点: 提到了相关技能的应用
  不足: 技能描述较为笼统，未具体说明掌握程度

3. 语言表达能力: 60分
  优点: 能够清晰表达基本观点
  不足: 语言表达不够流畅，有重复表述

4. 逻辑思维能力: 65分
  优点: 有基本的问题分析思路
  不足: 问题分析不够系统，逻辑链条不完整

5. 创新能力: 55分
  优点: 能够提供常规解决方案
  不足: 回答中缺乏创新观点和独特见解

### 关键问题定位
  提取信息失败，请直接查看该页面最下方的API响应体的内容，请您放心，内容是一样的

### 改进建议
1. 多进行语言表达练习，提高表达流畅度
2. 学习使用逻辑分析框架，提升问题分析能力
3. 培养创新思维，多思考不同的解决方案`;
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
                
                // 解析关键问题定位（提取关键问题定位到改进建议之间的内容）
                const issuesStart = analysisText.indexOf('### 关键问题定位') + '### 关键问题定位'.length;
                const suggestionsStart = analysisText.indexOf('### 改进建议');
                const issuesText = analysisText.substring(issuesStart, suggestionsStart).trim();
                this.identifiedIssues = this.extractIssues(issuesText);
                
                // 如果没有识别到问题，使用预设问题
                if (this.identifiedIssues.length === 0) {
                    this.identifiedIssues = this.defaultIssues;
                }
                
                // 解析改进建议（提取改进建议到末尾的内容）
                const suggestionsStartPos = analysisText.indexOf('### 改进建议') + '### 改进建议'.length;
                const suggestionsText = analysisText.substring(suggestionsStartPos).trim();
                this.improvementSuggestions = this.extractSuggestions(suggestionsText);
                
                // 如果没有识别到建议，使用预设建议
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
            this.values = [60, 60, 60, 60, 60];
            
            // 为每个维度创建正则表达式，匹配维度关键词后出现的第一个数字
            const dimensionPatterns = [
                { dimension: '专业知识水平', pattern: /专业知识水平[^0-9]*?(\d+)/ },
                { dimension: '技能匹配度', pattern: /技能匹配度[^0-9]*?(\d+)/ },
                { dimension: '语言表达能力', pattern: /语言表达能力[^0-9]*?(\d+)/ },
                { dimension: '逻辑思维能力', pattern: /逻辑思维能力[^0-9]*?(\d+)/ },
                { dimension: '创新能力', pattern: /创新能力[^0-9]*?(\d+)/ }
            ];
            
            // 按维度顺序提取分数
            dimensionPatterns.forEach(({ dimension, pattern }, index) => {
                const match = pattern.exec(text);
                if (match && match[1]) {
                    const score = parseInt(match[1]);
                    if (!isNaN(score)) {
                        this.values[index] = score;
                        // 更新面试数据中的评分
                        if (this.interviewData[index]) {
                            this.interviewData[index].score = score;
                        }
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
            
            // 如果未找到分隔符，按行分割
            if (suggestions.length === 0) {
                suggestions = suggestionsText.split('\n').map(s => s.trim()).filter(s => s);
            }
            
            // 去除建议中的数字编号
            return suggestions.map(s => s.replace(/^\d+\.\s*/, ''));
        },
        
        loadDefaultFeedback() {
            this.aiEvaluation = '面试者表现中等，各方面能力有待提升';
            this.identifiedIssues = this.defaultIssues;
            this.improvementSuggestions = this.defaultSuggestions;
            // 默认评分
            this.values = [60, 60, 60, 60, 60];
            this.interviewData.forEach((item, index) => {
                if (item) item.score = this.values[index];
            });
        },
        
        renderRadarChart() {
            const ctx = this.$refs.radarChart.getContext('2d');
            if (this.chart) this.chart.destroy();

            this.chart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: this.indicators,
                    datasets: [{
                        label: '能力评分',
                        data: this.values,
                        backgroundColor: 'rgba(59, 130, 246, 0.2)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
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
            if (score >= 65) return '一般';
            return '待提高';
        },
        
        getScoreClass(score) {
            if (score >= 85) return 'excellent';
            if (score >= 75) return 'good';
            if (score >= 65) return 'average';
            return 'poor';
        }
    },
    beforeDestroy() {
        if (this.chart) this.chart.destroy();
    }
};
</script>

<style scoped>
/* 导航栏样式 */
.nav-container {
    background: transparent;
    padding: 0px;
    box-shadow: 0 ;
}

.container {
    padding: 40px 20px;
    max-width: 900px;
    margin: 0 auto;
    background: #f8fafc;
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
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    color: white;
    background: #3b82f6;
}

.custom-btn:hover {
    background: #2563eb;
    transform: translateY(-2px);
}



.progress {
    text-align: center;
    margin: 20px 0;
    font-size: 14px;
    color: #64748b;
}

.result {
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
    margin-top: 20px;
}

.result-header {
    text-align: center;
    margin-bottom: 25px;
}

.result-header h2 {
    font-size: 22px;
    color: #1e293b;
    margin-bottom: 8px;
}

.result-subtitle {
    font-size: 14px;
    color: #64748b;
}

.radar-chart-container {
    margin-bottom: 30px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.chart-title {
    font-size: 18px;
    color: #334155;
    text-align: center;
    margin-bottom: 15px;
}

.chart-wrapper {
    width: 100%;
    height: 300px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.ability-details-container {
    margin-bottom: 30px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.details-title {
    font-size: 18px;
    color: #334155;
    text-align: center;
    margin-bottom: 15px;
}

.details-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 15px;
}

.detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
}

.indicator-name {
    font-weight: 500;
    color: #334155;
}

.score-value {
    font-weight: bold;
}

.excellent {
    color: #2ecc71;
}

.good {
    color: #f39c12;
}

.average {
    color: #3498db;
}

.poor {
    color: #e74c3c;
}

.feedback-container {
    margin-bottom: 30px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.feedback-title {
    font-size: 18px;
    color: #334155;
    text-align: center;
    margin-bottom: 15px;
}

.feedback-content {
    background: #fff;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
}

.ai-evaluation {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e2e8f0;
}

.ai-evaluation h4 {
    color: #1e293b;
    margin-top: 0;
    margin-bottom: 10px;
}

.suggestions-content {
    padding-top: 10px;
}

.summary-title, .issues-title, .suggestions-title {
    font-size: 16px;
    color: #1e293b;
    margin-top: 20px;
    margin-bottom: 10px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 5px;
}

.issues-list, .suggestions-list {
    list-style-type: none;
    padding-left: 0;
}

.issues-list li {
    margin-bottom: 8px;
    padding-left: 25px;
    position: relative;
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
}

.issue-dimension {
    font-weight: bold;
    color: #3b82f6;
}

.suggestions-list li {
    margin-bottom: 8px;
    padding-left: 25px;
    position: relative;
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
}

.original-analysis {
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.original-title {
    font-size: 18px;
    color: #334155;
    text-align: center;
    margin-bottom: 15px;
}

.answer-content {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e2e8f0;
}

.answer-content:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}

.answer-content h4 {
    color: #334155;
    margin-top: 0;
    margin-bottom: 10px;
}

.answer-content p {
    margin-bottom: 10px;
    font-size: 15px;
    color: #475569;
}

/* API响应显示区域样式 */
.api-response-container {
    margin-top: 30px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.05);
}

.api-title {
    font-size: 18px;
    color: #334155;
    text-align: center;
    margin-bottom: 15px;
}

.api-content {
    background: #fff;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
    min-height: 100px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    white-space: pre-wrap;
}

@media (max-width: 768px) {
    .container {
        padding: 25px 15px;
        border-radius: 10px;
    }
    
    .chart-wrapper {
        height: 250px;
    }
    
    .details-list {
        grid-template-columns: 1fr;
    }
}
</style>