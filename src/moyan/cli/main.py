"""
CLI主入口

Moyan系统的命令行主入口
"""

import sys
import argparse
from typing import List, Optional

from ..config.kline_config import get_supported_levels, DEFAULT_KLINE_LEVEL
from ..config.settings import default_config
from .commands import analyze_command, batch_command, web_command, info_command

def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='moyan',
        description='墨岩缠论分析系统 - 基于CZSC的专业股票技术分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析单只股票 (默认日线)
  moyan analyze 002167
  
  # 指定K线级别和时间区间
  moyan analyze 002167 --kline 15m --start 20250801 --end 20250928
  
  # 批量分析多只股票
  moyan batch 002167,300308,601138 --kline 1d
  
  # 启动Web界面
  moyan web
  
  # 查看系统信息
  moyan info
        """
    )
    
    # 添加全局参数
    parser.add_argument(
        '--version', 
        action='version', 
        version=f"Moyan v{default_config.system.version}"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    
    # 创建子命令
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令',
        metavar='COMMAND'
    )
    
    # analyze命令
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='分析单只股票',
        description='对指定股票进行缠论技术分析'
    )
    
    analyze_parser.add_argument(
        'stock_code',
        type=str,
        help='6位股票代码 (如: 002167)'
    )
    
    analyze_parser.add_argument(
        '--kline', '-k',
        type=str,
        default=DEFAULT_KLINE_LEVEL,
        choices=get_supported_levels(),
        help=f'K线级别 (默认: {DEFAULT_KLINE_LEVEL})'
    )
    
    analyze_parser.add_argument(
        '--start', '-s',
        type=str,
        help='开始日期 (YYYYMMDD格式)'
    )
    
    analyze_parser.add_argument(
        '--end', '-e',
        type=str,
        help='结束日期 (YYYYMMDD格式)'
    )
    
    analyze_parser.add_argument(
        '--days', '-d',
        type=int,
        help='获取天数 (优先级低于start/end)'
    )
    
    analyze_parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出目录 (默认: 当前目录)'
    )
    
    # batch命令
    batch_parser = subparsers.add_parser(
        'batch',
        help='批量分析多只股票',
        description='批量对多只股票进行缠论技术分析'
    )
    
    batch_parser.add_argument(
        'stock_codes',
        type=str,
        help='股票代码列表，用逗号分隔 (如: 002167,300308,601138)'
    )
    
    batch_parser.add_argument(
        '--kline', '-k',
        type=str,
        default=DEFAULT_KLINE_LEVEL,
        choices=get_supported_levels(),
        help=f'K线级别 (默认: {DEFAULT_KLINE_LEVEL})'
    )
    
    batch_parser.add_argument(
        '--start', '-s',
        type=str,
        help='开始日期 (YYYYMMDD格式)'
    )
    
    batch_parser.add_argument(
        '--end', '-e',
        type=str,
        help='结束日期 (YYYYMMDD格式)'
    )
    
    batch_parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出目录 (默认: 当前目录)'
    )
    
    batch_parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='并行处理 (实验性功能)'
    )
    
    # web命令
    web_parser = subparsers.add_parser(
        'web',
        help='启动Web界面',
        description='启动Streamlit Web界面'
    )
    
    web_parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Web服务端口 (默认: 8501)'
    )
    
    web_parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Web服务主机 (默认: localhost)'
    )
    
    # info命令
    info_parser = subparsers.add_parser(
        'info',
        help='显示系统信息',
        description='显示Moyan系统和依赖库的详细信息'
    )
    
    info_parser.add_argument(
        '--check-deps',
        action='store_true',
        help='检查依赖库版本'
    )
    
    return parser

def main(argv: Optional[List[str]] = None):
    """
    CLI主入口函数
    
    Args:
        argv: 命令行参数列表，默认使用sys.argv[1:]
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # 如果没有指定命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        # 根据命令调用相应的处理函数
        if args.command == 'analyze':
            return analyze_command(args)
        elif args.command == 'batch':
            return batch_command(args)
        elif args.command == 'web':
            return web_command(args)
        elif args.command == 'info':
            return info_command(args)
        else:
            print(f"❌ 未知命令: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
        return 130
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"❌ 执行失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
