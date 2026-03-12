#!/usr/bin/env python3
"""BPRecorder - Web UI v3 (按老板的图)"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess
import json
import threading
import wave
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.resolve()
RECORDS_DIR = WORKSPACE / "records"
RECORDINGS_DIR = WORKSPACE / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

rec_state = {"log": [], "pending": []}

HTML = """<!DOCTYPE html>
<html><head><title>🩺 BPRecorder</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,#6c5ce7 0%,#a29bfe 100%);min-height:100vh;padding:20px;}
.container{max-width:500px;margin:0 auto;}
.card{background:white;border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:0 4px 20px rgba(0,0,0,0.15);}

/* 第一个框 - 录音识别 */
.record-area h2{color:#333;margin-bottom:20px;font-size:18px;display:flex;align-items:center;gap:8px;}
.status-msg{text-align:center;padding:20px;color:#999;font-size:15px;}
.status-msg.error{color:#e74c3c;background:#fef2f2;border-radius:8px;}
.status-msg.success{color:#27ae60;background:#f0fdf4;border-radius:8px;}
.btn-row{display:flex;gap:12px;margin-bottom:16px;}
.btn{flex:1;padding:14px;border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;}
.btn-danger{background:#ff7675;color:white;}
.btn-success{background:#7bed9f;color:#2d3436;}
.btn:disabled{opacity:0.4;cursor:not-allowed;}
.divider{height:1px;background:#e9ecef;margin:16px 0;}

/* 识别结果列表 */
.result-list{min-height:60px;}
.result-item{display:flex;align-items:center;justify-content:space-between;padding:14px;margin-bottom:10px;background:#f8f9fa;border-radius:10px;border-left:4px solid #6c5ce7;}
.result-numbers{font-size:22px;font-weight:bold;color:#27ae60;font-family:monospace;}
.result-actions{display:flex;gap:8px;}
.result-actions .btn{padding:8px 12px;font-size:14px;flex:none;border-radius:8px;}
.btn-warning{background:#fdcb6e;color:#2d3436;}
.btn-info{background:#74b9ff;color:#2d3436;}

/* 计算按钮 */
.calc-row{margin-top:16px;}
.calc-row .btn{padding:16px;font-size:18px;width:100%;background:#6c5ce7;color:white;}

/* 第二个框 - 记录 */
.records-area h2{color:#333;margin-bottom:16px;font-size:18px;display:flex;align-items:center;gap:8px;}
.records{background:#f8f9fa;padding:16px;border-radius:12px;max-height:250px;overflow-y:auto;}
.record-item{padding:12px;border-bottom:1px solid #e9ecef;display:flex;justify-content:space-between;align-items:center;}
.record-item:last-child{border-bottom:none;}
.record-date{color:#666;font-size:14px;}
.record-data{font-family:monospace;font-size:16px;color:#27ae60;font-weight:600;}

/* 第三个框 - 日志 */
.log-area h2{color:#333;margin-bottom:12px;font-size:18px;display:flex;align-items:center;gap:8px;}
.log{background:#1e1e2e;color:#00ff88;padding:16px;border-radius:12px;font-family:monospace;font-size:13px;max-height:120px;overflow-y:auto;line-height:1.6;}
</style></head><body>
<div class="container">

<!-- 第一个框：录音识别 -->
<div class="card record-area">
<h2>🎤 录音识别</h2>
<div id="status" class="status-msg">点击录制开始测量</div>
<div class="btn-row">
<button id="startBtn" class="btn btn-danger" onclick="startRecord()">🔴 录制</button>
<button id="stopBtn" class="btn btn-success" onclick="stopRecord()" disabled>⏹️ 停止</button>
</div>
<div class="divider"></div>
<div id="resultList" class="result-list"></div>
<div id="calcRow" class="calc-row" style="display:none;">
<button class="btn btn-info" onclick="calcAverage()">📊 计算平均值</button>
</div>
</div>

<!-- 第二个框：记录 (已计算) -->
<div class="card records-area">
<h2>📋 记录 (已计算)</h2>
<div id="records" class="records">加载中...</div>
</div>

<!-- 第三个框：日志 -->
<div class="card log-area">
<h2>📝 日志</h2>
<div id="log" class="log">等待操作...</div>
</div>

</div>
<script>
let audioChunks = [];
let mediaRecorder = null;
let pendingData = [];

async function startRecord() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
                console.log('收到音频数据块，大小:', event.data.size, 'bytes');
            }
        };
        
        mediaRecorder.onstop = async () => {
            console.log('录音停止，数据块数量:', audioChunks.length);
            
            if (audioChunks.length === 0) {
                document.getElementById('status').textContent = '⚠️ 没有录音数据';
                document.getElementById('status').className = 'status-msg error';
                return;
            }
            
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            console.log('音频 Blob 大小:', audioBlob.size, 'bytes');
            
            // 发送 WebM 文件
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            document.getElementById('status').textContent = '📝 识别中...';
            document.getElementById('status').className = 'status-msg';
            
            try {
                const r = await fetch('/process-webm', {
                    method: 'POST',
                    body: formData
                });
                const data = await r.json();
                console.log('识别结果:', data);
                
                if (data.success) {
                    const d = data.data;
                    const item = {
                        id: Date.now().toString(),
                        high: d.high,
                        low: d.low,
                        pulse: d.pulse,
                        diff: d.diff,
                        timestamp: new Date().toLocaleString('zh-CN', {hour12:false})
                    };
                    pendingData.push(item);
                    renderPending();
                    document.getElementById('status').textContent = '✅ 识别成功';
                    document.getElementById('status').className = 'status-msg success';
                } else {
                    document.getElementById('status').textContent = '⚠️ ' + (data.error || '识别失败');
                    document.getElementById('status').className = 'status-msg error';
                }
            } catch (e) {
                console.error('错误:', e);
                document.getElementById('status').textContent = '❌ ' + e.message;
                document.getElementById('status').className = 'status-msg error';
            }
            
            // 恢复按钮状态
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            
            // 清理
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start(1000); // 每秒发送一个数据块
        
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('status').textContent = '🔴 录音中...';
        document.getElementById('status').className = 'status-msg success';
        
    } catch (e) {
        console.error('录音失败:', e);
        document.getElementById('status').textContent = '⚠️ ' + e.message;
        document.getElementById('status').className = 'status-msg error';
    }
}

function stopRecord() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
    }
}

function renderPending() {
    const container = document.getElementById('resultList');
    const calcRow = document.getElementById('calcRow');
    
    if (pendingData.length === 0) {
        container.innerHTML = '';
        calcRow.style.display = 'none';
    } else {
        container.innerHTML = pendingData.map(p => `
            <div class="result-item" data-id="${p.id}">
                <div class="result-numbers">${p.high}/${p.low}-${p.pulse}</div>
                <div class="result-actions">
                    <button class="btn btn-warning" onclick="editItem('${p.id}')">✏️</button>
                    <button class="btn btn-danger" onclick="deleteItem('${p.id}')">🗑️</button>
                </div>
            </div>
        `).join('');
        calcRow.style.display = 'block';
    }
}

function editItem(id) {
    const item = pendingData.find(p => p.id === id);
    if (!item) return;
    
    const newHigh = prompt('高压:', item.high);
    if (!newHigh) return;
    const newLow = prompt('低压:', item.low);
    if (!newLow) return;
    const newPulse = prompt('心率:', item.pulse);
    if (!newPulse) return;
    
    item.high = parseInt(newHigh);
    item.low = parseInt(newLow);
    item.pulse = parseInt(newPulse);
    item.diff = item.high - item.low;
    renderPending();
}

function deleteItem(id) {
    pendingData = pendingData.filter(p => p.id !== id);
    renderPending();
}

function calcAverage() {
    if (pendingData.length === 0) { alert('没有数据'); return; }
    
    const avgHigh = Math.round(pendingData.reduce((s, p) => s + p.high, 0) / pendingData.length);
    const avgLow = Math.round(pendingData.reduce((s, p) => s + p.low, 0) / pendingData.length);
    const avgPulse = Math.round(pendingData.reduce((s, p) => s + p.pulse, 0) / pendingData.length);
    const avgDiff = avgHigh - avgLow;
    const now = new Date();
    const timeStr = now.toLocaleString('zh-CN', {hour12:false}).replace(/\//g, '-');
    
    fetch('/save-record', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            high: avgHigh,
            low: avgLow,
            pulse: avgPulse,
            diff: avgDiff,
            count: pendingData.length,
            timestamp: timeStr
        })
    }).then(r=>r.json()).then(data=>{
        if(data.success) {
            alert(`✅ 已保存：${avgHigh}/${avgLow}(${avgDiff})-${avgPulse}`);
            pendingData = [];
            renderPending();
            loadRecords();
            document.getElementById('status').textContent = '✅ 已保存';
            document.getElementById('status').className = 'status-msg success';
        } else {
            alert('❌ ' + data.error);
        }
    });
}

function loadRecords() {
    fetch('/records').then(r=>r.json()).then(data=>{
        const container = document.getElementById('records');
        if (data.length === 0) {
            container.innerHTML = '<p style="color:#999;text-align:center;padding:20px;">暂无记录</p>';
        } else {
            container.innerHTML = data.map(r => `
                <div class="record-item">
                    <span class="record-date">${r.date}</span>
                    <span class="record-data">${r.data}</span>
                </div>
            `).join('');
        }
    }).catch(()=>{});
}

function loadLog() {
    fetch('/log').then(r=>r.text()).then(log=>{
        document.getElementById('log').textContent = log || '等待操作...';
    }).catch(()=>{});
}

// 初始加载
loadRecords();
loadLog();
renderPending();
</script></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            index_html = (WORKSPACE / "index.html").read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(index_html.encode("utf-8"))
        elif self.path == "/records":
            records = []
            if RECORDS_DIR.exists():
                recs = sorted(RECORDS_DIR.glob("*.md"), reverse=True)
                if recs:
                    content = recs[0].read_text()
                    lines = [l for l in content.split("\n") if l.startswith("- 20")]
                    for line in lines[-10:]:
                        try:
                            parts = line.replace("- ", "").split("---")
                            records.append(
                                {
                                    "date": parts[0],
                                    "data": parts[1] if len(parts) > 1 else "",
                                }
                            )
                        except:
                            pass
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(records).encode("utf-8"))
        elif self.path == "/log":
            log_text = (
                "\n".join(rec_state["log"][-20:]) if rec_state["log"] else "等待操作..."
            )
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(log_text.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/normalize":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                req = json.loads(body)
                text = req.get("text", "")
                result = self._normalize_bp(text)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        
        elif self.path == "/process-webm":
            # 处理 MediaRecorder 录制的 WebM 文件
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            # 读取 multipart/form-data
            boundary = None
            if "boundary=" in content_type:
                boundary = ("--" + content_type.split("boundary=")[1]).encode()

            body = self.rfile.read(content_length)

            # 简单解析 multipart
            if boundary:
                parts = body.split(boundary)
                for part in parts:
                    if b"audio" in part and b"filename=" in part:
                        # 找到音频数据
                        header_end = part.find(b"\r\n\r\n")
                        if header_end > 0:
                            audio_data = part[header_end + 4 :].rstrip(b"\r\n")
                            if len(audio_data) > 100:
                                result = self._process_webm_audio(audio_data)
                                self.send_response(200)
                                self.send_header("Content-type", "application/json")
                                self.end_headers()
                                self.wfile.write(
                                    json.dumps(result, ensure_ascii=False).encode(
                                        "utf-8"
                                    )
                                )
                                return

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        elif self.path == "/save-record":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                req = json.loads(body)

                high = req.get("high")
                low = req.get("low")
                pulse = req.get("pulse")
                diff = req.get("diff")
                count = req.get("count", 1)
                timestamp = req.get(
                    "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M")
                )

                record_line = f"- {timestamp}---{high}/{low}({diff})-{pulse}🩺B"
                if count > 1:
                    record_line += f" ({count}次平均)"

                month_file = RECORDS_DIR / f"{datetime.now().strftime('%Y-%m')}.md"
                if month_file.exists():
                    content = month_file.read_text()
                    lines = content.split("\n")
                    lines.insert(1, record_line)
                    month_file.write_text("\n".join(lines))
                else:
                    month_file.write_text(
                        f"# {datetime.now().strftime('%Y年%m月')} 血压记录\n\n{record_line}\n"
                    )

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                )

        else:
            self.send_response(404)
            self.end_headers()

    def _normalize_bp(self, text):
        """调用 ollama 标准化血压数据"""
        import requests
        
        prompt = f"""你是一个血压数据提取器。从以下语音识别文本中提取血压数据，输出标准化的 JSON 格式。

要求：
1. 高压/收缩压 → high
2. 低压/舒张压 → low  
3. 心率/脉率/脉搏/心跳 → pulse
4. 中文数字转阿拉伯数字：一百二=120，八十=80，六十=60
5. 去除单位：毫米汞柱、次/分、次每分等
6. 去除前缀后缀：如"高压是"、"测量结果是"等
7. 如果文本中有明确的数值，直接提取

只输出 JSON，不要其他内容。格式：
{{"high": 数字, "low": 数字, "pulse": 数字}}
如果无法提取完整数据，输出 {{"high": null, "low": null, "pulse": null}}

输入文本：{text}"""

        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen3.5:0.8b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            if r.status_code == 200:
                result = r.json()
                import re
                json_match = re.search(r'\{[^{}]*\}', result.get('response', ''))
                if json_match:
                    data = json.loads(json_match.group())
                    return {
                        "success": True,
                        "high": data.get("high"),
                        "low": data.get("low"),
                        "pulse": data.get("pulse")
                    }
            return {"success": False, "error": "无法识别"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def log_message(self, format, *args):
        pass

    def _process_webm_audio(self, webm_data):
        """处理 WebM 音频文件，返回识别结果"""
        rec_state["log"].append(
            f"[{datetime.now().strftime('%H:%M:%S')}] 📥 收到 WebM 数据 {len(webm_data)} bytes"
        )

        # 保存 WebM 文件
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        webm_file = RECORDINGS_DIR / f"rec_{ts}.webm"
        webm_file.write_bytes(webm_data)

        rec_state["log"].append(
            f"[{datetime.now().strftime('%H:%M:%S')}] 💾 保存：{webm_file.name}"
        )

        try:
            import whisper

            model = whisper.load_model("medium")
            res = model.transcribe(
                str(webm_file),
                language="zh",
                temperature=0.1,
                verbose=False,
                initial_prompt="血压测量，高压低压脉率，毫米汞柱，次每分",
            )
            text = res["text"].strip()
            rec_state["log"].append(f"💬 识别：{text}")

            import subprocess

            r = subprocess.run(
                [str(Path(__file__).parent / "bp_processor.py"), text],
                capture_output=True,
                text=True,
            )

            try:
                import json

                data = json.loads(r.stdout)
                if data.get("success"):
                    d = data["data"]
                    rec_state["log"].append(
                        f"✅ {d['high']}/{d['low']}({d['diff']})-{d['pulse']}"
                    )
                    return {"success": True, "data": d, "text": text}
                else:
                    rec_state["log"].append(f"⚠️ {data.get('error')}")
                    return {"success": False, "error": data.get("error"), "text": text}
            except Exception as e:
                rec_state["log"].append(f"⚠️ 解析失败：{e}")
                return {"success": False, "error": f"解析失败：{e}", "text": ""}
        except Exception as e:
            rec_state["log"].append(f"❌ {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 18888), Handler)
    print("🌐 Web UI v3: http://0.0.0.0:18888")
    server.serve_forever()
