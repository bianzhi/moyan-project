# src/moyan/utils/test_data.py
"""
测试数据生成器
用于在API限流时提供示例数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

def generate_test_stock_data(stock_code: str = "000001", days: int = 100) -> pd.DataFrame:
    """
    生成测试股票数据
    
    Args:
        stock_code: 股票代码
        days: 天数
        
    Returns:
        pd.DataFrame: 股票数据
    """
    # 生成日期序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 过滤工作日（简化处理）
    dates = dates[:days]
    
    # 生成基础价格走势
    np.random.seed(42)  # 固定随机种子，确保结果一致
    
    # 初始价格
    base_price = 10.0 if stock_code.startswith('00') else 15.0
    
    # 生成价格走势（随机游走 + 趋势）
    returns = np.random.normal(0.001, 0.02, len(dates))  # 日收益率
    
    # 添加一些趋势和周期性
    trend = np.linspace(0, 0.1, len(dates))  # 轻微上升趋势
    cycle = 0.05 * np.sin(np.linspace(0, 4*np.pi, len(dates)))  # 周期性波动
    
    returns = returns + trend/len(dates) + cycle/len(dates)
    
    # 计算价格序列
    prices = [base_price]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    # 生成OHLC数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成当日波动
        volatility = close * 0.02  # 2%的日内波动
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        
        # 确保开盘价在合理范围内
        if i == 0:
            open_price = close + np.random.uniform(-volatility/2, volatility/2)
        else:
            # 开盘价接近前一日收盘价
            prev_close = data[-1]['close']
            gap = np.random.uniform(-0.005, 0.005) * prev_close
            open_price = prev_close + gap
        
        # 确保价格逻辑正确
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # 生成成交量（基于价格变化）
        price_change = abs(close - open_price) / open_price
        base_volume = 1000000
        volume = int(base_volume * (1 + price_change * 5) * np.random.uniform(0.5, 2.0))
        
        data.append({
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data, index=dates)
    return df

def create_test_analysis_result(stock_code: str = "000001", 
                              stock_name: str = "测试股票") -> Dict[str, Any]:
    """
    创建测试分析结果
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        
    Returns:
        dict: 分析结果
    """
    # 生成测试数据
    df = generate_test_stock_data(stock_code, 100)
    
    # 创建基本分析结果结构
    result = {
        'stock_code': stock_code,
        'kline_level': '1d',
        'kline_name': '日线',
        'analysis_time': datetime.now().isoformat(),
        'success': True,
        'error': None,
        'data': {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'raw_df': df,
            'total_bars': len(df),
            'fx_count': 15,  # 模拟分型数量
            'bi_count': 8,   # 模拟笔数量
            'xd_count': 3,   # 模拟线段数量
            'data_start': df.index[0].strftime('%Y-%m-%d'),
            'data_end': df.index[-1].strftime('%Y-%m-%d'),
            
            # 模拟缠论要素
            'fractals': {
                'total_count': 15,
                'top_fractals': [
                    {'date': df.index[i], 'price': df.iloc[i]['high'] * 1.01}
                    for i in range(10, len(df), 8)
                ][:8],
                'bottom_fractals': [
                    {'date': df.index[i], 'price': df.iloc[i]['low'] * 0.99}
                    for i in range(5, len(df), 8)
                ][:7]
            },
            
            'strokes': {
                'total_count': 8,
                'up_strokes': 4,
                'down_strokes': 4,
                'avg_length': 12.5
            },
            
            'segments': {
                'total_count': 3,
                'avg_length': 25.0
            },
            
            'buy_points': [
                {
                    'date': df.index[i],
                    'price': df.iloc[i]['low'] * 0.98,
                    'type': f'第{(i%3)+1}类买点'
                }
                for i in range(20, len(df), 15)
            ][:5],
            
            'sell_points': [
                {
                    'date': df.index[i],
                    'price': df.iloc[i]['high'] * 1.02,
                    'type': f'第{(i%3)+1}类卖点'
                }
                for i in range(15, len(df), 15)
            ][:5],
            
            'divergences': [
                {
                    'date': df.index[i],
                    'type': '顶背驰' if i % 2 == 0 else '底背驰',
                    'strength': np.random.uniform(0.6, 0.9)
                }
                for i in range(30, len(df), 20)
            ][:3],
            
            'current_state': {
                'price': df.iloc[-1]['close'],
                'trend': '震荡',
                'fractal_state': '已形成底分型',
                'risk_level': '中等'
            }
        },
        'charts': {
            'main_chart': 'test_chart.png'
        },
        'reports': {
            'summary': 'test_report.md'
        }
    }
    
    return result

if __name__ == '__main__':
    # 测试数据生成
    print("生成测试数据...")
    df = generate_test_stock_data("000001", 50)
    print(f"生成了 {len(df)} 天的数据")
    print(f"价格范围: {df['low'].min():.2f} - {df['high'].max():.2f}")
    
    # 测试分析结果
    result = create_test_analysis_result("000001", "平安银行")
    print(f"\\n分析结果包含字段: {list(result.keys())}")
    print(f"数据字段: {list(result['data'].keys())}")
