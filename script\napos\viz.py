#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化增强接口调用脚本

功能：
- 调用可视化接口生成 HTML 可视化结果
- 支持流式响应处理
- 输出结构化可视化结果

Usage:
    # 通过 stdin 管道传入文本（推荐）
    echo "分析数据..." | python viz.py --sk <鉴权码> --shop-id <门店ID> --wdid <钉钉ID>

    # 通过 --input 参数传入
    python viz.py --input <文件路径或文本> --sk <鉴权码> --shop-id <门店ID> --wdid <钉钉ID>

Examples:
    # 推荐：通过 stdin 管道传入（避免编码问题）
    echo "门店分析数据..." | python viz.py --sk abc123 --shop-id 528860314 --wdid 12345

    # 从文件通过管道传入
    cat ./analysis_result.md | python viz.py --sk abc123 --shop-id 528860314 --wdid 12345

    # 通过参数直接传入（短文本）
    python viz.py --input "门店分析数据..." --sk abc123 --shop-id 528860314 --wdid 12345
"""

import sys
import os
import json
import uuid
import random
import argparse
from typing import Dict, Any, Iterator

# 可视化接口配置
VIZ_API_CONFIG = {
    "url": "https://open.shop.ele.me/OpenapiMcpWK/mcp/stream",
    "api_key": "ak-29412662d1a8819c-bff4-4739-bd06-d6e5f94efe0e",
    "biz_scene": "Viz_For_WuKong"
}


def build_viz_request_body(user_input: str, biz_scene: str) -> Dict[str, Any]:
    """
    构建可视化请求体

    Args:
        user_input: 用户输入内容（如一量三率分析结果 markdown）
        biz_scene: 业务场景标识

    Returns:
        dict: 请求体数据
    """
    request_id = str(random.randint(1000, 9999))
    progress_token = str(uuid.uuid4())

    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": "callLLMStack",
            "_meta": {
                "progressToken": progress_token
            },
            "arguments": {
                "bizScene": biz_scene,
                "bizParams": {
                    "report_md": user_input
                }
            }
        }
    }
    print(body)
    return body


def build_headers(sk: str, shop_id: str, wdid: str) -> Dict[str, str]:
    """
    构建请求头

    Args:
        sk: 用户鉴权码（必需）
        shop_id: 餐饮门店ID（必需）
        wdid: 钉钉ID（必需）

    Returns:
        dict: 请求头
    """
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "apiKey": VIZ_API_CONFIG["api_key"],
        "sk": sk,
        "shopId": shop_id,
        "WDID": wdid,
        "x-shard": "shopld=" + shop_id
    }

    return headers


def call_viz_api(user_input: str, sk: str, shop_id: str, wdid: str) -> Iterator[str]:
    """
    调用可视化增强接口（流式）

    Args:
        user_input: 用户输入内容（如一量三率分析结果 markdown）
        sk: 用户鉴权码（必需）
        shop_id: 餐饮门店ID（必需）
        wdid: 钉钉ID（必需）

    Yields:
        str: 流式响应内容片段
    """
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        yield json.dumps({
            "error": "缺少必要的依赖，请确保 Python 环境完整"
        }, ensure_ascii=False)
        return

    headers = build_headers(sk, shop_id, wdid)
    print("headers:", headers)

    body = build_viz_request_body(user_input, VIZ_API_CONFIG["biz_scene"])

    req = urllib.request.Request(
        VIZ_API_CONFIG["url"],
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    print("req:", req.get_full_url())

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            print("response:", response)
            # 处理流式响应
            for line in response:
                line = line.decode('utf-8').strip()
                if line:
                    yield line
    except urllib.error.HTTPError as e:
        print(f"HTTP 错误: {e.code}")
        yield json.dumps({
            "error": f"HTTP 错误: {e.code}",
            "message": e.read().decode('utf-8')
        }, ensure_ascii=False)
    except urllib.error.URLError as e:
        print(f"请求失败: {str(e.reason)}")
        yield json.dumps({
            "error": f"请求失败: {str(e.reason)}"
        }, ensure_ascii=False)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        yield json.dumps({
            "error": f"发生错误: {str(e)}"
        }, ensure_ascii=False)


def parse_stream_response(stream_lines: Iterator[str]) -> Dict[str, Any]:
    """
    解析流式响应

    Args:
        stream_lines: 流式响应行迭代器

    Returns:
        dict: 解析后的完整响应
    """
    content_parts = []

    for line in stream_lines:
        # 处理 SSE 格式
        if line.startswith("data: "):
            data = line[6:]  # 去掉 "data: " 前缀

            if data == "[DONE]":
                break

            try:
                json_data = json.loads(data)

                # 提取内容
                if "result" in json_data:
                    result = json_data["result"]
                    if isinstance(result, dict) and "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    content_parts.append(item["text"])
                        elif isinstance(content, str):
                            content_parts.append(content)

                # 处理错误
                if "error" in json_data:
                    return {
                        "success": False,
                        "error": json_data["error"]
                    }

            except json.JSONDecodeError:
                # 非 JSON 数据，直接追加
                content_parts.append(data)

    full_content = "".join(content_parts)

    return {
        "success": True,
        "content": full_content
    }


def visualize(user_input: str, sk: str, shop_id: str, wdid: str) -> Dict[str, Any]:
    """
    调用可视化接口并返回结果

    Args:
        user_input: 用户输入内容（如一量三率分析结果 markdown）
        sk: 用户鉴权码（必需）
        shop_id: 餐饮门店ID（必需）
        wdid: 钉钉ID（必需）

    Returns:
        dict: 可视化结果
    """
    try:
        stream = call_viz_api(user_input, sk, shop_id, wdid)
        result = parse_stream_response(stream)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

    return result


def main():
    parser = argparse.ArgumentParser(
        description='可视化增强接口调用工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--input', '-i',
        help='可视化输入：文件路径或直接文本内容（可选，不提供则从 stdin 读取）'
    )
    parser.add_argument(
        '--sk', '-s',
        required=True,
        help='用户鉴权码（必需）'
    )
    parser.add_argument(
        '--shop-id', '-a',
        required=True,
        help='餐饮门店ID（必需）'
    )
    parser.add_argument(
        '--wdid', '-w',
        required=True,
        help='钉钉ID（必需）'
    )
    parser.add_argument(
        '--raw', '-r',
        action='store_true',
        help='输出原始流式响应'
    )

    args = parser.parse_args()

    # 优先从 stdin 读取输入（推荐方式，避免编码问题）
    if args.input:
        user_input = args.input
    elif not sys.stdin.isatty():
        # 从 stdin 管道读取
        user_input = sys.stdin.read().strip()
        if not user_input:
            print("错误: stdin 输入为空")
            sys.exit(1)
    else:
        print("错误: 请通过 --input 参数或 stdin 管道提供输入内容")
        print("示例: echo '分析数据...' | python viz.py --sk abc123 --shop-id 528860314 --wdid 12345")
        sys.exit(1)

    if args.raw:
        # 输出原始流式响应
        for line in call_viz_api(user_input, args.sk, args.shop_id, args.wdid):
            print(line)
    else:
        # 解析并输出结构化结果
        result = visualize(user_input, args.sk, args.shop_id, args.wdid)

        if result.get("success"):
            content = result.get("content", "")
            print(content)
        else:
            print(f"错误: {result.get('error', '未知错误')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
