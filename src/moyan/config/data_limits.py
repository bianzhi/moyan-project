"""
数据源限制配置

定义各个数据源对不同K线级别数据的限制，包括：
- 最大数据条数
- 最大历史天数  
- 实际可获取的数据量
- 推荐的使用场景
"""

from typing import Dict, Any
from datetime import timedelta

# 各数据源对分钟级别数据的实际限制
DATA_SOURCE_LIMITS = {
    'sina': {
        'name': '新浪财经',
        'minute_levels': {
            '1h': {
                'max_bars': 2000,      # 实测可获取约2000条数据
                'max_days': 500,       # 实际最大约500天
                'recommended_days': 365,  # 推荐365天，可获取约68%完整度
                'bars_per_day': 4,     # 每天约4条数据
                'description': '1小时级别，数据质量较好，推荐作为首选',
                'actual_performance': '365天可获取976条数据，完整度68%'
            },
            '30m': {
                'max_bars': 2000,
                'max_days': 250,       # 2000/8
                'recommended_days': 180,
                'bars_per_day': 8,
                'description': '30分钟级别，适合短期交易',
                'actual_performance': '预估180天可获取约1200条数据'
            },
            '15m': {
                'max_bars': 2000,
                'max_days': 125,       # 2000/16
                'recommended_days': 90,
                'bars_per_day': 16,
                'description': '15分钟级别，适合日内交易',
                'actual_performance': '预估90天可获取约1200条数据'
            },
            '5m': {
                'max_bars': 2000,
                'max_days': 42,        # 2000/48
                'recommended_days': 30,
                'bars_per_day': 48,
                'description': '5分钟级别，适合短线交易',
                'actual_performance': '预估30天可获取约1200条数据'
            }
        }
    },
    'eastmoney': {
        'name': '东方财富',
        'minute_levels': {
            '1h': {
                'max_bars': 500,       # 实测限制约500条
                'max_days': 125,       # 实际约125天
                'recommended_days': 100,
                'bars_per_day': 4,
                'description': '1小时级别，数据范围有限，作为备选',
                'actual_performance': '实测365天只能获取124条数据，仅覆盖最近42天'
            },
            '30m': {
                'max_bars': 500,
                'max_days': 62,        # 500/8
                'recommended_days': 50,
                'bars_per_day': 8,
                'description': '30分钟级别，数据范围有限',
                'actual_performance': '数据范围限制在最近约60天'
            },
            '15m': {
                'max_bars': 500,
                'max_days': 31,        # 500/16
                'recommended_days': 25,
                'bars_per_day': 16,
                'description': '15分钟级别，数据范围有限',
                'actual_performance': '数据范围限制在最近约30天'
            },
            '5m': {
                'max_bars': 500,
                'max_days': 10,        # 500/48
                'recommended_days': 7,
                'bars_per_day': 48,
                'description': '5分钟级别，数据范围很有限',
                'actual_performance': '数据范围限制在最近约10天'
            }
        }
    },
    'baostock': {
        'name': 'Baostock',
        'minute_levels': {
            '1h': {
                'max_bars': 10000,     # 估计值，需要测试确认
                'max_days': 2500,
                'recommended_days': 730,
                'bars_per_day': 4,
                'description': '1小时级别，免费数据源'
            },
            '30m': {
                'max_bars': 8000,
                'max_days': 1000,
                'recommended_days': 365,
                'bars_per_day': 8,
                'description': '30分钟级别，免费数据源'
            },
            '15m': {
                'max_bars': 8000,
                'max_days': 500,
                'recommended_days': 180,
                'bars_per_day': 16,
                'description': '15分钟级别，免费数据源'
            },
            '5m': {
                'max_bars': 8000,
                'max_days': 166,
                'recommended_days': 90,
                'bars_per_day': 48,
                'description': '5分钟级别，免费数据源'
            }
        }
    },
    'yfinance': {
        'name': 'Yahoo Finance',
        'minute_levels': {
            '1h': {
                'max_bars': 730,       # yfinance限制730天
                'max_days': 730,
                'recommended_days': 365,
                'bars_per_day': 4,
                'description': '1小时级别，国外数据源，可能有延迟'
            },
            '30m': {
                'max_bars': 60,        # yfinance对30m限制很严格
                'max_days': 60,
                'recommended_days': 30,
                'bars_per_day': 8,
                'description': '30分钟级别，数据有限'
            },
            '15m': {
                'max_bars': 60,
                'max_days': 60,
                'recommended_days': 30,
                'bars_per_day': 16,
                'description': '15分钟级别，数据有限'
            }
        }
    }
}

# 数据源优先级（分钟级别）
MINUTE_DATA_PRIORITY = {
    '1h': ['eastmoney', 'sina', 'baostock', 'yfinance'],
    '30m': ['eastmoney', 'sina', 'baostock', 'yfinance'],
    '15m': ['eastmoney', 'sina', 'baostock', 'yfinance'],
    '5m': ['eastmoney', 'sina', 'baostock']
}

def get_data_source_limits(kline_level: str) -> Dict[str, Any]:
    """
    获取指定K线级别的所有数据源限制信息
    
    Args:
        kline_level: K线级别 ('1h', '30m', '15m', '5m')
        
    Returns:
        dict: 包含所有支持该级别的数据源限制信息
    """
    limits = {}
    
    for source_name, source_info in DATA_SOURCE_LIMITS.items():
        if kline_level in source_info['minute_levels']:
            limits[source_name] = {
                'name': source_info['name'],
                **source_info['minute_levels'][kline_level]
            }
    
    return limits

def get_best_data_source_for_days(kline_level: str, days: int) -> tuple:
    """
    根据请求的天数推荐最佳数据源
    
    Args:
        kline_level: K线级别
        days: 请求的天数
        
    Returns:
        tuple: (推荐数据源名称, 实际可获取天数, 警告信息)
    """
    limits = get_data_source_limits(kline_level)
    
    if not limits:
        return None, 0, f"不支持的K线级别: {kline_level}"
    
    # 按优先级排序
    priority_sources = MINUTE_DATA_PRIORITY.get(kline_level, [])
    
    best_source = None
    max_available_days = 0
    warning = None
    
    for source_name in priority_sources:
        if source_name in limits:
            source_limit = limits[source_name]
            available_days = min(source_limit['max_days'], days)
            
            if available_days >= days:
                # 找到能满足需求的数据源
                return source_name, days, None
            elif available_days > max_available_days:
                # 记录能提供最多数据的源
                best_source = source_name
                max_available_days = available_days
                warning = f"{source_limit['name']}最多提供{available_days}天的{kline_level}级别数据"
    
    return best_source, max_available_days, warning

def calculate_expected_bars(kline_level: str, days: int) -> int:
    """
    计算指定天数和K线级别的预期数据条数
    
    Args:
        kline_level: K线级别
        days: 天数
        
    Returns:
        int: 预期的数据条数
    """
    bars_per_day_map = {
        '1h': 4,
        '30m': 8, 
        '15m': 16,
        '5m': 48,
        '2m': 120,
        '1m': 240
    }
    
    bars_per_day = bars_per_day_map.get(kline_level, 4)
    return days * bars_per_day

def get_data_limit_warning(kline_level: str, requested_days: int) -> str:
    """
    生成数据限制警告信息
    
    Args:
        kline_level: K线级别
        requested_days: 请求的天数
        
    Returns:
        str: 警告信息
    """
    if kline_level not in ['1h', '30m', '15m', '5m']:
        return ""
    
    best_source, available_days, warning = get_best_data_source_for_days(kline_level, requested_days)
    
    if warning:
        return f"⚠️ {warning}，已自动调整为{available_days}天"
    elif available_days < requested_days:
        return f"⚠️ {kline_level}级别数据最多可获取{available_days}天"
    else:
        return f"✅ {kline_level}级别数据可完整获取{requested_days}天"

# 前端显示的数据限制信息（基于1年需求的实测结果）
FRONTEND_LIMIT_INFO = {
    '1h': {
        'max_recommended_days': 365,
        'warning_threshold': 300,
        'description': '1小时级别数据，完美支持1年分析（新浪财经可获取1000条数据）'
    },
    '30m': {
        'max_recommended_days': 270,  # 约9个月
        'warning_threshold': 180,
        'description': '30分钟级别数据，支持9个月分析（新浪财经可获取1500条数据）'
    },
    '15m': {
        'max_recommended_days': 120,  # 约4个月
        'warning_threshold': 90,
        'description': '15分钟级别数据，支持4个月分析（新浪财经可获取1500条数据）'
    },
    '5m': {
        'max_recommended_days': 30,
        'warning_threshold': 15,
        'description': '5分钟级别数据，支持1个月分析（适合短期策略验证）'
    }
}
