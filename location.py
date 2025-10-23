#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re


def parse_phone_result(html_content):
    """
    解析手机号查询结果的完整示例
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # 方法1：通过表格结构解析
    def parse_by_table():
        print('parse_by_table')
        results = {}

        # 查找包含结果的表格
        tables = soup.find_all('table')
        for table in tables:
            # 检查表格是否包含手机号相关信息
            if '查询结果' in table.text:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        key = key.replace(' ', '')
                        print(key, value)

                        if '归属地' in key:
                            results['location'] = value
                        elif '运营商' in key:
                            results['operator'] = value
                        elif '区号' in key:
                            results['area_code'] = value
                        elif '邮编' in key:
                            results['zip_code'] = value

        print(results)
        return results

    # 方法2：通过CSS类名解析（更精确）
    def parse_by_class():
        print('parse_by_class')
        results = {}

        # 假设结果有特定的class
        phone_elem = soup.find(class_='phone-number')
        location_elem = soup.find(class_='location')
        operator_elem = soup.find(class_='operator')

        if phone_elem:
            results['phone'] = phone_elem.get_text(strip=True)
        if location_elem:
            results['location'] = location_elem.get_text(strip=True)
        if operator_elem:
            results['operator'] = operator_elem.get_text(strip=True)

        return results

    # 方法3：通过文本模式匹配
    def parse_by_pattern():
        print('parse_by_pattern')
        results = {}
        text = soup.get_text()

        # 使用正则表达式匹配模式
        phone_pattern = r'手机号码[:：]\s*([^\s]+)'
        location_pattern = r'归属地[:：]\s*([^\n]+)'
        operator_pattern = r'运营商[:：]\s*([^\n]+)'

        phone_match = re.search(phone_pattern, text)
        location_match = re.search(location_pattern, text)
        operator_match = re.search(operator_pattern, text)

        if phone_match:
            results['phone'] = phone_match.group(1)
        if location_match:
            results['location'] = location_match.group(1)
        if operator_match:
            results['operator'] = operator_match.group(1)

        return results

    # 尝试多种解析方法
    results = parse_by_table()
    if not results:
        results = parse_by_class()
    if not results:
        results = parse_by_pattern()

    return results


def query_single_phone(phone):
    """
    查询手机号并解析结果
    """
    url = f"https://www.ip138.com/mobile.asp?mobile={phone}&action=mobile"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 确保中文正确显示

        if response.status_code == 200:
            results = parse_phone_result(response.text)
            return {
                'success': True,
                'phone': phone,
                'data': results
            }
        else:
            return {
                'success': False,
                'error': f'HTTP错误: {response.status_code}'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# 批量查询函数
def batch_query_phones(phone_list, delay=2):
    """
    批量查询手机号
    """
    import time
    from tqdm import tqdm  # 进度条库，可选

    results = []

    for phone in tqdm(phone_list, desc="查询进度"):
        result = query_single_phone(phone)
        results.append(result)

        # 添加延迟，避免请求过快
        time.sleep(delay)

    return results
