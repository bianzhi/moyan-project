# src/moyan/config/stock_db_builder.py
"""
A股数据库构建器
从多个数据源获取全部A股信息并构建本地SQLite数据库
"""

import sqlite3
import requests
import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime

class StockDatabaseBuilder:
    """A股数据库构建器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认数据库路径
            current_dir = os.path.dirname(__file__)
            self.db_path = os.path.join(current_dir, 'a_stock_database.db')
        else:
            self.db_path = db_path
        
        self.conn = None
        self.cursor = None
        
        # 数据源API配置
        self.data_sources = {
            'eastmoney': {
                'url': 'http://80.push2.eastmoney.com/api/qt/clist/get',
                'name': '东方财富'
            },
            'sina': {
                'url': 'http://hq.sinajs.cn/list=',
                'name': '新浪财经'
            }
        }
        
        # 拼音映射工具
        self.pinyin_helper = None
        
    def init_database(self):
        """初始化数据库表结构"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建股票信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                code TEXT PRIMARY KEY,           -- 股票代码
                name TEXT NOT NULL,              -- 股票名称
                pinyin TEXT,                     -- 拼音首字母
                full_pinyin TEXT,                -- 完整拼音
                market TEXT,                     -- 市场 (沪A/深A/创业板/科创板)
                industry TEXT,                   -- 行业
                price REAL DEFAULT 0,            -- 当前价格
                market_cap REAL DEFAULT 0,       -- 总市值(万元)
                pe_ratio REAL DEFAULT 0,         -- 市盈率
                listed_date TEXT,                -- 上市日期
                status TEXT DEFAULT 'active',    -- 状态 (active/suspended/delisted)
                source TEXT,                     -- 数据来源
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建拼音搜索索引
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pinyin ON stocks(pinyin)
        ''')
        
        # 创建名称搜索索引
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_name ON stocks(name)
        ''')
        
        # 创建市场分类索引
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market ON stocks(market)
        ''')
        
        # 创建元数据表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print(f"✅ 数据库初始化完成: {self.db_path}")
        
    def get_pinyin_helper(self):
        """获取拼音转换工具"""
        if self.pinyin_helper is None:
            try:
                from moyan.config.pinyin_helper import get_pinyin_initial
                self.pinyin_helper = get_pinyin_initial
            except ImportError:
                # 简单备用方案
                def simple_pinyin(text):
                    return ''.join([c.lower() if c.isalpha() else '' for c in text])
                self.pinyin_helper = simple_pinyin
        return self.pinyin_helper
        
    def fetch_eastmoney_data(self) -> List[Dict]:
        """从东方财富获取A股数据"""
        print("🌐 正在从东方财富获取A股数据...")
        all_stocks = []
        
        # 分批获取策略
        strategies = [
            # 按市值获取主流股票
            {'name': '大市值TOP1000', 'fid': 'f20', 'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23', 'pages': 10},
            # 按板块分别获取
            {'name': '沪市主板', 'fid': 'f3', 'fs': 'm:1+t:2,m:1+t:23', 'pages': 20},
            {'name': '深市主板', 'fid': 'f3', 'fs': 'm:0+t:6,m:0+t:80', 'pages': 15},
            {'name': '创业板', 'fid': 'f3', 'fs': 'm:0+t:81+s:2048', 'pages': 12},
            {'name': '科创板', 'fid': 'f3', 'fs': 'm:1+t:23+f:!50', 'pages': 8},
            # 按活跃度获取
            {'name': '活跃股票', 'fid': 'f5', 'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23', 'pages': 8},
        ]
        
        stock_codes = set()  # 用于去重
        
        for strategy in strategies:
            print(f"  📊 获取{strategy['name']}...")
            
            for page in range(1, strategy['pages'] + 1):
                try:
                    params = {
                        'pn': str(page),
                        'pz': '100',
                        'po': '1',
                        'np': '1',
                        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                        'fltt': '2',
                        'invt': '2',
                        'fid': strategy['fid'],
                        'fs': strategy['fs'],
                        'fields': 'f12,f14,f2,f3,f20,f116,f117,f26'  # 代码,名称,价格,涨跌幅,市值,总股本,流通股本,行业
                    }
                    
                    response = requests.get(self.data_sources['eastmoney']['url'], 
                                          params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data') and data['data'].get('diff'):
                            for stock in data['data']['diff']:
                                code = stock.get('f12', '')
                                name = stock.get('f14', '')
                                
                                if code and name and code not in stock_codes:
                                    stock_codes.add(code)
                                    
                                    # 确定市场类型
                                    if code.startswith('60'):
                                        market = '沪A主板'
                                    elif code.startswith('68'):
                                        market = '科创板'
                                    elif code.startswith('00'):
                                        market = '深A主板'
                                    elif code.startswith('30'):
                                        market = '创业板'
                                    else:
                                        market = '其他'
                                    
                                    stock_info = {
                                        'code': code,
                                        'name': name,
                                        'market': market,
                                        'price': stock.get('f2', 0) or 0,
                                        'market_cap': stock.get('f20', 0) or 0,
                                        'industry': stock.get('f26', '') or '',
                                        'source': 'eastmoney'
                                    }
                                    all_stocks.append(stock_info)
                    
                    # 避免请求过于频繁
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    ❌ 第{page}页获取失败: {e}")
                    continue
            
            print(f"    ✅ {strategy['name']}: 累计获取 {len(all_stocks)} 只股票")
        
        print(f"🎉 东方财富数据获取完成，共 {len(all_stocks)} 只股票")
        return all_stocks
    
    def save_stocks_to_db(self, stocks: List[Dict]):
        """保存股票数据到数据库"""
        print(f"💾 正在保存 {len(stocks)} 只股票到数据库...")
        
        pinyin_func = self.get_pinyin_helper()
        saved_count = 0
        updated_count = 0
        
        for stock in stocks:
            # 生成拼音
            pinyin = pinyin_func(stock['name'])
            
            # 检查股票是否已存在
            self.cursor.execute('SELECT code FROM stocks WHERE code = ?', (stock['code'],))
            exists = self.cursor.fetchone()
            
            if exists:
                # 更新现有记录
                self.cursor.execute('''
                    UPDATE stocks SET 
                        name = ?, pinyin = ?, market = ?, price = ?, 
                        market_cap = ?, industry = ?, source = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (
                    stock['name'], pinyin, stock['market'], stock['price'],
                    stock['market_cap'], stock['industry'], stock['source'],
                    stock['code']
                ))
                updated_count += 1
            else:
                # 插入新记录
                self.cursor.execute('''
                    INSERT INTO stocks (
                        code, name, pinyin, market, price, market_cap, 
                        industry, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock['code'], stock['name'], pinyin, stock['market'],
                    stock['price'], stock['market_cap'], stock['industry'],
                    stock['source']
                ))
                saved_count += 1
        
        # 更新元数据
        self.cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('last_update', datetime.now().isoformat()))
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('total_stocks', str(saved_count + updated_count)))
        
        self.conn.commit()
        print(f"✅ 数据保存完成: 新增 {saved_count} 只，更新 {updated_count} 只")
        
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        stats = {}
        
        # 总股票数
        self.cursor.execute('SELECT COUNT(*) FROM stocks')
        stats['total'] = self.cursor.fetchone()[0]
        
        # 按市场分类统计
        self.cursor.execute('''
            SELECT market, COUNT(*) FROM stocks 
            GROUP BY market ORDER BY COUNT(*) DESC
        ''')
        stats['by_market'] = dict(self.cursor.fetchall())
        
        # 最后更新时间
        self.cursor.execute('SELECT value FROM metadata WHERE key = "last_update"')
        result = self.cursor.fetchone()
        stats['last_update'] = result[0] if result else '未知'
        
        return stats
    
    def build_database(self):
        """构建完整的A股数据库"""
        print("🚀 开始构建A股本地数据库...")
        
        # 1. 初始化数据库
        self.init_database()
        
        # 2. 获取东财数据
        stocks = self.fetch_eastmoney_data()
        
        # 3. 保存到数据库
        if stocks:
            self.save_stocks_to_db(stocks)
        
        # 4. 显示统计信息
        stats = self.get_database_stats()
        print(f"\n📊 数据库构建完成:")
        print(f"  📈 总股票数: {stats['total']} 只")
        print(f"  📅 更新时间: {stats['last_update']}")
        print(f"  🏛️ 市场分布:")
        for market, count in stats['by_market'].items():
            print(f"    {market}: {count} 只")
        
        print(f"\n💾 数据库文件: {self.db_path}")
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

# 数据库操作类
class StockDatabase:
    """A股数据库查询接口（线程安全版本）"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            current_dir = os.path.dirname(__file__)
            self.db_path = os.path.join(current_dir, 'a_stock_database.db')
        else:
            self.db_path = db_path
        
        # 不在初始化时创建连接，而是在每次使用时创建
        self.conn = None
        
    def _get_connection(self):
        """获取数据库连接（线程安全）"""
        # 每次都创建新的连接，避免线程问题
        if not os.path.exists(self.db_path):
            return None
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
        return conn
    
    def search_stocks(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索股票"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            query = query.strip().lower()
            results = []
            
            cursor = conn.cursor()
            
            # 1. 精确代码匹配
            cursor.execute('''
                SELECT * FROM stocks WHERE LOWER(code) = ? LIMIT ?
            ''', (query, limit))
            for row in cursor.fetchall():
                results.append({
                    'code': row['code'],
                    'name': row['name'],
                    'pinyin': row['pinyin'],
                    'market': row['market'],
                    'price': row['price'],
                    'match_type': 'code',
                    'source': 'database'
                })
            
            if len(results) >= limit:
                return results[:limit]
            
            # 2. 代码前缀匹配
            if len(query) >= 3:
                cursor.execute('''
                    SELECT * FROM stocks WHERE LOWER(code) LIKE ? 
                    AND LOWER(code) != ? LIMIT ?
                ''', (f'{query}%', query, limit - len(results)))
                for row in cursor.fetchall():
                    results.append({
                        'code': row['code'],
                        'name': row['name'],
                        'pinyin': row['pinyin'],
                        'market': row['market'],
                        'price': row['price'],
                        'match_type': 'code_prefix',
                        'source': 'database'
                    })
            
            if len(results) >= limit:
                return results[:limit]
            
            # 3. 名称包含匹配
            cursor.execute('''
                SELECT * FROM stocks WHERE LOWER(name) LIKE ? LIMIT ?
            ''', (f'%{query}%', limit - len(results)))
            for row in cursor.fetchall():
                if not any(r['code'] == row['code'] for r in results):
                    results.append({
                        'code': row['code'],
                        'name': row['name'],
                        'pinyin': row['pinyin'],
                        'market': row['market'],
                        'price': row['price'],
                        'match_type': 'name',
                        'source': 'database'
                    })
            
            if len(results) >= limit:
                return results[:limit]
            
            # 4. 拼音匹配
            cursor.execute('''
                SELECT * FROM stocks WHERE LOWER(pinyin) LIKE ? LIMIT ?
            ''', (f'{query}%', limit - len(results)))
            for row in cursor.fetchall():
                if not any(r['code'] == row['code'] for r in results):
                    results.append({
                        'code': row['code'],
                        'name': row['name'],
                        'pinyin': row['pinyin'],
                        'market': row['market'],
                        'price': row['price'],
                        'match_type': 'pinyin',
                        'source': 'database'
                    })
            
            return results[:limit]
            
        except Exception as e:
            print(f"数据库搜索错误: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_stock_info(self, code: str) -> Optional[Dict]:
        """获取股票详细信息"""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM stocks WHERE code = ?', (code,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'code': row['code'],
                    'name': row['name'],
                    'pinyin': row['pinyin'],
                    'market': row['market'],
                    'price': row['price'],
                    'market_cap': row['market_cap'],
                    'industry': row['industry'],
                    'source': 'database'
                }
            return None
            
        except Exception as e:
            print(f"数据库查询错误: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        conn = self._get_connection()
        if not conn:
            return {'total': 0, 'by_market': {}}
        
        try:
            cursor = conn.cursor()
            
            # 总数
            cursor.execute('SELECT COUNT(*) FROM stocks')
            total = cursor.fetchone()[0]
            
            # 按市场分布
            cursor.execute('''
                SELECT market, COUNT(*) FROM stocks 
                GROUP BY market ORDER BY COUNT(*) DESC
            ''')
            by_market = dict(cursor.fetchall())
            
            return {
                'total': total,
                'by_market': by_market
            }
            
        except Exception as e:
            print(f"数据库统计错误: {e}")
            return {'total': 0, 'by_market': {}}
        finally:
            if conn:
                conn.close()
    
    def close(self):
        """关闭连接（已不需要，每次使用后自动关闭）"""
        pass

# 全局数据库实例
_stock_db = None

def get_stock_database():
    """获取全局股票数据库实例"""
    global _stock_db
    if _stock_db is None:
        _stock_db = StockDatabase()
    return _stock_db

def search_stocks_db(query: str, limit: int = 10) -> List[Dict]:
    """从本地数据库搜索股票"""
    db = get_stock_database()
    return db.search_stocks(query, limit)

def get_stock_info_db(code: str) -> Optional[Dict]:
    """从本地数据库获取股票信息"""
    db = get_stock_database()
    return db.get_stock_info(code)

# 构建数据库的主函数
def build_stock_database():
    """构建A股数据库的主函数"""
    builder = StockDatabaseBuilder()
    try:
        stats = builder.build_database()
        return stats
    finally:
        builder.close()

if __name__ == '__main__':
    # 构建数据库
    print("🏗️ 开始构建A股本地数据库...")
    stats = build_stock_database()
    
    print(f"\n🎉 数据库构建完成！")
    print(f"包含 {stats['total']} 只A股股票")
    
    # 测试搜索功能
    print(f"\n🔍 测试搜索功能:")
    test_queries = ['中际旭创', '300308', 'zjxc', '宁德时代', 'ndsd']
    
    for query in test_queries:
        results = search_stocks_db(query, 3)
        print(f"搜索 '{query}': 找到 {len(results)} 个结果")
        for r in results:
            print(f"  {r['code']} - {r['name']} [{r['market']}] [{r['match_type']}]")
