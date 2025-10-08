# src/moyan/core/enhanced_data_source.py
"""
增强的多数据源管理系统
支持多种数据源的自动切换和容错机制
"""

import warnings
import time
import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict, Tuple
from datetime import datetime, timedelta

class DataSourceBase(ABC):
    """数据源基类"""
    
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority  # 优先级，数字越小优先级越高
        self.available = False
        self.last_error = None
        self.success_count = 0
        self.error_count = 0
        self.last_success_time = None
        self.last_error_time = None
        
    @abstractmethod
    def _check_availability(self) -> bool:
        """检查数据源是否可用"""
        pass
    
    @abstractmethod
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """获取数据的具体实现"""
        pass
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        if not self.available:
            self.available = self._check_availability()
        return self.available
    
    def get_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """获取数据，带统计信息"""
        if not self.is_available():
            return None
            
        try:
            data = self._fetch_data(symbol, **kwargs)
            if data is not None and len(data) > 0:
                self.success_count += 1
                self.last_success_time = datetime.now()
                self.last_error = None
                return data
            else:
                self.error_count += 1
                self.last_error = "未获取到数据"
                self.last_error_time = datetime.now()
                return None
                
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.last_error_time = datetime.now()
            print(f"❌ {self.name}数据获取失败: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """获取数据源统计信息"""
        return {
            'name': self.name,
            'priority': self.priority,
            'available': self.available,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_count / max(1, self.success_count + self.error_count),
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'last_error': self.last_error
        }

class AkshareDataSource(DataSourceBase):
    """Akshare数据源 - 免费且稳定的A股数据源"""
    
    def __init__(self):
        super().__init__("akshare", priority=1)  # 高优先级
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查akshare是否可用"""
        try:
            import akshare as ak
            self.ak = ak
            return True  # 简化检查，避免不必要的API调用
        except ImportError:
            warnings.warn("akshare未安装，请运行: pip install akshare")
            return False
        except Exception as e:
            print(f"⚠️ akshare初始化失败: {e}")
            return False
    
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用akshare获取股票数据"""
        try:
            # 解析参数
            start_date = kwargs.get('start', '2024-01-01')
            end_date = kwargs.get('end', datetime.now().strftime('%Y-%m-%d'))
            kline_level = kwargs.get('kline_level', '1d')  # 获取K线级别
            
            # 转换股票代码格式 (去掉后缀)
            clean_symbol = symbol.split('.')[0]
            
            # 根据K线级别选择akshare的period参数
            period_map = {
                '1d': 'daily',
                '1wk': 'weekly', 
                '1mo': 'monthly',
                # akshare不支持分钟级别数据，对于分钟级别使用日线数据
                '15m': 'daily',
                '30m': 'daily',
                '1h': 'daily'
            }
            
            period = period_map.get(kline_level, 'daily')
            
            print(f"🔍 akshare获取数据: {clean_symbol}, {start_date} - {end_date}, K线级别: {kline_level} -> {period}")
            
            # 调用akshare API
            data = self.ak.stock_zh_a_hist(
                symbol=clean_symbol,
                period=period,
                start_date=start_date.replace('-', ''),  # akshare需要YYYYMMDD格式
                end_date=end_date.replace('-', ''),
                adjust=""  # 不复权
            )
            
            if data is None or len(data) == 0:
                print("⚠️ akshare返回空数据")
                return None
            
            print(f"✅ akshare原始数据: {data.shape}, 列名: {list(data.columns)}")
            
            # 标准化列名和索引
            data = data.rename(columns={
                '日期': 'Date',
                '开盘': 'Open', 
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low', 
                '成交量': 'Volume'
            })
            
            # 设置日期索引
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.set_index('Date')
            
            # 选择需要的列并重命名为yfinance格式
            result = pd.DataFrame({
                'Open': data['Open'],
                'High': data['High'], 
                'Low': data['Low'],
                'Close': data['Close'],
                'Volume': data['Volume']
            })
            
            # 对于分钟级别数据，给出警告
            if kline_level in ['15m', '30m', '1h']:
                print(f"⚠️ akshare不支持{kline_level}级别数据，已降级使用日线数据")
            
            print(f"✅ akshare处理后数据: {result.shape}")
            return result
            
        except Exception as e:
            print(f"❌ akshare详细错误: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"akshare数据获取失败: {e}")

class YFinanceDataSource(DataSourceBase):
    """YFinance数据源 - 带重试机制"""
    
    def __init__(self):
        super().__init__("yfinance", priority=3)  # 较低优先级
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查yfinance是否可用"""
        try:
            import yfinance as yf
            self.yf = yf
            return True
        except ImportError:
            warnings.warn("yfinance未安装，请运行: pip install yfinance")
            return False
    
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用yfinance获取股票数据，带重试机制"""
        max_retries = 3  # 增加重试次数
        base_delay = 5   # 增加基础延迟到5秒
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # 指数退避：5s, 10s, 20s
                    print(f"⏳ yfinance第{attempt + 1}次尝试，延迟{delay}秒...")
                    time.sleep(delay)
                
                ticker = self.yf.Ticker(symbol)
                data = ticker.history(**kwargs)
                
                if data is not None and len(data) > 0:
                    print(f"✅ yfinance成功获取 {len(data)} 条数据")
                    return data
                else:
                    print(f"⚠️ yfinance第{attempt + 1}次尝试未获取到数据")
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    print(f"⚠️ yfinance第{attempt + 1}次尝试遇到限流: {e}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        print("❌ yfinance所有重试均因限流失败")
                        return None
                else:
                    print(f"❌ yfinance遇到其他错误: {e}")
                    # 其他非限流错误直接退出
                    return None
        
        print("❌ yfinance所有重试均失败")
        return None

class BaostockDataSource(DataSourceBase):
    """Baostock数据源 - 免费的A股数据源，支持分钟级别"""
    
    def __init__(self):
        super().__init__("baostock", priority=2)  # 中等优先级，介于akshare和yfinance之间
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查baostock是否可用"""
        try:
            import baostock as bs
            self.bs = bs
            self.available = True
            return True
        except ImportError:
            warnings.warn("baostock未安装，请运行: pip install baostock")
            self.available = False
            return False
        except Exception as e:
            print(f"⚠️ baostock初始化失败: {e}")
            self.available = False
            return False
    
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用baostock获取股票数据"""
        try:
            # 登录baostock
            lg = self.bs.login()
            if lg.error_code != '0':
                print(f"❌ baostock登录失败: {lg.error_msg}")
                return None
            
            # 解析参数
            start_date = kwargs.get('start', '2024-01-01')
            end_date = kwargs.get('end', datetime.now().strftime('%Y-%m-%d'))
            kline_level = kwargs.get('kline_level', '1d')
            
            # 转换股票代码格式 (添加市场前缀)
            clean_symbol = symbol.split('.')[0]
            if clean_symbol.startswith('6'):
                bs_symbol = f"sh.{clean_symbol}"  # 上海
            else:
                bs_symbol = f"sz.{clean_symbol}"  # 深圳
            
            # 根据K线级别选择baostock的frequency参数
            frequency_map = {
                '1d': 'd',    # 日线
                '1wk': 'w',   # 周线
                '1mo': 'm',   # 月线
                '5m': '5',    # 5分钟
                '15m': '15',  # 15分钟
                '30m': '30',  # 30分钟
                '1h': '60'    # 60分钟
            }
            
            frequency = frequency_map.get(kline_level, 'd')
            
            print(f"🔍 baostock获取数据: {bs_symbol}, {start_date} - {end_date}, 频率: {frequency}")
            
            # 调用baostock API
            if frequency in ['5', '15', '30', '60']:
                # 分钟级别数据
                rs = self.bs.query_history_k_data_plus(
                    bs_symbol,
                    "date,time,code,open,high,low,close,volume,amount",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    frequency=frequency,
                    adjustflag="3"  # 不复权
                )
            else:
                # 日线级别数据
                rs = self.bs.query_history_k_data_plus(
                    bs_symbol,
                    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    frequency=frequency,
                    adjustflag="3"  # 不复权
                )
            
            # 检查查询结果
            if rs is None:
                print("❌ baostock查询返回None")
                return None
                
            if hasattr(rs, 'error_code') and rs.error_code != '0':
                print(f"❌ baostock查询失败: {rs.error_msg}")
                self.bs.logout()
                return None
            
            # 获取数据列表
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            # 登出
            self.bs.logout()
            
            if not data_list:
                print("⚠️ baostock返回空数据")
                return None
            
            # 转换为DataFrame
            if frequency in ['5', '15', '30', '60']:
                # 分钟级别数据
                columns = ["date", "time", "code", "open", "high", "low", "close", "volume", "amount"]
                df = pd.DataFrame(data_list, columns=columns)
                # 合并日期和时间
                df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                df = df.set_index('datetime')
            else:
                # 日线级别数据
                columns = ["date", "code", "open", "high", "low", "close", "preclose", "volume", "amount", "adjustflag", "turn", "tradestatus", "pctChg", "isST"]
                df = pd.DataFrame(data_list, columns=columns)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            # 标准化列名和数据类型
            result = pd.DataFrame({
                'Open': pd.to_numeric(df['open'], errors='coerce'),
                'High': pd.to_numeric(df['high'], errors='coerce'),
                'Low': pd.to_numeric(df['low'], errors='coerce'),
                'Close': pd.to_numeric(df['close'], errors='coerce'),
                'Volume': pd.to_numeric(df['volume'], errors='coerce')
            })
            
            # 过滤无效数据
            result = result.dropna()
            
            print(f"✅ baostock处理后数据: {result.shape}")
            return result
            
        except Exception as e:
            print(f"❌ baostock详细错误: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.bs.logout()
            except:
                pass
            return None


class EastmoneyDataSource(DataSourceBase):
    """东方财富数据源 - 通过爬虫获取分钟级别数据"""
    
    def __init__(self):
        super().__init__("eastmoney", priority=4)  # 较低优先级
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查requests是否可用"""
        try:
            import requests
            self.requests = requests
            self.available = True
            return True
        except ImportError:
            warnings.warn("requests未安装，请运行: pip install requests")
            self.available = False
            return False
    
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用东方财富API获取分钟级别数据"""
        try:
            # 解析参数
            kline_level = kwargs.get('kline_level', '1d')
            
            # 只支持分钟级别数据
            if kline_level not in ['5m', '15m', '30m', '1h']:
                print(f"⚠️ eastmoney暂不支持{kline_level}级别数据")
                return None
            
            # 转换股票代码格式
            clean_symbol = symbol.split('.')[0]
            if clean_symbol.startswith('6'):
                em_symbol = f"1.{clean_symbol}"  # 上海
            else:
                em_symbol = f"0.{clean_symbol}"  # 深圳
            
            # 频率映射
            klt_map = {
                '5m': '5',
                '15m': '15', 
                '30m': '30',
                '1h': '60'
            }
            
            klt = klt_map.get(kline_level, '30')
            
            print(f"🔍 eastmoney获取数据: {em_symbol}, K线级别: {kline_level}")
            
            # 解析时间参数以获取更多历史数据
            start_date = kwargs.get('start', '2024-01-01')
            end_date = kwargs.get('end', datetime.now().strftime('%Y-%m-%d'))
            
            # 计算需要的数据条数（根据时间范围和K线级别）
            from datetime import datetime as dt
            start_dt = dt.strptime(start_date, '%Y-%m-%d')
            end_dt = dt.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days
            
            # 根据K线级别估算需要的数据条数，使用最大可能的限制
            if kline_level == '1h':
                # 1小时线：每天约4条，使用最大限制
                estimated_bars = days_diff * 4 + 500
                max_limit = 15000  # Eastmoney可以支持更大的请求量
            elif kline_level == '30m':
                # 30分钟线：每天约8条
                estimated_bars = days_diff * 8 + 1000
                max_limit = 10000  # 提高限制
            elif kline_level == '15m':
                # 15分钟线：每天约16条
                estimated_bars = days_diff * 16 + 2000
                max_limit = 10000  # 提高限制
            else:
                # 5分钟线：每天约48条
                estimated_bars = days_diff * 48 + 5000
                max_limit = 10000  # 提高限制
            
            lmt = min(estimated_bars, max_limit)
            
            # 记录请求信息，便于调试
            print(f"🔍 eastmoney估算需要数据: {estimated_bars}条，实际请求: {lmt}条（最大限制{max_limit}）")
            print(f"📊 时间跨度{days_diff}天，{kline_level}级别理论需要{days_diff * {'1h':4,'30m':8,'15m':16,'5m':48}.get(kline_level,4)}条数据")
            
            # 构造请求URL
            url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': em_symbol,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': klt,
                'fqt': '1',
                'end': '20500101',
                'lmt': str(lmt)  # 动态调整数据条数
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'http://quote.eastmoney.com/'
            }
            
            response = self.requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ eastmoney请求失败: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            if not data or 'data' not in data or not data['data']:
                print("⚠️ eastmoney返回空数据")
                return None
            
            klines = data['data']['klines']
            if not klines:
                print("⚠️ eastmoney K线数据为空")
                return None
            
            # 解析K线数据
            records = []
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 6:
                    records.append({
                        'datetime': pd.to_datetime(parts[0]),
                        'open': float(parts[1]),
                        'close': float(parts[2]), 
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5])
                    })
            
            if not records:
                print("⚠️ eastmoney解析后数据为空")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(records)
            df = df.set_index('datetime')
            
            # 标准化列名
            result = pd.DataFrame({
                'Open': df['open'],
                'High': df['high'],
                'Low': df['low'],
                'Close': df['close'],
                'Volume': df['volume']
            })
            
            print(f"✅ eastmoney处理后数据: {result.shape}")
            return result
            
        except Exception as e:
            print(f"❌ eastmoney详细错误: {e}")
            return None

class SinaDataSource(DataSourceBase):
    """新浪财经数据源 - 支持分钟级别数据"""
    
    def __init__(self):
        super().__init__("sina", priority=1)  # 高优先级，仅次于akshare
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查requests是否可用"""
        try:
            import requests
            self.requests = requests
            self.available = True
            return True
        except ImportError:
            warnings.warn("requests未安装，请运行: pip install requests")
            self.available = False
            return False
    
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用新浪财经API获取分钟级别数据"""
        try:
            # 解析参数
            kline_level = kwargs.get('kline_level', '1d')
            
            # 支持日线和分钟级别数据
            if kline_level not in ['1d', '5m', '15m', '30m', '1h']:
                print(f"⚠️ sina暂不支持{kline_level}级别数据")
                return None
            
            # 转换股票代码格式
            clean_symbol = symbol.split('.')[0]
            if clean_symbol.startswith('6'):
                sina_symbol = f"sh{clean_symbol}"  # 上海
            elif clean_symbol.startswith('688'):
                sina_symbol = f"sh{clean_symbol}"  # 科创板
            else:
                sina_symbol = f"sz{clean_symbol}"  # 深圳
            
            # 频率映射
            scale_map = {
                '1d': '240',   # 240分钟 = 1天
                '5m': '5',
                '15m': '15', 
                '30m': '30',
                '1h': '60'
            }
            
            scale = scale_map.get(kline_level, '30')
            
            # 解析时间参数
            start_date = kwargs.get('start', '2024-01-01')
            end_date = kwargs.get('end', datetime.now().strftime('%Y-%m-%d'))
            
            # 计算时间差用于数据量估算
            from datetime import datetime as dt
            start_dt = dt.strptime(start_date, '%Y-%m-%d')
            end_dt = dt.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days
            
            print(f"🔍 sina获取数据: {sina_symbol}, K线级别: {kline_level}, 时间范围: {start_date} - {end_date}")
            
            # 根据K线级别计算理论数据量，统一使用1500条限制（实测sina最优值）
            if kline_level == '1d':
                # 日线：1500条可覆盖约6年数据
                expected_count = days_diff + 100
                max_limit = 1500  # sina日线最大1500条
            elif kline_level == '1h':
                # 1小时线：1500条可覆盖约1年数据
                expected_count = days_diff * 4 + 500
                max_limit = 1500  # sina 1h最大1500条
            elif kline_level == '30m':
                # 30分钟线：1500条可覆盖约9个月
                expected_count = days_diff * 8 + 400
                max_limit = 1500  # sina 30m最大1500条
            elif kline_level == '15m':
                # 15分钟线：1500条可覆盖约4个月
                expected_count = days_diff * 16 + 800
                max_limit = 1500  # sina 15m最大1500条
            elif kline_level == '5m':
                # 5分钟线：保持1000条限制（短期分析够用）
                expected_count = days_diff * 48 + 1000
                max_limit = 1000  # 5分钟数据通常用于短期分析
            else:
                expected_count = 1000
                max_limit = 1500
            
            datalen = min(expected_count, max_limit)
            
            # 记录请求信息，便于调试
            print(f"🔢 预计需要{expected_count}条数据，实际请求{datalen}条（最大限制{max_limit}）")
            if kline_level != '1d':
                print(f"📊 时间跨度{days_diff}天，{kline_level}级别理论需要{days_diff * {'1h':4,'30m':8,'15m':16,'5m':48}.get(kline_level,4)}条数据")
            
            # 构造请求URL
            url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
            params = {
                'symbol': sina_symbol,
                'scale': scale,
                'ma': 'no',
                'datalen': datalen
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Referer': 'https://finance.sina.com.cn/'
            }
            
            response = self.requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ sina请求失败: HTTP {response.status_code}")
                return None
            
            # 解析JSON数据
            data = response.json()
            
            if not data or not isinstance(data, list):
                print("⚠️ sina返回空数据或格式错误")
                return None
            
            # 解析K线数据
            records = []
            for item in data:
                if isinstance(item, dict) and 'day' in item:
                    try:
                        records.append({
                            'datetime': pd.to_datetime(item['day']),
                            'open': float(item['open']),
                            'high': float(item['high']),
                            'low': float(item['low']),
                            'close': float(item['close']),
                            'volume': float(item.get('volume', 0))
                        })
                    except (ValueError, KeyError) as e:
                        continue
            
            if not records:
                print("⚠️ sina解析后数据为空")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(records)
            df = df.set_index('datetime')
            df = df.sort_index()  # 按时间排序
            
            # 过滤时间范围
            try:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)  # 包含结束日期
                df_filtered = df[(df.index >= start_dt) & (df.index < end_dt)]
                print(f"📅 时间过滤: {len(df)} -> {len(df_filtered)} 条数据")
                df = df_filtered
            except Exception as e:
                print(f"⚠️ 时间过滤失败，使用全部数据: {e}")
            
            # 标准化列名
            result = pd.DataFrame({
                'Open': df['open'],
                'High': df['high'],
                'Low': df['low'],
                'Close': df['close'],
                'Volume': df['volume']
            })
            
            print(f"✅ sina最终数据: {result.shape}, 时间范围: {result.index.min()} - {result.index.max()}")
            return result
            
        except Exception as e:
            print(f"❌ sina详细错误: {e}")
            return None

class TushareDataSource(DataSourceBase):
    """Tushare数据源"""
    
    def __init__(self, token: Optional[str] = None):
        super().__init__("tushare", priority=5)  # 较低优先级，需要token
        self.token = token or os.environ.get("TUSHARE_TOKEN")
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查tushare是否可用"""
        try:
            import tushare as ts
            self.ts = ts
            if self.token:
                ts.set_token(self.token)
                return True
            else:
                print("⚠️ Tushare需要token才能使用")
                return False
        except ImportError:
            warnings.warn("tushare未安装，请运行: pip install tushare")
            return False
    
    def _fetch_data(self, symbol: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用tushare获取股票数据"""
        # TODO: 实现tushare数据获取逻辑
        print("⚠️ Tushare数据源暂未完全实现")
        return None

class MultiDataSourceManager:
    """多数据源管理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化多数据源管理器
        
        Args:
            config: 配置字典，包含数据源优先级等设置
        """
        self.config = config or {}
        self.data_sources: List[DataSourceBase] = []
        self.fallback_enabled = self.config.get('fallback_enabled', True)
        self.max_fallback_attempts = self.config.get('max_fallback_attempts', 3)
        
        # 初始化数据源
        self._init_data_sources()
        
        # 按优先级排序
        self.data_sources.sort(key=lambda x: x.priority)
        
        print(f"✅ 多数据源管理器已初始化，共{len(self.data_sources)}个数据源")
        for ds in self.data_sources:
            status = "可用" if ds.is_available() else "不可用"
            print(f"  📊 {ds.name} (优先级{ds.priority}): {status}")
    
    def _init_data_sources(self):
        """初始化所有数据源"""
        # 1. Akshare - 免费且稳定，但不支持分钟级别
        akshare_source = AkshareDataSource()
        self.data_sources.append(akshare_source)
        
        # 2. Sina - 新浪财经，支持分钟级别数据，稳定性好
        sina_source = SinaDataSource()
        self.data_sources.append(sina_source)
        
        # 3. Baostock - 免费且支持分钟级别数据
        baostock_source = BaostockDataSource()
        self.data_sources.append(baostock_source)
        
        # 4. Tushare - 需要token，数据质量高
        tushare_token = self.config.get('tushare_token')
        if tushare_token:
            tushare_source = TushareDataSource(tushare_token)
            self.data_sources.append(tushare_source)
        
        # 5. Eastmoney - 爬虫方式，仅分钟级别
        eastmoney_source = EastmoneyDataSource()
        self.data_sources.append(eastmoney_source)
        
        # 6. YFinance - 容易被限流，优先级最低
        yfinance_source = YFinanceDataSource()
        self.data_sources.append(yfinance_source)
    
    def get_stock_data(self, 
                      stock_code: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      kline_level: str = '1d',
                      **kwargs) -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取股票数据，自动尝试多个数据源
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            kline_level: K线级别 (1d, 30m, 1h等)
            
        Returns:
            Tuple[DataFrame, str]: (数据, 使用的数据源名称)
        """
        # 格式化股票代码
        symbol = self._format_symbol(stock_code)
        
        # 准备参数
        params = {
            'start': start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            'end': end_date or datetime.now().strftime('%Y-%m-%d'),
            'kline_level': kline_level,  # 明确传递K线级别
            **kwargs
        }
        
        print(f"📊 尝试获取股票数据: {stock_code}")
        print(f"📅 时间范围: {params['start']} 至 {params['end']}")
        print(f"📈 K线级别: {kline_level}")
        
        # 根据K线级别动态调整数据源优先级
        ordered_sources = self._get_ordered_sources_by_kline_level(kline_level)
        
        # 按优先级尝试各个数据源
        last_error_msg = ""
        minute_level_failed = False
        
        for i, data_source in enumerate(ordered_sources):
            if not data_source.is_available():
                print(f"⚠️ 跳过不可用的数据源: {data_source.name}")
                continue
            
            print(f"🔍 尝试数据源 {i+1}/{len(ordered_sources)}: {data_source.name}")
            
            try:
                # 根据数据源类型传递不同的参数
                if data_source.name == "akshare":
                    # akshare使用6位代码
                    clean_symbol = symbol.split('.')[0]
                    data = data_source.get_data(clean_symbol, **params)
                elif data_source.name == "sina":
                    # sina使用6位代码
                    clean_symbol = symbol.split('.')[0]
                    data = data_source.get_data(clean_symbol, **params)
                elif data_source.name == "baostock":
                    # baostock使用6位代码
                    clean_symbol = symbol.split('.')[0]
                    data = data_source.get_data(clean_symbol, **params)
                elif data_source.name == "eastmoney":
                    # eastmoney使用6位代码
                    clean_symbol = symbol.split('.')[0]
                    data = data_source.get_data(clean_symbol, **params)
                elif data_source.name == "yfinance":
                    # yfinance需要interval参数而不是kline_level，并且需要完整的symbol格式
                    yf_params = {
                        'start': params['start'],
                        'end': params['end'],
                        'interval': self._get_yfinance_interval(kline_level)
                    }
                    print(f"🔍 yfinance使用参数: symbol={symbol}, interval={yf_params['interval']}")
                    data = data_source.get_data(symbol, **yf_params)
                else:
                    data = data_source.get_data(symbol, **params)
                    
                if data is not None and len(data) > 0:
                    print(f"✅ {data_source.name} 成功获取 {len(data)} 条数据")
                    return data, data_source.name
                else:
                    print(f"⚠️ {data_source.name} 未获取到数据")
                    if data_source.name == "yfinance" and kline_level in ['15m', '30m', '1h', '5m', '2m', '1m']:
                        minute_level_failed = True
                        last_error_msg = f"{data_source.name}分钟级别数据获取失败"
                    
            except Exception as e:
                error_msg = f"{data_source.name} 获取失败: {e}"
                print(f"❌ {error_msg}")
                if data_source.name == "yfinance" and kline_level in ['15m', '30m', '1h', '5m', '2m', '1m']:
                    minute_level_failed = True
                    last_error_msg = error_msg
                
            # 如果不启用容错，第一个失败就停止
            if not self.fallback_enabled:
                break
        
        # 如果是分钟级别数据获取失败，给出特别提示
        if minute_level_failed and kline_level in ['15m', '30m', '1h', '5m', '2m', '1m']:
            print(f"❌ 分钟级别数据({kline_level})获取失败")
            print(f"💡 建议: 1) 稍后重试 2) 使用日线数据 3) 检查网络连接")
            print(f"📝 错误详情: {last_error_msg}")
        
        print("❌ 所有数据源均失败")
        return None, "none"
    
    def _get_ordered_sources_by_kline_level(self, kline_level: str) -> List:
        """根据K线级别返回优先级排序的数据源列表"""
        # 基于实测结果，sina在日线和分钟级别都表现优异
        if kline_level in ['15m', '30m', '1h', '5m', '2m', '1m']:
            print(f"🔄 检测到分钟级别数据({kline_level})，调整数据源优先级：sina > baostock > eastmoney > yfinance > akshare")
            # 重新排序：sina优先（支持1500条数据）
            minute_sources = []
            other_sources = []
            
            for ds in self.data_sources:
                if ds.name in ["sina", "baostock", "eastmoney", "yfinance"]:
                    minute_sources.append(ds)
                else:
                    other_sources.append(ds)
            
            # 按优先级排序分钟级别数据源：sina(1) > baostock(2) > eastmoney(4) > yfinance(3)
            minute_sources.sort(key=lambda x: x.priority)
            
            return minute_sources + other_sources
        elif kline_level in ['1d']:
            # 日线数据：sina可获取6年数据(1500条)，优于akshare的1年数据(244条)
            print(f"🔄 检测到日线级别数据({kline_level})，调整数据源优先级：sina > akshare > baostock > yfinance > eastmoney")
            # 重新排序：sina优先
            ordered_sources = []
            source_priority = {'sina': 1, 'akshare': 2, 'baostock': 3, 'yfinance': 4, 'eastmoney': 5}
            
            # 按新的优先级排序
            available_sources = [(ds, source_priority.get(ds.name, 99)) for ds in self.data_sources if ds.available]
            available_sources.sort(key=lambda x: x[1])
            
            return [ds for ds, _ in available_sources]
        else:
            # 周线、月线等：sina不支持，使用akshare优先（实测akshare表现良好）
            print(f"🔄 检测到周线/月线级别数据({kline_level})，使用默认优先级：akshare > sina > baostock > yfinance > eastmoney")
            return sorted(self.data_sources, key=lambda x: x.priority)
    
    def _format_symbol(self, stock_code: str) -> str:
        """格式化股票代码为各数据源需要的格式"""
        # 对于A股，大多数情况下直接使用6位代码
        if len(stock_code) == 6 and stock_code.isdigit():
            # 为yfinance添加后缀
            if stock_code.startswith('6'):
                return f"{stock_code}.SS"  # 上海
            else:
                return f"{stock_code}.SZ"  # 深圳
        return stock_code
    
    def _get_yfinance_interval(self, kline_level: str) -> str:
        """将K线级别转换为yfinance的interval参数"""
        interval_map = {
            '1d': '1d',
            '1wk': '1wk', 
            '1mo': '1mo',
            '30m': '30m',
            '15m': '15m',
            '1h': '1h',
            '5m': '5m',
            '2m': '2m',
            '1m': '1m'
        }
        return interval_map.get(kline_level, '1d')
    
    def get_available_sources(self) -> List[str]:
        """获取可用的数据源列表"""
        return [ds.name for ds in self.data_sources if ds.is_available()]
    
    def get_stats(self) -> Dict:
        """获取所有数据源的统计信息"""
        return {
            'total_sources': len(self.data_sources),
            'available_sources': len(self.get_available_sources()),
            'sources': [ds.get_stats() for ds in self.data_sources]
        }
    
    def reset_stats(self):
        """重置所有数据源的统计信息"""
        for ds in self.data_sources:
            ds.success_count = 0
            ds.error_count = 0
            ds.last_success_time = None
            ds.last_error_time = None
            ds.last_error = None

# 默认配置
DEFAULT_CONFIG = {
    'fallback_enabled': True,
    'max_fallback_attempts': 3,
    'tushare_token': None,  # 用户需要自己配置
}

# 全局实例
_data_source_manager = None

def get_data_source_manager(config: Optional[Dict] = None) -> MultiDataSourceManager:
    """获取全局数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = MultiDataSourceManager(config or DEFAULT_CONFIG)
    return _data_source_manager

if __name__ == '__main__':
    # 测试多数据源系统
    print("🧪 测试多数据源系统...")
    
    manager = MultiDataSourceManager()
    
    # 测试获取数据
    data, source = manager.get_stock_data("000001", start_date="2024-01-01", end_date="2024-01-10")
    
    if data is not None:
        print(f"✅ 测试成功！使用数据源: {source}")
        print(f"📊 数据形状: {data.shape}")
        print(f"📅 数据范围: {data.index[0]} 至 {data.index[-1]}")
    else:
        print("❌ 测试失败")
    
    # 显示统计信息
    stats = manager.get_stats()
    print(f"\\n📈 数据源统计:")
    for source_stats in stats['sources']:
        print(f"  {source_stats['name']}: 成功率 {source_stats['success_rate']:.2%}")
