# src/moyan/config/stock_search.py
"""
A股全市场股票搜索引擎
支持股票代码、名称、拼音搜索
"""

import requests
import json
import re
from typing import List, Dict, Optional
import threading
import time
from functools import lru_cache

class AStockSearchEngine:
    """A股全市场搜索引擎"""
    
    def __init__(self):
        self.stock_cache = {}
        self.last_update = 0
        self.cache_ttl = 86400  # 24小时缓存
        self.lock = threading.Lock()
        
        # 东财API配置
        self.eastmoney_api = "http://80.push2.eastmoney.com/api/qt/clist/get"
        
        # 拼音映射缓存
        self.pinyin_cache = {}
        
    def _get_pinyin_initial(self, chinese_text: str) -> str:
        """
        获取中文拼音首字母（使用专业拼音工具）
        """
        if chinese_text in self.pinyin_cache:
            return self.pinyin_cache[chinese_text]
        
        try:
            from moyan.config.pinyin_helper import get_pinyin_initial
            result = get_pinyin_initial(chinese_text)
        except ImportError:
            # 备用简单映射
            result = ''
            for char in chinese_text:
                if '\u4e00' <= char <= '\u9fff':  # 中文字符
                    # 简单映射规则
                    unicode_val = ord(char)
                    result += chr(ord('a') + (unicode_val % 26))
                elif char.isalpha():
                    result += char.lower()
        
        self.pinyin_cache[chinese_text] = result
        return result
    
    def _fetch_all_stocks(self) -> Dict:
        """
        从东财API获取全部A股数据（分批获取）
        """
        all_stocks = {}
        
        # 优化的获取策略：平衡覆盖面和效率
        strategies = [
            # 1. 大市值股票（前3页，覆盖主流蓝筹）
            {
                'name': '大市值股票TOP300',
                'fid': 'f20',  # 按总市值排序
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'pz': '100', 'pn': '1'
            },
            {
                'name': '大市值股票300-600',
                'fid': 'f20',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'pz': '100', 'pn': '2'
            },
            {
                'name': '大市值股票600-900',
                'fid': 'f20',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'pz': '100', 'pn': '3'
            },
            
            # 2. 活跃股票（前2页，覆盖热门）
            {
                'name': '活跃股票TOP200',
                'fid': 'f5',   # 按成交量排序
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'pz': '100', 'pn': '1'
            },
            {
                'name': '活跃股票200-400',
                'fid': 'f5',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'pz': '100', 'pn': '2'
            },
            
            # 3. 分板块全覆盖（每板块2页）
            {
                'name': '沪市主板A',
                'fid': 'f3',
                'fs': 'm:1+t:2,m:1+t:23',  # 沪市
                'pz': '100', 'pn': '1'
            },
            {
                'name': '沪市主板B',
                'fid': 'f3',
                'fs': 'm:1+t:2,m:1+t:23',
                'pz': '100', 'pn': '2'
            },
            {
                'name': '深市主板A',
                'fid': 'f3', 
                'fs': 'm:0+t:6,m:0+t:80',  # 深市主板
                'pz': '100', 'pn': '1'
            },
            {
                'name': '深市主板B',
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80',
                'pz': '100', 'pn': '2'
            },
            {
                'name': '创业板A',
                'fid': 'f3',
                'fs': 'm:0+t:81+s:2048',   # 创业板
                'pz': '100', 'pn': '1'
            },
            {
                'name': '创业板B',
                'fid': 'f3',
                'fs': 'm:0+t:81+s:2048',
                'pz': '100', 'pn': '2'
            },
            {
                'name': '科创板A',
                'fid': 'f3',
                'fs': 'm:1+t:23+f:!50',   # 科创板
                'pz': '100', 'pn': '1'
            },
            {
                'name': '科创板B',
                'fid': 'f3',
                'fs': 'm:1+t:23+f:!50',
                'pz': '100', 'pn': '2'
            }
        ]
        
        print(f"使用 {len(strategies)} 个优化策略获取A股数据")
        
        for strategy in strategies:
            try:
                print(f"正在获取{strategy['name']}数据...")
                
                params = {
                    'pn': strategy.get('pn', '1'),
                    'pz': strategy['pz'],
                    'po': '1',
                    'np': '1',
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': '2',
                    'invt': '2',
                    'fid': strategy['fid'],
                    'fs': strategy['fs'],
                    'fields': 'f12,f14,f2,f3,f20,f5'  # 代码,名称,价格,涨跌幅,市值,成交量
                }
                
                response = requests.get(self.eastmoney_api, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and data['data'].get('diff'):
                        batch_stocks = self._parse_eastmoney_data(data['data']['diff'])
                        # 合并数据，避免重复
                        for code, info in batch_stocks.items():
                            if code not in all_stocks:
                                all_stocks[code] = info
                        print(f"  ✅ {strategy['name']}: 新增 {len(batch_stocks)} 只，总计 {len(all_stocks)} 只")
                    else:
                        print(f"  ❌ {strategy['name']}: 无数据返回")
                else:
                    print(f"  ❌ {strategy['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {strategy['name']}获取失败: {e}")
                continue
        
        if len(all_stocks) > 0:
            print(f"🎉 成功获取 {len(all_stocks)} 只A股数据")
            return all_stocks
        else:
            print("⚠️ 所有API策略都失败，使用本地数据库")
            return self._get_fallback_stocks()
    
    def _parse_eastmoney_data(self, stocks_data: List) -> Dict:
        """
        解析东财API返回的股票数据
        """
        stocks = {}
        
        for stock in stocks_data:
            try:
                code = stock.get('f12', '')  # 股票代码
                name = stock.get('f14', '')  # 股票名称
                
                if code and name:
                    # 生成拼音首字母
                    pinyin = self._get_pinyin_initial(name)
                    
                    stocks[code] = {
                        'name': name,
                        'pinyin': pinyin,
                        'full_pinyin': pinyin,  # 简化版本
                        'price': stock.get('f2', 0),  # 当前价格
                        'change': stock.get('f3', 0),  # 涨跌幅
                        'market': '沪A' if code.startswith('6') else '深A' if code.startswith('0') else '创业板' if code.startswith('3') else '其他'
                    }
            except Exception as e:
                continue
        
        print(f"成功获取 {len(stocks)} 只股票数据")
        return stocks
    
    def _get_fallback_stocks(self) -> Dict:
        """
        获取备用股票数据（从本地数据库）
        """
        try:
            from moyan.config.stock_database import STOCK_DATA
            fallback_stocks = {}
            
            for code, info in STOCK_DATA.items():
                fallback_stocks[code] = {
                    'name': info['name'],
                    'pinyin': info['pinyin'],
                    'full_pinyin': info.get('full_pinyin', info['pinyin']),
                    'price': 0,  # 没有实时价格
                    'change': 0,
                    'market': '沪A' if code.startswith('6') else '深A' if code.startswith('0') else '创业板' if code.startswith('3') else '其他'
                }
            
            print(f"加载本地数据库: {len(fallback_stocks)} 只股票")
            return fallback_stocks
            
        except ImportError:
            print("无法加载本地股票数据库")
            return {}
    
    def update_stock_cache(self):
        """
        更新股票缓存
        """
        with self.lock:
            current_time = time.time()
            if current_time - self.last_update > self.cache_ttl:
                print("正在更新股票数据...")
                new_data = self._fetch_all_stocks()
                if new_data:
                    self.stock_cache.update(new_data)
                    self.last_update = current_time
                    print(f"股票数据更新完成，共 {len(self.stock_cache)} 只")
    
    def get_stock_info(self, code: str) -> Optional[Dict]:
        """
        根据股票代码获取股票信息
        """
        # 确保缓存是最新的
        self.update_stock_cache()
        return self.stock_cache.get(code)
    
    def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索股票，支持代码、名称、拼音
        """
        if not query:
            return []
        
        # 确保缓存是最新的
        self.update_stock_cache()
        
        query = query.strip().lower()
        results = []
        
        # 首先从本地数据库搜索（常用股票，更准确）
        local_codes = set()
        try:
            from moyan.config.stock_database import search_stock as local_search
            local_results = local_search(query)
            for result in local_results[:5]:  # 本地结果优先，但限制数量
                local_codes.add(result['code'])
                results.append({
                    'code': result['code'],
                    'name': result['name'],
                    'pinyin': result['pinyin'],
                    'match_type': f"local_{result['match_type']}",
                    'source': 'local'
                })
        except ImportError:
            pass
        
        # 然后搜索全市场数据
        for code, info in self.stock_cache.items():
            if len(results) >= limit:
                break
                
            # 避免重复（本地已有的跳过）
            if code in local_codes:
                continue
            
            match_type = None
            
            # 1. 精确匹配股票代码
            if query == code:
                match_type = 'code'
            # 2. 代码前缀匹配
            elif code.startswith(query) and len(query) >= 3:
                match_type = 'code_prefix'
            # 3. 股票名称包含匹配
            elif query in info['name'].lower():
                match_type = 'name'
            # 4. 拼音首字母匹配
            elif query == info['pinyin'].lower():
                match_type = 'pinyin'
            # 5. 拼音首字母前缀匹配
            elif info['pinyin'].lower().startswith(query) and len(query) >= 2:
                match_type = 'pinyin_prefix'
            
            if match_type:
                results.append({
                    'code': code,
                    'name': info['name'],
                    'pinyin': info['pinyin'],
                    'match_type': match_type,
                    'source': 'api',
                    'price': info.get('price', 0),
                    'change': info.get('change', 0),
                    'market': info.get('market', '')
                })
        
        # 按匹配优先级排序
        priority = {
            'local_code': 1, 'local_pinyin': 2, 'code': 3, 'pinyin': 4,
            'local_code_prefix': 5, 'code_prefix': 6, 'local_name': 7, 'name': 8,
            'local_pinyin_prefix': 9, 'pinyin_prefix': 10
        }
        
        results.sort(key=lambda x: priority.get(x['match_type'], 20))
        
        return results[:limit]

# 全局搜索引擎实例
_search_engine = None

def get_search_engine():
    """获取全局搜索引擎实例"""
    global _search_engine
    if _search_engine is None:
        _search_engine = AStockSearchEngine()
    return _search_engine

def search_all_stocks(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索全市场股票
    """
    engine = get_search_engine()
    return engine.search_stocks(query, limit)

def get_all_stock_info(code: str) -> Optional[Dict]:
    """
    获取股票信息（全市场）
    """
    engine = get_search_engine()
    return engine.get_stock_info(code)

# 测试函数
if __name__ == "__main__":
    # 测试搜索功能
    test_queries = ["中际旭创", "300308", "zjxc", "平安银行", "000001", "payh"]
    
    for query in test_queries:
        print(f"\n搜索 '{query}':")
        results = search_all_stocks(query, 5)
        for result in results:
            print(f"  {result['code']} - {result['name']} ({result.get('pinyin', '')}) [{result['match_type']}] [{result['source']}]")
