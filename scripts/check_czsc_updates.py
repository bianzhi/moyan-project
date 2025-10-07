#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CZSC版本更新检查工具
Check for CZSC version updates
"""
import subprocess
import requests
import sys
import json
from datetime import datetime
from packaging import version
import argparse

def get_installed_version():
    """获取当前安装的CZSC版本"""
    try:
        result = subprocess.run(['pip', 'show', 'czsc'], 
                              capture_output=True, text=True, check=True)
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split()[-1].strip()
    except subprocess.CalledProcessError:
        return None
    return None

def get_latest_version():
    """从PyPI获取最新版本"""
    try:
        response = requests.get('https://pypi.org/pypi/czsc/json', timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['info']['version']
    except requests.RequestException as e:
        print(f"❌ 获取PyPI信息失败: {e}")
        return None

def get_release_info(tag_name):
    """获取GitHub release信息"""
    try:
        url = f"https://api.github.com/repos/waditu/czsc/releases/tags/v{tag_name}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None

def compare_versions(current, latest):
    """比较版本号"""
    try:
        v_current = version.parse(current)
        v_latest = version.parse(latest)
        
        if v_current < v_latest:
            return "outdated"
        elif v_current > v_latest:
            return "ahead"
        else:
            return "latest"
    except Exception:
        return "unknown"

def check_breaking_changes(current_ver, latest_ver):
    """检查是否有破坏性更新"""
    try:
        v_current = version.parse(current_ver)
        v_latest = version.parse(latest_ver)
        
        # 主版本号变化通常意味着破坏性更新
        if v_latest.major > v_current.major:
            return "major"
        elif v_latest.minor > v_current.minor:
            return "minor"
        elif v_latest.micro > v_current.micro:
            return "patch"
        else:
            return "none"
    except Exception:
        return "unknown"

def suggest_update_strategy(change_type):
    """建议更新策略"""
    strategies = {
        "patch": {
            "risk": "低",
            "action": "建议立即更新",
            "description": "通常是bug修复和小改进"
        },
        "minor": {
            "risk": "中等", 
            "action": "建议测试后更新",
            "description": "新功能，通常向后兼容"
        },
        "major": {
            "risk": "高",
            "action": "谨慎评估后手动更新", 
            "description": "可能包含破坏性变更"
        }
    }
    return strategies.get(change_type, {
        "risk": "未知",
        "action": "建议查看更新日志",
        "description": "无法确定变更类型"
    })

def run_compatibility_test():
    """运行基本兼容性测试"""
    print("🧪 运行基本兼容性测试...")
    
    try:
        # 测试基本导入
        result = subprocess.run([
            sys.executable, '-c', 
            'import czsc; from czsc import CZSC, RawBar; print("✅ 基本导入测试通过")'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ CZSC基本导入测试通过")
            return True
        else:
            print(f"❌ 基本导入测试失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 兼容性测试超时")
        return False
    except Exception as e:
        print(f"❌ 兼容性测试异常: {e}")
        return False

def update_czsc(target_version=None):
    """更新CZSC"""
    print(f"📥 开始更新CZSC{'到版本 ' + target_version if target_version else ''}...")
    
    try:
        # 备份当前版本信息
        current_version = get_installed_version()
        if current_version:
            print(f"💾 当前版本: {current_version}")
        
        # 执行更新
        cmd = ['pip', 'install', '--upgrade']
        if target_version:
            cmd.append(f'czsc=={target_version}')
        else:
            cmd.append('czsc')
            
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        new_version = get_installed_version()
        print(f"✅ 更新成功! 新版本: {new_version}")
        
        # 运行兼容性测试
        if run_compatibility_test():
            print("🎉 更新完成，所有测试通过!")
            return True
        else:
            print("⚠️ 更新完成，但兼容性测试失败，请检查代码")
            if current_version:
                print(f"💡 如需回滚，执行: pip install czsc=={current_version}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 更新失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description='CZSC版本更新检查工具')
    parser.add_argument('--update', action='store_true', help='自动更新到最新版本')
    parser.add_argument('--version', help='更新到指定版本')
    parser.add_argument('--test', action='store_true', help='只运行兼容性测试')
    args = parser.parse_args()
    
    print('🔍 CZSC版本更新检查工具')
    print('=' * 60)
    print(f'🕐 检查时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    # 如果只是测试
    if args.test:
        run_compatibility_test()
        return
    
    # 如果指定了要更新到特定版本
    if args.version:
        if update_czsc(args.version):
            print("🎉 指定版本更新完成!")
        else:
            print("❌ 指定版本更新失败!")
        return
    
    # 获取版本信息
    print("📦 正在检查版本信息...")
    current_version = get_installed_version()
    latest_version = get_latest_version()
    
    if not current_version:
        print("❌ 未检测到已安装的CZSC，请先安装: pip install czsc")
        return
        
    if not latest_version:
        print("❌ 无法获取最新版本信息，请检查网络连接")
        return
    
    print(f"📊 当前版本: {current_version}")
    print(f"🚀 最新版本: {latest_version}")
    print()
    
    # 比较版本
    status = compare_versions(current_version, latest_version)
    
    if status == "latest":
        print("✅ 您使用的已是最新版本!")
        print("💡 运行 --test 参数可以测试当前版本的兼容性")
        
    elif status == "ahead":
        print("🔬 您使用的版本比PyPI最新版本更新 (可能是开发版本)")
        
    elif status == "outdated":
        print("🔔 发现新版本可用!")
        
        # 分析更新类型
        change_type = check_breaking_changes(current_version, latest_version)
        strategy = suggest_update_strategy(change_type)
        
        print(f"📋 更新类型: {change_type.upper()}")
        print(f"⚠️ 风险级别: {strategy['risk']}")
        print(f"💡 建议行动: {strategy['action']}")
        print(f"📝 变更说明: {strategy['description']}")
        print()
        
        # 获取release信息
        release_info = get_release_info(latest_version)
        if release_info:
            published_date = release_info.get('published_at', '').split('T')[0]
            print(f"📅 发布日期: {published_date}")
            if release_info.get('body'):
                print("📖 更新说明:")
                # 显示前500字符的更新说明
                body = release_info['body'][:500]
                if len(release_info['body']) > 500:
                    body += "..."
                print(f"   {body}")
                print()
        
        print("🔗 更多信息:")
        print(f"   📋 Release页面: https://github.com/waditu/czsc/releases/tag/v{latest_version}")
        print(f"   📦 PyPI页面: https://pypi.org/project/czsc/{latest_version}/")
        print()
        
        print("🛠️ 更新命令:")
        print(f"   pip install --upgrade czsc")
        print(f"   # 或指定版本: pip install czsc=={latest_version}")
        print()
        
        # 如果用户选择自动更新
        if args.update:
            print("🚀 开始自动更新...")
            if update_czsc():
                print("🎉 自动更新成功完成!")
            else:
                print("❌ 自动更新失败，请手动处理")
        else:
            print("💡 使用 --update 参数可以自动更新")
            print("💡 使用 --version <版本号> 可以更新到指定版本")
    else:
        print("❓ 无法确定版本状态，请手动检查")
    
    print()
    print("🆘 需要帮助?")
    print("   📖 查看更新指南: docs/developer_guide/czsc_update_guide.md")
    print("   🐛 报告问题: https://github.com/waditu/czsc/issues")

if __name__ == "__main__":
    main()
