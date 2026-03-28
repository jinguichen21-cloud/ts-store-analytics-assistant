#!/usr/bin/env python3
"""
经营接口 HTTP 调用脚本

功能：
- 调用经营分析接口获取门店诊断数据
- 支持流式响应处理
- 输出结构化分析结果

Usage:
    python tool.py --account-id <门店ID> --sk <鉴权码> --tool-code <工具码>

Examples:
    python tool.py --account-id 528860314 --sk abc123 --tool-code yiliangsanlv
    python tool.py --account-id 528860314 --sk abc123 --tool-code yiliangsanlv 
"""

import sys
import os
import json
import uuid
import random
import argparse
from typing import Optional, Dict, Any, Iterator

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 接口配置
API_CONFIG = {
    "url": "https://open.shop.ele.me/OpenapiMcpWK/mcp/stream",
    "api_key": "ak-29412662d1a8819c-bff4-4739-bd06-d6e5f94efe0e",
    "biz_scene": "napos-store-analytics-assistant"
}


def build_request_body(account_id: str, tool_code: str) -> Dict[str, Any]:
    """
    构建请求体

    Args:
        account_id: 餐饮门店ID
        tool_code: 工具码（如 yiliangsanlv）

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
                "bizScene": API_CONFIG["biz_scene"],
                "bizParams": {
                    "accountId": account_id,
                    "tool_code": tool_code
                }
            }
        }
    }

    return body


def build_headers(sk: str, shopId: str, wdid: str) -> Dict[str, str]:
    """
    构建请求头

    Args:
        sk: 用户鉴权码（必需）
        shopId: 餐饮门店ID（必需）
        wdid: 钉钉ID（必需）

    Returns:
        dict: 请求头
    """
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "apiKey": API_CONFIG["api_key"],
        "sk": sk,
        "shopId": shopId,
        "WDID": wdid,
        "x-shard": "shopld="+shopId
    }

    return headers


def call_business_api(account_id: str, tool_code: str, sk: str, wdid: str) -> Iterator[str]:
    """
    调用经营分析接口（流式）

    Args:
        account_id: 餐饮门店ID
        tool_code: 工具码（如 yiliangsanlv）
        sk: 用户鉴权码（必需）
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

    headers = build_headers(sk, account_id, wdid)
    body = build_request_body(account_id, tool_code)

    req = urllib.request.Request(
        API_CONFIG["url"],
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            # 处理流式响应
            for line in response:
                line = line.decode('utf-8').strip()
                if line:
                    yield line
    except urllib.error.HTTPError as e:
        yield json.dumps({
            "error": f"HTTP 错误: {e.code}",
            "message": e.read().decode('utf-8')
        }, ensure_ascii=False)
    except urllib.error.URLError as e:
        yield json.dumps({
            "error": f"请求失败: {str(e.reason)}"
        }, ensure_ascii=False)
    except Exception as e:
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


def analyze_store(account_id: str, tool_code: str, sk: str, wdid: str) -> Dict[str, Any]:
    """
    分析门店经营数据

    Args:
        account_id: 餐饮门店ID
        tool_code: 工具码（如 yiliangsanlv）
        sk: 用户鉴权码（必需）
        wdid: 钉钉ID（必需）

    Returns:
        dict: 分析结果
    """
    stream = call_business_api(account_id, tool_code, sk, wdid)
    result = parse_stream_response(stream)
    return result


def main():
    parser = argparse.ArgumentParser(
        description='经营接口调用工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--account-id', '-a',
        required=True,
        help='餐饮门店ID（必需）'
    )
    parser.add_argument(
        '--tool-code', '-t',
        required=True,
        help='工具码（如 yiliangsanlv，必需）'
    )
    parser.add_argument(
        '--sk', '-s',
        required=True,
        help='用户鉴权码（必需）'
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

    print(f"正在调用工具 [{args.tool_code}] 分析门店: {args.account_id}")
    print("-" * 50)

    if args.raw:
        # 输出原始流式响应
        for line in call_business_api(args.account_id, args.tool_code, args.sk, args.wdid):
            print(line)
    else:
        # 解析并输出结构化结果
        result = analyze_store(args.account_id, args.tool_code, args.sk, args.wdid)

        if result.get("success"):
            content = result.get("content", "")
            print(content)

        else:
            print(f"错误: {result.get('error', '未知错误')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
