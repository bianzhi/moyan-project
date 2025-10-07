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
            
            # 转换股票代码格式 (去掉后缀)
            clean_symbol = symbol.split('.')[0]
            
            print(f"🔍 akshare获取数据: {clean_symbol}, {start_date} - {end_date}")
            
            # 调用akshare API
            data = self.ak.stock_zh_a_hist(
                symbol=clean_symbol,
                period="daily",
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
        max_retries = 2
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    print(f"⏳ yfinance第{attempt + 1}次尝试，延迟{delay}秒...")
                    time.sleep(delay)
                
                ticker = self.yf.Ticker(symbol)
                data = ticker.history(**kwargs)
                
                if data is not None and len(data) > 0:
                    return data
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    if attempt < max_retries - 1:
                        continue
                raise e
        
        return None

class TushareDataSource(DataSourceBase):
    """Tushare数据源"""
    
    def __init__(self, token: Optional[str] = None):
        super().__init__("tushare", priority=2)
        self.token = token
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
        # 1. Akshare - 免费且稳定
        akshare_source = AkshareDataSource()
        self.data_sources.append(akshare_source)
        
        # 2. Tushare - 需要token
        tushare_token = self.config.get('tushare_token')
        if tushare_token:
            tushare_source = TushareDataSource(tushare_token)
            self.data_sources.append(tushare_source)
        
        # 3. YFinance - 容易被限流，优先级最低
        yfinance_source = YFinanceDataSource()
        self.data_sources.append(yfinance_source)
    
    def get_stock_data(self, 
                      stock_code: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      **kwargs) -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取股票数据，自动尝试多个数据源
        
        Returns:
            Tuple[DataFrame, str]: (数据, 使用的数据源名称)
        """
        # 格式化股票代码
        symbol = self._format_symbol(stock_code)
        
        # 准备参数
        params = {
            'start': start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            'end': end_date or datetime.now().strftime('%Y-%m-%d'),
            **kwargs
        }
        
        print(f"📊 尝试获取股票数据: {stock_code}")
        print(f"📅 时间范围: {params['start']} 至 {params['end']}")
        
        # 按优先级尝试各个数据源
        for i, data_source in enumerate(self.data_sources):
            if not data_source.is_available():
                print(f"⚠️ 跳过不可用的数据源: {data_source.name}")
                continue
            
            print(f"🔍 尝试数据源 {i+1}/{len(self.data_sources)}: {data_source.name}")
            
            try:
                data = data_source.get_data(symbol, **params)
                if data is not None and len(data) > 0:
                    print(f"✅ {data_source.name} 成功获取 {len(data)} 条数据")
                    return data, data_source.name
                else:
                    print(f"⚠️ {data_source.name} 未获取到数据")
                    
            except Exception as e:
                print(f"❌ {data_source.name} 获取失败: {e}")
                
            # 如果不启用容错，第一个失败就停止
            if not self.fallback_enabled:
                break
        
        print("❌ 所有数据源均失败")
        return None, "none"
    
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
