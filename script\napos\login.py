#!/usr/bin/env python3
#
# 登陆脚本
# 封装所有接口的 curl 调用及 SSE 返回解析，隐藏复杂的请求细节
#
# 用法（${SKILL_DIR} = 本 Skill 根目录，与 SKILL.md 同级）：
#   获取门店列表：
#     python3 "${SKILL_DIR}/script/napos/login.py" NaposCodeToShop <淘宝闪购授权码> <钉钉ID>
#
# 示例：
#   python3 "${SKILL_DIR}/script/napos/login.py" NaposCodeToShop "abc123" "377705"

import sys
import json
import random
import argparse

import requests


API_URL = "https://open.shop.ele.me/OpenapiMcpWK/mcp/stream"
API_KEY = "ak-29412662d1a8819c-bff4-4739-bd06-d6e5f94efe0e"
CURL_TIMEOUT = 30
CURL_CONNECT_TIMEOUT = 10


def generate_progress_token() -> str:
    """生成32位数字随机进度令牌"""
    return ''.join(random.choices('0123456789', k=32))


def parse_sse_response(response_text: str) -> str:
    """解析 SSE 响应，提取 processData.output 或 result"""
    for line in response_text.strip().split('\n'):
        line = line.strip()
        if not line.startswith('data:'):
            continue
        json_str = line[5:].strip()
        if json_str == '[done]':
            continue
        try:
            data = json.loads(json_str)
            if 'processData' in data:
                return data['processData'].get('output', '')
            elif 'result' in data:
                return json.dumps(data['result'], ensure_ascii=False)
        except (json.JSONDecodeError, KeyError):
            pass
    return ''


def call_napos_code_to_shop(sk: str, wdid: str) -> str:
    """调用 NaposCodeToShop 接口获取门店列表"""
    progress_token = generate_progress_token()

    headers = {
        'Accept': 'application/json, text/event-stream',
        'Content-Type': 'application/json',
        'apiKey': API_KEY,
        'sk': sk,
        'WDID': wdid
    }

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "NaposCodeToShop",
            "_meta": {
                "progressToken": progress_token
            },
            "arguments": {
                "code": sk
            }
        }
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=(CURL_CONNECT_TIMEOUT, CURL_TIMEOUT)
        )
        response.raise_for_status()
        return parse_sse_response(response.text)
    except requests.RequestException as e:
        print(f"错误：请求 NaposCodeToShop 失败，请检查网络或授权码: {e}", file=sys.stderr)
        sys.exit(1)


def call_llm_stack_tool(tool_name: str, sk: str, wdid: str, shop_id: str, extra_params: str = None) -> str:
    """调用 callLLMStack 接口执行营销工具"""
    progress_token = generate_progress_token()

    if extra_params:
        biz_params = {"mktToolName": tool_name, "params": json.loads(extra_params)}
    else:
        biz_params = {"mktToolName": tool_name}

    headers = {
        'Accept': 'application/json, text/event-stream',
        'Content-Type': 'application/json',
        'apiKey': API_KEY,
        'sk': sk,
        'WDID': wdid,
        'shopId': shop_id
    }

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "callLLMStack",
            "_meta": {
                "progressToken": progress_token
            },
            "arguments": {
                "bizScene": "wukong_mkt_tools",
                "bizParams": biz_params
            }
        }
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=(CURL_CONNECT_TIMEOUT, CURL_TIMEOUT)
        )
        response.raise_for_status()
        return parse_sse_response(response.text)
    except requests.RequestException as e:
        print(f"错误：请求 {tool_name} 失败，请检查网络、授权码或门店ID: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Napos 登录和工具调用脚本',
        usage='%(prog)s NaposCodeToShop <淘宝闪购授权码> <钉钉ID>\n       %(prog)s <mktToolName> <淘宝闪购授权码> <钉钉ID> <shopId> [额外JSON参数]'
    )
    parser.add_argument('tool_name', help='工具名称，如 NaposCodeToShop 或其他 mktToolName')
    parser.add_argument('arg2', nargs='?', help='淘宝闪购授权码（NaposCodeToShop）或淘宝闪购授权码（其他工具）')
    parser.add_argument('arg3', nargs='?', help='钉钉ID（NaposCodeToShop）或钉钉ID（其他工具）')
    parser.add_argument('arg4', nargs='?', help='门店ID（其他工具时需要）')
    parser.add_argument('arg5', nargs='?', help='额外JSON参数（可选）')

    args = parser.parse_args()

    if args.tool_name == "NaposCodeToShop":
        if not args.arg2 or not args.arg3:
            print("错误：NaposCodeToShop 需要传入淘宝闪购授权码和钉钉ID", file=sys.stderr)
            sys.exit(1)
        result = call_napos_code_to_shop(args.arg2, args.arg3)
        print(result)
    else:
        if not args.arg2 or not args.arg3 or not args.arg4:
            print(f"错误：{args.tool_name} 需要传入淘宝闪购授权码、钉钉ID和门店ID", file=sys.stderr)
            sys.exit(1)
        result = call_llm_stack_tool(args.tool_name, args.arg2, args.arg3, args.arg4, args.arg5)
        print(result)


if __name__ == "__main__":
    main()
