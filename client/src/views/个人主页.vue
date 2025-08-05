<template>
    <div class="nav-container">
        
        <div class="blog-container">
            <div v-for="blog in extractedData" :key="blog.id" class="blog-card" @click="goToBlogPage(blog)">
                <div class="blog-header">
                    <h3 class="blog-title">{{ blog.title }}</h3>
                    <h4 class="blog-author">{{ blog.username }}</h4>
                    <span class="blog-date">{{ formatDate(blog.date) }}</span>
                </div>
                <p class="comment-count">评论数量：{{ getCommentsForBlog(blog.date).length }}</p>
                <p class="like-count">点赞数量：{{ blog.likeCount }}</p>
                <button class="delete-btn" @click.stop="deleteBlog(blog)">删除</button>
            </div>
        </div>
        <!--
        <div class="fixed-button-container">
            <button class="friend-btn" @click="openFriendApplyDialog">好友申请</button>
        </div>
        -->
        <div  class="friend-dialog" :class="{ 'show': showFriendApplyDialog }">
            <div class="dialog-header">好友申请</div>
            <div class="dialog-content">
                <ul>
                    <li v-for="apply in friendApplys" :key="apply.username" class="apply-item">
                        {{ apply.username }}的申请 - {{ apply.isReplied }}
                        <button class="accept-btn" @click="acceptFriendApply(apply.username)">接受</button>
                        <button class="reject-btn" @click="rejectFriendApply(apply.username)">拒绝</button>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'PersonalHome',
    data() {
        return {
            activeIndex: 'personal',
            sortedBlogs: [],
            extractedData: [],
            allComments: [],
            username: '',
            showFriendApplyDialog: false,
            friendApplys: []
        };
    },
    computed: {
        getCommentsForBlog() {
            return (blogDate) => {
                if (!this.allComments) return [];
                return this.allComments.filter(comment => comment && comment.blogDate === blogDate);
            };
        }
    },
    methods: {
        handleSelect(index) {
            this.activeIndex = index;
            console.log('当前选中：', index);
            if (index === 'home') {
                this.$router.push('/home');
            }
            if (index === 'exit') {
                // 可在此处添加退出登录等逻辑
            }
        },
        async fetchUserBlogs() {
            try {
                const apiUrl = 'https://tender-secure-bluegill.ngrok-free.app';
                // 配置请求头
                const headers = { 'ngrok-skip-browser-warning': 'true' };
                
                const [blogsRes, commentsRes] = await Promise.all([
                    axios.get(`${apiUrl}/api/personBlogs/${this.username}`, { headers }),
                    axios.get(`${apiUrl}/api/getComments`, { headers })
                ]);
                this.sortedBlogs = blogsRes.data.a;
                this.extractedData = this.sortedBlogs.map((blogItem) => ({
                    date: blogItem.date,
                    title: blogItem.title,
                    content: blogItem.content,
                    username: blogItem.username
                }));

                this.allComments = commentsRes.data;

                // 预加载点赞数量
                const blogsWithLikes = await Promise.all(this.extractedData.map(async (blog) => {
                    const likeCount = await this.getLikeCount(blog.username, blog.date);
                    return {
                        ...blog,
                        likeCount
                    };
                }));
                this.extractedData = blogsWithLikes;
            } catch (error) {
                console.error('获取数据失败:', error);
            }
        },
        async getLikeCount(blogUsername, blogDate) {
            try {
                const apiUrl = 'https://tender-secure-bluegill.ngrok-free.app';
                const headers = { 'ngrok-skip-browser-warning': 'true' };
                
                const response = await axios.get(`${apiUrl}/api/getTotallikes/${blogUsername}/${blogDate}`, { headers });
                return response.data.number;
            } catch (error) {
                console.error('获取点赞数量失败:', error);
                return 0;
            }
        },
        goToBlogPage(blog) {
            const blogComments = this.getCommentsForBlog(blog.date);
            const blogData = {
                content: blog.content,
                comments: blogComments,
                username: blog.username,
                date: blog.date,
                title: blog.title
            };
            localStorage.setItem('selectedBlogData', JSON.stringify(blogData));
            this.$router.push({ name: 'blog' });
        },
        async deleteBlog(blog) {
            try {
                const apiUrl = 'https://tender-secure-bluegill.ngrok-free.app';
                const headers = { 'ngrok-skip-browser-warning': 'true' };
                
                const response = await axios.delete(`${apiUrl}/api/deleteBlogsByTime`, { 
                    headers,
                    data: { date: blog.date }
                });
                if (response.status === 200) {
                    this.extractedData = this.extractedData.filter(b => b.date !== blog.date);
                } else {
                    console.error('删除博客失败，状态码:', response.status);
                }
            } catch (error) {
                console.error('删除博客失败:', error);
            }
        },
        formatDate(dateStr) {
            const date = new Date(dateStr);
            date.setTime(date.getTime() );
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
        },
        openFriendApplyDialog() {
            this.showFriendApplyDialog = true;
            this.fetchFriendApplys();
        },
        async fetchFriendApplys() {
            try {
                const apiUrl = 'https://tender-secure-bluegill.ngrok-free.app';
                const headers = { 'ngrok-skip-browser-warning': 'true' };
                
                const response = await axios.get(`${apiUrl}/api/getApplys/${this.username}`, { headers });
                this.friendApplys = response.data.friendApplys;
            } catch (error) {
                console.error('获取好友申请失败:', error);
            }
        },
        async acceptFriendApply(friendUsername) {
            try {
                const apiUrl = 'https://tender-secure-bluegill.ngrok-free.app';
                const headers = { 'ngrok-skip-browser-warning': 'true' };
                
                const response = await axios.post(`${apiUrl}/api/updateFriendApply`, 
                    { currentUsername: this.username, friendUsername, status: 'accept' },
                    { headers }
                );
                if (response.status === 200) {
                    console.log('接受好友申请成功');
                    await this.fetchFriendApplys();
                } else {
                    console.error('接受好友申请失败，状态码:', response.status);
                }
            } catch (error) {
                console.error('接受好友申请失败:', error);
            }
        },
        async rejectFriendApply(friendUsername) {
            try {
                const apiUrl = 'https://tender-secure-bluegill.ngrok-free.app';
                const headers = { 'ngrok-skip-browser-warning': 'true' };
                
                const response = await axios.post(`${apiUrl}/api/updateFriendApply`, 
                    { currentUsername: this.username, friendUsername, status: 'reject' },
                    { headers }
                );
                if (response.status === 200) {
                    console.log('拒绝好友申请成功');
                    await this.fetchFriendApplys();
                } else {
                    console.error('拒绝好友申请失败，状态码:', response.status);
                }
            } catch (error) {
                console.error('拒绝好友申请失败:', error);
            }
        }
    },
    mounted() {
        this.username = localStorage.getItem('username');
        this.fetchUserBlogs();
        //this.fetchFriendApplys();
    }
};
</script>

<style scoped>
/* 样式保持不变 */
.nav-container {
    background: transparent;
    padding: 0px;
    box-shadow: 0 ;
    min-height: 100vh;
}

.header-section {
    text-align: center;
    margin-bottom: 20px;
}

.title {
    font-size: 28px;
    color: #4CAF50;
    margin: 0;
    font-weight: 600;
}

.designer {
    font-size: 14px;
    color: #6c757d;
    margin-top: 5px;
    display: block;
}

/* 导航菜单样式 */
.nav-menu {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 20px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
}

.nav-item {
    padding: 12px 22px;
    border-radius: 8px;
    font-size: 16px;
    color: #333;
    text-decoration: none;
    transition: all 0.3s ease;
    background: #f5f7fa;
}

.nav-item.active {
    background: #409eff;
    color: white;
}

.nav-item:hover:not(.active) {
    background: #e6f7ff;
}

/* 博客容器样式 */
.blog-container {
    padding: 20px;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-around;
}

.blog-card {
    width: calc(25% - 10px);
    margin-bottom: 20px;
    background-color: #fff;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    padding: 15px;
    transition: transform 0.2s ease;
}

.blog-card:hover {
    transform: scale(1.03);
    cursor: pointer;
}

.blog-header {
    margin-bottom: 10px;
}

.blog-title {
    font-size: 18px;
    font-weight: bold;
    color: #333;
    margin-bottom: 10px;
}

.blog-author {
    font-size: 14px;
    color: #666;
    margin-bottom: 5px;
}

.blog-date {
    color: #999;
    margin-bottom: 10px;
    display: block;
}

.comment-count,
.like-count {
    color: #666;
    margin-bottom: 5px;
}

.delete-btn {
    margin-top: 10px;
    padding: 6px 12px;
    background: #f56c6c;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.3s ease;
}

.delete-btn:hover {
    background: #f78989;
}

/* 固定按钮样式 */
.fixed-button-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 100;
}

.friend-btn {
    padding: 8px 16px;
    background: #409eff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.3s ease;
}

.friend-btn:hover {
    background: #66b1ff;
}

/* 好友申请对话框样式 */
.friend-dialog {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.friend-dialog.show {
    opacity: 1;
    visibility: visible;
}

.dialog-header {
    background: #fff;
    padding: 15px 20px;
    font-size: 18px;
    font-weight: bold;
    border-radius: 8px 8px 0 0;
    width: 300px;
    text-align: center;
}

.dialog-content {
    background: #fff;
    width: 300px;
    border-radius: 0 0 8px 8px;
}

.apply-item {
    padding: 15px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.accept-btn,
.reject-btn {
    padding: 4px 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

.accept-btn {
    background: #67c23a;
    color: white;
    margin-left: 5px;
}

.reject-btn {
    background: #f56c6c;
    color: white;
}

/* 响应式设计 */
@media (max-width: 992px) {
    .blog-card {
        width: calc(50% - 10px);
    }
}

@media (max-width: 768px) {
    .blog-card {
        width: 100%;
    }
    
    .nav-menu {
        flex-wrap: wrap;
    }
    
    .nav-item {
        padding: 8px 12px;
        font-size: 14px;
    }
}
</style>