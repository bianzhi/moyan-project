# CZSC库更新管理指南

本指南详细说明当CZSC核心库有更新时，Moyan项目如何管理和应用这些更新。

## 🎯 更新机制概述

Moyan项目通过`pyproject.toml`中的依赖声明来管理CZSC版本，支持多种更新策略以平衡稳定性和功能性。

## 📋 更新场景分类

### 1️⃣ 兼容性更新 (Patch Updates)
**例子**: 0.10.2 → 0.10.3
- **特点**: Bug修复、性能优化、不改变API
- **风险**: 低
- **建议**: 自动更新

### 2️⃣ 功能性更新 (Minor Updates)  
**例子**: 0.10.x → 0.11.0
- **特点**: 新增功能、可能有新API、向后兼容
- **风险**: 中等
- **建议**: 测试后更新

### 3️⃣ 破坏性更新 (Major Updates)
**例子**: 0.x.x → 1.0.0
- **特点**: API变更、可能不兼容
- **风险**: 高
- **建议**: 仔细评估后手动更新

### 4️⃣ 安全性更新 (Security Updates)
**例子**: 修复安全漏洞的任何版本
- **特点**: 修复安全问题
- **风险**: 不更新风险更高
- **建议**: 立即更新

## ⚙️ 版本控制策略

### 当前配置 (宽松策略)

```toml
# pyproject.toml
[project]
dependencies = [
    "czsc>=0.9.8",  # 接受任何 >= 0.9.8 的版本
]
```

**优点**: 
- 自动获得bug修复和新功能
- 减少维护工作量

**缺点**: 
- 可能引入不兼容的变更
- 行为可能发生意外变化

### 推荐配置 (兼容性策略)

```toml
# pyproject.toml
[project]
dependencies = [
    "czsc~=0.10.0",  # 只接受 0.10.x 版本的更新
]
```

**优点**: 
- 自动获得补丁更新
- 避免破坏性变更
- 行为相对稳定

**缺点**: 
- 需要手动升级到新的minor版本
- 可能错过重要的新功能

### 严格配置 (锁定策略)

```toml
# pyproject.toml
[project]
dependencies = [
    "czsc==0.10.2",  # 锁定到特定版本
]
```

**优点**: 
- 完全可预测的行为
- 避免任何意外变更

**缺点**: 
- 错过所有更新 (包括安全修复)
- 需要手动管理所有更新

### 范围配置 (平衡策略)

```toml
# pyproject.toml
[project]
dependencies = [
    "czsc>=0.9.8,<1.0",  # 0.9.8 到 0.x.x
]
```

**优点**: 
- 获得功能更新和修复
- 避免主要版本的破坏性变更

**缺点**: 
- 仍有潜在的不兼容风险

## 🔄 实际更新操作流程

### 方法一: 检查并手动更新

```bash
# 1. 检查当前安装的CZSC版本
pip show czsc

# 2. 检查可用的新版本
pip index versions czsc

# 3. 检查更新日志
# 访问: https://github.com/waditu/czsc/releases

# 4. 在测试环境中更新
pip install --upgrade czsc

# 5. 运行兼容性测试
python tests/test_basic.py
moyan analyze 002167 --kline 1d

# 6. 如果测试通过，更新生产环境
```

### 方法二: 自动更新脚本

创建 `scripts/update_czsc.sh`:

```bash
#!/bin/bash
# CZSC自动更新脚本

echo "🔄 CZSC更新检查开始..."

# 获取当前版本
CURRENT_VERSION=$(pip show czsc | grep Version | cut -d' ' -f2)
echo "📦 当前CZSC版本: $CURRENT_VERSION"

# 检查最新版本
LATEST_VERSION=$(pip index versions czsc | head -1 | cut -d'(' -f2 | cut -d')' -f1)
echo "🚀 最新CZSC版本: $LATEST_VERSION"

if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    echo "📥 发现新版本，开始更新..."
    
    # 备份当前环境
    pip freeze > requirements_backup.txt
    
    # 更新CZSC
    pip install --upgrade czsc
    
    # 运行测试
    echo "🧪 运行兼容性测试..."
    if python tests/test_basic.py; then
        echo "✅ 更新成功，所有测试通过"
        rm requirements_backup.txt
    else
        echo "❌ 测试失败，回滚到之前版本"
        pip install czsc==$CURRENT_VERSION
        echo "💡 请查看更新日志并手动处理兼容性问题"
    fi
else
    echo "✅ 已是最新版本，无需更新"
fi
```

### 方法三: 使用requirements.txt锁定版本

```bash
# 1. 生成当前环境的精确版本
pip freeze | grep czsc > czsc_version.txt

# 2. 在requirements.txt中锁定版本
echo "czsc==0.10.2" >> requirements.txt

# 3. 需要更新时修改requirements.txt
# 4. 重新安装
pip install -r requirements.txt
```

## 🧪 兼容性测试策略

### 1. 基础功能测试

```python
# tests/test_czsc_compatibility.py
import pytest
from moyan import MoyanAnalyzer

def test_basic_analysis():
    """测试基础分析功能"""
    analyzer = MoyanAnalyzer(kline_level="1d")
    result = analyzer.analyze("000001")
    assert result["status"] == "success"
    assert "current_price" in result["analysis_data"]

def test_all_kline_levels():
    """测试所有K线级别"""
    levels = ["15m", "30m", "1h", "1d", "1wk", "1mo"]
    analyzer = MoyanAnalyzer()
    
    for level in levels:
        analyzer.kline_level = level
        # 确保配置加载正常
        assert analyzer.kline_config["name"] is not None

def test_data_format_compatibility():
    """测试数据格式兼容性"""
    from moyan.analyzer.auto_analyzer import AutoAnalyzer
    analyzer = AutoAnalyzer()
    
    # 模拟数据转换
    test_data = {
        'Open': [10.0], 'High': [11.0], 
        'Low': [9.0], 'Close': [10.5], 'Volume': [1000]
    }
    # 确保转换函数正常工作
    assert hasattr(analyzer, 'convert_to_czsc_format')
```

### 2. API兼容性测试

```python
# tests/test_api_compatibility.py
def test_czsc_imports():
    """测试CZSC导入兼容性"""
    try:
        import czsc
        from czsc import CZSC, RawBar
        assert hasattr(czsc, '__version__')
        assert CZSC is not None
        assert RawBar is not None
    except ImportError as e:
        pytest.fail(f"CZSC导入失败: {e}")

def test_czsc_core_api():
    """测试CZSC核心API"""
    from czsc import RawBar, CZSC
    import pandas as pd
    
    # 创建测试数据
    bars = [
        RawBar(symbol="TEST", id=i, freq="1d", 
               dt=pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
               open=10+i, close=10+i+0.5, high=11+i, low=9+i, 
               vol=1000+i*100, amount=10000+i*1000)
        for i in range(10)
    ]
    
    # 测试CZSC核心功能
    c = CZSC(bars)
    assert hasattr(c, 'fx_list')
    assert hasattr(c, 'bi_list')
    assert len(c.bars_raw) == 10
```

## 📊 版本兼容性矩阵

| Moyan版本 | 支持的CZSC版本 | 状态 | 说明 |
|-----------|----------------|------|------|
| 1.0.0 | 0.9.8 - 0.10.x | ✅ 稳定 | 当前版本 |
| 1.0.1 | 0.9.8 - 0.11.x | 🧪 测试中 | 计划版本 |
| 1.1.0 | 0.10.0 - 0.12.x | 📋 规划中 | 未来版本 |

## 🚨 破坏性更新处理

### 识别破坏性更新

1. **版本号变化**: 主版本号增加 (0.x.x → 1.0.0)
2. **更新日志**: 包含"BREAKING CHANGE"关键词
3. **API变化**: 导入路径、函数签名变化
4. **行为变化**: 相同输入产生不同输出

### 处理步骤

```bash
# 1. 创建测试分支
git checkout -b test-czsc-update

# 2. 在隔离环境中测试
conda create -n moyan_test python=3.11 -y
conda activate moyan_test
pip install -e .

# 3. 更新CZSC到新版本
pip install czsc==<new_version>

# 4. 运行完整测试套件
pytest tests/ -v

# 5. 运行实际分析测试
moyan analyze 002167 --kline 1d
moyan analyze 300308 --kline 15m

# 6. 检查输出差异
diff old_output/ new_output/

# 7. 如果需要修改代码
# 更新 src/moyan/ 中的相关代码

# 8. 更新pyproject.toml中的版本要求
# 9. 更新文档和测试
# 10. 合并到主分支
```

## 🔔 更新通知机制

### 1. GitHub Actions自动检查

```yaml
# .github/workflows/check-czsc-updates.yml
name: Check CZSC Updates
on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一上午9点检查
  
jobs:
  check-updates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Check for CZSC updates
        run: |
          pip install czsc
          CURRENT=$(pip show czsc | grep Version | cut -d' ' -f2)
          LATEST=$(pip index versions czsc | head -1 | cut -d'(' -f2 | cut -d')' -f1)
          
          if [ "$CURRENT" != "$LATEST" ]; then
            echo "🔔 CZSC新版本可用: $LATEST (当前: $CURRENT)"
            # 可以发送通知到Slack、邮件等
          fi
```

### 2. 手动检查脚本

```python
# scripts/check_czsc_updates.py
import subprocess
import requests
import json

def check_czsc_updates():
    """检查CZSC更新"""
    # 获取当前版本
    result = subprocess.run(['pip', 'show', 'czsc'], 
                          capture_output=True, text=True)
    current_version = None
    for line in result.stdout.split('\n'):
        if line.startswith('Version:'):
            current_version = line.split()[-1]
            break
    
    # 获取PyPI最新版本
    response = requests.get('https://pypi.org/pypi/czsc/json')
    latest_version = response.json()['info']['version']
    
    print(f"📦 当前CZSC版本: {current_version}")
    print(f"🚀 最新CZSC版本: {latest_version}")
    
    if current_version != latest_version:
        print("🔔 发现新版本！")
        print("📋 更新命令: pip install --upgrade czsc")
        print("📖 更新日志: https://github.com/waditu/czsc/releases")
        return True
    else:
        print("✅ 已是最新版本")
        return False

if __name__ == "__main__":
    check_czsc_updates()
```

## 📋 更新最佳实践

### 1. 生产环境更新流程

```bash
# 生产环境更新检查清单
□ 在开发环境中测试新版本
□ 运行完整的测试套件
□ 检查更新日志中的破坏性变更
□ 备份当前环境配置
□ 在预生产环境中验证
□ 准备回滚方案
□ 执行生产环境更新
□ 验证核心功能正常
□ 监控运行状态
```

### 2. 版本管理建议

```toml
# 推荐的版本配置策略
[project]
dependencies = [
    # 开发阶段: 使用宽松版本
    "czsc>=0.9.8",
    
    # 测试阶段: 使用兼容性版本
    # "czsc~=0.10.0",
    
    # 生产阶段: 使用锁定版本
    # "czsc==0.10.2",
]

# 可选: 分环境配置
[project.optional-dependencies]
dev = ["czsc>=0.9.8"]
test = ["czsc~=0.10.0"] 
prod = ["czsc==0.10.2"]
```

### 3. 文档维护

每次CZSC更新后，需要更新以下文档：
- `docs/CZSC_INTEGRATION_GUIDE.md`
- `docs/user_guide/installation.md`
- `CHANGELOG.md`
- `README.md`

## 🎯 总结

Moyan项目的CZSC更新管理遵循以下原则：

1. **安全第一**: 优先应用安全更新
2. **稳定优先**: 在稳定性和新功能之间平衡
3. **测试驱动**: 所有更新都要经过测试验证
4. **渐进更新**: 避免跳跃式大版本更新
5. **文档同步**: 更新代码的同时更新文档

通过这套机制，Moyan项目能够在保持稳定性的同时，及时获得CZSC的改进和新功能。

---

**记住：更新是为了更好，但稳定是基础！** 🚀
