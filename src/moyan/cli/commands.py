"""
CLI命令实现

实现各种命令行命令的具体逻辑
"""

import os
import sys
from typing import Any
from pathlib import Path

def analyze_command(args: Any) -> int:
    """
    执行分析命令
    
    Args:
        args: 命令行参数
        
    Returns:
        int: 退出码
    """
    try:
        from ..core.analyzer import MoyanAnalyzer
        
        print(f"🚀 开始分析股票: {args.stock_code}")
        print(f"📈 K线级别: {args.kline}")
        
        # 创建分析器
        analyzer = MoyanAnalyzer(kline_level=args.kline)
        
        # 执行分析
        result = analyzer.analyze(
            stock_code=args.stock_code,
            start_date=args.start,
            end_date=args.end,
            days=args.days
        )
        
        if result['success']:
            print(f"✅ 分析完成: {args.stock_code}")
            
            # 显示摘要
            summary = analyzer.get_analysis_summary(result)
            print("\n📊 分析摘要:")
            for key, value in summary.items():
                if key != 'stock_code':
                    print(f"  {key}: {value}")
            
            # 显示输出文件
            if result.get('charts'):
                print(f"\n📈 图表文件: {result['charts']['main_chart']}")
            if result.get('reports'):
                print(f"📄 报告文件: {result['reports']['markdown']}")
            
            return 0
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            return 1
            
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return 1

def batch_command(args: Any) -> int:
    """
    执行批量分析命令
    
    Args:
        args: 命令行参数
        
    Returns:
        int: 退出码
    """
    try:
        from ..core.analyzer import MoyanAnalyzer
        
        # 解析股票代码列表
        stock_codes = [code.strip() for code in args.stock_codes.split(',')]
        
        print(f"🚀 开始批量分析 {len(stock_codes)} 只股票")
        print(f"📈 K线级别: {args.kline}")
        print(f"📋 股票列表: {', '.join(stock_codes)}")
        
        # 创建分析器
        analyzer = MoyanAnalyzer(kline_level=args.kline)
        
        # 执行批量分析
        results = analyzer.batch_analyze(
            stock_codes=stock_codes,
            start_date=args.start,
            end_date=args.end
        )
        
        # 统计结果
        success_count = sum(1 for r in results.values() if r.get('success', False))
        total_count = len(results)
        
        print(f"\n📊 批量分析结果: {success_count}/{total_count} 成功")
        
        # 显示详细结果
        print("\n📋 详细结果:")
        for stock_code, result in results.items():
            if result.get('success', False):
                summary = analyzer.get_analysis_summary(result)
                price = summary.get('current_price', 'N/A')
                trend = summary.get('trend_status', 'N/A')
                print(f"  ✅ {stock_code}: 价格={price}, 趋势={trend}")
            else:
                error = result.get('error', '未知错误')
                print(f"  ❌ {stock_code}: {error}")
        
        return 0 if success_count > 0 else 1
        
    except Exception as e:
        print(f"❌ 批量分析失败: {e}")
        return 1

def web_command(args: Any) -> int:
    """
    执行Web界面命令
    
    Args:
        args: 命令行参数
        
    Returns:
        int: 退出码
    """
    try:
        print(f"🌐 启动Web界面...")
        print(f"🔗 地址: http://{args.host}:{args.port}")
        print("💡 提示: 按 Ctrl+C 停止服务")
        
        # 检查streamlit是否安装
        try:
            import streamlit
        except ImportError:
            print("❌ Streamlit未安装，请运行: pip install streamlit")
            return 1
        
        # 查找streamlit应用文件
        app_file = Path(__file__).parent.parent / "web" / "streamlit_app.py"
        
        if not app_file.exists():
            print(f"❌ 找不到Web应用文件: {app_file}")
            return 1
        
        # 启动streamlit
        import subprocess
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(app_file),
            "--server.port", str(args.port),
            "--server.address", args.host,
            "--server.headless", "true"
        ]
        
        return subprocess.call(cmd)
        
    except Exception as e:
        print(f"❌ Web界面启动失败: {e}")
        return 1

def info_command(args: Any) -> int:
    """
    执行信息显示命令
    
    Args:
        args: 命令行参数
        
    Returns:
        int: 退出码
    """
    try:
        from ..config.settings import default_config
        from ..config.kline_config import get_supported_levels
        
        # 显示系统信息
        print("=" * 70)
        print(f"🎯 {default_config.system.name}")
        print("=" * 70)
        print(f"📊 版本: {default_config.system.version}")
        print(f"👥 作者: {default_config.system.author}")
        print(f"📝 描述: {default_config.system.description}")
        print()
        
        # 显示功能特性
        print("✨ 核心功能:")
        for feature in default_config.system.features:
            print(f"  • {feature}")
        print()
        
        # 显示支持的K线级别
        print("📈 支持的K线级别:")
        for level in get_supported_levels():
            from ..config.kline_config import get_kline_config
            config = get_kline_config(level)
            print(f"  • {level}: {config['name']} - {config['description']}")
        print()
        
        # 检查依赖库
        if args.check_deps:
            print("🔍 依赖库检查:")
            
            dependencies = [
                ('czsc', 'CZSC核心库'),
                ('pandas', '数据处理'),
                ('numpy', '数值计算'),
                ('matplotlib', '图表绘制'),
                ('yfinance', '数据获取'),
                ('streamlit', 'Web界面 (可选)'),
                ('plotly', '交互图表 (可选)'),
            ]
            
            for pkg_name, description in dependencies:
                try:
                    pkg = __import__(pkg_name)
                    version = getattr(pkg, '__version__', 'unknown')
                    print(f"  ✅ {pkg_name} v{version} - {description}")
                except ImportError:
                    print(f"  ❌ {pkg_name} - {description} (未安装)")
        
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"❌ 信息显示失败: {e}")
        return 1

def web_command(args):
    """启动Web界面"""
    print("🌐 启动墨岩缠论分析系统Web界面")
    print("=" * 60)
    
    try:
        # 检查依赖
        try:
            import streamlit
            print(f"✅ Streamlit v{streamlit.__version__} 已安装")
        except ImportError:
            print("❌ Streamlit未安装，请运行: pip install streamlit")
            return 1
        
        try:
            import plotly
            print(f"✅ Plotly v{plotly.__version__} 已安装")
        except ImportError:
            print("❌ Plotly未安装，请运行: pip install plotly")
            return 1
        
        # 启动Web应用
        from ..web.app import run_web_app
        
        host = getattr(args, 'host', 'localhost')
        port = getattr(args, 'port', 8501)
        
        print(f"📍 地址: http://{host}:{port}")
        print("💡 按 Ctrl+C 停止服务")
        print("🔄 正在启动...")
        
        # 直接运行streamlit应用
        import streamlit.web.cli as stcli
        import sys
        from pathlib import Path
        
        # 获取web应用文件路径
        web_app_path = Path(__file__).parent.parent / "web" / "app.py"
        
        # 构建streamlit运行参数
        sys.argv = [
            "streamlit",
            "run",
            str(web_app_path),
            "--server.address", host,
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light"
        ]
        
        # 启动streamlit
        stcli.main()
        
    except KeyboardInterrupt:
        print("\n👋 Web服务已停止")
        return 0
    except Exception as e:
        print(f"❌ 启动Web界面失败: {e}")
        return 1
