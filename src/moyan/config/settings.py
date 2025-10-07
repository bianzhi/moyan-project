"""
系统配置

Moyan系统的全局配置管理
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ChartConfig:
    """图表配置"""
    # Mac高DPI显示器优化
    figsize: tuple = (16, 14)  # 图表尺寸 (英寸)
    dpi: int = 200             # 创建时DPI
    save_dpi: int = 300        # 保存时DPI
    font_size: int = 10        # 字体大小
    line_width: float = 1.5    # 线条粗细
    axes_line_width: float = 1.2  # 坐标轴粗细
    
    # 图表样式
    style: str = 'default'     # matplotlib样式
    grid: bool = True          # 是否显示网格
    grid_alpha: float = 0.3    # 网格透明度

@dataclass
class MacdConfig:
    """MACD指标配置"""
    fast_period: int = 12      # 快速EMA周期
    slow_period: int = 26      # 慢速EMA周期
    signal_period: int = 9     # 信号线周期

@dataclass
class DataConfig:
    """数据获取配置"""
    default_start_date: str = '20250101'  # 默认开始日期
    data_source: str = 'yfinance'         # 数据源
    timeout: int = 30                     # 超时时间(秒)
    retry_times: int = 3                  # 重试次数
    retry_delay: float = 1.0              # 重试延迟(秒)

@dataclass
class CzscConfig:
    """CZSC分析配置"""
    min_k_num: int = 7         # 最小K线数量
    max_k_num: int = 1000      # 最大K线数量
    bi_mode: str = 'new'       # 笔模式
    xd_mode: str = 'strict'    # 线段模式
    
    # 信号配置
    signals_module_name: str = 'czsc.signals'  # 信号模块名
    factors_module_name: str = 'czsc.factors'  # 因子模块名

@dataclass
class ColorConfig:
    """颜色配置"""
    # K线颜色
    up_color: str = 'red'          # 上涨颜色
    down_color: str = 'green'      # 下跌颜色
    
    # 分型颜色
    top_fx_color: str = 'red'      # 顶分型
    bottom_fx_color: str = 'green' # 底分型
    
    # 笔颜色
    up_bi_color: str = 'blue'      # 向上笔
    down_bi_color: str = 'orange'  # 向下笔
    
    # 买卖点颜色
    buy_point_color: str = 'lime'  # 买点
    sell_point_color: str = 'red'  # 卖点
    
    # MACD颜色
    macd_color: str = 'blue'       # MACD线
    signal_color: str = 'red'      # 信号线
    hist_up_color: str = 'red'     # 柱状图上涨
    hist_down_color: str = 'green' # 柱状图下跌

@dataclass
class OutputConfig:
    """输出配置"""
    image_format: str = 'png'      # 图片格式
    image_quality: int = 95        # 图片质量
    report_format: str = 'markdown' # 报告格式
    encoding: str = 'utf-8'        # 文件编码
    
    # 输出目录
    output_dir: str = 'output'     # 输出目录
    charts_dir: str = 'charts'     # 图表目录
    reports_dir: str = 'reports'   # 报告目录

@dataclass
class LogConfig:
    """日志配置"""
    level: str = 'INFO'            # 日志级别
    format: str = '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}'
    rotation: str = '10 MB'        # 日志轮转大小
    retention: str = '30 days'     # 日志保留时间
    
    # 日志文件
    log_dir: str = 'logs'          # 日志目录
    log_file: str = 'moyan.log'    # 日志文件名

@dataclass
class SystemInfo:
    """系统信息"""
    name: str = '墨岩缠论分析系统'
    english_name: str = 'Moyan CZSC Analysis System'
    version: str = '1.0.0'
    author: str = 'CZSC Community'
    description: str = '基于CZSC的专业股票技术分析应用平台'
    features: list = field(default_factory=lambda: [
        '缠论技术分析 (分型、笔、线段、背驰、买卖点)',
        '多时间周期支持 (15m/30m/1h/1d/1wk/1mo)',
        'MACD技术指标集成',
        'Mac高分辨率显示器优化',
        '专业级图表输出',
        '详细分析报告生成'
    ])

class MoyanConfig:
    """Moyan系统配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径 (可选)
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 初始化默认配置
        self.chart = ChartConfig()
        self.macd = MacdConfig()
        self.data = DataConfig()
        self.czsc = CzscConfig()
        self.color = ColorConfig()
        self.output = OutputConfig()
        self.log = LogConfig()
        self.system = SystemInfo()
        
        # 如果指定了配置文件，则加载
        if self.config_file and os.path.exists(self.config_file):
            self._load_from_file()
        
        # 加载环境变量配置
        self._load_from_env()
        
        # 创建输出目录
        self._create_directories()
    
    def _load_from_file(self):
        """从文件加载配置"""
        # TODO: 实现从TOML/YAML文件加载配置
        pass
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 数据源配置
        if os.getenv('MOYAN_DATA_SOURCE'):
            self.data.data_source = os.getenv('MOYAN_DATA_SOURCE')
        
        # 输出目录配置
        if os.getenv('MOYAN_OUTPUT_DIR'):
            self.output.output_dir = os.getenv('MOYAN_OUTPUT_DIR')
        
        # 日志级别配置
        if os.getenv('MOYAN_LOG_LEVEL'):
            self.log.level = os.getenv('MOYAN_LOG_LEVEL')
    
    def _create_directories(self):
        """创建必要的目录"""
        dirs_to_create = [
            self.output.output_dir,
            os.path.join(self.output.output_dir, self.output.charts_dir),
            os.path.join(self.output.output_dir, self.output.reports_dir),
            self.log.log_dir,
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get_chart_config(self) -> Dict[str, Any]:
        """获取图表配置字典"""
        return {
            'figsize': self.chart.figsize,
            'dpi': self.chart.dpi,
            'save_dpi': self.chart.save_dpi,
            'font_size': self.chart.font_size,
            'line_width': self.chart.line_width,
            'axes_line_width': self.chart.axes_line_width,
            'style': self.chart.style,
            'grid': self.chart.grid,
            'grid_alpha': self.chart.grid_alpha,
        }
    
    def get_macd_config(self) -> Dict[str, Any]:
        """获取MACD配置字典"""
        return {
            'fast_period': self.macd.fast_period,
            'slow_period': self.macd.slow_period,
            'signal_period': self.macd.signal_period,
        }
    
    def get_color_config(self) -> Dict[str, Any]:
        """获取颜色配置字典"""
        return {
            'up_color': self.color.up_color,
            'down_color': self.color.down_color,
            'top_fx_color': self.color.top_fx_color,
            'bottom_fx_color': self.color.bottom_fx_color,
            'up_bi_color': self.color.up_bi_color,
            'down_bi_color': self.color.down_bi_color,
            'buy_point_color': self.color.buy_point_color,
            'sell_point_color': self.color.sell_point_color,
            'macd_color': self.color.macd_color,
            'signal_color': self.color.signal_color,
            'hist_up_color': self.color.hist_up_color,
            'hist_down_color': self.color.hist_down_color,
        }
    
    def update_config(self, section: str, **kwargs):
        """
        更新配置
        
        Args:
            section: 配置段名 (chart, macd, data, etc.)
            **kwargs: 配置项
        """
        if hasattr(self, section):
            config_obj = getattr(self, section)
            for key, value in kwargs.items():
                if hasattr(config_obj, key):
                    setattr(config_obj, key, value)
    
    def save_config(self, file_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            file_path: 保存路径，默认使用初始化时的配置文件路径
        """
        # TODO: 实现配置保存功能
        pass
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MoyanConfig(version={self.system.version}, data_source={self.data.data_source})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()

# 全局默认配置实例
default_config = MoyanConfig()
