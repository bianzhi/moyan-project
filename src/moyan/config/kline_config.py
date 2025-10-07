"""
K线级别配置

定义支持的K线级别和相关参数
"""

# K线级别配置
KLINE_LEVELS = {
    '15m': {
        'name': '15分钟线',
        'interval': '15m',
        'yfinance_interval': '15m',
        'default_days': 30,  # 默认获取30天数据
        'max_days': 60,      # 最大60天
        'description': '15分钟K线，适合短线交易',
        'min_bars': 50,      # 最少K线数量
        'recommended_bars': 200,  # 推荐K线数量
    },
    '30m': {
        'name': '30分钟线', 
        'interval': '30m',
        'yfinance_interval': '30m',
        'default_days': 60,  # 默认获取60天数据
        'max_days': 120,     # 最大120天
        'description': '30分钟K线，适合日内交易',
        'min_bars': 50,
        'recommended_bars': 150,
    },
    '1h': {
        'name': '1小时线',
        'interval': '1h', 
        'yfinance_interval': '1h',
        'default_days': 120, # 默认获取120天数据
        'max_days': 240,     # 最大240天
        'description': '1小时K线，适合短中线交易',
        'min_bars': 50,
        'recommended_bars': 120,
    },
    '1d': {
        'name': '日线',
        'interval': '1d',
        'yfinance_interval': '1d', 
        'default_days': 365, # 默认获取1年数据
        'max_days': 1095,    # 最大3年
        'description': '日K线，适合中长线分析',
        'min_bars': 30,
        'recommended_bars': 250,
    },
    '1wk': {
        'name': '周线',
        'interval': '1wk',
        'yfinance_interval': '1wk',
        'default_days': 1095, # 默认获取3年数据
        'max_days': 1825,     # 最大5年
        'description': '周K线，适合长线投资分析',
        'min_bars': 20,
        'recommended_bars': 100,
    },
    '1mo': {
        'name': '月线',
        'interval': '1mo',
        'yfinance_interval': '1mo', 
        'default_days': 1825, # 默认获取5年数据
        'max_days': 3650,     # 最大10年
        'description': '月K线，适合超长线分析',
        'min_bars': 12,
        'recommended_bars': 60,
    }
}

# 默认K线级别
DEFAULT_KLINE_LEVEL = '1d'

# K线级别分组
KLINE_GROUPS = {
    'intraday': ['15m', '30m', '1h'],           # 日内级别
    'daily': ['1d'],                            # 日线级别  
    'weekly_monthly': ['1wk', '1mo'],           # 周月级别
    'short_term': ['15m', '30m', '1h', '1d'],   # 短期分析
    'long_term': ['1d', '1wk', '1mo'],          # 长期分析
}

# 级别优先级 (数字越小优先级越高)
KLINE_PRIORITY = {
    '15m': 1,
    '30m': 2, 
    '1h': 3,
    '1d': 4,
    '1wk': 5,
    '1mo': 6,
}

def get_kline_config(level: str) -> dict:
    """
    获取K线级别配置
    
    Args:
        level: K线级别代码
        
    Returns:
        dict: K线级别配置字典
        
    Raises:
        ValueError: 不支持的K线级别
    """
    if level not in KLINE_LEVELS:
        raise ValueError(f"不支持的K线级别: {level}，支持的级别: {list(KLINE_LEVELS.keys())}")
    
    return KLINE_LEVELS[level].copy()

def get_supported_levels() -> list:
    """获取支持的K线级别列表"""
    return list(KLINE_LEVELS.keys())

def get_level_name(level: str) -> str:
    """获取K线级别中文名称"""
    config = get_kline_config(level)
    return config['name']

def get_level_description(level: str) -> str:
    """获取K线级别描述"""
    config = get_kline_config(level)
    return config['description']

def is_intraday_level(level: str) -> bool:
    """判断是否为日内级别"""
    return level in KLINE_GROUPS['intraday']

def is_daily_level(level: str) -> bool:
    """判断是否为日线级别"""
    return level in KLINE_GROUPS['daily']

def is_weekly_monthly_level(level: str) -> bool:
    """判断是否为周月级别"""
    return level in KLINE_GROUPS['weekly_monthly']

def get_recommended_bars(level: str) -> int:
    """获取推荐的K线数量"""
    config = get_kline_config(level)
    return config['recommended_bars']

def get_min_bars(level: str) -> int:
    """获取最少的K线数量"""
    config = get_kline_config(level)
    return config['min_bars']

def validate_kline_level(level: str) -> bool:
    """验证K线级别是否有效"""
    return level in KLINE_LEVELS

def get_level_priority(level: str) -> int:
    """获取K线级别优先级"""
    return KLINE_PRIORITY.get(level, 999)
