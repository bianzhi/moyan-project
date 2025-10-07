"""
核心分析器

Moyan系统的主要分析接口，封装了CZSC核心库的功能
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import warnings

# 导入CZSC核心库
try:
    import czsc
    from czsc import CZSC, RawBar
except ImportError as e:
    raise ImportError(f"CZSC核心库未安装: {e}。请运行: pip install czsc>=0.9.8")

# 导入Moyan配置和组件
from ..config.kline_config import (
    KLINE_LEVELS, DEFAULT_KLINE_LEVEL, 
    get_kline_config, validate_kline_level
)
from ..config.settings import default_config
from ..analyzer.auto_analyzer import AutoAnalyzer

class MoyanAnalyzer:
    """
    墨岩缠论分析器
    
    基于CZSC核心库的高级分析接口，提供完整的缠论分析功能
    """
    
    def __init__(self, 
                 kline_level: Optional[str] = None,
                 config: Optional[Any] = None):
        """
        初始化分析器
        
        Args:
            kline_level: K线级别 ('15m', '30m', '1h', '1d', '1wk', '1mo')
            config: 配置对象，默认使用全局配置
        """
        # 设置配置
        self.config = config or default_config
        
        # 设置K线级别
        self.kline_level = kline_level or DEFAULT_KLINE_LEVEL
        if not validate_kline_level(self.kline_level):
            warnings.warn(f"不支持的K线级别: {self.kline_level}，使用默认级别: {DEFAULT_KLINE_LEVEL}")
            self.kline_level = DEFAULT_KLINE_LEVEL
        
        self.kline_config = get_kline_config(self.kline_level)
        
        # 初始化内部分析器
        self._auto_analyzer = AutoAnalyzer(kline_level=self.kline_level, output_base_dir="./output")
        
        # 分析结果缓存
        self._analysis_cache = {}
        
        print(f"✅ 墨岩分析器已初始化")
        print(f"📈 K线级别: {self.kline_config['name']} ({self.kline_level})")
        print(f"🔧 CZSC版本: {getattr(czsc, '__version__', 'unknown')}")
    
    def analyze(self, 
                stock_code: str,
                start_date: Optional[str] = None,
                end_date: Optional[str] = None,
                days: Optional[int] = None,
                force_refresh: bool = False) -> Dict[str, Any]:
        """
        分析股票
        
        Args:
            stock_code: 6位股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)  
            days: 获取天数
            force_refresh: 是否强制刷新缓存
            
        Returns:
            dict: 分析结果
        """
        # 生成缓存键
        cache_key = f"{stock_code}_{self.kline_level}_{start_date}_{end_date}_{days}"
        
        # 检查缓存
        if not force_refresh and cache_key in self._analysis_cache:
            print(f"📋 使用缓存的分析结果: {stock_code}")
            return self._analysis_cache[cache_key]
        
        print(f"🚀 开始分析股票: {stock_code}")
        print(f"📈 K线级别: {self.kline_config['name']}")
        
        try:
            # 使用内部分析器进行分析
            success = self._auto_analyzer.run_analysis(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                days=days
            )
            
            if not success:
                raise RuntimeError("分析失败")
            
            # 获取实际生成的文件路径
            chart_path = getattr(self._auto_analyzer, 'last_chart_path', None)
            report_path = getattr(self._auto_analyzer, 'last_report_path', None)
            
            # 构建分析结果
            result = {
                'stock_code': stock_code,
                'kline_level': self.kline_level,
                'kline_name': self.kline_config['name'],
                'analysis_time': datetime.now().isoformat(),
                'success': True,
                'data': self._auto_analyzer.analysis_result,
                'charts': {
                    'main_chart': chart_path,
                },
                'reports': {
                    'markdown': report_path,
                }
            }
            
            # 缓存结果
            self._analysis_cache[cache_key] = result
            
            print(f"✅ 分析完成: {stock_code}")
            return result
            
        except Exception as e:
            error_result = {
                'stock_code': stock_code,
                'kline_level': self.kline_level,
                'analysis_time': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'data': None,
                'charts': None,
                'reports': None,
            }
            print(f"❌ 分析失败: {stock_code} - {e}")
            return error_result
    
    def batch_analyze(self, 
                     stock_codes: List[str],
                     **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        批量分析股票
        
        Args:
            stock_codes: 股票代码列表
            **kwargs: 传递给analyze方法的参数
            
        Returns:
            dict: {stock_code: analysis_result}
        """
        results = {}
        total = len(stock_codes)
        
        print(f"🚀 开始批量分析 {total} 只股票")
        
        for i, stock_code in enumerate(stock_codes, 1):
            print(f"\n📊 进度: {i}/{total} - 分析 {stock_code}")
            
            try:
                result = self.analyze(stock_code, **kwargs)
                results[stock_code] = result
                
                if result['success']:
                    print(f"✅ {stock_code} 分析成功")
                else:
                    print(f"❌ {stock_code} 分析失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"❌ {stock_code} 分析异常: {e}")
                results[stock_code] = {
                    'stock_code': stock_code,
                    'success': False,
                    'error': str(e)
                }
        
        success_count = sum(1 for r in results.values() if r.get('success', False))
        print(f"\n🎉 批量分析完成: {success_count}/{total} 成功")
        
        return results
    
    def get_analysis_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取分析摘要
        
        Args:
            result: analyze方法返回的结果
            
        Returns:
            dict: 分析摘要
        """
        if not result.get('success', False):
            return {'error': result.get('error', '分析失败')}
        
        data = result.get('data', {})
        
        return {
            'stock_code': result['stock_code'],
            'kline_level': result['kline_name'],
            'current_price': data.get('current_price'),
            'trend_status': data.get('trend_status'),
            'fx_count': data.get('fx_count', 0),
            'bi_count': data.get('bi_count', 0),
            'buy_points': data.get('buy_points', 0),
            'sell_points': data.get('sell_points', 0),
            'up_bi_avg': data.get('up_bi_avg_pct', 0),
            'down_bi_avg': data.get('down_bi_avg_pct', 0),
        }
    
    def switch_kline_level(self, new_level: str):
        """
        切换K线级别
        
        Args:
            new_level: 新的K线级别
        """
        if not validate_kline_level(new_level):
            raise ValueError(f"不支持的K线级别: {new_level}")
        
        if new_level != self.kline_level:
            self.kline_level = new_level
            self.kline_config = get_kline_config(new_level)
            self._auto_analyzer = AutoAnalyzer(kline_level=new_level)
            self._analysis_cache.clear()  # 清空缓存
            
            print(f"🔄 已切换到K线级别: {self.kline_config['name']} ({new_level})")
    
    def clear_cache(self):
        """清空分析结果缓存"""
        self._analysis_cache.clear()
        print("🗑️ 分析结果缓存已清空")
    
    def get_supported_levels(self) -> List[str]:
        """获取支持的K线级别"""
        return list(KLINE_LEVELS.keys())
    
    def get_level_info(self, level: Optional[str] = None) -> Dict[str, Any]:
        """
        获取K线级别信息
        
        Args:
            level: K线级别，默认为当前级别
            
        Returns:
            dict: 级别信息
        """
        target_level = level or self.kline_level
        return get_kline_config(target_level)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MoyanAnalyzer(level={self.kline_level}, czsc_version={getattr(czsc, '__version__', 'unknown')})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()
