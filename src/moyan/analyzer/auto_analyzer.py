#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缠论自动分析系统
用户只需输入6位股票代码，自动进行全面的缠论技术分析
包含：分型、笔、线段、背驰、买卖点等核心概念
输出：详细分析报告 + 可视化图表

作者：CZSC自动分析系统
创建时间：2025-09-28
"""

import yfinance as yf
import czsc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# 导入配置
from ..config.kline_config import KLINE_LEVELS, DEFAULT_KLINE_LEVEL, get_kline_config
from ..config.settings import default_config

class AutoAnalyzer:
    """缠论自动分析器"""
    
    def __init__(self, kline_level=None, output_base_dir="./output"):
        """
        初始化分析器
        
        Args:
            kline_level (str): K线级别，可选值: '15m', '30m', '1d', '1wk'
            output_base_dir (str): 输出文件基础目录，默认 './output'
        """
        self.stock_code = None
        self.symbol = None
        self.stock_name = None
        self.df = None
        self.bars = []
        self.c = None
        self.analysis_result = {}
        
        # 文件路径记录
        self.last_chart_path = None
        self.last_report_path = None
        
        # Web数据缓存
        self.web_data = {
            'raw_df': None,
            'processed_bars': None,
            'fx_list': None,
            'bi_list': None,
            'xd_list': None
        }
        
        # 设置输出目录
        self.output_base_dir = output_base_dir
        self.charts_dir = os.path.join(output_base_dir, "charts")
        self.reports_dir = os.path.join(output_base_dir, "reports")
        
        # 设置K线级别
        self.kline_level = kline_level or DEFAULT_KLINE_LEVEL
        if self.kline_level not in KLINE_LEVELS:
            print(f"⚠️ 不支持的K线级别: {self.kline_level}，使用默认级别: {DEFAULT_KLINE_LEVEL}")
            self.kline_level = DEFAULT_KLINE_LEVEL
        
        self.kline_config = KLINE_LEVELS[self.kline_level]
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def _ensure_output_dirs(self):
        """确保输出目录存在"""
        os.makedirs(self.charts_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _generate_timestamp(self):
        """生成时间戳字符串"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def _get_chart_filename(self):
        """生成图表文件名（带时间戳）"""
        timestamp = self._generate_timestamp()
        kline_suffix = self.kline_level if self.kline_level != '1d' else 'daily'
        filename = f"{self.stock_code}_{kline_suffix}_czsc_analysis_{timestamp}.png"
        return os.path.join(self.charts_dir, filename)
    
    def _get_report_filename(self):
        """生成报告文件名（带时间戳）"""
        timestamp = self._generate_timestamp()
        kline_suffix = self.kline_level if self.kline_level != '1d' else 'daily'
        filename = f"{self.stock_code}_{kline_suffix}_czsc_report_{timestamp}.md"
        return os.path.join(self.reports_dir, filename)
        
    def get_stock_data(self, stock_code, start_date=None, end_date=None, days=None):
        """
        获取股票数据
        
        Args:
            stock_code (str): 6位股票代码
            start_date (str): 开始日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认根据K线级别设置
            end_date (str): 结束日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当前日期
            days (int): 获取天数，当start_date和end_date都未指定时使用，默认根据K线级别设置
        """
        self.stock_code = stock_code
        
        # 判断股票市场并构造symbol
        if stock_code.startswith('6'):
            self.symbol = f"{stock_code}.SS"  # 上交所
        elif stock_code.startswith(('0', '3')):
            self.symbol = f"{stock_code}.SZ"  # 深交所
        else:
            raise ValueError(f"不支持的股票代码格式: {stock_code}")
        
        print(f"📊 正在获取股票 {stock_code} 的数据...")
        print(f"📈 K线级别: {self.kline_config['name']} ({self.kline_level})")
        
        # 处理日期参数，根据K线级别设置默认值
        if start_date is None and end_date is None and days is None:
            # 使用K线级别的默认天数
            days = self.kline_config['default_days']
            
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
                days = self.kline_config['default_days']
                start_dt = datetime.now() - timedelta(days=days)
                start_date = start_dt.strftime('%Y%m%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
        
        # 标准化日期格式
        def format_date(date_str):
            if len(date_str) == 8:  # YYYYMMDD
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return date_str  # 已经是 YYYY-MM-DD 格式
        
        start_date_formatted = format_date(start_date)
        end_date_formatted = format_date(end_date)
        
        print(f"📅 时间区间: {start_date_formatted} 至 {end_date_formatted}")
        
        try:
            # 使用新的多数据源系统获取股票数据
            from moyan.core.enhanced_data_source import get_data_source_manager
            
            print("🔄 使用多数据源系统获取数据...")
            data_manager = get_data_source_manager()
            
            # 获取数据
            data, source_name = data_manager.get_stock_data(
                stock_code=stock_code,
                start_date=start_date_formatted,
                end_date=end_date_formatted
            )
            
            if data is not None and len(data) > 0:
                self.df = data
                print(f"✅ 使用 {source_name} 数据源成功获取 {len(data)} 条数据")
                
                # 获取股票基本信息，优先使用本地数据库
                try:
                    from moyan.config.stock_database import get_stock_info
                    stock_info = get_stock_info(stock_code)
                    if stock_info:
                        self.stock_name = stock_info['name']
                    else:
                        # 直接使用股票代码，不再访问yfinance获取名称
                        self.stock_name = f'股票{stock_code}'
                except ImportError:
                    # 没有本地数据库，直接使用股票代码
                    self.stock_name = f'股票{stock_code}'
                
                print(f"✅ 成功获取 {len(self.df)} 条{self.kline_config['name']}数据")
                print(f"📈 股票名称: {self.stock_name}")
                print(f"📅 实际数据范围: {self.df.index[0].strftime('%Y-%m-%d %H:%M' if 'm' in self.kline_level else '%Y-%m-%d')} 至 {self.df.index[-1].strftime('%Y-%m-%d %H:%M' if 'm' in self.kline_level else '%Y-%m-%d')}")
                
                return True
            else:
                raise ValueError("多数据源系统未获取到数据")
                
        except Exception as e:
            print(f"⚠️ 多数据源获取失败，回退到yfinance: {e}")
            
            # 回退到原有的yfinance方式
            ticker = yf.Ticker(self.symbol)
            interval = self.kline_config['yfinance_interval']
            
            self.df = ticker.history(
                start=start_date_formatted, 
                end=end_date_formatted,
                interval=interval
            )
            
            if len(self.df) == 0:
                raise ValueError("未获取到数据")
            
            # 获取股票基本信息，优先使用本地数据库
            try:
                from moyan.config.stock_database import get_stock_info
                stock_info = get_stock_info(stock_code)
                if stock_info:
                    self.stock_name = stock_info['name']
                else:
                    # 直接使用股票代码，不再访问yfinance获取名称
                    self.stock_name = f'股票{stock_code}'
            except ImportError:
                # 没有本地数据库，直接使用股票代码
                self.stock_name = f'股票{stock_code}'
            
            print(f"✅ 成功获取 {len(self.df)} 条{self.kline_config['name']}数据")
            print(f"📈 股票名称: {self.stock_name}")
            print(f"📅 实际数据范围: {self.df.index[0].strftime('%Y-%m-%d %H:%M' if 'm' in self.kline_level else '%Y-%m-%d')} 至 {self.df.index[-1].strftime('%Y-%m-%d %H:%M' if 'm' in self.kline_level else '%Y-%m-%d')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return False
    
    def convert_to_czsc_format(self):
        """转换为CZSC格式"""
        print("🔄 转换数据格式...")
        
        self.bars = []
        for i, (date, row) in enumerate(self.df.iterrows()):
            bar = czsc.RawBar(
                symbol=self.symbol,
                id=i,
                freq=czsc.Freq.D,
                dt=pd.to_datetime(date),
                open=row['Open'],
                close=row['Close'],
                high=row['High'],
                low=row['Low'],
                vol=int(row['Volume']),
                amount=int(row['Volume'] * row['Close'])
            )
            self.bars.append(bar)
        
        print(f"✅ 数据格式转换完成: {len(self.bars)} 根K线")
    
    def czsc_analysis(self):
        """进行CZSC缠论分析"""
        print("🧮 开始缠论分析...")
        
        try:
            # 创建CZSC对象
            self.c = czsc.CZSC(self.bars)
            
            print(f"✅ 缠论分析完成")
            print(f"  📈 原始K线: {len(self.c.bars_raw)} 根")
            print(f"  🔄 处理后K线: {len(self.c.bars_ubi)} 根")
            print(f"  🔺 识别分型: {len(self.c.fx_list)} 个")
            print(f"  📏 构建笔: {len(self.c.bi_list)} 笔")
            
            # 调试：检查CZSC是否提供线段数据
            if hasattr(self.c, 'xd_list'):
                print(f"  📐 CZSC线段数量: {len(self.c.xd_list)}")
            else:
                print("  ⚠️ CZSC未提供线段数据，将使用备用算法")
            
            # 打印CZSC对象的关键属性，用于调试
            attrs = [attr for attr in dir(self.c) if not attr.startswith('_') and 'list' in attr]
            print(f"  🔍 CZSC可用列表: {', '.join(attrs)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 缠论分析失败: {e}")
            return False
    
    def analyze_fractals(self):
        """分析分型"""
        print("🔍 分析分型...")
        
        top_fx = [fx for fx in self.c.fx_list if fx.mark.value == '顶分型']
        bottom_fx = [fx for fx in self.c.fx_list if fx.mark.value == '底分型']
        
        fractal_analysis = {
            'total_count': len(self.c.fx_list),
            'top_count': len(top_fx),
            'bottom_count': len(bottom_fx),
            'top_fractals': top_fx,  # 保留所有顶分型
            'bottom_fractals': bottom_fx,  # 保留所有底分型
            'latest_fractal': self.c.fx_list[-1] if self.c.fx_list else None
        }
        
        self.analysis_result['fractals'] = fractal_analysis
        print(f"  🔴 顶分型: {len(top_fx)} 个")
        print(f"  🟢 底分型: {len(bottom_fx)} 个")
    
    def analyze_strokes(self):
        """分析笔"""
        print("🔍 分析笔...")
        
        up_strokes = [bi for bi in self.c.bi_list if bi.direction.value == '向上']
        down_strokes = [bi for bi in self.c.bi_list if bi.direction.value == '向下']
        
        # 计算笔的统计信息
        up_changes = []
        down_changes = []
        
        if up_strokes:
            up_changes = [((bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx) * 100 for bi in up_strokes]
        
        if down_strokes:
            down_changes = [((bi.fx_a.fx - bi.fx_b.fx) / bi.fx_a.fx) * 100 for bi in down_strokes]
        
        stroke_analysis = {
            'total_count': len(self.c.bi_list),
            'up_count': len(up_strokes),
            'down_count': len(down_strokes),
            'up_strokes': up_strokes,
            'down_strokes': down_strokes,
            'up_avg_change': np.mean(up_changes) if up_changes else 0,
            'up_max_change': max(up_changes) if up_changes else 0,
            'down_avg_change': np.mean(down_changes) if down_changes else 0,
            'down_max_change': max(down_changes) if down_changes else 0,
            'latest_stroke': self.c.bi_list[-1] if self.c.bi_list else None
        }
        
        self.analysis_result['strokes'] = stroke_analysis
        print(f"  📈 向上笔: {len(up_strokes)} 笔，平均涨幅 {stroke_analysis['up_avg_change']:.2f}%")
        print(f"  📉 向下笔: {len(down_strokes)} 笔，平均跌幅 {stroke_analysis['down_avg_change']:.2f}%")
    
    def analyze_segments(self):
        """分析线段（使用CZSC内置线段）"""
        print("🔍 分析线段...")
        
        # 使用CZSC内置的线段识别结果
        xd_list = getattr(self.c, 'xd_list', [])
        
        # 如果CZSC没有线段数据，使用简化算法作为备用
        if not xd_list and len(self.c.bi_list) >= 3:
            print("⚠️ CZSC未生成线段数据，使用备用算法...")
            # 备用：基于笔方向变化识别线段（简化版）
            segments = []
            current_segment = [self.c.bi_list[0]]
            
            for i in range(1, len(self.c.bi_list)):
                current_bi = self.c.bi_list[i]
                prev_bi = current_segment[-1]
                
                # 检查是否构成新线段的开始
                # 线段结束条件：至少3笔 + 方向变化
                if (len(current_segment) >= 3 and 
                    current_bi.direction != prev_bi.direction):
                    segments.append(current_segment.copy())
                    current_segment = [current_bi]
                else:
                    current_segment.append(current_bi)
            
            # 添加最后一个线段
            if len(current_segment) >= 3:
                segments.append(current_segment)
                
            xd_list = segments  # 使用备用结果
        
        segment_analysis = {
            'total_count': len(xd_list),
            'segments': xd_list,
            'avg_length': np.mean([len(seg) for seg in xd_list]) if xd_list else 0,
            'xd_raw': xd_list  # 保存原始CZSC线段数据
        }
        
        self.analysis_result['segments'] = segment_analysis
        print(f"  📏 识别线段: {len(xd_list)} 个")
        print(f"  📊 线段平均长度: {segment_analysis['avg_length']:.1f} 笔")
    
    def analyze_divergence(self):
        """分析背驰"""
        print("🔍 分析背驰...")
        
        divergences = []
        
        # 简化的背驰识别：比较相邻同向笔的力度
        if len(self.c.bi_list) >= 4:
            for i in range(2, len(self.c.bi_list)):
                current_bi = self.c.bi_list[i]
                prev_same_direction = None
                
                # 找到前一个同方向的笔
                for j in range(i-1, -1, -1):
                    if self.c.bi_list[j].direction == current_bi.direction:
                        prev_same_direction = self.c.bi_list[j]
                        break
                
                if prev_same_direction:
                    # 计算笔的幅度
                    if current_bi.direction.value == '向上':
                        current_change = (current_bi.fx_b.fx - current_bi.fx_a.fx) / current_bi.fx_a.fx
                        prev_change = (prev_same_direction.fx_b.fx - prev_same_direction.fx_a.fx) / prev_same_direction.fx_a.fx
                    else:
                        current_change = (current_bi.fx_a.fx - current_bi.fx_b.fx) / current_bi.fx_a.fx
                        prev_change = (prev_same_direction.fx_a.fx - prev_same_direction.fx_b.fx) / prev_same_direction.fx_a.fx
                    
                    # 判断背驰（当前笔幅度明显小于前一笔）
                    if current_change < prev_change * 0.7:  # 阈值可调整
                        divergence_type = "顶背驰" if current_bi.direction.value == '向上' else "底背驰"
                        divergences.append({
                            'type': divergence_type,
                            'current_bi': current_bi,
                            'prev_bi': prev_same_direction,
                            'current_change': current_change * 100,
                            'prev_change': prev_change * 100,
                            'strength': (prev_change - current_change) / prev_change * 100
                        })
        
        self.analysis_result['divergences'] = divergences
        print(f"  ⚠️ 识别背驰: {len(divergences)} 个")
    
    def analyze_buy_sell_points(self):
        """分析买卖点"""
        print("🔍 分析买卖点...")
        
        buy_points = []
        sell_points = []
        
        # 基于分型和背驰识别买卖点
        for i, fx in enumerate(self.c.fx_list):
            if fx.mark.value == '底分型':
                # 第一类买点：底分型
                buy_type = "第一类买点"
                
                # 检查是否有背驰确认
                for div in self.analysis_result.get('divergences', []):
                    if (div['type'] == '底背驰' and 
                        abs((fx.dt - div['current_bi'].fx_b.dt).days) <= 5):
                        buy_type = "第二类买点"
                        break
                
                buy_points.append({
                    'type': buy_type,
                    'date': fx.dt,
                    'price': fx.fx,
                    'fractal': fx
                })
            
            elif fx.mark.value == '顶分型':
                # 第一类卖点：顶分型
                sell_type = "第一类卖点"
                
                # 检查是否有背驰确认
                for div in self.analysis_result.get('divergences', []):
                    if (div['type'] == '顶背驰' and 
                        abs((fx.dt - div['current_bi'].fx_b.dt).days) <= 5):
                        sell_type = "第二类卖点"
                        break
                
                sell_points.append({
                    'type': sell_type,
                    'date': fx.dt,
                    'price': fx.fx,
                    'fractal': fx
                })
        
        # 第三类买卖点：基于线段的突破
        segments = self.analysis_result.get('segments', {}).get('segments', [])
        if len(segments) >= 2:
            latest_segment = segments[-1]
            if len(latest_segment) >= 2:
                if latest_segment[0].direction.value == '向上':
                    # 向上线段突破前高可能是第三类买点
                    buy_points.append({
                        'type': "第三类买点",
                        'date': latest_segment[-1].fx_b.dt,
                        'price': latest_segment[-1].fx_b.fx,
                        'fractal': None
                    })
                else:
                    # 向下线段跌破前低可能是第三类卖点
                    sell_points.append({
                        'type': "第三类卖点",
                        'date': latest_segment[-1].fx_b.dt,
                        'price': latest_segment[-1].fx_b.fx,
                        'fractal': None
                    })
        
        # 保留所有买卖点，不只是最近10个
        self.analysis_result['buy_points'] = buy_points
        self.analysis_result['sell_points'] = sell_points
        
        print(f"  🟢 买点: {len(buy_points)} 个")
        print(f"  🔴 卖点: {len(sell_points)} 个")
    
    def analyze_current_status(self):
        """分析当前状态"""
        print("🔍 分析当前状态...")
        
        current_price = self.bars[-1].close
        latest_fx = self.analysis_result['fractals']['latest_fractal']
        latest_stroke = self.analysis_result['strokes']['latest_stroke']
        
        # 计算距离最新分型的位置
        fx_distance = 0
        fx_status = "未知"
        if latest_fx:
            fx_distance = ((current_price - latest_fx.fx) / latest_fx.fx) * 100
            if latest_fx.mark.value == '顶分型':
                fx_status = "已跌破顶分型" if current_price < latest_fx.fx else "仍在顶分型上方"
            else:
                fx_status = "已突破底分型" if current_price > latest_fx.fx else "仍在底分型下方"
        
        # 趋势判断
        recent_strokes = self.c.bi_list[-3:] if len(self.c.bi_list) >= 3 else self.c.bi_list
        up_count = len([bi for bi in recent_strokes if bi.direction.value == '向上'])
        down_count = len([bi for bi in recent_strokes if bi.direction.value == '向下'])
        
        if up_count > down_count:
            trend_status = "多头趋势"
        elif down_count > up_count:
            trend_status = "空头趋势"
        else:
            trend_status = "震荡格局"
        
        current_status = {
            'current_price': current_price,
            'fx_distance': fx_distance,
            'fx_status': fx_status,
            'trend_status': trend_status,
            'latest_fx': latest_fx,
            'latest_stroke': latest_stroke
        }
        
        self.analysis_result['current_status'] = current_status
        print(f"  💰 当前价格: {current_price:.2f}")
        print(f"  📊 趋势状态: {trend_status}")
        print(f"  🎯 分型状态: {fx_status}")
    
    def prepare_analysis_result(self):
        """准备分析结果，确保包含所有必要字段"""
        # 添加基本信息到分析结果
        # 获取正确的线段数量
        xd_count = 0
        if hasattr(self.c, 'xd_list') and self.c.xd_list:
            xd_count = len(self.c.xd_list)
        else:
            xd_count = self.analysis_result.get('segments', {}).get('total_count', 0)
        
        self.analysis_result.update({
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'data_start': self.df.index[0].strftime('%Y-%m-%d') if len(self.df) > 0 else '',
            'data_end': self.df.index[-1].strftime('%Y-%m-%d') if len(self.df) > 0 else '',
            'total_bars': len(self.bars),
            'fx_count': len(self.c.fx_list) if self.c else 0,
            'bi_count': len(self.c.bi_list) if self.c else 0,
            'xd_count': xd_count,
            'raw_df': self.df,
        })
    def _draw_pivot_zones(self, ax):
        """绘制中枢区域"""
        if len(self.c.bi_list) < 3:
            return
        
        # 简化的中枢识别：寻找价格重叠区域
        pivot_zones = []
        for i in range(len(self.c.bi_list) - 2):
            bi1 = self.c.bi_list[i]
            bi2 = self.c.bi_list[i + 1]
            bi3 = self.c.bi_list[i + 2]
            
            # 获取三笔的价格范围
            prices = [bi1.fx_a.fx, bi1.fx_b.fx, bi2.fx_a.fx, bi2.fx_b.fx, bi3.fx_a.fx, bi3.fx_b.fx]
            min_price = min(prices)
            max_price = max(prices)
            
            # 检查是否有重叠（简化判断）
            if max_price - min_price < (max_price + min_price) * 0.1:  # 重叠度阈值
                pivot_zones.append({
                    'start_time': bi1.fx_a.dt,
                    'end_time': bi3.fx_b.dt,
                    'high': max_price,
                    'low': min_price
                })
        
        # 绘制中枢区域
        for i, zone in enumerate(pivot_zones):
            ax.fill_between([zone['start_time'], zone['end_time']], 
                           zone['low'], zone['high'], 
                           alpha=0.2, color='purple', 
                           label='中枢区域' if i == 0 else "")
    
    def _draw_divergence_points(self, ax):
        """绘制背驰点"""
        divergences = self.analysis_result.get('divergences', [])
        
        for i, div in enumerate(divergences):
            # 背驰点用特殊标记
            if div['type'] == '顶背驰':
                ax.scatter(div['current_bi'].fx_b.dt, div['current_bi'].fx_b.fx, 
                          marker='X', s=200, color='red', alpha=0.8, zorder=6,
                          edgecolors='darkred', linewidth=2,
                          label='顶背驰' if i == 0 else "")
            else:
                ax.scatter(div['current_bi'].fx_b.dt, div['current_bi'].fx_b.fx, 
                          marker='X', s=200, color='green', alpha=0.8, zorder=6,
                          edgecolors='darkgreen', linewidth=2,
                          label='底背驰' if i == 0 else "")
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        import pandas as pd
        
        # 转换为pandas Series
        price_series = pd.Series(prices)
        
        # 计算EMA
        ema_fast = price_series.ewm(span=fast).mean()
        ema_slow = price_series.ewm(span=slow).mean()
        
        # 计算MACD线
        macd_line = ema_fast - ema_slow
        
        # 计算信号线
        signal_line = macd_line.ewm(span=signal).mean()
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    def _draw_buy_sell_points(self, ax):
        """用简洁图标绘制买卖点"""
        buy_points = self.analysis_result.get('buy_points', [])
        sell_points = self.analysis_result.get('sell_points', [])
        
        # 买点用不同形状的绿色标记
        buy_markers = {'第一类买点': 'o', '第二类买点': 's', '第三类买点': 'D'}
        sell_markers = {'第一类卖点': 'o', '第二类卖点': 's', '第三类卖点': 'D'}
        
        for i, bp in enumerate(buy_points):
            marker = buy_markers.get(bp['type'], 'o')
            ax.scatter(bp['date'], bp['price'], marker=marker, s=150, 
                      color='lime', alpha=0.9, zorder=7,
                      edgecolors='darkgreen', linewidth=2,
                      label=bp['type'] if i == 0 or bp['type'] not in [b['type'] for b in buy_points[:i]] else "")
        
        # 卖点用不同形状的红色标记
        for i, sp in enumerate(sell_points):
            marker = sell_markers.get(sp['type'], 'o')
            ax.scatter(sp['date'], sp['price'], marker=marker, s=150, 
                      color='red', alpha=0.9, zorder=7,
                      edgecolors='darkred', linewidth=2,
                      label=sp['type'] if i == 0 or sp['type'] not in [s['type'] for s in sell_points[:i]] else "")
    
    def generate_visualization(self):
        """生成可视化图表"""
        print("🎨 生成可视化图表...")
        
        # Mac高DPI显示器优化设置
        plt.rcParams['figure.dpi'] = 200  # 高DPI显示
        plt.rcParams['savefig.dpi'] = 300  # 保存高质量
        plt.rcParams['font.size'] = 10     # 适合高DPI的字体大小
        plt.rcParams['axes.linewidth'] = 1.2  # 稍粗的坐标轴线
        plt.rcParams['lines.linewidth'] = 1.5  # 稍粗的线条
        
        # 创建图表 - Mac高分辨率显示器优化 + MACD指标
        # 针对Mac 300DPI显示器，使用更高DPI以获得细腻效果
        fig = plt.figure(figsize=(16, 14), dpi=200)  # 增加高度以容纳MACD
        gs = fig.add_gridspec(6, 3, height_ratios=[4, 1.5, 1.2, 1, 1, 1], width_ratios=[2, 1, 1])
        
        # 1. 主K线图 + 缠论分析
        ax1 = fig.add_subplot(gs[0, :])
        
        dates = [bar.dt for bar in self.bars]
        opens = [bar.open for bar in self.bars]
        highs = [bar.high for bar in self.bars]
        lows = [bar.low for bar in self.bars]
        closes = [bar.close for bar in self.bars]
        
        # 绘制K线
        for i in range(len(dates)):
            color = 'red' if closes[i] >= opens[i] else 'green'
            ax1.plot([dates[i], dates[i]], [lows[i], highs[i]], color='gray', linewidth=0.8)
            ax1.plot([dates[i], dates[i]], [opens[i], closes[i]], color=color, linewidth=3)
        
        # 绘制分型
        for fx in self.c.fx_list:
            if fx.mark.value == '顶分型':
                ax1.scatter(fx.dt, fx.fx, color='red', marker='v', s=120, zorder=5, 
                           edgecolors='darkred', linewidth=2, label='顶分型' if fx == self.c.fx_list[0] else "")
            else:
                ax1.scatter(fx.dt, fx.fx, color='green', marker='^', s=120, zorder=5,
                           edgecolors='darkgreen', linewidth=2, label='底分型' if fx == self.c.fx_list[0] else "")
        
        # 绘制笔
        for i, bi in enumerate(self.c.bi_list):
            color = 'blue' if bi.direction.value == '向上' else 'orange'
            ax1.plot([bi.fx_a.dt, bi.fx_b.dt], [bi.fx_a.fx, bi.fx_b.fx], 
                     color=color, linewidth=3, alpha=0.8,
                     label='向上笔' if i == 0 and bi.direction.value == '向上' else 
                           ('向下笔' if i == 0 and bi.direction.value == '向下' else ""))
        
        # 绘制中枢（简化版：连续3笔以上的重叠区域）
        self._draw_pivot_zones(ax1)
        
        # 标注背驰点
        self._draw_divergence_points(ax1)
        
        # 用简洁图标标注买卖点
        self._draw_buy_sell_points(ax1)
        
        ax1.set_title(f'{self.stock_code} ({self.stock_name}) 缠论技术分析图', fontsize=18, fontweight='bold')
        ax1.set_ylabel('价格 (元)', fontsize=14)
        ax1.legend(loc='upper left', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 2. 成交量图
        ax2 = fig.add_subplot(gs[1, :])
        volumes = [bar.vol for bar in self.bars]
        colors = ['red' if closes[i] >= opens[i] else 'green' for i in range(len(closes))]
        ax2.bar(dates, volumes, color=colors, alpha=0.7)
        ax2.set_ylabel('成交量', fontsize=12)
        ax2.set_title('成交量', fontsize=14)
        
        # 3. MACD指标
        ax3 = fig.add_subplot(gs[2, :])
        
        # 计算MACD
        macd_line, signal_line, histogram = self._calculate_macd(closes)
        
        # 绘制MACD线和信号线
        ax3.plot(dates, macd_line, color='blue', linewidth=1.5, label='MACD', alpha=0.8)
        ax3.plot(dates, signal_line, color='red', linewidth=1.5, label='Signal', alpha=0.8)
        
        # 绘制柱状图
        colors = ['red' if h >= 0 else 'green' for h in histogram]
        ax3.bar(dates, histogram, color=colors, alpha=0.6, width=1, label='Histogram')
        
        # 添加零轴线
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
        
        ax3.set_title('MACD指标', fontsize=14)
        ax3.set_ylabel('MACD')
        ax3.legend(loc='upper right', fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        # 4. 分型统计
        ax4 = fig.add_subplot(gs[3, 0])
        fx_data = self.analysis_result['fractals']
        fx_counts = [fx_data['top_count'], fx_data['bottom_count']]
        fx_labels = ['顶分型', '底分型']
        bars_fx = ax4.bar(fx_labels, fx_counts, color=['red', 'green'], alpha=0.8)
        ax4.set_title('分型统计', fontsize=14)
        ax4.set_ylabel('数量')
        
        for bar in bars_fx:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}', 
                     ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 5. 笔统计
        ax5 = fig.add_subplot(gs[3, 1])
        stroke_data = self.analysis_result['strokes']
        stroke_counts = [stroke_data['up_count'], stroke_data['down_count']]
        stroke_labels = ['向上笔', '向下笔']
        bars_stroke = ax4.bar(stroke_labels, stroke_counts, color=['blue', 'orange'], alpha=0.8)
        ax4.set_title('笔统计', fontsize=14)
        ax4.set_ylabel('数量')
        
        for bar in bars_stroke:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.2, f'{int(height)}', 
                     ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 5. 买卖点统计
        ax5 = fig.add_subplot(gs[3, 0])
        buy_sell_data = [len(self.analysis_result.get('buy_points', [])), 
                        len(self.analysis_result.get('sell_points', []))]
        buy_sell_labels = ['买点', '卖点']
        bars_bs = ax5.bar(buy_sell_labels, buy_sell_data, color=['green', 'red'], alpha=0.8)
        ax5.set_title('买卖点统计', fontsize=14)
        ax5.set_ylabel('数量')
        
        for bar in bars_bs:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}', 
                     ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 6. 背驰统计
        ax6 = fig.add_subplot(gs[3, 1])
        divergences = self.analysis_result.get('divergences', [])
        top_div = len([d for d in divergences if d['type'] == '顶背驰'])
        bottom_div = len([d for d in divergences if d['type'] == '底背驰'])
        div_counts = [top_div, bottom_div]
        div_labels = ['顶背驰', '底背驰']
        bars_div = ax6.bar(div_labels, div_counts, color=['red', 'green'], alpha=0.8)
        ax6.set_title('背驰统计', fontsize=14)
        ax6.set_ylabel('数量')
        
        for bar in bars_div:
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height + 0.05, f'{int(height)}', 
                     ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 7. 中枢统计
        ax7 = fig.add_subplot(gs[3, 2])
        # 计算中枢数量（简化）
        pivot_count = max(0, len(self.c.bi_list) - 2) if len(self.c.bi_list) >= 3 else 0
        ax7.bar(['中枢'], [pivot_count], color='purple', alpha=0.8)
        ax7.set_title('中枢统计', fontsize=14)
        ax7.set_ylabel('数量')
        ax7.text(0, pivot_count + 0.05, f'{pivot_count}', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 8. 图例说明
        ax8 = fig.add_subplot(gs[4, :])
        ax8.axis('off')
        ax8.set_title('缠论技术分析图例说明', fontsize=16, fontweight='bold', pad=20)
        
        # 创建图例说明
        legend_text = [
            "📊 图例说明:",
            "🔺 分型: ▲底分型(绿) ▼顶分型(红)  📏 笔: —向上笔(蓝) —向下笔(橙)",
            "🎯 买点: ●第一类 ■第二类 ♦第三类(绿色)  🎯 卖点: ●第一类 ■第二类 ♦第三类(红色)",
            "⚠️ 背驰: ✖顶背驰(红) ✖底背驰(绿)  🔄 中枢: 紫色阴影区域",
            "",
            "💡 操作提示:",
            "• 买点出现时关注，卖点出现时警惕  • 背驰信号增强买卖点可信度",
            "• 中枢区域常为整理平台  • 结合趋势和成交量综合判断"
        ]
        
        y_pos = 0.9
        for text in legend_text:
            if text.startswith('📊') or text.startswith('💡'):
                ax8.text(0.02, y_pos, text, fontsize=14, fontweight='bold', 
                        transform=ax8.transAxes)
            elif text == "":
                pass  # 空行
            else:
                ax8.text(0.05, y_pos, text, fontsize=12, 
                        transform=ax8.transAxes)
            y_pos -= 0.15
        
        plt.tight_layout()
        
        # 确保输出目录存在
        self._ensure_output_dirs()
        
        # 生成带时间戳的文件名
        chart_filename = self._get_chart_filename()
        
        # 保存图表 - Mac高DPI显示器优化设置
        plt.savefig(chart_filename, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', 
                   format='png', pil_kwargs={'optimize': True})
        plt.close()
        
        # 保存文件路径
        self.last_chart_path = chart_filename
        
        print(f"✅ 可视化图表已保存: {chart_filename}")
        return chart_filename
    
    def generate_report(self):
        """生成详细分析报告"""
        print("📄 生成分析报告...")
        
        # 确保输出目录存在
        self._ensure_output_dirs()
        
        # 生成带时间戳的文件名
        report_filename = self._get_report_filename()
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"# {self.stock_code} ({self.stock_name}) 缠论技术分析报告\n\n")
            
            # 基本信息
            f.write("## 📊 基本信息\n\n")
            f.write(f"- **股票代码**: {self.stock_code}\n")
            f.write(f"- **股票名称**: {self.stock_name}\n")
            f.write(f"- **分析日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **数据范围**: {self.df.index[0].strftime('%Y-%m-%d')} 至 {self.df.index[-1].strftime('%Y-%m-%d')}\n")
            f.write(f"- **数据量**: {len(self.bars)} 个交易日\n\n")
            
            # 当前状态
            current = self.analysis_result['current_status']
            f.write("## 💰 当前状态\n\n")
            f.write(f"- **当前价格**: {current['current_price']:.2f} 元\n")
            f.write(f"- **趋势状态**: {current['trend_status']}\n")
            f.write(f"- **分型状态**: {current['fx_status']}\n")
            if current['latest_fx']:
                f.write(f"- **最新分型**: {current['latest_fx'].mark.value} @ {current['latest_fx'].dt.strftime('%Y-%m-%d')} ({current['latest_fx'].fx:.2f}元)\n")
            f.write(f"- **距离最新分型**: {current['fx_distance']:+.2f}%\n\n")
            
            # 分型分析
            fx_data = self.analysis_result['fractals']
            f.write("## 🔺 分型分析\n\n")
            f.write(f"- **总分型数**: {fx_data['total_count']} 个\n")
            f.write(f"- **顶分型数**: {fx_data['top_count']} 个\n")
            f.write(f"- **底分型数**: {fx_data['bottom_count']} 个\n\n")
            
            f.write("### 最近分型详情\n\n")
            f.write("| 日期 | 类型 | 价格 |\n")
            f.write("|------|------|------|\n")
            recent_fx = (fx_data['top_fractals'][-5:] + fx_data['bottom_fractals'][-5:])
            recent_fx.sort(key=lambda x: x.dt, reverse=True)
            for fx in recent_fx[:10]:
                f.write(f"| {fx.dt.strftime('%Y-%m-%d')} | {fx.mark.value} | {fx.fx:.2f}元 |\n")
            f.write("\n")
            
            # 笔分析
            stroke_data = self.analysis_result['strokes']
            f.write("## 📏 笔分析\n\n")
            f.write(f"- **总笔数**: {stroke_data['total_count']} 笔\n")
            f.write(f"- **向上笔**: {stroke_data['up_count']} 笔，平均涨幅 {stroke_data['up_avg_change']:.2f}%，最大涨幅 {stroke_data['up_max_change']:.2f}%\n")
            f.write(f"- **向下笔**: {stroke_data['down_count']} 笔，平均跌幅 {stroke_data['down_avg_change']:.2f}%，最大跌幅 {stroke_data['down_max_change']:.2f}%\n\n")
            
            # 线段分析
            segment_data = self.analysis_result['segments']
            f.write("## 📐 线段分析\n\n")
            f.write(f"- **线段数量**: {segment_data['total_count']} 个\n")
            f.write(f"- **平均长度**: {segment_data['avg_length']:.1f} 笔/线段\n\n")
            
            # 背驰分析
            divergences = self.analysis_result['divergences']
            f.write("## ⚠️ 背驰分析\n\n")
            f.write(f"- **背驰总数**: {len(divergences)} 个\n")
            
            if divergences:
                f.write("\n### 背驰详情\n\n")
                f.write("| 类型 | 日期 | 强度 | 说明 |\n")
                f.write("|------|------|------|------|\n")
                for div in divergences[-5:]:  # 最近5个
                    f.write(f"| {div['type']} | {div['current_bi'].fx_b.dt.strftime('%Y-%m-%d')} | {div['strength']:.1f}% | 当前笔{div['current_change']:.1f}% vs 前笔{div['prev_change']:.1f}% |\n")
            f.write("\n")
            
            # 买卖点分析
            buy_points = self.analysis_result['buy_points']
            sell_points = self.analysis_result['sell_points']
            
            f.write("## 🎯 买卖点分析\n\n")
            f.write(f"- **买点总数**: {len(buy_points)} 个\n")
            f.write(f"- **卖点总数**: {len(sell_points)} 个\n\n")
            
            if buy_points:
                f.write("### 买点详情\n\n")
                f.write("| 类型 | 日期 | 价格 |\n")
                f.write("|------|------|------|\n")
                for bp in buy_points[-5:]:
                    f.write(f"| {bp['type']} | {bp['date'].strftime('%Y-%m-%d')} | {bp['price']:.2f}元 |\n")
                f.write("\n")
            
            if sell_points:
                f.write("### 卖点详情\n\n")
                f.write("| 类型 | 日期 | 价格 |\n")
                f.write("|------|------|------|\n")
                for sp in sell_points[-5:]:
                    f.write(f"| {sp['type']} | {sp['date'].strftime('%Y-%m-%d')} | {sp['price']:.2f}元 |\n")
                f.write("\n")
            
            # 投资建议
            f.write("## 💡 投资建议\n\n")
            
            # 基于分析结果给出建议
            trend = current['trend_status']
            fx_status = current['fx_status']
            
            if trend == "多头趋势" and "突破" in fx_status:
                suggestion = "🟢 **建议关注** - 多头趋势且突破关键分型，可考虑适量买入"
            elif trend == "空头趋势" and "跌破" in fx_status:
                suggestion = "🔴 **建议回避** - 空头趋势且跌破关键分型，建议观望或减仓"
            else:
                suggestion = "🟡 **谨慎观望** - 趋势不明确，建议等待更清晰的信号"
            
            f.write(f"{suggestion}\n\n")
            
            # 操作要点
            f.write("### 操作要点\n\n")
            f.write("1. **买入时机**: 关注底分型确认和背驰信号\n")
            f.write("2. **卖出时机**: 关注顶分型确认和背驰信号\n")
            f.write("3. **止损设置**: 跌破关键底分型或支撑位\n")
            f.write("4. **仓位管理**: 建议分批操作，控制风险\n\n")
            
            # 风险提示
            f.write("## ⚠️ 风险提示\n\n")
            f.write("- 本分析基于缠论技术分析，仅供参考，不构成投资建议\n")
            f.write("- 股市有风险，投资需谨慎\n")
            f.write("- 请结合基本面分析和市场环境综合判断\n")
            f.write("- 建议设置合理止损，控制投资风险\n\n")
            
            f.write("---\n")
            f.write("*本报告由CZSC自动分析系统生成*\n")
        
        # 保存文件路径
        self.last_report_path = report_filename
        
        print(f"✅ 分析报告已保存: {report_filename}")
        return report_filename
    
    def run_analysis(self, stock_code, start_date=None, end_date=None, days=None, kline_level=None):
        """
        运行完整分析流程
        
        Args:
            stock_code (str): 6位股票代码
            start_date (str): 开始日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认根据K线级别设置
            end_date (str): 结束日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'，默认当前日期
            days (int): 获取天数，当start_date和end_date都未指定时使用，默认根据K线级别设置
            kline_level (str): K线级别，可选值: '15m', '30m', '1d', '1wk'
        """
        # 如果指定了新的K线级别，更新配置
        if kline_level and kline_level != self.kline_level:
            if kline_level in KLINE_LEVELS:
                self.kline_level = kline_level
                self.kline_config = KLINE_LEVELS[self.kline_level]
                print(f"🔄 切换K线级别为: {self.kline_config['name']}")
            else:
                print(f"⚠️ 不支持的K线级别: {kline_level}，继续使用: {self.kline_config['name']}")
        print(f"🚀 开始分析股票 {stock_code}")
        print("=" * 60)
        
        try:
            # 1. 获取数据
            if not self.get_stock_data(stock_code, start_date, end_date, days):
                return False
            
            # 2. 转换格式
            self.convert_to_czsc_format()
            
            # 3. 缠论分析
            if not self.czsc_analysis():
                return False
            
            # 4. 各项分析
            self.analyze_fractals()
            self.analyze_strokes()
            self.analyze_segments()
            self.analyze_divergence()
            self.analyze_buy_sell_points()
            self.analyze_current_status()
            
            # 5. 准备分析结果
            self.prepare_analysis_result()
            
            # 6. 生成可视化
            chart_file = self.generate_visualization()
            
            # 7. 生成报告
            report_file = self.generate_report()
            
            print("\n" + "=" * 60)
            print("🎉 分析完成！")
            print(f"📊 可视化图表: {chart_file}")
            print(f"📄 分析报告: {report_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 分析过程中出现错误: {e}")
            import traceback
            print("详细错误信息:")
            traceback.print_exc()
            return False


def main():
    """主函数"""
    print("🎯 缠论自动分析系统")
    print("=" * 60)
    print("功能：输入6位股票代码，自动进行全面缠论分析")
    print("包含：分型、笔、线段、背驰、买卖点等核心概念")
    print("输出：详细分析报告 + 可视化图表")
    print("默认时间区间：2025年1月1日 至 当前日期")
    print("=" * 60)
    
    while True:
        try:
            # 获取用户输入
            print("\n📊 请输入分析参数:")
            stock_code = input("股票代码 (6位数字): ").strip()
            
            if stock_code.lower() == 'quit':
                print("👋 感谢使用！")
                break
            
            # 验证股票代码
            if not stock_code.isdigit() or len(stock_code) != 6:
                print("❌ 请输入正确的6位数字股票代码")
                continue
            
            # 获取时间参数
            print("\n📅 时间区间设置 (直接回车使用默认值):")
            start_input = input("开始日期 (YYYYMMDD，默认20250101): ").strip()
            end_input = input("结束日期 (YYYYMMDD，默认当前日期): ").strip()
            
            start_date = start_input if start_input else None
            end_date = end_input if end_input else None
            
            # 验证日期格式
            if start_date and (not start_date.isdigit() or len(start_date) != 8):
                print("❌ 开始日期格式错误，请使用YYYYMMDD格式")
                continue
            
            if end_date and (not end_date.isdigit() or len(end_date) != 8):
                print("❌ 结束日期格式错误，请使用YYYYMMDD格式")
                continue
            
            # 创建分析器并运行分析
            analyzer = CZSCAutoAnalyzer()
            success = analyzer.run_analysis(stock_code, start_date, end_date)
            
            if success:
                print("\n✅ 分析成功完成！")
                
                # 询问是否继续
                continue_analysis = input("\n是否继续分析其他股票？(y/n): ").strip().lower()
                if continue_analysis != 'y':
                    print("👋 感谢使用！")
                    break
            else:
                print("\n❌ 分析失败，请检查股票代码或网络连接")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，感谢使用！")
            break
        except Exception as e:
            print(f"\n❌ 程序出现错误: {e}")


if __name__ == "__main__":
    main()
