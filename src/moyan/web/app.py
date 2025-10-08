# src/moyan/web/app.py
"""
墨岩缠论分析系统Web界面
基于Streamlit构建的交互式股票技术分析平台
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '../../..')
src_path = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

try:
    from moyan.core.analyzer import MoyanAnalyzer
    from moyan.web.enhanced_chart import EnhancedChartGenerator
    from moyan.config.stock_database import search_stock, get_stock_info
    from moyan.config.stock_search import search_all_stocks, get_all_stock_info, get_search_engine
    from moyan.config.stock_db_builder import search_stocks_db, get_stock_info_db, get_stock_database
except ImportError as e:
    st.error(f"导入模块失败: {e}")
    st.error(f"当前工作目录: {os.getcwd()}")
    st.error(f"Python路径: {sys.path}")
    st.stop()

def create_app():
    """创建并配置Streamlit应用"""
    st.set_page_config(
        page_title="墨岩缠论分析系统",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 添加自定义CSS样式来调整左侧栏字体大小
    st.markdown("""
    <style>
    .css-1d391kg {  /* 左侧栏容器 */
        font-size: 0.8rem !important;
    }
    .stSelectbox > div > div > div {  /* 下拉框 */
        font-size: 0.8rem !important;
    }
    .stTextInput > div > div > input {  /* 文本输入框 */
        font-size: 0.8rem !important;
    }
    .stCheckbox > label {  /* 复选框标签 */
        font-size: 0.8rem !important;
    }
    .stRadio > label {  /* 单选按钮标签 */
        font-size: 0.8rem !important;
    }
    .stNumberInput > div > div > input {  /* 数字输入框 */
        font-size: 0.8rem !important;
    }
    .stDateInput > div > div > input {  /* 日期输入框 */
        font-size: 0.8rem !important;
    }
    .sidebar .markdown-text-container {  /* 左侧栏Markdown文本 */
        font-size: 0.8rem !important;
    }
    .stButton > button {  /* 按钮 */
        font-size: 0.9rem !important;
        padding: 0.3rem 0.6rem !important;
    }
    /* 左侧栏标题样式 */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        font-size: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    /* 左侧栏小标题样式 */
    .css-1d391kg .stMarkdown p strong {
        font-size: 0.85rem !important;
        font-weight: bold !important;
    }
    /* 左侧栏斜体小标题样式 */
    .css-1d391kg .stMarkdown p em {
        font-size: 0.8rem !important;
        font-style: italic !important;
        color: #666 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 标题
    st.title("📊 墨岩缠论分析系统")
    # 使用示例和数据库优势
    with st.expander("📝 本地数据库搜索指南", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 搜索示例**")
            st.markdown("**股票代码**: `000001`, `300308`, `600519`")
            st.markdown("**股票名称**: `平安银行`, `中际旭创`, `贵州茅台`") 
            st.markdown("**拼音首字母**: `payh`, `zjxc`, `gzmt`")
            st.markdown("**模糊搜索**: `银行`, `科技`, `新能源`")
            
        with col2:
            st.markdown("**💾 数据库优势**")
            st.markdown("✅ **4298只A股全覆盖**")
            st.markdown("⚡ **毫秒级搜索响应**")
            st.markdown("🔍 **智能拼音匹配**")
            st.markdown("📊 **精确市场分类**")
            st.markdown("🛡️ **离线可用无网络依赖**")
    
    st.markdown("---")
    
    # 侧边栏配置
    st.sidebar.header("📋 分析配置")
    
    # 智能股票搜索（本地数据库）
    st.sidebar.markdown("### 📊 股票选择")
    
    # 显示数据库状态
    with st.sidebar.expander("💾 本地数据库状态", expanded=False):
        try:
            db = get_stock_database()
            stats = db.get_stats()
            if stats.get('total', 0) > 0:
                st.success(f"✅ 本地数据库: {stats['total']} 只A股")
                st.info("📊 市场分布:")
                for market, count in stats.get('by_market', {}).items():
                    st.text(f"  {market}: {count} 只")
                    
                # 添加在线数据源备用
                engine = get_search_engine()
                online_count = len(engine.stock_cache)
                if online_count > 0:
                    st.info(f"🌐 在线备用: {online_count} 只股票")
                else:
                    if st.button("🔄 更新在线数据"):
                        engine.update_stock_cache()
                        st.rerun()
            else:
                st.warning("⚠️ 本地数据库为空")
                if st.button("🏗️ 重建数据库"):
                    from moyan.config.stock_db_builder import build_stock_database
                    with st.spinner("正在重建数据库..."):
                        build_stock_database()
                    st.success("数据库重建完成!")
                    st.rerun()
        except Exception as e:
            st.error(f"数据库连接失败: {e}")
            st.info("将使用在线API作为备用数据源")
    
    # 创建搜索输入框
    search_query = st.sidebar.text_input(
        "股票搜索 (本地数据库4298只)",
        value="",
        placeholder="如: 中际旭创, 300308, zjxc",
        help="优先从本地数据库搜索4298只A股，支持代码、名称、拼音首字母"
    )
    
    # 如果有搜索内容，显示搜索结果
    stock_code = ""
    selected_stock_name = ""
    
    if search_query:
        # 优先使用本地数据库搜索
        search_results = []
        
        try:
            # 1. 本地数据库搜索（优先）
            db_results = search_stocks_db(search_query, limit=8)
            for result in db_results:
                search_results.append({
                    'code': result['code'],
                    'name': result['name'],
                    'pinyin': result.get('pinyin', ''),
                    'match_type': result['match_type'],
                    'source': 'database',
                    'market': result.get('market', ''),
                    'price': result.get('price', 0)
                })
            
            # 2. 如果本地数据库结果不足，补充在线搜索
            if len(search_results) < 5:
                online_results = search_all_stocks(search_query, limit=5)
                for result in online_results:
                    # 避免重复
                    if not any(r['code'] == result['code'] for r in search_results):
                        search_results.append(result)
                        
        except Exception as e:
            st.sidebar.warning(f"本地数据库搜索失败: {e}")
            # 备用：使用在线搜索
            search_results = search_all_stocks(search_query, limit=10)
        
        if search_results:
            # 创建选择选项
            options = []
            for result in search_results:
                source_icon = "💾" if result['source'] == 'database' else "🏠" if result['source'] == 'local' else "🌐"
                market_info = f"[{result.get('market', '')}]" if result.get('market') else ""
                price_info = f"¥{result.get('price', 0):.2f}" if result.get('price', 0) > 0 else ""
                
                display_text = f"{source_icon} {result['code']} - {result['name']} {market_info} {price_info}"
                options.append(display_text)
            
            if len(options) == 1:
                # 只有一个结果，自动选择
                selected_option = options[0]
                stock_code = search_results[0]['code']
                selected_stock_name = search_results[0]['name']
                st.sidebar.success(f"✅ 已选择: {search_results[0]['code']} - {search_results[0]['name']}")
            else:
                # 多个结果，让用户选择
                selected_option = st.sidebar.selectbox(
                    f"选择股票 (找到{len(search_results)}个结果)",
                    options,
                    help="💾=本地数据库 🏠=常用股票 🌐=在线数据"
                )
                
                if selected_option:
                    # 解析选择的股票代码 (更稳健的解析)
                    parts = selected_option.split(' - ')
                    if len(parts) >= 2:
                        stock_code = parts[0].split(' ')[-1]  # 获取代码部分
                        selected_stock_name = parts[1].split(' [')[0]  # 获取名称部分
        else:
            st.sidebar.warning(f"⚠️ 未找到匹配的股票: {search_query}")
            st.sidebar.info("💡 提示：本地数据库包含4298只A股，支持模糊搜索")
    
    # 显示当前选择的股票
    if stock_code:
        # 优先从本地数据库获取信息
        stock_info = get_stock_info_db(stock_code)
        if not stock_info:
            # 备用1：从在线API获取
            stock_info = get_all_stock_info(stock_code)
        if not stock_info:
            # 备用2：从常用股票库获取
            stock_info = get_stock_info(stock_code)
        
        if stock_info:
            price_str = f" (¥{stock_info['price']:.2f})" if stock_info.get('price', 0) > 0 else ""
            market_str = f" [{stock_info.get('market', '')}]" if stock_info.get('market') else ""
            st.sidebar.info(f"🎯 当前股票: {stock_code} - {stock_info['name']}{market_str}{price_str}")
        else:
            st.sidebar.info(f"🎯 当前股票: {stock_code} - {selected_stock_name}")
    else:
        st.sidebar.info("请输入股票搜索关键词")
    
    # K线级别选择
    kline_level = st.sidebar.selectbox(
        "K线级别",
        options=["1d", "1wk", "1mo", "1h", "30m", "15m"],
        index=0,
        help="选择K线数据的时间级别"
    )
    
    # 时间范围设置
    st.sidebar.subheader("📅 时间范围")
    time_mode = st.sidebar.radio(
        "时间模式",
        ["最近N天", "自定义范围"],
        index=0
    )
    
    if time_mode == "最近N天":
        days_input = st.sidebar.number_input(
            "天数",
            min_value=30,
            max_value=1000,
            value=120,
            step=30,
            help="获取最近N天的数据"
        )
        start_date_str = None
        end_date_str = None
    else:
        start_date = st.sidebar.date_input(
            "开始日期",
            value=datetime(2025, 1, 1),
            max_value=datetime.now()
        )
        end_date = st.sidebar.date_input(
            "结束日期",
            value=datetime.now(),
            max_value=datetime.now()
        )
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        days_input = None
    
    # 显示选项
    st.sidebar.subheader("🎨 显示选项")
    
    # 基础图表
    show_kline = st.sidebar.checkbox("K线图", value=True)
    show_volume = st.sidebar.checkbox("成交量", value=True)
    show_ma = st.sidebar.checkbox("移动平均线", value=True)
    
    # 缠论要素
    st.sidebar.markdown("**缠论要素**")
    
    # 分型控制
    st.sidebar.markdown("*分型*")
    show_top_fx = st.sidebar.checkbox("顶分型", value=True)
    show_bottom_fx = st.sidebar.checkbox("底分型", value=True)
    
    # 笔控制
    st.sidebar.markdown("*笔*")
    show_up_bi = st.sidebar.checkbox("上升笔", value=True)
    show_down_bi = st.sidebar.checkbox("下降笔", value=True)
    
    # 线段和中枢
    st.sidebar.markdown("*线段和中枢*")
    show_xd = st.sidebar.checkbox("线段", value=True)
    show_zs = st.sidebar.checkbox("中枢", value=True)
    
    # 买卖点
    st.sidebar.markdown("**买卖点**")
    
    # 买点分类控制
    st.sidebar.markdown("*买点类型*")
    show_buy1 = st.sidebar.checkbox("第一类买点", value=True)
    show_buy2 = st.sidebar.checkbox("第二类买点", value=True)
    show_buy3 = st.sidebar.checkbox("第三类买点", value=True)
    
    # 卖点分类控制
    st.sidebar.markdown("*卖点类型*")
    show_sell1 = st.sidebar.checkbox("第一类卖点", value=True)
    show_sell2 = st.sidebar.checkbox("第二类卖点", value=True)
    show_sell3 = st.sidebar.checkbox("第三类卖点", value=True)
    
    # 背驰
    show_divergence = st.sidebar.checkbox("背驰标记", value=True)
    
    # 技术指标
    st.sidebar.markdown("**技术指标**")
    show_macd = st.sidebar.checkbox("MACD", value=True)
    show_rsi = st.sidebar.checkbox("RSI", value=False)
    show_boll = st.sidebar.checkbox("布林带", value=False)
    
    # 分析选项和按钮
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        analyze_button = st.button("🚀 开始分析", use_container_width=True)
    with col2:
        use_test_data = st.checkbox("测试", help="使用模拟数据演示")
    
    if analyze_button:
        if not stock_code:
            st.sidebar.error("请输入股票代码！")
        else:
            with st.spinner("⏳ 正在获取数据并进行缠论分析..."):
                try:
                    if use_test_data:
                        # 使用测试数据
                        from moyan.utils.test_data import create_test_analysis_result
                        
                        # 获取股票名称
                        stock_info = get_stock_info_db(stock_code)
                        stock_name = stock_info['name'] if stock_info else selected_stock_name or f"股票{stock_code}"
                        
                        result = create_test_analysis_result(stock_code, stock_name)
                        st.info("ℹ️ 使用测试数据进行演示分析")
                    else:
                        # 使用真实数据
                        analyzer = MoyanAnalyzer(kline_level=kline_level)
                        result = analyzer.analyze(
                            stock_code=stock_code,
                            start_date=start_date_str,
                            end_date=end_date_str,
                            days=days_input
                        )
                    
                    if result['success']:
                        st.success("✅ 分析完成！")
                        
                        display_options = {
                            'show_kline': show_kline,
                            'show_volume': show_volume,
                            'show_ma': show_ma,
                            'show_top_fx': show_top_fx,
                            'show_bottom_fx': show_bottom_fx,
                            'show_up_bi': show_up_bi,
                            'show_down_bi': show_down_bi,
                            'show_xd': show_xd,
                            'show_buy1': show_buy1,
                            'show_buy2': show_buy2,
                            'show_buy3': show_buy3,
                            'show_sell1': show_sell1,
                            'show_sell2': show_sell2,
                            'show_sell3': show_sell3,
                            'show_divergence': show_divergence,
                            'show_zs': show_zs,
                            'show_macd': show_macd,
                            'show_rsi': show_rsi,
                            'show_boll': show_boll,
                        }
                        
                        display_analysis_results(result, display_options)
                    else:
                        error_msg = result.get('error', '未知错误')
                        st.error(f"❌ 分析失败: {error_msg}")
                        
                        # 提供详细的错误说明和建议
                        if "Rate limited" in error_msg or "Too Many Requests" in error_msg:
                            st.warning("⚠️ 数据接口被限流，请稍后重试")
                            st.info("💡 建议：")
                            st.info("- 等待1-2分钟后重新尝试")
                            st.info("- 或者尝试分析其他股票")
                            st.info("- 本地数据库包含4298只A股供选择")
                        elif "未获取到数据" in error_msg:
                            st.warning("⚠️ 无法获取股票数据")
                            st.info("💡 可能原因：")
                            st.info("- 股票代码不存在或已退市")
                            st.info("- 网络连接问题")
                            st.info("- 数据源暂时不可用")
                        else:
                            st.info("💡 建议：检查股票代码是否正确，或尝试其他股票")
                        
                except Exception as e:
                    st.error(f"❌ 分析过程中出现异常: {str(e)}")

def display_analysis_results(result, display_options):
    """显示分析结果"""
    data = result['data']
    # 确保股票名称不为空
    stock_name = data.get('stock_name', '')
    if not stock_name or stock_name == 'undefined':
        stock_name = result.get('stock_code', '未知股票')
    
    st.subheader(f"📈 {stock_name} ({result['stock_code']}) - {result['kline_name']}分析")
    
    # 基本统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("数据期间", f"{data['data_start']} ~ {data['data_end']}")
    with col2:
        st.metric("数据量", f"{data['total_bars']} 根K线")
    with col3:
        st.metric("分型数量", f"{data['fx_count']} 个")
    with col4:
        st.metric("笔数量", f"{data['bi_count']} 笔")
    
    # 尝试生成交互式图表
    try:
        chart_generator = EnhancedChartGenerator(result)
        fig = chart_generator.create_interactive_chart(display_options)
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
        })
    except Exception as e:
        st.error(f"❌ 图表生成失败: {str(e)}")
        # 提供基础信息作为替代
        st.write("📊 **原始数据概览**")
        if 'raw_df' in data and data['raw_df'] is not None:
            st.dataframe(data['raw_df'].tail(10))
    
    # 详细分析数据
    create_analysis_tabs(data)

def create_analysis_tabs(data):
    """创建分析结果标签页"""
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 基本信息", "🎯 分型分析", "📈 笔线段", "🏛️ 中枢分析", "🔍 买卖点"])
    
    with tab1:
        st.write("### 📊 股票基本信息")
        info_data = {
            "项目": ["股票代码", "股票名称", "数据开始", "数据结束", "总K线数", "分型数量", "笔数量", "线段数量", "中枢数量"],
            "值": [
                data.get('stock_code', 'N/A'),
                data.get('stock_name', 'N/A'),
                data.get('data_start', 'N/A'),
                data.get('data_end', 'N/A'),
                data.get('total_bars', 'N/A'),
                data.get('fx_count', 'N/A'),
                data.get('bi_count', 'N/A'),
                data.get('xd_count', 'N/A'),
                data.get('pivot_count', 'N/A')
            ]
        }
        st.table(pd.DataFrame(info_data))
    
    with tab2:
        st.write("### 🎯 分型分析")
        st.write("分型是缠论中最基础的概念，表示局部高点或低点。")
        if data.get('fx_count', 0) > 0:
            st.write(f"- 总计发现 **{data['fx_count']}** 个分型")
            st.write("- 分型类型包括顶分型(▼)和底分型(▲)")
        else:
            st.write("暂无分型数据")
    
    with tab3:
        st.write("### 📈 笔和线段")
        st.write("笔是连接相邻分型的线段，线段是更高级别的结构。")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**笔信息**")
            if data.get('bi_count', 0) > 0:
                st.write(f"- 总计 **{data['bi_count']}** 笔")
                st.write("- 笔的方向有向上(蓝色)和向下(橙色)")
            else:
                st.write("暂无笔数据")
        
        with col2:
            st.write("**线段信息**")
            if data.get('xd_count', 0) > 0:
                st.write(f"- 总计 **{data['xd_count']}** 线段")
                st.write("- 线段用紫色虚线表示")
            else:
                st.write("暂无线段数据")
    
    with tab4:
        st.write("### 🏛️ 中枢分析")
        st.write("中枢是缠论的核心概念，表示价格在一定区间内的震荡整理。")
        
        pivots = data.get('pivots', [])
        pivot_count = data.get('pivot_count', 0)
        
        if pivot_count > 0:
            st.write(f"- 总计识别 **{pivot_count}** 个中枢")
            st.write("- 中枢用紫色半透明区域表示")
            st.write("- 中枢的形成需要至少3笔的价格重叠")
            
            if pivots:
                st.write("**中枢详情**")
                for i, pivot in enumerate(pivots, 1):
                    duration = (pivot['end_dt'] - pivot['start_dt']).days
                    price_range = pivot['high'] - pivot['low']
                    range_pct = (price_range / pivot['center']) * 100
                    
                    with st.expander(f"中枢 {i} - {pivot.get('type', '标准中枢')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**时间范围**: {pivot['start_dt'].strftime('%Y-%m-%d')} ~ {pivot['end_dt'].strftime('%Y-%m-%d')}")
                            st.write(f"**持续时间**: {duration} 天")
                            st.write(f"**参与笔数**: {pivot.get('bi_count', 3)} 笔")
                        with col2:
                            st.write(f"**价格区间**: {pivot['low']:.2f} ~ {pivot['high']:.2f}")
                            st.write(f"**中枢中心**: {pivot['center']:.2f}")
                            st.write(f"**波动幅度**: {range_pct:.2f}%")
        else:
            st.write("- 暂未识别到有效中枢")
            st.write("- 中枢的形成需要足够的笔数量和价格重叠")
    
    with tab5:
        st.write("### 🔍 买卖点分析")
        st.write("根据缠论理论识别的买卖点信号。")
        
        buy_points = data.get('buy_points', [])
        sell_points = data.get('sell_points', [])
        
        if buy_points or sell_points:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**买点**")
                if buy_points:
                    for bp in buy_points[-5:]:  # 显示最近5个
                        st.write(f"- {bp['date']}: {bp['type']}类买点 (价格: {bp['price']:.2f})")
                else:
                    st.write("暂无买点信号")
            
            with col2:
                st.write("**卖点**")
                if sell_points:
                    for sp in sell_points[-5:]:  # 显示最近5个
                        st.write(f"- {sp['date']}: {sp['type']}类卖点 (价格: {sp['price']:.2f})")
                else:
                    st.write("暂无卖点信号")
        else:
            st.write("暂无买卖点数据")

# 主程序入口
if __name__ == "__main__":
    create_app()
