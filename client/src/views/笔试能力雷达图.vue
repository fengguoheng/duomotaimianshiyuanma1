<template>
    <div class="nav-container">
        <div class="container">
            <div class="button-group">
                <button @click="showRadarChart" class="custom-btn">查看我的笔试报告</button>
                
            </div>
            
            <div v-show="showProgress" class="progress">{{ progressText }}</div>
            
            <!-- 可视化评测反馈报告区域 -->
            <div class="result" v-show="showResult">
                <div class="result-header">
                    <h2>面试者能力评估报告</h2>
                    <p class="result-subtitle">基于笔试答案生成的能力评测反馈</p>
                </div>
                
                <!-- 雷达图区域 -->
                <div class="radar-chart-container">
                    <h3 class="chart-title">能力雷达图</h3>
                    <div class="chart-wrapper">
                        <canvas ref="radarChart" width="400" height="300"></canvas>
                    </div>
                </div>
                
                
                
                <
                
                <!-- 原分析结果 -->
                <div v-html="answerHtml" class="original-analysis">
                    <h3 class="original-title">详细分析结果</h3>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { Chart, registerables, RadarController, PolarAreaController } from 'chart.js';

export default {
    data() {
        return {
            showResult: false,
            showProgress: false,
            progressText: '',
            answerHtml: '',
            feedbackHtml: '',
            indicators: [
                '专业知识水平',
                '技能匹配度',
                '语言表达能力',
                '逻辑思维能力',
                '创新能力' // 新增
            ],
            values: [60, 60, 60, 60, 60], // 初始评分
            aiEvaluation: '暂无综合评价',
            chart: null,
            selectedCareer: '',
            scoreLevel: {
                85: '优秀',
                75: '良好',
                65: '一般',
                55: '待提高'
            },
            // 预设关键问题库（包含用户指定问题）
            defaultIssues: [
                "回答缺乏STAR结构（情境-任务-行动-结果）",
                "技术术语使用不准确（如混淆卷积层与池化层功能）",
                "眼神交流不足（模拟面试中视线频繁偏移）",
                "回答过于笼统（未用具体数据量化成果）",
                "岗位核心技能掌握不扎实（如Hadoop组件功能混淆）"
            ],
            // 预设改进建议库
            defaultSuggestions: [
                "学习STAR法则，用'在XX项目中，通过XX方法，实现XX目标'结构回答",
                "整理技术术语手册，区分易混淆概念（如CNN各层作用）",
                "通过镜子练习或录像复盘，改善眼神交流和肢体语言",
                "准备3个项目案例，用具体数据（如'准确率提升20%'）量化成果",
                "针对岗位要求，完成Hadoop/Spark官方文档实操练习"
            ]
        };
    },
    mounted() {
        Chart.register(...registerables);
        Chart.register(RadarController, PolarAreaController);
        window.Chart = Chart;
        this.selectedCareer = localStorage.getItem('career') || '人工智能工程师';
    },
    methods: {
        tomianshi() {
            this.$router.push('/mianshi');
        },
        async showRadarChart() {
            try {
                const question = localStorage.getItem('question');
                const answer = localStorage.getItem('answer');

                if (!question || !answer) {
                    alert('请先完成笔试并获取评估结果');
                    return;
                }

                this.showProgress = true;
                this.progressText = '正在生成评估报告...';

                // 强化岗位约束的提示词
                const prompt = `=== 【岗位强约束：${this.selectedCareer}】 ===
你现在是${this.selectedCareer}岗位的专业面试官，需从以下维度评估面试者笔试表现：
1. 专业知识水平：评估理论知识、技能掌握及项目经验的技术深度
2. 技能匹配度：分析硬技能（如编程/工具）和软技能与岗位的契合度
3. 语言表达能力：评估表达清晰度、术语准确性及逻辑连贯性
4. 逻辑思维能力：评估问题解决思路和技术方案的因果关系
5. 创新能力：评估沟通技巧、案例阐述方式及岗位适配度

笔试题目及答案：
---
题目：${localStorage.getItem('question')}
答案：${localStorage.getItem('answer')}
---

要求：
1. 每个维度需指出优点与不足（如"回答缺乏STAR结构"）
2. 改进建议需具体可操作（如"通过模拟面试训练眼神交流"）
3. 结合岗位需求给出技术学习路径`;

                const response = await fetch('https://117.72.49.76:443/post_answer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: 'test_user', question: prompt })
                });

                const data = await response.json();
                const chatText = data.data || '';

                this.parseRadarData(chatText);
                this.answerHtml = this.parseMarkdownToHtml(chatText);
                this.generateFeedback(chatText);
                this.aiEvaluation = this.extractAIEvaluation(chatText);

                this.showResult = true;
                this.showProgress = false;
                this.renderRadarChart();
            } catch (error) {
                console.error('生成评估报告失败:', error);
                this.progressText = '报告生成失败，请重试';
                this.showResult = true;
                // 加载默认反馈
                this.feedbackHtml = this.getDefaultFeedback();
            }
        },

        parseRadarData(chatText) {
            try {
                const content = chatText.toLowerCase();
                // 专业知识水平
                this.values[0] = this.assessScore(content, '专业知识水平', ['扎实', '深入理解'], ['欠缺', '不熟悉', '混淆']);
                // 技能匹配度
                this.values[1] = this.assessScore(content, '技能匹配度', ['匹配', '熟练', '契合'], ['不匹配', '不足', '缺乏']);
                // 语言表达能力
                this.values[2] = this.assessScore(content, '语言表达能力', ['清晰', '准确', '严谨'], ['模糊', '混乱', '欠佳']);
                // 逻辑思维能力
                this.values[3] = this.assessScore(content, '逻辑思维能力', ['条理', '严密', '系统'], ['混乱', '断层', '缺乏']);
                // 
                this.values[4] = this.assessScore(content, '创新能力', ['优秀', '良好', '流畅'], ['不足', '欠缺', '待提高']);
            } catch (error) {
                console.error('提取评分出错:', error);
            }
        },

        assessScore(content, dimension, positive, negative) {
            const dimensionText = content.split(dimension)[1] || '';
            let score = 50;
            positive.forEach(word => score += dimensionText.includes(word) ? 10 : 0);
            negative.forEach(word => score -= dimensionText.includes(word) ? 10 : 0);
            return Math.max(0, Math.min(100, score));
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

        parseMarkdownToHtml(markdown) {
            if (!markdown) return '<p>暂无详细分析结果</p>';
            return markdown
                .replace(/\*\*(.*?)\*\*/g, '<h3>$1</h3>')
                .replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>')
                .replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>')
                .split('\n\n').map(p => p.trim().startsWith('<h3>') || p.trim().startsWith('<ul>') 
                    ? p : `<p>${p}</p>`).join('');
        },

        generateFeedback(chatText) {
            try {
                const content = chatText;
                const issues = this.extractIssues(content);
                const suggestions = this.extractSuggestions(content);

                let feedbackHtml = '<div class="feedback-summary">';
                if (issues.length > 0) {
                    feedbackHtml += `<h4 class="issues-title">关键问题定位</h4>`;
                    feedbackHtml += `<ul class="issues-list">`;
                    issues.forEach(issue => {
                        feedbackHtml += `<li><span class="issue-dimension">${issue.dimension}：</span>${issue.content}</li>`;
                    });
                    feedbackHtml += `</ul>`;
                }

                if (suggestions.length > 0) {
                    feedbackHtml += `<h4 class="suggestions-title">改进建议</h4>`;
                    feedbackHtml += `<ul class="suggestions-list">`;
                    suggestions.forEach(suggestion => {
                        feedbackHtml += `<li>${suggestion}</li>`;
                    });
                    feedbackHtml += `</ul>`;
                }
                feedbackHtml += `</div>`;
                this.feedbackHtml = feedbackHtml;
            } catch (error) {
                console.error('生成反馈出错:', error);
                this.feedbackHtml = this.getDefaultFeedback();
            }
        },

        extractIssues(content) {
            const issueRegex = /(\d+\.\s*.*?)\s*：[\s\S]*?不足|欠缺|需要改进|有待提高|不清晰/gi;
            const matches = [];
            let match;
            while ((match = issueRegex.exec(content)) !== null) {
                const dimension = match[1].replace(/\d+\.\s*/, '').trim();
                const issueText = content.substring(issueRegex.lastIndex - 50, issueRegex.lastIndex)
                    .replace(/.*?：/, '').replace(/不足|欠缺|需要改进|有待提高|不清晰/, '').trim();
                matches.push({ dimension, content: issueText });
            }
            // 若无匹配，使用预设问题
            if (matches.length === 0) {
                return [
                    { dimension: '创新能力', content: this.defaultIssues[0] },
                    { dimension: '专业知识水平', content: this.defaultIssues[1] }
                ];
            }
            return matches;
        },

        extractSuggestions(content) {
            const suggestRegex = /改进建议[\s\S]*?：([\s\S]*?)(?=\d+\.|\Z)/;
            const match = suggestRegex.exec(content);
            if (match) {
                return match[1].split('；').map(s => s.trim()).filter(s => s);
            }
            // 若无匹配，使用预设建议
            return this.defaultSuggestions.slice(0, 3);
        },

        getDefaultFeedback() {
            return `
                <div class="feedback-summary">
                    <h4 class="issues-title">关键问题定位</h4>
                    <ul class="issues-list">
                        <li><span class="issue-dimension">创新能力：</span>${this.defaultIssues[0]}</li>
                        <li><span class="issue-dimension">专业知识水平：</span>${this.defaultIssues[1]}</li>
                    </ul>
                    <h4 class="suggestions-title">改进建议</h4>
                    <ul class="suggestions-list">
                        <li>${this.defaultSuggestions[0]}</li>
                        <li>${this.defaultSuggestions[1]}</li>
                        <li>${this.defaultSuggestions[2]}</li>
                    </ul>
                </div>
            `;
        },

        extractAIEvaluation(chatText) {
            const evalRegex = /综合评价[\s\S]*?：([\s\S]*?)(?=改进建议|$)/;
            const match = evalRegex.exec(chatText);
            return match ? match[1].trim() : '面试者在专业知识和创新能力上有提升空间，需强化核心技能和表达能力。';
        },

        getScoreLevel(score) {
            if (score >= 80) return '优秀';
            if (score >= 70) return '良好';
            if (score >= 60) return '一般';
            return '待提高';
        },

        getScoreClass(score) {
            if (score >= 80) return 'excellent';
            if (score >= 70) return 'good';
            if (score >= 60) return 'average';
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
    max-width: 800px;
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

.answer-content p {
    margin-bottom: 15px;
    font-size: 15px;
    color: #334155;
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