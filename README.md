# 智学网查分系统
## 开发介绍
前端采用html+javascript+css开发，使用bootstrap框架

后端使用python+django开发

智学网api来自:[@anwenhu/zhixuewang-python](https://github.com/anwenhu/zhixuewang-python)

## 生产环境参数
系统采用nginx+uwsgi部署生产环境，前后端使用socket通信

nginx反向代理https

## 部署说明

### 目录结构
exam -> 主程序

examweb -> 查分应用（所有查分相关的源码都在这里）

-> exams -> 存储缓存的考试信息

-> templates -> html静态文件

static -> 静态文件

### 启动前注意事项
请先前往exam/settings.py设置SECRET_KEY和mysql连接信息
启动前，请先运行
```bash
python manage.py makemigrations
python manage.py migrate
```
