"""
墨岩缠论分析系统 (Moyan CZSC Analysis System)

基于CZSC核心库构建的专业股票技术分析应用平台

主要功能:
- 缠论技术分析 (分型、笔、线段、背驰、买卖点)
- 多时间周期支持 (15m, 30m, 1d, 1wk)
- MACD技术指标集成
- Mac高分辨率显示器优化
- 专业级图表输出和报告生成

作者: CZSC Community
版本: 1.0.0
许可: MIT License
"""

__version__ = "1.0.0"
__author__ = "CZSC Community"
__email__ = "czsc@example.com"
__license__ = "MIT"

# 导入核心组件
from .core.analyzer import MoyanAnalyzer
from .analyzer.auto_analyzer import AutoAnalyzer
from .config.settings import MoyanConfig
from .config.kline_config import KLINE_LEVELS, DEFAULT_KLINE_LEVEL

# 导入工具函数
from .utils import create_chart, save_chart, generate_report, export_report

__all__ = [
    # 版本信息
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    
    # 核心组件
    "MoyanAnalyzer",
    "AutoAnalyzer", 
    "MoyanConfig",
    
    # 配置
    "KLINE_LEVELS",
    "DEFAULT_KLINE_LEVEL",
    
    # 工具函数
    "create_chart",
    "save_chart",
    "generate_report", 
    "export_report",
]

def welcome():
    """显示欢迎信息"""
    print("=" * 70)
    print("🎯 墨岩缠论分析系统 (Moyan CZSC Analysis System)")
    print("=" * 70)
    print(f"📊 版本: {__version__}")
    print(f"👥 作者: {__author__}")
    print(f"📄 许可: {__license__}")
    print()
    print("✨ 核心功能:")
    print("  🎯 缠论技术分析 (基于CZSC核心库)")
    print("  📈 多时间周期支持 (15m/30m/1d/1wk)")
    print("  📊 MACD技术指标集成")
    print("  🖥️ Mac高DPI显示优化")
    print("  📄 专业级报告生成")
    print()
    print("🚀 快速开始:")
    print("  from moyan import MoyanAnalyzer")
    print("  analyzer = MoyanAnalyzer()")
    print("  analyzer.analyze('002167')")
    print()
    print("📚 更多信息: https://github.com/waditu/czsc")
    print("=" * 70)

# 检查CZSC依赖
def check_czsc_dependency():
    """检查CZSC库依赖"""
    try:
        import czsc
        czsc_version = getattr(czsc, '__version__', 'unknown')
        print(f"✅ CZSC核心库已加载: v{czsc_version}")
        return True
    except ImportError as e:
        print(f"❌ CZSC核心库未安装: {e}")
        print("请运行: pip install czsc>=0.9.8")
        return False

# 自动检查依赖
if not check_czsc_dependency():
    import warnings
    warnings.warn(
        "CZSC核心库未正确安装，部分功能可能不可用。请运行: pip install czsc>=0.9.8",
        ImportWarning
    )
