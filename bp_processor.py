#!/usr/bin/env python3
"""
血压记录处理脚本
从识别文字中提取血压数据，生成格式化记录
"""

import re
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.resolve()
RECORDS_DIR = WORKSPACE / "records"


def normalize_blood_pressure_terms(text):
    """规范化血压相关的同义词"""
    # 将各种可能的心率/脉搏表述统一为"脉率"
    replacements = [
        ("心律", "脉率"),
        ("心跳", "脉率"),
        ("心跳数", "脉率"),
        ("频率", "脉率"),
        ("次每分", "脉率"),
        ("脉搏", "脉率"),
        ("收缩压", "高压"),
        ("舒张压", "低压"),
        ("毫米汞柱", ""),
        ("测量结束", ""),
        ("根据世界卫生组织标准", ""),
        ("谢谢使用", ""),
        ("祝您健康", ""),
    ]

    processed_text = text
    for old, new in replacements:
        processed_text = processed_text.replace(old, new)

    return processed_text


def extract_bp_data(text):
    """从识别文字中提取血压数据"""

    # 规范化同义词
    normalized_text = normalize_blood_pressure_terms(text)
    original_text = text  # 保存原文本用于调试

    def extract_number_after(text_segments, keywords):
        """在关键词后提取数字的函数"""
        for segment in text_segments:
            for kw in keywords:
                if kw in segment:
                    # 找到关键词后的数字
                    kw_pos = segment.find(kw)
                    after_kw = segment[kw_pos + len(kw) :].strip()
                    numbers = re.findall(r"\d+", after_kw)
                    for num_str in numbers:
                        num_val = int(num_str)
                        # 检查数值是否在合理范围内
                        if kw in ["高压", "收缩压"] and 90 <= num_val <= 200:
                            return num_val
                        elif kw in ["低压", "舒张压"] and 50 <= num_val <= 130:
                            return num_val
                        elif kw in ["脉率", "心率", "脉搏"] and 40 <= num_val <= 200:
                            return num_val
        return None

    # 查找可能包含血压数据的文本片段
    # 按各种标点符号分割文本
    separators = [
        "，",
        ",",
        "。",
        ".",
        "；",
        ";",
        "：",
        ":",
        "、",
        " ",
        "-",
        "_",
        "/",
        "|",
    ]
    text_parts = [normalized_text]

    for sep in separators:
        new_parts = []
        for part in text_parts:
            new_parts.extend(part.split(sep))
        text_parts = new_parts

    # 尝试不同的方法提取数据
    high_raw = extract_number_after(text_parts, ["高压", "高压", "高壓"])
    low_raw = extract_number_after(text_parts, ["低压", "低压", "低壓"])
    pulse_raw = extract_number_after(text_parts, ["脉率", "心率", "脉搏", "脈", "次"])

    # 如果以上方法未成功，嘗試更廣泛的匹配模式
    if not high_raw or not low_raw or not pulse_raw:
        # 匹配格式：数字(可能带单位)的组合
        # 例如：120毫米汞柱，80毫米汞柱，60次每分
        high_patterns = [
            r"高压[\s\S]*?(\d{3})",
            r"高压[\s\S]*?(\d{2}[^\d])",
            r"高压.*?(\d{2,3})",
        ]

        for pattern in high_patterns:
            match = re.search(pattern, normalized_text)
            if match:
                val = int(match.group(1))
                if 90 <= val <= 200:
                    high_raw = val
                    break

        low_patterns = [
            r"低压[\s\S]*?(\d{3})",
            r"低压[\s\S]*?(\d{2}[^\d])",
            r"低压.*?(\d{2,3})",
        ]

        for pattern in low_patterns:
            match = re.search(pattern, normalized_text)
            if match:
                val = int(match.group(1))
                if 50 <= val <= 130:
                    low_raw = val
                    break

        pulse_patterns = [
            r"脉率[\s\S]*?(\d{3})",
            r"心率[\s\S]*?(\d{2}[^\d])",
            r"心率.*?(\d{2,3})",
            r"脉率.*?(\d{2,3})",
        ]

        for pattern in pulse_patterns:
            match = re.search(pattern, normalized_text)
            if match:
                val = int(match.group(1))
                if 40 <= val <= 200:
                    pulse_raw = val
                    break

    # 最后的备用策略：从所有数字中挑选
    if not all([high_raw, low_raw, pulse_raw]):
        all_numbers = re.findall(r"\d+", normalized_text)
        candidates = []
        for num_str in all_numbers:
            try:
                val = int(num_str)
                # 根据范围分类
                if 90 <= val <= 200:
                    if not high_raw:
                        high_raw = val
                elif 50 <= val <= 130:
                    if not low_raw:
                        low_raw = val
                elif 40 <= val <= 200:
                    if not pulse_raw:
                        pulse_raw = val
            except:
                continue

    # 驗证提取结果
    if high_raw and low_raw and pulse_raw:
        if high_raw > low_raw:  # 确保高压高于低压
            return {
                "success": True,
                "data": {
                    "high": int(high_raw),
                    "low": int(low_raw),
                    "pulse": int(pulse_raw),
                    "diff": int(high_raw - low_raw),
                },
                "text": original_text,
            }

    # 如果所有方法都失败，返回失败信息
    return {"success": False, "error": "未能提取血压数据", "text": original_text}


def format_record(high, low, pulse, timestamp=None):
    """生成格式化记录"""
    if timestamp is None:
        timestamp = datetime.now()

    diff = high - low
    time_str = timestamp.strftime("%H:%M")

    return f" {time_str}---{high}/{low}({diff})-{pulse}🩺B"


def save_record(formatted_line, date=None):
    """保存记录到 MD 文件"""
    if date is None:
        date = datetime.now()

    RECORDS_DIR.mkdir(exist_ok=True)

    # 按月保存
    month_file = RECORDS_DIR / f"{date.year}-{date.month:02d}.md"

    # 创建或追加
    if not month_file.exists():
        month_file.write_text(f"# {date.year}年{date.month}月 血压记录\n\n")

    content = month_file.read_text()

    # 添加新记录
    date_line = f"- {date.strftime('%Y-%m-%d')}{formatted_line}\n"

    if date_line not in content:
        content += date_line
        month_file.write_text(content)

    return month_file


def process_message(text, save_directly=False):
    """处理收到的消息"""
    # 提取数据
    bp_data = extract_bp_data(text)

    if not bp_data["success"]:
        return bp_data

    # 格式化
    d = bp_data["data"]
    now = datetime.now()
    formatted = format_record(d["high"], d["low"], d["pulse"], now)

    # 保存（可选）
    if save_directly:
        saved_file = save_record(formatted, now)
        return {
            "success": True,
            "data": d,
            "formatted": formatted,
            "saved_to": str(saved_file),
            "text": text,
        }
    else:
        # Web UI 模式：不保存，只返回数据
        return {
            "success": True,
            "data": d,
            "formatted": formatted,
            "pending": True,
            "text": text,
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 捂查是否有 --save 参数
        save_directly = "--save" in sys.argv
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        text = " ".join(args)
    else:
        # 從 stdin 读取
        import io

        text = sys.stdin.read()
        save_directly = False

    result = process_message(text, save_directly=save_directly)
    print(json.dumps(result, ensure_ascii=False, indent=2))
