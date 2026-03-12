# BPRecorder 技术文档

## 系统架构

### 前端架构
```
浏览器 (HTTPS)
    ↓
index.html (三区布局)
    ├── 识别区：textarea + Web Speech API
    ├── 待选区：数字提取结果
    └── 记录区：格式化输出
```

### 核心设计变更
**v3.0 重大变更：**
- ❌ 移除 Whisper 本地识别（依赖大、延迟高）
- ✅ 改用系统 Web Speech API（轻量、低延迟）
- ✅ 三区独立设计（识别→待选→记录）
- ✅ 浏览器自适应引擎选择

---

## 三区布局详解

### 第一区：识别区（输入区）

**HTML 结构：**
```html
<div class="recognition-area">
    <textarea id="resultText"><!-- 可编辑 --></textarea>
    <div class="transfer-section">
        <button id="dictateBtn">🎤</button>
        <button id="addBtn">⬇</button>
    </div>
</div>
```

**功能逻辑：**
1. **手工输入**：textarea 支持随时编辑
2. **语音输入**：调用 Web Speech API
3. **实时提取**：oninput 事件实时检测数字
4. **手动转移**：点击 ⬇ 按钮转移至待选区

**数字提取算法：**
```javascript
function extractThreeNumbers(text) {
    // 策略1：关键词匹配
    const highMatch = text.match(/高压[^\d]*(\d{2,3})|收缩压[^\d]*(\d{2,3})/);
    const lowMatch = text.match(/低压[^\d]*(\d{2,3})|舒张压[^\d]*(\d{2,3})/);
    const pulseMatch = text.match(/心率[^\d]*(\d{2,3})|脉率[^\d]*(\d{2,3})/);
    
    // 策略2：位置匹配（无关键词时）
    const allNumbers = text.match(/\d{2,3}/g);
    // 第1个=高压，第2个=低压，第3个=心率
}
```

**同义词映射表：**
| 输入词 | 映射为 |
|--------|--------|
| 高压/收缩压 | 高压 |
| 低压/舒张压 | 低压 |
| 心率/脉率/脉搏/心跳 | 心率 |

---

### 第二区：待选区

**数据结构：**
```javascript
pendingData = [{
    id: timestamp,
    high: 120,
    low: 80,
    pulse: 60,
    originalText: "高压120低压80心率60"
}]
```

**操作：**
- ✅ 修改：弹出 prompt 编辑数字
- 🗑️ 删除：从数组移除
- ⬇️ 采纳：转移至记录区

**采纳逻辑：**
```javascript
// 单条：直接格式化
// 多条：计算平均后格式化
const result = {
    time: currentTime,
    high: avgHigh,
    low: avgLow,
    pulse: avgPulse,
    diff: high - low,
    count: pendingData.length,
    sources: [...originalData]  // 保留原始数据
}
```

---

### 第三区：记录区

**输出格式：**
```
23:45---120/80(40)-60🩺
```

**多条平均示例：**
```
来源：118/78/58、120/82/60、122/80/62
结果：23:45---120/80(40)-60🩺
```

---

## Web Speech API 实现

### 浏览器检测逻辑
```javascript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

// 平台检测
const isIOS = /iPad|iPhone|iPod/.test(ua);
const isMac = /Mac/.test(ua) && !isIOS;
const isWin = /Windows/.test(ua);
const isAndroid = /Android/.test(ua);
const isLinux = /Linux/.test(ua) && !isAndroid;
const isEdge = /Edg/.test(ua);
const isSafari = /Safari/.test(ua) && !/Chrome/.test(ua);
```

### 推荐策略
| 平台 | 浏览器 | 底层引擎 | 可用性 |
|------|--------|----------|--------|
| iOS | Safari | Apple Speech | ✅ |
| macOS | Safari | Apple Speech | ✅ |
| Windows | Edge | Microsoft Speech | ✅ |
| Android | Edge | Microsoft Speech | ✅ |
| Linux | Edge | Microsoft Speech | ✅ |
| 任意 | Chrome | Google Speech | ❌ 国内不可用 |

### 为什么不能直接用系统API？

**Web 应用限制：**
- Web Speech API 必须由浏览器实现
- Chrome 强制使用 Google 服务
- 无法绕过浏览器直接调用系统 API

**解决方案：**
- 使用 Electron 开发桌面应用（可调用系统 API）
- 或提示用户使用 Edge/Safari

---

## 语音识别配置

```javascript
const recognition = new SpeechRecognition();
recognition.lang = 'zh-CN';           // 中文
recognition.continuous = true;        // 持续识别
recognition.interimResults = true;    // 显示中间结果
recognition.maxAlternatives = 1;      // 单一结果
```

**关键配置：**
- `continuous: true` - 不因沉默断开
- `interimResults: true` - 实时反馈
- 自动重启：onend 事件重新启动

---

## 文件清单

### 核心文件
- `index.html` - 前端主界面（584行）
- `bp_processor.py` - 数据处理（272行）

### 辅助文件
- `webui_v3.py` - 备用 Web 服务
- `requirements.txt` - Python 依赖
- `README.md` - 用户文档
- `BPRecorder_技术文档.md` - 本文档

### 数据目录
- `recordings/` - 录音文件（如保留）
- `records/` - 血压记录（Markdown格式）

---

## 部署要点

### 必须 HTTPS
麦克风权限要求安全上下文，必须 HTTPS。

### 反向代理
```nginx
server {
    listen 443 ssl;
    location / {
        proxy_pass http://localhost:18888;
    }
}
```

### 本地开发
```bash
# 仅用于开发，听写功能不可用
python3 -m http.server 18888
```

---

## 版本历史

### v3.0（当前）- 2026-03-11
- 移除 Whisper 依赖
- 改用 Web Speech API
- 三区独立设计
- 浏览器自适应

### v2.x
- 使用 Whisper 本地识别
- 音频文件上传模式

---

## 技术限制

1. **Chrome 不可用** - 强制 Google 语音，国内不通
2. **Firefox 不支持** - 无 Web Speech API
3. **必须 HTTPS** - 麦克风权限要求
4. **无法直接调系统API** - 需浏览器中转

## 未来方向

1. **Electron 桌面版** - 直接调用系统语音
2. **服务端语音识别** - 火山引擎/讯飞API
3. **移动端 App** - 原生调用系统听写
