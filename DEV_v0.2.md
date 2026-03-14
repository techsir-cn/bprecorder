# BPRecorder v0.2 开发文档

## 开发版本
- v0.2-2603130033
- 基于需求文档：REQUIREMENTS_v0.2.md

---

## 一、识别模块化开发

### 1.1 布局改造

#### 当前代码位置
- 标题区：line 214 `<h2>📝 识别区（输入区）</h2>`
- 状态区：line 216 `<div id="status" class="status info">`

#### 改造内容
1. 标题改为"📝 识别区"
2. 描述改为"支持直接输入和当前选择方式"
3. 右上角添加当前方式显示区域
4. "听写"按钮改为"识别"按钮

#### 实现步骤
1. 修改HTML结构：标题+描述合并，添加当前方式显示
2. CSS添加当前方式显示样式
3. JS添加当前方式变量 `currentRecognitionMethod`
4. 识别按钮onclick绑定到currentRecognitionMethod

### 1.2 长按配置

#### 实现
- 识别区标题添加 `oncontextmenu` 事件（右键）或 `onlongpress`（移动端）
- 移动端用 `touchstart` + `setTimeout` 检测长按
- 长按进入配置区（显示/隐藏配置DOM）

### 1.3 配置区

#### 配置区DOM
```html
<div id="recognitionConfig" style="display:none;">
  <h3>识别方式配置</h3>
  <label><input type="radio" name="recognition" value="browser" checked> 前端听写</label>
  <!-- 预留选项disabled -->
  <label><input type="radio" name="recognition" value="cloud" disabled> 云端听写(预留)</label>
  <label><input type="radio" name="recognition" value="bluetooth" disabled> 蓝牙识别(预留)</label>
  <label><input type="radio" name="recognition" value="camera" disabled> 拍照识别(预留)</label>
  <button onclick="saveRecognitionConfig()">保存</button>
</div>
```

#### 保存逻辑
- 保存到 localStorage
- 更新 currentRecognitionMethod
- 更新UI显示

---

## 二、提取模块化开发

### 2.1 待选区配置

#### 当前代码位置
- 函数：line 398 `extractThreeNumbers(text)`
- 正则关键词：line 400-402

#### 改造内容
1. 待选区标题添加长按事件
2. 配置区显示当前正则公式，可编辑
3. 保存后更新正则

#### 实现步骤
1. 提取正则公式到配置变量
2. 添加配置区DOM（正则输入框）
3. 长按标题显示配置区
4. 保存时更新正则变量

### 2.2 代码结构

```javascript
// 提取模块配置
const extractionConfig = {
    method: 'regex',
    regex: {
        high: '高压|收缩压',
        low: '低压|舒张压',
        pulse: '心率|脉率|脉搏|心跳'
    }
};

function extractThreeNumbers(text) {
    if (extractionConfig.method === 'regex') {
        // 使用可配置的正则
    }
}
```

---

## 三、记录区模块化开发

### 3.1 当前代码位置
- 格式化：line 715 `const text = \`${item.time}---${item.high}/${item.low}(${item.diff})-${item.pulse}🩺\`;`

### 3.2 改造内容
1. 记录区标题添加长按事件
2. 配置区显示格式模板，可编辑
3. 备注移到最下方

### 3.3 格式配置
```javascript
const recordFormat = {
    template: 'HH:MM---高压/低压(压差)-心率🩺',
    // 可用变量: HH, MM, high, low, diff, pulse
};
```

### 3.4 实现步骤
1. 提取格式化字符串到配置变量
2. 添加配置区DOM（模板输入框）
3. 长按标题显示配置区
4. 备注分离：正式内容 + 备注

---

## 四、模块化架构

### 4.1 模块注册表
```javascript
const modules = {
    recognition: {
        current: 'browser',
        browser: { name: '前端听写', start: browserStart, stop: browserStop },
        cloud: { name: '云端听写', start: cloudStart, stop: cloudStop, disabled: true },
        bluetooth: { name: '蓝牙识别', start: btStart, stop: btStop, disabled: true },
        camera: { name: '拍照识别', start: cameraStart, stop: cameraStop, disabled: true }
    },
    extraction: {
        current: 'regex',
        regex: { name: '正则', extract: regexExtract },
        model: { name: '小模型', extract: modelExtract, disabled: true }
    },
    storage: {
        current: 'none',
        none: { name: '无存储', save: noop, load: noop },
        cloud: { name: '云端存储', save: cloudSave, load: cloudLoad, disabled: true }
    }
};
```

### 4.2 调用方式
```javascript
// 识别
modules.recognition[modules.recognition.current].start();

// 提取
const data = modules.extraction[modules.extraction.current].extract(text);

// 存储
modules.storage[modules.storage.current].save(record);
```

---

## 五、开发顺序

1. ✅ 备份 v0.1-2603130032
2. 更新版本号到 v0.2-2603130033
3. 实现识别模块化（布局 + 长按配置）
4. 实现提取模块化（正则可配置）
5. 实现记录区模块化（格式可配置 + 备注分离）
6. 添加模块化架构代码
7. 测试
8. commit

---

## 验收标准

- [ ] 识别区显示当前方式，右上角
- [ ] "听写"改为"识别"
- [ ] 长按识别区标题进入配置
- [ ] 配置区可选择识别方式
- [ ] 长按待选区标题进入配置
- [ ] 正则公式可编辑
- [ ] 长按记录区标题进入配置
- [ ] 记录格式可编辑
- [ ] 备注显示在记录最下方
- [ ] 复制只复制正式内容
