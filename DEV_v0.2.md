# BPRecorder v0.2 开发文档

## 开发版本
- v0.2-2603140034
- 基于需求文档：REQUIREMENTS_v0.2.md

---

## 一、识别模块开发

### 1.1 布局改造

#### 当前代码位置
- 文件：index.html
- 版本号：line 210
- 标题：line 214 `<h2>📝 识别区（输入区）</h2>`
- 状态区：line 216 `<div id="status">`
- 听写按钮：line 221 `<button id="dictateBtn">听写</button>`

#### 改造内容
1. 标题行：`📝 识别区（输入区）`
2. 下一行显示描述：`支持直接输入和前端听写`（前端听写是{当前选择方式}，动态显示）
3. 右上角不需要额外显示当前方式，因为描述里已经显示
4. "听写"按钮改为"识别"按钮

#### HTML修改
```html
<!-- 识别区 -->
<div class="card">
    <h2>📝 识别区（输入区）</h2>
    <div id="status" class="status info">支持直接输入和<span id="currentMethod">前端听写</span></div>
    ...
    <button id="dictateBtn" class="btn btn-dictate">识别</button>
    ...
</div>
```

### 1.2 识别配置区

#### 触发方式
- 长按"识别"按钮 → 显示配置区

#### 配置区DOM结构
```html
<div id="recognitionConfig" style="display:none;">
    <h3>识别方式配置</h3>
    <label><input type="radio" name="recognitionMethod" value="browser" checked> 前端听写</label>
    <label><input type="radio" name="recognitionMethod" value="cloud" disabled> 云端听写(预留)</label>
    <label><input type="radio" name="recognitionMethod" value="bluetooth" disabled> 蓝牙识别(预留)</label>
    <label><input type="radio" name="recognitionMethod" value="camera" disabled> 拍照识别(预留)</label>
    <!-- 云端配置项 -->
    <div id="cloudConfig" style="display:none;">
        <input type="text" id="cloudUrl" placeholder="API URL">
        <input type="text" id="cloudToken" placeholder="Token">
    </div>
    <!-- 蓝牙配置项 -->
    <div id="bluetoothConfig" style="display:none;">
        <select id="bluetoothDevice"></select>
    </div>
    <button onclick="saveRecognitionConfig()">保存</button>
</div>
```

#### JS逻辑
```javascript
// 识别配置
const recognitionConfig = {
    current: 'browser',  // 当前方式
    cloud: { url: '', token: '' },
    bluetooth: { device: '' }
};

// 长按检测
let dictateBtnTimer = null;
dictateBtn.addEventListener('touchstart', () => {
    dictateBtnTimer = setTimeout(() => {
        document.getElementById('recognitionConfig').style.display = 'block';
    }, 800);
});
dictateBtn.addEventListener('touchend', () => {
    if (dictateBtnTimer) clearTimeout(dictateBtnTimer);
});

// 保存配置
function saveRecognitionConfig() {
    const selected = document.querySelector('input[name="recognitionMethod"]:checked').value;
    recognitionConfig.current = selected;
    document.getElementById('currentMethod').textContent = getMethodName(selected);
    saveConfig();
    document.getElementById('recognitionConfig').style.display = 'none';
}

// 获取方式名称
function getMethodName(method) {
    const names = {
        browser: '前端听写',
        cloud: '云端听写',
        bluetooth: '蓝牙识别',
        camera: '拍照识别'
    };
    return names[method] || method;
}
```

### 1.3 识别按钮行为

#### 当前代码位置
- 函数：line 368 `dictateBtn.onclick`

#### 改造内容
- 语音识别（前端听写/云端听写）：有"识别"和"停止"两个状态
- 蓝牙/拍照：只有"识别"，一次性动作

```javascript
dictateBtn.onclick = function() {
    const method = recognitionConfig.current;
    if (method === 'browser' || method === 'cloud') {
        // 语音识别：有开始/停止两个状态
        if (isListening) {
            stopListening();
            dictateBtn.textContent = '识别';
        } else {
            startListening();
            dictateBtn.textContent = '停止';
        }
    } else if (method === 'bluetooth') {
        // 蓝牙：一次性动作
        startBluetooth();
    } else if (method === 'camera') {
        // 拍照：一次性动作
        startCamera();
    }
};
```

---

## 二、提取模块开发

### 2.1 当前代码位置
- 函数：line 398 `extractThreeNumbers(text)`
- 正则关键词：line 419-421（高压/低压/心率关键词硬编码）

### 2.2 提取配置区

#### 触发方式
- 长按"提取"按钮 → 显示配置区

#### 配置区DOM结构
```html
<div id="extractionConfig" style="display:none;">
    <h3>提取方式配置</h3>
    <label><input type="radio" name="extractionMethod" value="regex" checked onchange="toggleExtractionConfig()"> 正则</label>
    <label><input type="radio" name="extractionMethod" value="model" disabled onchange="toggleExtractionConfig()"> 模型(预留)</label>
    
    <!-- 正则配置 -->
    <div id="regexConfig">
        <input type="text" id="regexHigh" placeholder="高压关键词（用|分隔）" value="高压|收缩压">
        <input type="text" id="regexLow" placeholder="低压关键词（用|分隔）" value="低压|舒张压">
        <input type="text" id="regexPulse" placeholder="心率关键词（用|分隔）" value="心率|脉率|脉搏|心跳">
    </div>
    
    <!-- 模型配置 -->
    <div id="modelConfig" style="display:none;">
        <input type="text" id="modelUrl" placeholder="模型URL">
        <input type="text" id="modelToken" placeholder="Token（可选）">
        <textarea id="modelPrompt" placeholder="提示词"></textarea>
    </div>
    
    <button onclick="saveExtractionConfig()">保存</button>
</div>
```

#### JS逻辑
```javascript
// 提取配置
const extractionConfig = {
    current: 'regex',
    regex: {
        high: ['高压', '收缩压'],
        low: ['低压', '舒张压'],
        pulse: ['心率', '脉率', '脉搏', '心跳']
    },
    model: {
        url: '',
        token: '',
        prompt: ''
    }
};

// 长按检测
let addBtnTimer = null;
addBtn.addEventListener('touchstart', () => {
    addBtnTimer = setTimeout(() => {
        document.getElementById('extractionConfig').style.display = 'block';
    }, 800);
});

// 切换配置显示
function toggleExtractionConfig() {
    const method = document.querySelector('input[name="extractionMethod"]:checked').value;
    document.getElementById('regexConfig').style.display = method === 'regex' ? 'block' : 'none';
    document.getElementById('modelConfig').style.display = method === 'model' ? 'block' : 'none';
}

// 保存配置
function saveExtractionConfig() {
    const method = document.querySelector('input[name="extractionMethod"]:checked').value;
    extractionConfig.current = method;
    
    if (method === 'regex') {
        extractionConfig.regex.high = document.getElementById('regexHigh').value.split('|');
        extractionConfig.regex.low = document.getElementById('regexLow').value.split('|');
        extractionConfig.regex.pulse = document.getElementById('regexPulse').value.split('|');
    } else if (method === 'model') {
        extractionConfig.model.url = document.getElementById('modelUrl').value;
        extractionConfig.model.token = document.getElementById('modelToken').value;
        extractionConfig.model.prompt = document.getElementById('modelPrompt').value;
    }
    
    saveConfig();
    document.getElementById('extractionConfig').style.display = 'none';
}
```

### 2.3 提取函数改造

```javascript
function extractThreeNumbers(text) {
    if (extractionConfig.current === 'regex') {
        return extractByRegex(text);
    } else if (extractionConfig.current === 'model') {
        return extractByModel(text);
    }
}

function extractByRegex(text) {
    const highKeywords = extractionConfig.regex.high;
    const lowKeywords = extractionConfig.regex.low;
    const pulseKeywords = extractionConfig.regex.pulse;
    // ... 原有正则逻辑
}

function extractByModel(text) {
    // 调用模型API（预留）
    // POST extractionConfig.model.url
    // Header: Authorization: Bearer token
    // Body: prompt + text
}
```

---

## 三、记录区模块开发

### 3.1 当前代码位置
- 格式化：line 715

### 3.2 配置区

#### 触发方式
- 长按记录区标题 → 显示配置区

```html
<div id="recordConfig" style="display:none;">
    <h3>记录格式配置</h3>
    <input type="text" id="recordFormat" value="HH:MM---high/low(diff)-pulse🩺">
    <small>可用变量: HH, MM, high, low, diff, pulse</small>
    <button onclick="saveRecordConfig()">保存</button>
</div>
```

### 3.3 格式化函数

```javascript
const recordFormatConfig = {
    template: 'HH:MM---high/low(diff)-pulse🩺'
};

function formatRecord(item) {
    const time = item.time.split(':');
    return recordFormatConfig.template
        .replace('HH', time[0])
        .replace('MM', time[1])
        .replace('high', item.high)
        .replace('low', item.low)
        .replace('diff', item.diff)
        .replace('pulse', item.pulse);
}
```

### 3.4 备注分离

```javascript
function renderRecords() {
    recordList.innerHTML = recordData.map((item, index) => {
        const text = formatRecord(item);
        const sources = item.sources ? `（来源：...）` : '';
        return `
            <div class="record-item">
                <div>
                    <span>${text}</span>
                </div>
                <button onclick="copyRecord('${text}')">复制</button>
            </div>
            ${sources ? `<div class="record-note">${sources}</div>` : ''}
        `;
    }).join('');
}
```

---

## 四、配置文件系统

### 4.1 用户标识

#### 未注册用户
- 生成唯一cookie: `userId=uuid`
- 目录结构: `./users/{cookie}/config.json`

#### 注册用户
- 用户名作为标识
- 目录结构: `./users/{username}/config.json`

### 4.2 配置文件格式

```json
{
    "recognition": {
        "current": "browser",
        "cloud": { "url": "", "token": "" },
        "bluetooth": { "device": "" }
    },
    "extraction": {
        "current": "regex",
        "regex": {
            "high": ["高压", "收缩压"],
            "low": ["低压", "舒张压"],
            "pulse": ["心率", "脉率", "脉搏", "心跳"]
        },
        "model": {
            "url": "",
            "token": "",
            "prompt": ""
        }
    },
    "record": {
        "format": "HH:MM---high/low(diff)-pulse🩺"
    }
}
```

### 4.3 默认配置
- 首次进入页面时使用默认配置
- 默认配置即当前硬编码的配置

### 4.4 配置读写

```javascript
// 保存配置到服务器
function saveConfig() {
    const userId = getCookie('userId') || generateUserId();
    const config = {
        recognition: recognitionConfig,
        extraction: extractionConfig,
        record: recordFormatConfig
    };
    
    fetch('/api/config/' + userId, {
        method: 'POST',
        body: JSON.stringify(config)
    });
}

// 加载配置
function loadConfig() {
    const userId = getCookie('userId');
    if (!userId) {
        // 使用默认配置
        return;
    }
    
    fetch('/api/config/' + userId)
        .then(res => res.json())
        .then(config => {
            Object.assign(recognitionConfig, config.recognition);
            Object.assign(extractionConfig, config.extraction);
            Object.assign(recordFormatConfig, config.record);
        });
}
```

---

## 五、开发顺序

1. 备份当前版本 v0.1-2603130032
2. 更新版本号到 v0.2-2603140034
3. 实现识别模块化（布局 + 长按配置 + 按钮行为）
4. 实现提取模块化（长按配置 + 正则可配置）
5. 实现记录区模块化（格式可配置 + 备注分离）
6. 实现配置文件系统（cookie + 目录结构）
7. 测试
8. commit

---

## 六、验收清单

- [ ] 识别区标题和描述分行显示
- [ ] 描述显示"支持直接输入和{当前方式}"
- [ ] "听写"按钮改为"识别"
- [ ] 长按识别按钮进入配置区
- [ ] 配置区可选择识别方式
- [ ] 长按提取按钮进入配置区
- [ ] 配置区可选择提取方式（正则/模型）
- [ ] 正则公式可编辑
- [ ] 长按记录区标题进入配置区
- [ ] 记录格式可编辑
- [ ] 备注显示在记录最下方
- [ ] 复制只复制正式内容
- [ ] 配置按cookie/用户名保存