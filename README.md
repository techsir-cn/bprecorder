# BPRecorder - 血压听写记录系统

🩺 支持语音听写和手工输入的血压记录系统，自动提取血压数据并格式化保存

---

## 快速开始

### 方式 1：Web UI（推荐）

**启动：**
```bash
cd /Users/changwei/codeproject/BP
python3 -m http.server 18888
```

**访问：** http://localhost:18888 或反代后的HTTPS地址

**注意：** 必须使用HTTPS才能使用听写功能

---

## 三区布局设计

### 1️⃣ 识别区（输入区）
- **左侧**：可编辑文本框，支持手工输入
- **右侧**：🎤 听写按钮 + ⬇ 加入待选区按钮
- **功能**：
  - 手工输入血压数据（如"高压120低压80心率60"）
  - 点击🎤按钮启动系统听写
  - 实时提取数字预览
  - 点击⬇按钮转移至待选区

### 2️⃣ 待选区（纯数字）
- 显示提取的高压/低压/心率三个数字
- 支持修改、删除单条数据
- 多条数据可计算平均值
- 点击"采纳"按钮转移至记录区

### 3️⃣ 记录区（格式化结果）
- 格式：`时间---高压/低压(压差)-心率🩺`
- 示例：`23:45---120/80(40)-60🩺`
- 支持复制功能
- 显示原始数据来源（多条时）

---

## 数字提取逻辑

### 支持输入格式

**关键词识别：**
```
"高压120低压80心率60" → 120/80/60
"收缩压120舒张压80脉率60" → 120/80/60
"血压120，低压80，心跳60" → 120/80/60
```

**纯数字位置识别（按顺序）：**
```
"120 80 60" → 第1个=高压，第2个=低压，第3个=心率
"120，80，60" → 同上
```

**同义词归一化：**
- 高压/收缩压 → 高压
- 低压/舒张压 → 低压
- 心率/脉率/脉搏/心跳 → 心率

---

## 浏览器兼容性

| 平台 | 推荐浏览器 | 语音引擎 | 状态 |
|------|-----------|----------|------|
| **iOS** | Safari | Apple | ✅ 完美支持 |
| **macOS** | Safari | Apple | ✅ 完美支持 |
| **Windows** | Edge | Microsoft | ✅ 完美支持 |
| **Android** | Edge | Microsoft | ✅ 完美支持 |
| **Linux** | Edge | Microsoft | ✅ 支持 |

**不支持：**
- ❌ Chrome（所有平台）- 使用Google语音，国内不可用
- ❌ Firefox - 不支持Web Speech API

**提示：** 系统会自动检测浏览器并提示用户使用正确的浏览器

---

## 文件结构

```
BPRecorder/
├── index.html              # 主界面（三区布局）
├── bp_processor.py         # 血压数据处理器
├── webui_v3.py            # Web服务（备用）
├── recordings/            # 录音文件目录
├── records/               # 血压记录保存目录
├── requirements.txt       # Python依赖
├── README.md             # 本文件
└── BPRecorder_技术文档.md  # 详细技术文档
```

---

## 核心功能

### 听写功能
- 使用 Web Speech API 调用系统语音识别
- 支持连续语音识别
- 自动检测数字并预览
- 浏览器自动选择最佳引擎（Apple/Microsoft）

### 手工输入
- textarea 随时可编辑
- 支持复制粘贴
- 实时数字提取预览

### 数据处理
- 单条记录：格式化保存
- 多条记录：自动计算平均值后格式化
- 保留原始数据来源供核对
- 支持修改、删除、复制

---

## 部署建议

### 本地使用
```bash
cd /Users/changwei/codeproject/BP
python3 -m http.server 18888
```

### 反向代理（推荐用于移动设备）

**Nginx 配置示例：**
```nginx
location / {
    proxy_pass http://127.0.0.1:18888;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # WebSocket支持
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

**注意：** 必须使用HTTPS才能使用听写功能（麦克风权限要求）

---

## 依赖安装

```bash
pip3 install -r requirements.txt

# 如需音频处理（可选）
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Linux
```

---

## 开发者

- 版本：v0.1
- 更新：2026-03-13
- 特点：系统语音识别，无需API Key
