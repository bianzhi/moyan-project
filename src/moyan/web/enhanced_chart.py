# src/moyan/web/enhanced_chart.py
"""
增强图表生成器，用于生成交互式Plotly图表
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
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
        
        # 确保df的索引是datetime类型
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
        
        # 过滤掉非交易日（成交量为0或NaN的日期）
        if 'Volume' in self.df.columns:
            self.trading_df = self.df[self.df['Volume'] > 0].copy()
        else:
            # 如果没有成交量数据，使用价格变化来判断交易日
            self.trading_df = self.df.dropna(subset=['Close']).copy()
        
        print(f"Debug: 原始数据 {len(self.df)} 条，过滤后交易日数据 {len(self.trading_df)} 条")  # 调试输出

    def _get_x_data(self):
        """获取优化的X轴数据，避免时间间隙"""
        if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m']:
            # 对于分钟级别数据，使用格式化的时间标签以避免间隙
            # 根据数据量调整时间格式
            data_count = len(self.trading_df)
            if data_count > 200:
                # 数据量大时，只显示日期
                return [dt.strftime('%m-%d') for dt in self.trading_df.index]
            elif data_count > 100:
                # 中等数据量，显示日期和小时
                return [dt.strftime('%m-%d %H:00') for dt in self.trading_df.index]
            else:
                # 数据量少时，显示完整时间
                return [dt.strftime('%m-%d %H:%M') for dt in self.trading_df.index]
        else:
            # 日线及以上级别使用原始时间索引
            return self.trading_df.index

    def _add_candlestick(self, fig, row, col):
        """添加K线图（中国股市红涨绿跌配色，剔除非交易日）"""
        if len(self.trading_df) > 0:
            x_data = self._get_x_data()
            
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
                showlegend=False
            ), row=row, col=col)

    def _add_volume(self, fig, row, col):
        """添加成交量（使用过滤后的交易日数据）"""
        if 'Volume' in self.trading_df.columns and len(self.trading_df) > 0:
            x_data = self._get_x_data()
            colors = ['red' if row['Close'] > row['Open'] else 'green' for _, row in self.trading_df.iterrows()]
            fig.add_trace(go.Bar(
                x=x_data,
                y=self.trading_df['Volume'],
                marker_color=colors,
                name='成交量',
                showlegend=False
            ), row=row, col=col)

    def _add_ma(self, fig, row, col, periods=[5, 20]):
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
                    showlegend=True
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
            top_dates = []
            top_prices = []
            
            for fx in top_fractals:
                if hasattr(fx, 'dt') and hasattr(fx, 'fx'):
                    top_dates.append(fx.dt)
                    top_prices.append(fx.fx)
                    
            print(f"Debug: 实际绘制的顶分型: {len(top_dates)}")  # 调试输出
            
            if top_dates:
                # 标记位置稍微高于实际价格，避免与卖点重叠
                top_positions = [price * 1.02 for price in top_prices]
                
                fig.add_trace(go.Scatter(
                    x=top_dates,
                    y=top_positions,
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=10, color='red', line=dict(color='darkred', width=1)),
                    name='顶分型',
                    text=['▼'] * len(top_dates) if show_labels else None,
                    textposition="top center",
                    showlegend=True,
                    legendgroup='top_fractals'  # 顶分型图例组
                ), row=row, col=col)
            
        # 绘制底分型（标记在K线底部）
        if show_bottom and bottom_fractals:
            bottom_dates = []
            bottom_prices = []
            
            for fx in bottom_fractals:
                if hasattr(fx, 'dt') and hasattr(fx, 'fx'):
                    bottom_dates.append(fx.dt)
                    bottom_prices.append(fx.fx)
                    
            print(f"Debug: 实际绘制的底分型: {len(bottom_dates)}")  # 调试输出
            
            if bottom_dates:
                # 标记位置稍微低于实际价格，避免与买点重叠
                bottom_positions = [price * 0.98 for price in bottom_prices]
                
                fig.add_trace(go.Scatter(
                    x=bottom_dates,
                    y=bottom_positions,
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=10, color='green', line=dict(color='darkgreen', width=1)),
                    name='底分型',
                    text=['▲'] * len(bottom_dates) if show_labels else None,
                    textposition="bottom center",
                    showlegend=True,
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
                    fig.add_trace(go.Scatter(
                        x=[stroke.fx_a.dt, stroke.fx_b.dt],
                        y=[stroke.fx_a.fx, stroke.fx_b.fx],
                        mode='lines',
                        line=dict(color='blue', width=3),
                        name='向上笔' if not up_legend_shown else None,
                        showlegend=not up_legend_shown,
                        text=f'向上笔{i+1}' if show_labels else None,
                        textposition="middle center",
                        legendgroup='up_strokes'
                    ), row=row, col=col)
                    up_legend_shown = True
        
        # 绘制向下笔
        if show_down:
            down_legend_shown = False
            for i, stroke in enumerate(down_strokes):
                if hasattr(stroke, 'fx_a') and hasattr(stroke, 'fx_b'):
                    fig.add_trace(go.Scatter(
                        x=[stroke.fx_a.dt, stroke.fx_b.dt],
                        y=[stroke.fx_a.fx, stroke.fx_b.fx],
                        mode='lines',
                        line=dict(color='orange', width=3),
                        name='向下笔' if not down_legend_shown else None,
                        showlegend=not down_legend_shown,
                        text=f'向下笔{i+1}' if show_labels else None,
                        textposition="middle center",
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
                    
                    fig.add_trace(go.Scatter(
                        x=[start_point.dt, end_point.dt],
                        y=[start_point.fx, end_point.fx],
                        mode='lines+markers',  # 添加端点标记
                        line=dict(color='purple', width=4, dash='dash'),
                        marker=dict(size=8, color='purple', symbol='diamond'),
                        name='线段' if i == 0 else None,
                        showlegend=(i == 0),
                        text=f'线段{i+1}' if show_labels else None,
                        textposition="middle center",
                        legendgroup='segments'  # 线段图例组
                    ), row=row, col=col)
                    
                    # 如果显示标注，添加线段编号
                    if show_labels:
                        mid_x = start_point.dt + (end_point.dt - start_point.dt) / 2
                        mid_y = (start_point.fx + end_point.fx) / 2
                        fig.add_annotation(
                            x=mid_x, y=mid_y,
                            text=f"XD{i+1}",
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
                    
                    fig.add_trace(go.Scatter(
                        x=[date],
                        y=[pos],
                        mode='markers',
                        marker=dict(symbol=symbol, size=12, color=color, 
                                   line=dict(color='darkgreen', width=2)),
                        name=type_name if show_legend else None,
                        text=[type_name.replace('买点', 'B')] if show_labels else None,
                        textposition="bottom center",
                        showlegend=show_legend,
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
                    
                    fig.add_trace(go.Scatter(
                        x=[date],
                        y=[pos],
                        mode='markers',
                        marker=dict(symbol=symbol, size=12, color=color, 
                                   line=dict(color='darkred', width=2)),
                        name=type_name if show_legend else None,
                        text=[type_name.replace('卖点', 'S')] if show_labels else None,
                        textposition="top center",
                        showlegend=show_legend,
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
            
            fig.add_trace(go.Scatter(
                x=top_dates,
                y=top_prices,
                mode='markers',
                marker=dict(symbol='x', size=16, color='red', line=dict(width=3)),
                name='顶背驰',
                text=['顶背驰'] * len(top_dates),
                textposition="top center",
                showlegend=True,
                legendgroup='top_divergence'
            ), row=row, col=col)
        
        # 绘制底背驰  
        if bottom_divergences:
            bottom_dates = [div['current_bi'].fx_b.dt for div in bottom_divergences]
            bottom_prices = [div['current_bi'].fx_b.fx * 0.95 for div in bottom_divergences]
            
            fig.add_trace(go.Scatter(
                x=bottom_dates,
                y=bottom_prices,
                mode='markers',
                marker=dict(symbol='x', size=16, color='green', line=dict(width=3)),
                name='底背驰',
                text=['底背驰'] * len(bottom_dates),
                textposition="bottom center",
                showlegend=True,
                legendgroup='bottom_divergence'
            ), row=row, col=col)

    def _add_pivots(self, fig, row, col, show_labels=False):
        """添加中枢区域（使用分析结果中的中枢数据）"""
        pivots = self.data.get('pivots', [])
        
        if not pivots:
            return
        
        for i, pivot in enumerate(pivots):
            # 绘制中枢区域
            fig.add_shape(
                type="rect",
                xref="x", yref="y",
                x0=pivot['start_dt'], y0=pivot['low'],
                x1=pivot['end_dt'], y1=pivot['high'],
                fillcolor="purple",
                opacity=0.2,
                layer="below",
                line_width=0,
                row=row, col=col
            )
            
            # 添加中枢边界线
            fig.add_hline(
                y=pivot['high'], 
                line_dash="dash", 
                line_color="purple", 
                opacity=0.6,
                row=row, col=col
            )
            fig.add_hline(
                y=pivot['low'], 
                line_dash="dash", 
                line_color="purple", 
                opacity=0.6,
                row=row, col=col
            )
            
            # 添加中枢标签
            if show_labels:
                fig.add_annotation(
                    x=pivot['start_dt'] + (pivot['end_dt'] - pivot['start_dt']) / 2,
                    y=pivot['center'],
                    text=f"ZS{i+1}",
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
                    x=[pivot['start_dt']],
                    y=[pivot['center']],
                    mode='markers',
                    marker=dict(
                        size=0,  # 不显示标记
                        color='purple'
                    ),
                    name='中枢区域',
                    showlegend=True,
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
            
            fig.add_trace(go.Scatter(
                x=x_data, y=macd, 
                mode='lines', name='MACD', 
                line=dict(color='blue', width=1)
            ), row=row, col=col)
            
            fig.add_trace(go.Scatter(
                x=x_data, y=signal, 
                mode='lines', name='Signal', 
                line=dict(color='orange', width=1)
            ), row=row, col=col)
            
            colors = ['red' if val >= 0 else 'green' for val in histogram]
            fig.add_trace(go.Bar(
                x=x_data, y=histogram, 
                name='Histogram', 
                marker_color=colors, 
                showlegend=False
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
            
            fig.add_trace(go.Scatter(
                x=x_data, y=rsi, 
                mode='lines', name='RSI', 
                line=dict(color='purple', width=1)
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

    def _add_statistics_panels(self, fig):
        """添加统计面板（买卖条件统计、背驰统计、中枢统计）"""
        
        # 获取统计数据
        fractals_data = self.data.get('fractals', {})
        strokes_data = self.data.get('strokes', {})
        buy_points = self.data.get('buy_points', [])
        sell_points = self.data.get('sell_points', [])
        divergences = self.data.get('divergences', [])
        
        # 1. 买卖条件统计（左下）
        buy_count = len(buy_points)
        sell_count = len(sell_points)
        
        fig.add_trace(go.Bar(
            x=['买点', '卖点'],
            y=[buy_count, sell_count],
            marker_color=['green', 'red'],
            text=[str(buy_count), str(sell_count)],
            textposition='auto',
            name='买卖点统计',
            showlegend=False
        ), row=4, col=1)
        
        # 2. 背驰统计（中下）
        top_div = len([d for d in divergences if d.get('type') == '顶背驰'])
        bottom_div = len([d for d in divergences if d.get('type') == '底背驰'])
        
        fig.add_trace(go.Bar(
            x=['顶背驰', '底背驰'],
            y=[top_div, bottom_div],
            marker_color=['red', 'green'],
            text=[str(top_div), str(bottom_div)],
            textposition='auto',
            name='背驰统计',
            showlegend=False
        ), row=4, col=2)
        
        # 3. 中枢统计（右下）
        # 从分析结果中获取正确的中枢数量
        pivots = self.data.get('pivots', [])
        pivot_count = len(pivots)
        
        fig.add_trace(go.Bar(
            x=['中枢'],
            y=[pivot_count],
            marker_color=['purple'],
            text=[str(pivot_count)],
            textposition='auto',
            name='中枢统计',
            showlegend=False
        ), row=4, col=3)
        
        # 4. 分型统计（最右下）
        top_fx_count = fractals_data.get('top_count', 0)
        bottom_fx_count = fractals_data.get('bottom_count', 0)
        
        fig.add_trace(go.Bar(
            x=['顶分型', '底分型'],
            y=[top_fx_count, bottom_fx_count],
            marker_color=['red', 'green'],
            text=[str(top_fx_count), str(bottom_fx_count)],
            textposition='auto',
            name='分型统计',
            showlegend=False
        ), row=4, col=4)

    def create_interactive_chart(self, display_options):
        """
        创建交互式Plotly图表（专业缠论分析样式）
        :param display_options: 控制显示哪些元素的字典
        """
        
        # 创建专业布局：主图 + 成交量 + MACD + 统计面板
        fig = make_subplots(
            rows=4, cols=4,
            shared_xaxes=True,
            vertical_spacing=0.05,
            horizontal_spacing=0.05,
            row_heights=[0.5, 0.2, 0.2, 0.1],  # 主图、成交量、MACD、统计
            column_widths=[0.7, 0.1, 0.1, 0.1],  # 主要图表和统计面板
            specs=[
                [{"colspan": 4}, None, None, None],  # 主图占满整行
                [{"colspan": 4}, None, None, None],  # 成交量占满整行
                [{"colspan": 4}, None, None, None],  # MACD占满整行
                [{}, {}, {}, {}]  # 统计面板分4列
            ],
            subplot_titles=[
                f"{self.stock_code} ({self.data.get('stock_name', self.stock_code)}) 缠论技术分析图",
                "成交量", "MACD指标", "", "", "", ""
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
                            show_labels=False)
        
        # 笔独立控制
        if display_options.get('show_up_bi') or display_options.get('show_down_bi'):
            self._add_strokes(fig, 1, 1,
                            show_up=display_options.get('show_up_bi'),
                            show_down=display_options.get('show_down_bi'),
                            show_labels=False)
        
        if display_options.get('show_xd'):
            self._add_segments(fig, 1, 1, show_labels=False)
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
                                    show_labels=False)
        if display_options.get('show_divergence'):
            self._add_divergence(fig, 1, 1)
        if display_options.get('show_zs'):
            self._add_pivots(fig, 1, 1, show_labels=False)
        if display_options.get('show_boll'):
            self._add_bollinger_bands(fig, 1, 1)

        # 第2行：成交量
        if display_options.get('show_volume'):
            self._add_volume(fig, 2, 1)

        # 第3行：MACD
        if display_options.get('show_macd'):
            self._add_macd(fig, 3, 1)

        # 第4行：统计面板
        self._add_statistics_panels(fig)

        # 更新坐标轴
        fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        fig.update_yaxes(title_text="MACD", row=3, col=1)
        
        # 统计面板坐标轴标题
        fig.update_yaxes(title_text="买卖条件统计", row=4, col=1, title_font_size=10)
        fig.update_yaxes(title_text="背驰统计", row=4, col=2, title_font_size=10)
        fig.update_yaxes(title_text="中枢统计", row=4, col=3, title_font_size=10)
        fig.update_yaxes(title_text="分型统计", row=4, col=4, title_font_size=10)

        # 设置专业的布局样式
        fig.update_layout(
            height=1100,  # 增加高度以容纳统计面板和图例说明
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
            margin=dict(t=80, b=120, l=60, r=60),  # 增加底部边距以容纳图例说明
            font=dict(size=10),
            title_font_size=16,
            hovermode="x unified",
            # 去掉范围选择器，保持专业外观
            xaxis_rangeslider_visible=False,
        )
        
        # 配置时间轴以移除间隙并确保全程标注
        # 对于分钟级别数据，使用category模式来避免时间间隙
        if self.kline_level in ['1h', '30m', '15m', '5m', '2m', '1m']:
            # 为分钟级别数据创建连续的时间轴
            data_count = len(self.trading_df)
            
            # 根据数据量动态调整标签数量
            if data_count <= 50:
                tick_count = min(data_count, 10)  # 少量数据显示更多标签
            elif data_count <= 150:
                tick_count = min(data_count // 6, 15)  # 中等数据量
            else:
                tick_count = min(data_count // 10, 20)  # 大量数据避免过密
            
            fig.update_xaxes(
                type='category',  # 使用category类型避免时间间隙
                categoryorder='category ascending',
                tickangle=45,
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                # 确保时间标签全程显示
                tickmode='linear',  # 线性分布时间标签
                nticks=tick_count,  # 动态调整标签数量
                tickfont=dict(size=9),  # 调整字体大小
                # 强制显示首尾标签
                tick0=0,  # 从第一个数据点开始
                dtick=max(1, data_count // tick_count)  # 计算标签间隔
            )
        else:
            # 日线及以上级别保持原有设置
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                # 移除非交易日的间隙
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),  # 隐藏周末
                ],
                # 确保时间标签均匀分布
                tickmode='linear',
                nticks=15  # 适当的标签数量
            )
        
        # 添加图例说明文本 - 分成多个部分避免遮挡
        fig.add_annotation(
            text="缠论技术分析图例说明:",
            xref="paper", yref="paper",
            x=0.01, y=-0.05,
            showarrow=False,
            font=dict(size=11, color="black", family="Arial Bold"),
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
