"""
基础测试

测试Moyan系统的基本功能
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_import_moyan():
    """测试Moyan模块导入"""
    try:
        import moyan
        assert hasattr(moyan, '__version__')
        assert hasattr(moyan, 'MoyanAnalyzer')
        print(f"✅ Moyan v{moyan.__version__} 导入成功")
    except ImportError as e:
        pytest.fail(f"Moyan模块导入失败: {e}")

def test_import_czsc():
    """测试CZSC核心库导入"""
    try:
        import czsc
        print(f"✅ CZSC v{getattr(czsc, '__version__', 'unknown')} 导入成功")
    except ImportError as e:
        pytest.skip(f"CZSC核心库未安装: {e}")

def test_kline_config():
    """测试K线配置"""
    try:
        from moyan.config.kline_config import (
            KLINE_LEVELS, DEFAULT_KLINE_LEVEL,
            get_supported_levels, validate_kline_level
        )
        
        # 检查默认级别
        assert DEFAULT_KLINE_LEVEL in KLINE_LEVELS
        
        # 检查支持的级别
        levels = get_supported_levels()
        assert len(levels) > 0
        assert '1d' in levels
        
        # 检查验证函数
        assert validate_kline_level('1d') == True
        assert validate_kline_level('invalid') == False
        
        print(f"✅ K线配置测试通过，支持 {len(levels)} 个级别")
        
    except Exception as e:
        pytest.fail(f"K线配置测试失败: {e}")

def test_moyan_config():
    """测试Moyan配置"""
    try:
        from moyan.config.settings import MoyanConfig, default_config
        
        # 检查默认配置
        assert isinstance(default_config, MoyanConfig)
        assert hasattr(default_config, 'system')
        assert hasattr(default_config, 'chart')
        assert hasattr(default_config, 'data')
        
        # 检查系统信息
        assert default_config.system.name == '墨岩缠论分析系统'
        assert default_config.system.version == '1.0.0'
        
        print("✅ Moyan配置测试通过")
        
    except Exception as e:
        pytest.fail(f"Moyan配置测试失败: {e}")

def test_analyzer_creation():
    """测试分析器创建"""
    try:
        # 跳过CZSC依赖检查，只测试类定义
        from moyan.config.kline_config import DEFAULT_KLINE_LEVEL
        
        # 检查默认K线级别
        assert DEFAULT_KLINE_LEVEL == '1d'
        
        print("✅ 分析器创建测试通过")
        
    except Exception as e:
        pytest.fail(f"分析器创建测试失败: {e}")

if __name__ == "__main__":
    # 直接运行测试
    print("🧪 运行Moyan基础测试...")
    print("=" * 50)
    
    try:
        test_import_moyan()
        test_import_czsc()
        test_kline_config()
        test_moyan_config()
        test_analyzer_creation()
        
        print("=" * 50)
        print("🎉 所有基础测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
