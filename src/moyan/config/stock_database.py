# src/moyan/config/stock_database.py
"""
股票代码数据库，支持代码、名称、拼音搜索
"""

# 常用股票代码映射表
STOCK_DATABASE = {
    # 主要指数ETF
    "000001": {"name": "平安银行", "pinyin": "payh", "full_pinyin": "pinganyin hang"},
    "000002": {"name": "万科A", "pinyin": "wka", "full_pinyin": "wanke a"},
    "000858": {"name": "五粮液", "pinyin": "wly", "full_pinyin": "wuliangye"},
    "000895": {"name": "双汇发展", "pinyin": "shfz", "full_pinyin": "shuanghui fazhan"},
    
    # 创业板
    "300059": {"name": "东方财富", "pinyin": "dfcf", "full_pinyin": "dongfang caifu"},
    "300502": {"name": "新易盛", "pinyin": "xys", "full_pinyin": "xinyisheng"},
    "300750": {"name": "宁德时代", "pinyin": "ndsd", "full_pinyin": "ningde shidai"},
    
    # 科创板
    "688519": {"name": "南微医学", "pinyin": "nwyx", "full_pinyin": "nanwei yixue"},
    "688981": {"name": "中芯国际", "pinyin": "zxgj", "full_pinyin": "zhongxin guoji"},
    
    # 主板常用股票
    "600036": {"name": "招商银行", "pinyin": "zsyh", "full_pinyin": "zhaoshang yinhang"},
    "600519": {"name": "贵州茅台", "pinyin": "gzmt", "full_pinyin": "guizhou maotai"},
    "600887": {"name": "伊利股份", "pinyin": "ylgf", "full_pinyin": "yili gufen"},
    "601318": {"name": "中国平安", "pinyin": "zgpa", "full_pinyin": "zhongguo pingan"},
    "601888": {"name": "中国中免", "pinyin": "zgzm", "full_pinyin": "zhongguo zhongmian"},
    
    # 深主板
    "002167": {"name": "东方锆业", "pinyin": "dfzy", "full_pinyin": "dongfang gaiye"},
    "002415": {"name": "海康威视", "pinyin": "hkws", "full_pinyin": "haikang weishi"},
    "300308": {"name": "中际旭创", "pinyin": "zjxc", "full_pinyin": "zhongji xuchuang"},
    "002594": {"name": "比亚迪", "pinyin": "byd", "full_pinyin": "biyadi"},
    "002916": {"name": "深南电路", "pinyin": "sndl", "full_pinyin": "shennan dianlu"},
    
    # 中小板转主板
    "002230": {"name": "科大讯飞", "pinyin": "kdxf", "full_pinyin": "keda xunfei"},
    "002714": {"name": "牧原股份", "pinyin": "mygf", "full_pinyin": "muyuan gufen"},
    
    # 港股通标的
    "000700": {"name": "腾讯控股", "pinyin": "txkg", "full_pinyin": "tengxun kongu"},
    "000941": {"name": "中国移动", "pinyin": "zgyd", "full_pinyin": "zhongguo yidong"},
    
    # 最近热门股票
    "001219": {"name": "青岛食品", "pinyin": "qdsp", "full_pinyin": "qingdao shipin"},
    "001696": {"name": "宗申动力", "pinyin": "zsdl", "full_pinyin": "zongshen dongli"},
    "300763": {"name": "锦浪科技", "pinyin": "jlkj", "full_pinyin": "jinlang keji"},
    
    # 银行股
    "600000": {"name": "浦发银行", "pinyin": "pfyh", "full_pinyin": "pufa yinhang"},
    "601398": {"name": "工商银行", "pinyin": "gsyh", "full_pinyin": "gongshang yinhang"},
    "601939": {"name": "建设银行", "pinyin": "jsyh", "full_pinyin": "jianshe yinhang"},
    "601988": {"name": "中国银行", "pinyin": "zgyh", "full_pinyin": "zhongguo yinhang"},
    
    # 保险股  
    "601318": {"name": "中国平安", "pinyin": "zgpa", "full_pinyin": "zhongguo pingan"},
    "601601": {"name": "中国太保", "pinyin": "zgtb", "full_pinyin": "zhongguo taibao"},
    "601628": {"name": "中国人寿", "pinyin": "zgrs", "full_pinyin": "zhongguo renshou"},
    
    # 白酒股
    "000568": {"name": "泸州老窖", "pinyin": "lzlj", "full_pinyin": "luzhou laojiao"},
    "000799": {"name": "酒鬼酒", "pinyin": "jgj", "full_pinyin": "jiugui jiu"},
    "002304": {"name": "洋河股份", "pinyin": "yhgf", "full_pinyin": "yanghe gufen"},
    
    # 医药股
    "600276": {"name": "恒瑞医药", "pinyin": "hryy", "full_pinyin": "hengrui yiyao"},
    "300015": {"name": "爱尔眼科", "pinyin": "aeyk", "full_pinyin": "aier yanke"},
    "000661": {"name": "长春高新", "pinyin": "ccgx", "full_pinyin": "changchun gaoxin"},
    "300142": {"name": "沃森生物", "pinyin": "wssw", "full_pinyin": "wosen shengwu"},
    
    # ETF基金
    "510050": {"name": "50ETF", "pinyin": "50etf", "full_pinyin": "wushi etf"},
    "510300": {"name": "300ETF", "pinyin": "300etf", "full_pinyin": "sanbaietf"},
    "510500": {"name": "500ETF", "pinyin": "500etf", "full_pinyin": "wubaietf"},
    "159919": {"name": "300ETF", "pinyin": "300etf", "full_pinyin": "chuangyeetf"},
}

def search_stock(query):
    """
    搜索股票，支持代码、名称、拼音
    
    Args:
        query (str): 搜索关键词
        
    Returns:
        list: 匹配的股票列表，每个元素包含 {'code': '', 'name': '', 'pinyin': ''}
    """
    if not query:
        return []
    
    query = query.strip().lower()
    results = []
    
    for code, info in STOCK_DATABASE.items():
        # 1. 精确匹配股票代码
        if query == code:
            results.append({
                'code': code,
                'name': info['name'],
                'pinyin': info['pinyin'],
                'match_type': 'code'
            })
            continue
        
        # 2. 代码前缀匹配
        if code.startswith(query) and len(query) >= 3:
            results.append({
                'code': code,
                'name': info['name'],
                'pinyin': info['pinyin'],
                'match_type': 'code_prefix'
            })
            continue
        
        # 3. 股票名称包含匹配
        if query in info['name'].lower():
            results.append({
                'code': code,
                'name': info['name'],
                'pinyin': info['pinyin'],
                'match_type': 'name'
            })
            continue
        
        # 4. 拼音首字母匹配
        if query == info['pinyin'].lower():
            results.append({
                'code': code,
                'name': info['name'],
                'pinyin': info['pinyin'],
                'match_type': 'pinyin'
            })
            continue
        
        # 5. 拼音首字母前缀匹配
        if info['pinyin'].lower().startswith(query) and len(query) >= 2:
            results.append({
                'code': code,
                'name': info['name'],
                'pinyin': info['pinyin'],
                'match_type': 'pinyin_prefix'
            })
            continue
        
        # 6. 全拼音匹配
        if query in info['full_pinyin'].lower().replace(' ', ''):
            results.append({
                'code': code,
                'name': info['name'],
                'pinyin': info['pinyin'],
                'match_type': 'full_pinyin'
            })
    
    # 按匹配类型排序：精确匹配 > 前缀匹配 > 包含匹配
    priority = {
        'code': 1,
        'pinyin': 2,
        'code_prefix': 3,
        'name': 4,
        'pinyin_prefix': 5,
        'full_pinyin': 6
    }
    
    results.sort(key=lambda x: priority.get(x['match_type'], 10))
    
    return results[:10]  # 最多返回10个结果

def get_stock_info(code):
    """
    根据股票代码获取股票信息
    
    Args:
        code (str): 股票代码
        
    Returns:
        dict: 股票信息或None
    """
    return STOCK_DATABASE.get(code)

def get_all_stocks():
    """
    获取所有股票列表
    
    Returns:
        list: 所有股票信息
    """
    return [
        {
            'code': code,
            'name': info['name'],
            'pinyin': info['pinyin']
        }
        for code, info in STOCK_DATABASE.items()
    ]

# 测试函数
if __name__ == "__main__":
    # 测试搜索功能
    test_queries = ["000001", "平安", "payh", "茅台", "600519", "dfzy", "byd"]
    
    for query in test_queries:
        results = search_stock(query)
        print(f"搜索 '{query}':")
        for result in results:
            print(f"  {result['code']} - {result['name']} ({result['pinyin']}) [{result['match_type']}]")
        print()
