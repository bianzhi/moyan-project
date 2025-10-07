"""
数据源管理

管理各种数据源的接入和数据获取
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import warnings
from datetime import datetime, timedelta

# 导入配置
from ..config.kline_config import get_kline_config, validate_kline_level
from ..config.settings import default_config

class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """获取数据的抽象方法"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        pass

class YFinanceDataSource(DataSource):
    """YFinance数据源"""
    
    def __init__(self):
        self.name = "yfinance"
        self._check_availability()
    
    def _check_availability(self):
        """检查yfinance是否可用"""
        try:
            import yfinance as yf
            self.yf = yf
            self.available = True
        except ImportError:
            self.available = False
            warnings.warn("yfinance未安装，请运行: pip install yfinance")
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self.available
    
    def get_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """
        获取股票数据，带重试机制避免限流
        
        Args:
            symbol: 股票代码 (如: 002167.SZ)
            **kwargs: 其他参数 (start, end, interval等)
            
        Returns:
            pandas.DataFrame: 股票数据
        """
        if not self.available:
            raise RuntimeError("yfinance数据源不可用")
        
        import time
        max_retries = 3
        base_delay = 2  # 基础延迟2秒
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # 指数退避
                    print(f"⏳ 第{attempt + 1}次尝试，延迟{delay}秒...")
                    time.sleep(delay)
                
                ticker = self.yf.Ticker(symbol)
                data = ticker.history(**kwargs)
                
                if data is not None and len(data) > 0:
                    return data
                else:
                    print(f"⚠️ 第{attempt + 1}次尝试未获取到数据")
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    print(f"⚠️ 第{attempt + 1}次尝试遇到限流: {e}")
                    if attempt < max_retries - 1:
                        continue
                else:
                    print(f"❌ yfinance数据获取失败: {e}")
                    break
        
        print("❌ 所有重试均失败")
        return None

class TushareDataSource(DataSource):
    """Tushare数据源 (可选)"""
    
    def __init__(self, token: Optional[str] = None):
        self.name = "tushare"
        self.token = token
        self._check_availability()
    
    def _check_availability(self):
        """检查tushare是否可用"""
        try:
            import tushare as ts
            self.ts = ts
            if self.token:
                ts.set_token(self.token)
            self.available = True
        except ImportError:
            self.available = False
            warnings.warn("tushare未安装，请运行: pip install tushare")
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self.available
    
    def get_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码 (如: 002167.SZ)
            **kwargs: 其他参数
            
        Returns:
            pandas.DataFrame: 股票数据
        """
        if not self.available:
            raise RuntimeError("tushare数据源不可用")
        
        # TODO: 实现tushare数据获取逻辑
        print("⚠️ Tushare数据源暂未实现")
        return None

class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self, config: Optional[Any] = None):
        """
        初始化数据源管理器
        
        Args:
            config: 配置对象
        """
        self.config = config or default_config
        self.data_sources = {}
        self.default_source = None
        
        # 初始化数据源
        self._init_data_sources()
    
    def _init_data_sources(self):
        """初始化数据源"""
        # 初始化yfinance
        yf_source = YFinanceDataSource()
        if yf_source.is_available():
            self.data_sources['yfinance'] = yf_source
            if not self.default_source:
                self.default_source = 'yfinance'
            print("✅ YFinance数据源已加载")
        
        # 初始化tushare (可选)
        try:
            ts_source = TushareDataSource()
            if ts_source.is_available():
                self.data_sources['tushare'] = ts_source
                print("✅ Tushare数据源已加载")
        except Exception as e:
            print(f"⚠️ Tushare数据源加载失败: {e}")
        
        if not self.data_sources:
            raise RuntimeError("没有可用的数据源")
        
        print(f"📊 数据源管理器已初始化，默认源: {self.default_source}")
    
    def get_stock_data(self, 
                      stock_code: str,
                      kline_level: str = '1d',
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      days: Optional[int] = None,
                      source: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取股票数据
        
        Args:
            stock_code: 6位股票代码
            kline_level: K线级别
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            days: 获取天数
            source: 指定数据源
            
        Returns:
            dict: 包含数据和元信息的字典
        """
        # 验证K线级别
        if not validate_kline_level(kline_level):
            raise ValueError(f"不支持的K线级别: {kline_level}")
        
        kline_config = get_kline_config(kline_level)
        
        # 选择数据源
        source_name = source or self.default_source
        if source_name not in self.data_sources:
            raise ValueError(f"数据源不可用: {source_name}")
        
        data_source = self.data_sources[source_name]
        
        # 构造股票代码
        symbol = self._format_symbol(stock_code)
        
        # 处理时间参数
        start_formatted, end_formatted = self._process_time_params(
            start_date, end_date, days, kline_config
        )
        
        print(f"📊 获取股票数据: {stock_code}")
        print(f"📈 K线级别: {kline_config['name']} ({kline_level})")
        print(f"📅 时间区间: {start_formatted} 至 {end_formatted}")
        print(f"🔗 数据源: {source_name}")
        
        # 获取数据
        try:
            if source_name == 'yfinance':
                data = data_source.get_data(
                    symbol=symbol,
                    start=start_formatted,
                    end=end_formatted,
                    interval=kline_config['yfinance_interval']
                )
            else:
                data = data_source.get_data(symbol=symbol)
            
            if data is None or len(data) == 0:
                print("❌ 未获取到数据")
                return None
            
            # 获取股票名称 (尝试)
            stock_name = self._get_stock_name(symbol, source_name)
            
            result = {
                'stock_code': stock_code,
                'symbol': symbol,
                'stock_name': stock_name,
                'kline_level': kline_level,
                'kline_config': kline_config,
                'data_source': source_name,
                'start_date': start_formatted,
                'end_date': end_formatted,
                'data': data,
                'data_count': len(data),
                'actual_start': data.index[0].strftime('%Y-%m-%d %H:%M' if 'm' in kline_level else '%Y-%m-%d'),
                'actual_end': data.index[-1].strftime('%Y-%m-%d %H:%M' if 'm' in kline_level else '%Y-%m-%d'),
            }
            
            print(f"✅ 成功获取 {len(data)} 条{kline_config['name']}数据")
            print(f"📈 股票名称: {stock_name}")
            print(f"📅 实际数据范围: {result['actual_start']} 至 {result['actual_end']}")
            
            return result
            
        except Exception as e:
            print(f"❌ 数据获取失败: {e}")
            return None
    
    def _format_symbol(self, stock_code: str) -> str:
        """
        格式化股票代码为数据源需要的格式
        
        Args:
            stock_code: 6位股票代码
            
        Returns:
            str: 格式化后的代码
        """
        if not stock_code.isdigit() or len(stock_code) != 6:
            raise ValueError(f"无效的股票代码: {stock_code}")
        
        # 判断市场
        if stock_code.startswith('6'):
            return f"{stock_code}.SS"  # 上交所
        elif stock_code.startswith(('0', '3')):
            return f"{stock_code}.SZ"  # 深交所
        else:
            raise ValueError(f"不支持的股票代码格式: {stock_code}")
    
    def _process_time_params(self, 
                           start_date: Optional[str],
                           end_date: Optional[str], 
                           days: Optional[int],
                           kline_config: Dict[str, Any]) -> tuple:
        """
        处理时间参数
        
        Returns:
            tuple: (start_formatted, end_formatted)
        """
        # 处理日期参数，根据K线级别设置默认值
        if start_date is None and end_date is None and days is None:
            # 使用K线级别的默认天数
            days = kline_config['default_days']
            
        if days is not None:
            # 使用天数计算
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days)
            start_date = start_dt.strftime('%Y%m%d')
            end_date = end_dt.strftime('%Y%m%d')
        else:
            # 使用指定的日期
            if start_date is None:
                # 根据K线级别设置默认开始日期
                days = kline_config['default_days']
                start_dt = datetime.now() - timedelta(days=days)
                start_date = start_dt.strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
        
        # 标准化日期格式
        def format_date(date_str):
            if len(date_str) == 8:  # YYYYMMDD
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return date_str  # 已经是 YYYY-MM-DD 格式
        
        return format_date(start_date), format_date(end_date)
    
    def _get_stock_name(self, symbol: str, source_name: str) -> str:
        """
        获取股票名称，优先使用本地股票数据库
        
        Args:
            symbol: 股票代码
            source_name: 数据源名称
            
        Returns:
            str: 股票名称
        """
        # 1. 优先使用本地股票数据库
        try:
            from moyan.config.stock_database import get_stock_info
            stock_info = get_stock_info(symbol)
            if stock_info:
                return stock_info['name']
        except ImportError:
            pass
        
        # 2. 不再访问yfinance，避免高频请求导致限流
        # 直接返回默认名称
        
        # 3. 默认返回带股票代码的名称
        return f'股票{symbol}'
    
    def get_available_sources(self) -> List[str]:
        """获取可用的数据源列表"""
        return list(self.data_sources.keys())
    
    def set_default_source(self, source_name: str):
        """
        设置默认数据源
        
        Args:
            source_name: 数据源名称
        """
        if source_name not in self.data_sources:
            raise ValueError(f"数据源不存在: {source_name}")
        
        self.default_source = source_name
        print(f"✅ 默认数据源已设置为: {source_name}")
    
    def add_data_source(self, name: str, source: DataSource):
        """
        添加数据源
        
        Args:
            name: 数据源名称
            source: 数据源实例
        """
        if source.is_available():
            self.data_sources[name] = source
            if not self.default_source:
                self.default_source = name
            print(f"✅ 数据源已添加: {name}")
        else:
            print(f"❌ 数据源不可用: {name}")
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"DataSourceManager(sources={list(self.data_sources.keys())}, default={self.default_source})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()
