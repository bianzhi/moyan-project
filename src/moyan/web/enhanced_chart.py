# src/moyan/web/enhanced_chart.py
"""
增强图表生成器，用于生成交互式Plotly图表
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class EnhancedChartGenerator:
    """增强图表生成器，用于生成交互式Plotly图表"""
    def __init__(self, analysis_result):
        self.result = analysis_result
        self.data = analysis_result['data']
        self.stock_code = analysis_result['stock_code']
        self.kline_level = analysis_result['kline_level']
        self.kline_name = analysis_result['kline_name']
        
        # 获取数据
        self.df = self.data.get('raw_df')
        if self.df is None:
            raise ValueError("原始数据不可用")
        
        # 数据完整性校验和清理
        self.trading_df = self._validate_and_clean_data()
        
        print(f"Debug: 原始数据 {len(self.df)} 条，校验后数据 {len(self.trading_df)} 条")  # 调试输出

    def _datetime_to_index(self, dt):
        """将时间转换为数据索引位置"""
        try:
            return self.trading_df.index.get_loc(dt)
        except KeyError:
            # 如果找不到精确匹配，找最接近的
            closest_idx = self.trading_df.index.get_indexer([dt], method='nearest')[0]
            return closest_idx if closest_idx >= 0 else None

    def _validate_and_clean_data(self):
        """
        数据完整性校验和清理
        
        Returns:
            pd.DataFrame: 清理后的数据
        """
        df = self.df.copy()
        
        # 确保df的索引是datetime类型
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # 1. 检查必要列是否存在
        required_columns = ['Open', 'High', 'Low', 'Close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的数据列: {missing_columns}")
        
        # 2. 移除空值行
        original_length = len(df)
        df = df.dropna(subset=required_columns)
        
        if len(df) < original_length:
            print(f"⚠️ 移除了 {original_length - len(df)} 行空值数据")
        
        # 3. 检查数据有效性
        invalid_rows = df[
            (df['High'] < df['Low']) |  # 最高价小于最低价
            (df['Open'] <= 0) |        # 开盘价小于等于0
            (df['High'] <= 0) |        # 最高价小于等于0
            (df['Low'] <= 0) |         # 最低价小于等于0
            (df['Close'] <= 0)         # 收盘价小于等于0
        ]
        
        if len(invalid_rows) > 0:
            print(f"⚠️ 发现 {len(invalid_rows)} 行无效数据，已移除")
            df = df.drop(invalid_rows.index)
        
        # 4. 过滤交易日数据
        if 'Volume' in df.columns:
            # 使用成交量过滤交易日，但保留成交量为0但价格有变化的数据
            trading_mask = (df['Volume'] > 0) | (df['Close'] != df['Open'])
            df = df[trading_mask].copy()
        else:
            # 如果没有成交量数据，确保价格数据有效
            df = df.dropna(subset=['Close']).copy()
        
        # 5. 检查价格异常值（价格变化超过50%的数据点）
        if len(df) > 1:
            df_sorted = df.sort_index()
            price_changes = df_sorted['Close'].pct_change().abs()
            abnormal_changes = price_changes > 0.5  # 50%的变化
            
            if abnormal_changes.sum() > 0:
                print(f"⚠️ 发现 {abnormal_changes.sum()} 个异常价格变化点")
                # 标记为可疑数据但不删除
                df.loc[abnormal_changes, 'suspicious'] = True
        
        # 6. 确保数据按时间排序
        df = df.sort_index()
        
        # 7. 检查时间连续性（仅对分钟级数据）
        if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m']:
            self._check_time_continuity(df)
        
        # 8. 最终验证：确保至少有最小数量的数据点
        min_data_points = 10
        if len(df) < min_data_points:
            raise ValueError(f"数据量不足，至少需要 {min_data_points} 个数据点，实际只有 {len(df)} 个")
        
        return df
    
    def _check_time_continuity(self, df):
        """
        检查时间连续性
        
        Args:
            df: 数据DataFrame
        """
        if len(df) < 2:
            return
        
        # 计算时间间隔
        time_diffs = df.index.to_series().diff()[1:]
        
        # 根据K线级别确定预期间隔
        expected_intervals = {
            '1h': timedelta(hours=1),
            '30m': timedelta(minutes=30),
            '15m': timedelta(minutes=15),
            '5m': timedelta(minutes=5),
            '2m': timedelta(minutes=2),
            '1m': timedelta(minutes=1)
        }
        
        if self.kline_level in expected_intervals:
            expected_interval = expected_intervals[self.kline_level]
            
            # 允许一定的时间误差（考虑交易时间和节假日）
            tolerance = expected_interval * 0.1  # 10%的误差
            
            # 找出时间间隔异常的点
            abnormal_intervals = time_diffs[
                (time_diffs < expected_interval - tolerance) |
                (time_diffs > expected_interval * 5)  # 超过5倍间隔认为是异常
            ]
            
            if len(abnormal_intervals) > 0:
                print(f"⚠️ 发现 {len(abnormal_intervals)} 个时间间隔异常点")
                # 可以选择填充缺失的时间点或标记异常

    def _get_x_data(self):
        """获取优化的X轴数据，避免时间间隙但支持悬停显示日期"""
        if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m']:
            # 分钟级别：使用序号避免间隙，但保留原始时间用于悬停显示
            x_data = list(range(len(self.trading_df)))
        else:
            # 日线级别：使用序号避免间隙，但保留原始时间用于悬停显示  
            x_data = list(range(len(self.trading_df)))
        
        # 调试输出：确保X轴数据一致性
        print(f"Debug: X轴数据长度: {len(x_data)}, 范围: {x_data[0] if x_data else 'N/A'} - {x_data[-1] if x_data else 'N/A'}")
        return x_data

    def _add_candlestick(self, fig, row, col):
        """添加K线图（中国股市红涨绿跌配色，剔除非交易日）"""
        if len(self.trading_df) > 0:
            x_data = self._get_x_data()
            
            # 创建时间信息的悬停
            hover_text = []
            for i, (idx, row_data) in enumerate(self.trading_df.iterrows()):
                date_str = idx.strftime('%Y-%m-%d %H:%M') if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m'] else idx.strftime('%Y-%m-%d')
                hover_text.append(f"时间: {date_str}")
            
            fig.add_trace(go.Candlestick(
                x=x_data,
                open=self.trading_df['Open'],
                high=self.trading_df['High'],
                low=self.trading_df['Low'],
                close=self.trading_df['Close'],
                name='K线',
                increasing_line_color='red',
                increasing_fillcolor='red',
                decreasing_line_color='green', 
                decreasing_fillcolor='green',
                line=dict(width=1),
                showlegend=False,
                hoverinfo='text',
                hovertext=hover_text
            ), row=row, col=col)

    def _add_volume(self, fig, row, col):
        """添加成交量（使用过滤后的交易日数据）"""
        if 'Volume' in self.trading_df.columns and len(self.trading_df) > 0:
            x_data = self._get_x_data()
            colors = ['red' if row_data['Close'] > row_data['Open'] else 'green' for _, row_data in self.trading_df.iterrows()]
            
            # 创建悬停信息，显示时间和成交量
            hover_text = []
            for i, (idx, row_data) in enumerate(self.trading_df.iterrows()):
                date_str = idx.strftime('%Y-%m-%d %H:%M') if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m'] else idx.strftime('%Y-%m-%d')
                hover_info = f"日期: {date_str}<br>成交量: {row_data['Volume']:,.0f}"
                hover_text.append(hover_info)
            
            fig.add_trace(go.Bar(
                x=x_data,
                y=self.trading_df['Volume'],
                marker_color=colors,
                name='成交量',
                showlegend=False,
                hoverinfo='text',
                hovertext=hover_text
            ), row=row, col=col)

    def _add_ma(self, fig, row, col, periods=[5, 10]):
        """添加移动平均线（使用过滤后的交易日数据）"""
        if len(self.trading_df) > 0:
            x_data = self._get_x_data()
            for p in periods:
                ma = self.trading_df['Close'].rolling(window=p).mean()
                
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=ma,
                    mode='lines',
                    name=f'MA{p}',
                    line=dict(width=1),
                    showlegend=True,
                    hoverinfo='skip'  # 不显示悬停信息
                ), row=row, col=col)

    def _add_fractals(self, fig, row, col, show_top=True, show_bottom=True, show_labels=False):
        """添加分型标记（使用真实CZSC数据，支持独立控制）"""
        fractals_data = self.data.get('fractals', {})
        
        # 获取顶分型和底分型数据
        top_fractals = fractals_data.get('top_fractals', [])
        bottom_fractals = fractals_data.get('bottom_fractals', [])
        
        print(f"Debug: 顶分型数量: {len(top_fractals)}, 底分型数量: {len(bottom_fractals)}")  # 调试输出
        
        # 绘制顶分型（标记在K线顶部）
        if show_top and top_fractals:
            top_indices = []
            top_prices = []
            
            for fx in top_fractals:
                if hasattr(fx, 'dt') and hasattr(fx, 'fx'):
                    idx = self._datetime_to_index(fx.dt)
                    if idx is not None:
                        top_indices.append(idx)
                        top_prices.append(fx.fx)
                    
            print(f"Debug: 实际绘制的顶分型: {len(top_indices)}")  # 调试输出
            
            if top_indices:
                # 标记位置稍微高于实际价格，避免与卖点重叠
                top_positions = [price * 1.02 for price in top_prices]
                
                fig.add_trace(go.Scatter(
                    x=top_indices,
                    y=top_positions,
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=10, color='red', line=dict(color='darkred', width=1)),
                    name='顶分型',
                    text=None,  # 顶分型标识已移除（根据用户要求）
                    textposition="top center",
                    showlegend=True,
                    hoverinfo='skip',  # 不显示悬停信息
                    legendgroup='top_fractals'  # 顶分型图例组
                ), row=row, col=col)
            
        # 绘制底分型（标记在K线底部）
        if show_bottom and bottom_fractals:
            bottom_indices = []
            bottom_prices = []
            
            for fx in bottom_fractals:
                if hasattr(fx, 'dt') and hasattr(fx, 'fx'):
                    idx = self._datetime_to_index(fx.dt)
                    if idx is not None:
                        bottom_indices.append(idx)
                        bottom_prices.append(fx.fx)
                    
            print(f"Debug: 实际绘制的底分型: {len(bottom_indices)}")  # 调试输出
            
            if bottom_indices:
                # 标记位置稍微低于实际价格，避免与买点重叠
                bottom_positions = [price * 0.98 for price in bottom_prices]
                
                fig.add_trace(go.Scatter(
                    x=bottom_indices,
                    y=bottom_positions,
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=10, color='green', line=dict(color='darkgreen', width=1)),
                    name='底分型',
                    text=None,  # 底分型标识已移除（根据用户要求）
                    textposition="bottom center",
                    showlegend=True,
                    hoverinfo='skip',  # 不显示悬停信息
                    legendgroup='bottom_fractals'  # 底分型图例组
                ), row=row, col=col)

    def _add_strokes(self, fig, row, col, show_up=True, show_down=True, show_labels=False):
        """添加笔（使用真实CZSC数据，支持独立控制）"""
        strokes_data = self.data.get('strokes', {})
        
        up_strokes = strokes_data.get('up_strokes', [])
        down_strokes = strokes_data.get('down_strokes', [])
        
        # 绘制向上笔
        if show_up:
            up_legend_shown = False
            for i, stroke in enumerate(up_strokes):
                if hasattr(stroke, 'fx_a') and hasattr(stroke, 'fx_b'):
                    # 转换时间坐标为索引坐标
                    start_idx = self._datetime_to_index(stroke.fx_a.dt)
                    end_idx = self._datetime_to_index(stroke.fx_b.dt)
                    
                    if start_idx is not None and end_idx is not None:
                        fig.add_trace(go.Scatter(
                            x=[start_idx, end_idx],
                            y=[stroke.fx_a.fx, stroke.fx_b.fx],
                            mode='lines',
                            line=dict(color='blue', width=3),
                            name='向上笔' if not up_legend_shown else None,
                            showlegend=not up_legend_shown,
                            text=None,  # 向上笔标识已移除（根据用户要求）
                            textposition="middle center",
                            hoverinfo='skip',  # 不显示悬停信息
                            legendgroup='up_strokes'
                        ), row=row, col=col)
                        up_legend_shown = True
        
        # 绘制向下笔
        if show_down:
            down_legend_shown = False
            for i, stroke in enumerate(down_strokes):
                if hasattr(stroke, 'fx_a') and hasattr(stroke, 'fx_b'):
                    # 转换时间坐标为索引坐标
                    start_idx = self._datetime_to_index(stroke.fx_a.dt)
                    end_idx = self._datetime_to_index(stroke.fx_b.dt)
                    
                    if start_idx is not None and end_idx is not None:
                        fig.add_trace(go.Scatter(
                            x=[start_idx, end_idx],
                            y=[stroke.fx_a.fx, stroke.fx_b.fx],
                            mode='lines',
                            line=dict(color='orange', width=3),
                            name='向下笔' if not down_legend_shown else None,
                            showlegend=not down_legend_shown,
                            text=None,  # 向下笔标识已移除（根据用户要求）
                            textposition="middle center",
                            hoverinfo='skip',  # 不显示悬停信息
                            legendgroup='down_strokes'
                        ), row=row, col=col)
                        down_legend_shown = True

    def _add_segments(self, fig, row, col, show_labels=False):
        """添加线段（使用真实CZSC数据）"""
        segments_data = self.data.get('segments', {})
        segments = segments_data.get('segments', [])
        
        print(f"Debug: 线段数量: {len(segments)}")  # 调试输出
        
        # 绘制线段
        for i, segment in enumerate(segments):
            if len(segment) >= 2:
                # 线段由多个笔组成，连接首尾
                start_stroke = segment[0]
                end_stroke = segment[-1]
                
                if (hasattr(start_stroke, 'fx_a') and hasattr(start_stroke, 'fx_b') and
                    hasattr(end_stroke, 'fx_a') and hasattr(end_stroke, 'fx_b')):
                    
                    # 线段从第一笔的起点到最后一笔的终点
                    start_point = start_stroke.fx_a
                    end_point = end_stroke.fx_b
                    
                    print(f"Debug: 线段{i+1}: {start_point.dt} -> {end_point.dt}")  # 调试输出
                    
                    # 转换时间坐标为索引坐标
                    start_idx = self._datetime_to_index(start_point.dt)
                    end_idx = self._datetime_to_index(end_point.dt)
                    
                    if start_idx is not None and end_idx is not None:
                        fig.add_trace(go.Scatter(
                            x=[start_idx, end_idx],
                            y=[start_point.fx, end_point.fx],
                            mode='lines+markers',  # 添加端点标记
                            line=dict(color='purple', width=4, dash='dash'),
                            marker=dict(size=8, color='purple', symbol='diamond'),
                            name='线段' if i == 0 else None,
                            showlegend=(i == 0),
                            text=None,  # 线段标识已移除（根据用户要求）
                            textposition="middle center",
                            hoverinfo='skip',  # 不显示悬停信息
                            legendgroup='segments'  # 线段图例组
                        ), row=row, col=col)
                        
                        # 恢复线段标签显示，但移除文字标识（根据用户要求）
                        if show_labels:
                            mid_x = start_idx + (end_idx - start_idx) / 2
                            mid_y = (start_point.fx + end_point.fx) / 2
                            fig.add_annotation(
                                x=mid_x, y=mid_y,
                                text="",  # 移除XD1文字，保留标记位置
                                showarrow=False,
                                font=dict(size=10, color="purple"),
                                bgcolor="white",
                                bordercolor="purple",
                                borderwidth=1,
                                row=row, col=col
                            )

    def _add_buy_sell_points(self, fig, row, col, buy_types=None, sell_types=None, show_labels=False):
        """添加买卖点（使用真实CZSC数据，支持按类型独立控制）"""
        buy_points = self.data.get('buy_points', [])
        sell_points = self.data.get('sell_points', [])
        
        print(f"Debug: 买点数量: {len(buy_points)}, 卖点数量: {len(sell_points)}")  # 调试输出
        print(f"Debug: buy_types={buy_types}, sell_types={sell_types}")  # 调试输出
        
        # 打印买卖点的时间分布
        if buy_points:
            buy_dates = [bp['date'] for bp in buy_points]
            print(f"Debug: 买点时间范围: {min(buy_dates)} ~ {max(buy_dates)}")
        if sell_points:
            sell_dates = [sp['date'] for sp in sell_points]
            print(f"Debug: 卖点时间范围: {min(sell_dates)} ~ {max(sell_dates)}")
        
        # 买点标记（按类型过滤）
        if buy_types and buy_points:
            # 过滤出需要显示的买点类型
            filtered_buy_points = [bp for bp in buy_points if bp['type'] in buy_types]
            print(f"Debug: 过滤后的买点数量: {len(filtered_buy_points)}")
            
            if filtered_buy_points:
                buy_dates = [bp['date'] for bp in filtered_buy_points]
                buy_prices = [bp['price'] for bp in filtered_buy_points]
                buy_point_types = [bp['type'] for bp in filtered_buy_points]
                
                # 标记位置更低，避免与底分型重叠
                buy_positions = [price * 0.95 for price in buy_prices]
                
                # 不同类型买点使用不同形状和颜色
                symbols = {'第一类买点': 'circle', '第二类买点': 'square', '第三类买点': 'diamond'}
                colors = {'第一类买点': 'lightgreen', '第二类买点': 'green', '第三类买点': 'darkgreen'}
                
                added_types = set()  # 跟踪已添加的图例类型
                for i, (date, pos, type_name) in enumerate(zip(buy_dates, buy_positions, buy_point_types)):
                    symbol = symbols.get(type_name, 'circle')
                    color = colors.get(type_name, 'lightgreen')
                    show_legend = type_name not in added_types
                    
                    # 转换时间坐标为索引坐标
                    date_idx = self._datetime_to_index(date)
                    if date_idx is not None:
                        fig.add_trace(go.Scatter(
                            x=[date_idx],
                            y=[pos],
                            mode='markers',
                            marker=dict(symbol=symbol, size=12, color=color, 
                                       line=dict(color='darkgreen', width=2)),
                            name=type_name if show_legend else None,
                            text=None,  # 买点标识已移除（根据用户要求）
                            textposition="bottom center",
                            showlegend=show_legend,
                            hoverinfo='skip',  # 不显示悬停信息
                            legendgroup=f'buy_{type_name}'  # 每种类型独立图例组
                        ), row=row, col=col)
                        
                        if show_legend:
                            added_types.add(type_name)
        
        # 卖点标记（按类型过滤）
        if sell_types and sell_points:
            # 过滤出需要显示的卖点类型
            filtered_sell_points = [sp for sp in sell_points if sp['type'] in sell_types]
            print(f"Debug: 过滤后的卖点数量: {len(filtered_sell_points)}")
            
            if filtered_sell_points:
                sell_dates = [sp['date'] for sp in filtered_sell_points]
                sell_prices = [sp['price'] for sp in filtered_sell_points]
                sell_point_types = [sp['type'] for sp in filtered_sell_points]
                
                # 标记位置更高，避免与顶分型重叠
                sell_positions = [price * 1.05 for price in sell_prices]
                
                # 不同类型卖点使用不同形状和颜色
                symbols = {'第一类卖点': 'circle', '第二类卖点': 'square', '第三类卖点': 'diamond'}
                colors = {'第一类卖点': 'lightcoral', '第二类卖点': 'red', '第三类卖点': 'darkred'}
                
                added_types = set()  # 跟踪已添加的图例类型
                for i, (date, pos, type_name) in enumerate(zip(sell_dates, sell_positions, sell_point_types)):
                    symbol = symbols.get(type_name, 'circle')
                    color = colors.get(type_name, 'lightcoral')
                    show_legend = type_name not in added_types
                    
                    # 转换时间坐标为索引坐标
                    date_idx = self._datetime_to_index(date)
                    if date_idx is not None:
                        fig.add_trace(go.Scatter(
                            x=[date_idx],
                            y=[pos],
                            mode='markers',
                            marker=dict(symbol=symbol, size=12, color=color,
                                       line=dict(color='darkred', width=2)),
                            name=type_name if show_legend else None,
                            text=None,  # 卖点标识已移除（根据用户要求）
                            textposition="top center",
                            showlegend=show_legend,
                            hoverinfo='skip',  # 不显示悬停信息
                            legendgroup=f'sell_{type_name}'  # 每种类型独立图例组
                        ), row=row, col=col)
                        
                        if show_legend:
                            added_types.add(type_name)

    def _add_divergence(self, fig, row, col):
        """添加背驰标记（使用真实CZSC数据，分别控制顶底背驰）"""
        divergences = self.data.get('divergences', [])
        
        # 分别收集顶背驰和底背驰
        top_divergences = [div for div in divergences if div['type'] == '顶背驰']
        bottom_divergences = [div for div in divergences if div['type'] == '底背驰']
        
        # 绘制顶背驰
        if top_divergences:
            top_dates = [div['current_bi'].fx_b.dt for div in top_divergences]
            top_prices = [div['current_bi'].fx_b.fx * 1.05 for div in top_divergences]
            
            # 转换时间坐标为索引坐标
            top_indices = []
            for date in top_dates:
                idx = self._datetime_to_index(date)
                if idx is not None:
                    top_indices.append(idx)
            
            if top_indices:
                fig.add_trace(go.Scatter(
                    x=top_indices,
                    y=top_prices[:len(top_indices)],
                    mode='markers',
                    marker=dict(symbol='x', size=16, color='red', line=dict(width=3)),
                    name='顶背驰',
                    text=None,  # 顶背驰标识已移除（根据用户要求）
                    textposition="top center",
                    showlegend=True,
                    hoverinfo='skip',  # 不显示悬停信息
                    legendgroup='top_divergence'
                ), row=row, col=col)
        
        # 绘制底背驰  
        if bottom_divergences:
            bottom_dates = [div['current_bi'].fx_b.dt for div in bottom_divergences]
            bottom_prices = [div['current_bi'].fx_b.fx * 0.95 for div in bottom_divergences]
            
            # 转换时间坐标为索引坐标
            bottom_indices = []
            for date in bottom_dates:
                idx = self._datetime_to_index(date)
                if idx is not None:
                    bottom_indices.append(idx)
            
            if bottom_indices:
                fig.add_trace(go.Scatter(
                    x=bottom_indices,
                    y=bottom_prices[:len(bottom_indices)],
                    mode='markers',
                    marker=dict(symbol='x', size=16, color='green', line=dict(width=3)),
                    name='底背驰',
                    text=None,  # 底背驰标识已移除（根据用户要求）
                    textposition="bottom center",
                    showlegend=True,
                    hoverinfo='skip',  # 不显示悬停信息
                    legendgroup='bottom_divergence'
                ), row=row, col=col)

    def _add_pivots(self, fig, row, col, show_labels=False):
        """添加中枢区域（使用分析结果中的中枢数据）"""
        pivots = self.data.get('pivots', [])
        
        if not pivots:
            return
        
        for i, pivot in enumerate(pivots):
            # 转换时间坐标为索引坐标
            start_idx = self._datetime_to_index(pivot['start_dt'])
            end_idx = self._datetime_to_index(pivot['end_dt'])
            
            if start_idx is not None and end_idx is not None:
                # 绘制中枢区域
                fig.add_shape(
                    type="rect",
                    xref="x", yref="y",
                    x0=start_idx, y0=pivot['low'],
                    x1=end_idx, y1=pivot['high'],
                    fillcolor="purple",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                    row=row, col=col
                )
                
                # 中枢边界线已移除（根据用户要求）
                # fig.add_hline(
                #     y=pivot['high'], 
                #     line_dash="dash", 
                #     line_color="purple", 
                #     opacity=0.6,
                #     row=row, col=col
                # )
                # fig.add_hline(
                #     y=pivot['low'], 
                #     line_dash="dash", 
                #     line_color="purple", 
                #     opacity=0.6,
                #     row=row, col=col
                # )
                
                # 恢复中枢标签显示，但移除文字标识（根据用户要求）
                if show_labels:
                    fig.add_annotation(
                        x=start_idx + (end_idx - start_idx) / 2,
                        y=pivot['center'],
                        text="",  # 移除ZS1文字，保留标记位置
                        showarrow=False,
                        font=dict(size=10, color="white"),
                        bgcolor="purple",
                        bordercolor="purple",
                        borderwidth=1,
                        row=row, col=col
                    )
            
            # 添加到图例（只添加一次）
            if i == 0:
                fig.add_trace(go.Scatter(
                    x=[start_idx],
                    y=[pivot['center']],
                    mode='markers',
                    marker=dict(
                        size=0,  # 不显示标记
                        color='purple'
                    ),
                    name='中枢区域',
                    showlegend=True,
                    hoverinfo='skip',  # 不显示悬停信息
                    legendgroup='pivots'
                ), row=row, col=col)

    def _add_macd(self, fig, row, col):
        """添加MACD指标（使用过滤后的交易日数据）"""
        if len(self.trading_df) > 0:
            x_data = self._get_x_data()
            # 简化的MACD计算
            ema12 = self.trading_df['Close'].ewm(span=12).mean()
            ema26 = self.trading_df['Close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            # 只为histogram创建悬停信息（统一显示日期）
            hover_text_hist = []
            for i, (idx, row_data) in enumerate(self.trading_df.iterrows()):
                date_str = idx.strftime('%Y-%m-%d %H:%M') if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m'] else idx.strftime('%Y-%m-%d')
                hover_text_hist.append(f"日期: {date_str}<br>MACD: {macd.iloc[i]:.4f}<br>Signal: {signal.iloc[i]:.4f}<br>Histogram: {histogram.iloc[i]:.4f}")
            
            # MACD线 - 不显示悬停信息
            fig.add_trace(go.Scatter(
                x=x_data, y=macd, 
                mode='lines', name='MACD', 
                line=dict(color='blue', width=1),
                hoverinfo='skip'
            ), row=row, col=col)
            
            # Signal线 - 不显示悬停信息
            fig.add_trace(go.Scatter(
                x=x_data, y=signal, 
                mode='lines', name='Signal', 
                line=dict(color='orange', width=1),
                hoverinfo='skip'
            ), row=row, col=col)
            
            # Histogram柱状图 - 显示统一的悬停信息
            colors = ['red' if val >= 0 else 'green' for val in histogram]
            fig.add_trace(go.Bar(
                x=x_data, y=histogram, 
                name='Histogram', 
                marker_color=colors, 
                showlegend=False,
                hoverinfo='text',
                hovertext=hover_text_hist
            ), row=row, col=col)

    def _add_rsi(self, fig, row, col):
        """添加RSI指标（使用过滤后的交易日数据）"""
        if len(self.trading_df) > 0:
            x_data = self._get_x_data()
            # 简化的RSI计算
            delta = self.trading_df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 创建悬停信息
            hover_text = []
            for i, (idx, row_data) in enumerate(self.trading_df.iterrows()):
                date_str = idx.strftime('%Y-%m-%d %H:%M') if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m'] else idx.strftime('%Y-%m-%d')
                hover_text.append(f"日期: {date_str}<br>RSI: {rsi.iloc[i]:.2f}")
            
            fig.add_trace(go.Scatter(
                x=x_data, y=rsi, 
                mode='lines', name='RSI', 
                line=dict(color='purple', width=1),
                hoverinfo='text',
                hovertext=hover_text
            ), row=row, col=col)
            
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=row, col=col)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=row, col=col)

    def _add_bollinger_bands(self, fig, row, col):
        """添加布林带（使用过滤后的交易日数据）"""
        if len(self.trading_df) > 0:
            x_data = self._get_x_data()
            window = 20
            rolling_mean = self.trading_df['Close'].rolling(window=window).mean()
            rolling_std = self.trading_df['Close'].rolling(window=window).std()
            upper_band = rolling_mean + (rolling_std * 2)
            lower_band = rolling_mean - (rolling_std * 2)
            
            fig.add_trace(go.Scatter(
                x=x_data, y=upper_band, 
                mode='lines', name='Upper Band', 
                line=dict(color='gray', width=1, dash='dot')
            ), row=row, col=col)
            
            fig.add_trace(go.Scatter(
                x=x_data, y=rolling_mean, 
                mode='lines', name='Middle Band', 
                line=dict(color='blue', width=1)
            ), row=row, col=col)
            
            fig.add_trace(go.Scatter(
                x=x_data, y=lower_band, 
                mode='lines', name='Lower Band', 
                line=dict(color='gray', width=1, dash='dot')
            ), row=row, col=col)

    def _add_comprehensive_statistics(self, fig):
        """添加综合统计面板（单列布局）"""
        # 直接从根级别获取买卖点数据（根据实际的数据结构）
        buy_points = self.data.get('buy_points', [])
        sell_points = self.data.get('sell_points', [])
        
        divergences = self.data.get('divergences', [])
        pivots = self.data.get('pivots', [])
        
        # 修正分型数据结构
        fractals_data = self.data.get('fractals', {})
        top_fractals = fractals_data.get('top_fractals', [])
        bottom_fractals = fractals_data.get('bottom_fractals', [])
        
        # 如果top_fractals和bottom_fractals为空，尝试从其他结构获取
        if not top_fractals and not bottom_fractals:
            # 尝试从计数获取
            top_count = fractals_data.get('top_count', 0)
            bottom_count = fractals_data.get('bottom_count', 0)
            # 创建虚拟列表用于计数
            top_fractals = list(range(top_count))
            bottom_fractals = list(range(bottom_count))
        
        # 额外调试：打印完整的数据结构键
        print(f"Debug: 完整数据键: {list(self.data.keys())}")
        if 'buy_sell_points' in self.data:
            print(f"Debug: buy_sell_points键: {list(self.data['buy_sell_points'].keys())}")
        
        # 调试输出
        print(f"Debug: 统计面板数据 - 买点:{len(buy_points)}, 卖点:{len(sell_points)}, 背驰:{len(divergences)}, 中枢:{len(pivots)}, 顶分型:{len(top_fractals)}, 底分型:{len(bottom_fractals)}")
        
        # 创建综合统计条形图
        categories = ['买点', '卖点', '顶背驰', '底背驰', '中枢', '顶分型', '底分型']
        values = [
            len(buy_points),
            len(sell_points),
            len([d for d in divergences if d.get('type') == '顶背驰']),
            len([d for d in divergences if d.get('type') == '底背驰']),
            len(pivots),
            len(top_fractals),
            len(bottom_fractals)
        ]
        colors = ['green', 'red', 'red', 'green', 'purple', 'red', 'green']
        
        print(f"Debug: 统计面板值: {values}")  # 调试输出
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=values,
            textposition='auto',
            name='统计信息',
            showlegend=False,
            hoverinfo='x+y',
            hovertemplate='%{x}: %{y}<extra></extra>'
        ), row=4, col=1)
        
        # 确保统计面板的Y轴范围正确显示
        max_value = max(values) if values else 1
        fig.update_yaxes(range=[0, max_value * 1.1], row=4, col=1)
        
        # 强制设置统计面板的标题和可见性
        fig.update_yaxes(title_text="数量", row=4, col=1)
        fig.update_xaxes(title_text="统计项目", row=4, col=1)
        
        print(f"Debug: 统计面板图表已添加到第4行第1列，Y轴范围: [0, {max_value * 1.1}]")

    def create_interactive_chart(self, display_options):
        """
        创建交互式Plotly图表（专业缠论分析样式）
        :param display_options: 控制显示哪些元素的字典
        """
        
        # 创建专业布局：主图 + 成交量 + MACD + 统计面板
        fig = make_subplots(
            rows=4, cols=1,  # 简化为单列布局，确保十字线能正确跨图显示
            shared_xaxes=True,  # 前三个子图共享X轴
            shared_yaxes=False,  # Y轴不共享
            vertical_spacing=0.02,  # 减小垂直间距，让图表更紧凑
            row_heights=[0.4, 0.2, 0.2, 0.2],  # 主图、成交量、MACD、统计（增加统计面板高度）
            subplot_titles=[
                f"{self.stock_code} ({self.data.get('stock_name', self.stock_code)}) 缠论技术分析图",
                "成交量", "MACD指标", "统计面板"
            ]
        )

        # 第1行：主图（K线图 + 缠论要素）
        if display_options.get('show_kline'):
            self._add_candlestick(fig, 1, 1)
        if display_options.get('show_ma'):
            self._add_ma(fig, 1, 1)
        
        # 分型独立控制
        if display_options.get('show_top_fx') or display_options.get('show_bottom_fx'):
            self._add_fractals(fig, 1, 1, 
                            show_top=display_options.get('show_top_fx'), 
                            show_bottom=display_options.get('show_bottom_fx'),
                            show_labels=True)
        
        # 笔独立控制
        if display_options.get('show_up_bi') or display_options.get('show_down_bi'):
            self._add_strokes(fig, 1, 1,
                            show_up=display_options.get('show_up_bi'),
                            show_down=display_options.get('show_down_bi'),
                            show_labels=True)
        
        if display_options.get('show_xd'):
            self._add_segments(fig, 1, 1, show_labels=True)
        # 买卖点按类型独立控制
        buy_types = {}
        sell_types = {}
        if display_options.get('show_buy1'): buy_types['第一类买点'] = True
        if display_options.get('show_buy2'): buy_types['第二类买点'] = True
        if display_options.get('show_buy3'): buy_types['第三类买点'] = True
        if display_options.get('show_sell1'): sell_types['第一类卖点'] = True
        if display_options.get('show_sell2'): sell_types['第二类卖点'] = True
        if display_options.get('show_sell3'): sell_types['第三类卖点'] = True
        
        if buy_types or sell_types:
            self._add_buy_sell_points(fig, 1, 1,
                                    buy_types=buy_types,
                                    sell_types=sell_types,
                                    show_labels=True)
        if display_options.get('show_divergence'):
            self._add_divergence(fig, 1, 1)
        # 中枢显示（可选，默认不显示以保持图表清洁）
        if display_options.get('show_zs', False):  # 默认关闭中枢显示
            self._add_pivots(fig, 1, 1, show_labels=True)
        if display_options.get('show_boll'):
            self._add_bollinger_bands(fig, 1, 1)

        # 第2行：成交量
        if display_options.get('show_volume'):
            self._add_volume(fig, 2, 1)

        # 第3行：MACD
        if display_options.get('show_macd'):
            self._add_macd(fig, 3, 1)

        # 第4行：统计面板（简化为单个综合统计图）
        try:
            print("Debug: 开始添加统计面板...")
            self._add_comprehensive_statistics(fig)
            print("Debug: 统计面板添加完成")
        except Exception as e:
            print(f"Debug: 统计面板添加失败: {e}")
            import traceback
            traceback.print_exc()

        # 更新坐标轴
        fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=3, col=1)
        fig.update_yaxes(title_text="统计", row=4, col=1)

        # 设置专业的布局样式 - 优化用户体验
        fig.update_layout(
            height=1100,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top", y=0.98,
                xanchor="left", x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="gray",
                borderwidth=1
            ),
            template="plotly_white",
            margin=dict(t=80, b=120, l=60, r=60),
            font=dict(size=10),
            title_font_size=16,
            # 核心改进：使用closest模式，时间信息显示在空白处
            hovermode="closest",  # 只显示最接近的数据点，时间信息不遮挡
            xaxis_rangeslider_visible=False,
            dragmode='pan',
            # 增强交互响应
            hoverdistance=50,  # 减小距离，提高精确度
            spikedistance=200,  # 适中的检测距离
        )
        
        # 为所有子图添加统一光标配置 - 清理无用hovertext
        # 注意：Candlestick不支持connectgaps属性，只对line traces有效
        fig.update_traces(
            selector=dict(type='scatter'),
            line=dict(width=1),
            connectgaps=False,
            # 移除无用的hovertemplate，使用默认的悬停信息
        )
        
        # 为柱状图添加清洁的悬停配置
        fig.update_traces(
            selector=dict(type='bar'),
            # 移除无用的hovertemplate，使用默认的悬停信息
        )
        
        # 配置时间轴 - 使用序号避免间隙，但显示月份标识
        data_count = len(self.trading_df)
        
        # 生成月份标签
        time_indices = self.trading_df.index
        month_labels = []
        month_positions = []
        
        # 找到每个月的第一个交易日位置
        current_month = None
        for i, dt in enumerate(time_indices):
            month_key = dt.strftime('%Y-%m')
            if month_key != current_month:
                current_month = month_key
                month_labels.append(dt.strftime('%m月'))
                month_positions.append(i)
        
        # 确保有开始和结束标签
        if len(month_positions) == 0 or month_positions[0] != 0:
            month_positions.insert(0, 0)
            month_labels.insert(0, time_indices[0].strftime('%m月'))
        if month_positions[-1] != data_count - 1:
            month_positions.append(data_count - 1)
            month_labels.append(time_indices[-1].strftime('%m月'))
        
        # 配置X轴 - 实用的十字线显示（前三个子图）
        fig.update_xaxes(
            type='linear',
            tickangle=0,
            showgrid=False,
            tickmode='array',
            tickvals=month_positions,
            ticktext=month_labels,
            tickfont=dict(size=10, color='#666666'),
            showline=True,
            linewidth=1,
            linecolor='#e0e0e0',
            range=[0, data_count - 1],
            # 优化的十字虚线光标配置
            showspikes=True,
            spikecolor="rgba(120,120,120,0.9)",  # 更清晰的灰色
            spikesnap="cursor",
            spikemode="across",  # 跨图显示
            spikethickness=2,  # 稍微粗一点，更明显
            spikedash="dash",  # 虚线样式
            matches='x',
            row=[1, 2, 3]  # 只应用于前三个子图
        )
        
        # 统计面板的X轴配置（独立）
        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#e0e0e0',
            tickfont=dict(size=10, color='#666666'),
            row=4, col=1  # 只应用于统计面板
        )
        
        # 配置Y轴 - 实用的十字线显示
        fig.update_yaxes(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='#e0e0e0',
            tickfont=dict(size=10, color='#666666'),
            # 优化的十字虚线光标配置
            showspikes=True,
            spikecolor="rgba(120,120,120,0.9)",  # 更清晰的灰色
            spikesnap="cursor",
            spikemode="across",  # 跨图显示
            spikethickness=2,  # 稍微粗一点，更明显
            spikedash="dash"  # 虚线样式
        )
        fig.add_annotation(
            text="📊 使用说明: 将鼠标悬停在任意位置，统一显示所有图表的对应数据 | 十字虚线光标精确定位",
            xref="paper", yref="paper",
            x=0.01, y=-0.05,
            showarrow=False,
            font=dict(size=10, color="blue", family="Arial"),
            align="left"
        )
        
        fig.add_annotation(
            text="🔺 分型: ▲底分型(绿) ▼顶分型(红) | 📏 笔: —向上笔(蓝) —向下笔(橙)",
            xref="paper", yref="paper",
            x=0.01, y=-0.07,
            showarrow=False,
            font=dict(size=9, color="gray"),
            align="left"
        )
        
        fig.add_annotation(
            text="🎯 买点: ●第一类(浅绿) ■第二类(绿) ♦第三类(深绿) | 🎯 卖点: ●第一类(浅红) ■第二类(红) ♦第三类(深红)",
            xref="paper", yref="paper",
            x=0.01, y=-0.09,
            showarrow=False,
            font=dict(size=9, color="gray"),
            align="left"
        )
        
        fig.add_annotation(
            text="⚠️ 背驰: ✖顶背驰(红) ✖底背驰(绿) | 🔄 中枢: 紫色阴影区域 | 💡 提示: 买卖点和分型标记已分层显示，避免重叠",
            xref="paper", yref="paper",
            x=0.01, y=-0.11,
            showarrow=False,
            font=dict(size=9, color="gray"),
            align="left"
        )
        
        return fig
