"""调教数据解析器"""
import re
import json
from typing import List, Dict
from bs4 import BeautifulSoup

from rm_rank.tuning.tuning_models import TuningData
from rm_rank.tuning.tuning_errors import ParserError, HTMLStructureError, DataFormatError
from rm_rank.logger import logger


class TuningParser:
    """解析HTML提取调教数据"""
    
    def parse_tuning_data(self, html: str) -> List[TuningData]:
        """解析HTML提取调教数据
        
        Args:
            html: index.html的HTML内容
            
        Returns:
            调教数据列表
            
        Raises:
            ParserError: HTML结构无法解析
        """
        try:
            # 从HTML中提取JavaScript数据
            tuning_data_list = self._extract_from_javascript(html)
            
            if not tuning_data_list:
                logger.warning("未能从HTML中提取到调教数据")
            else:
                logger.info(f"成功提取 {len(tuning_data_list)} 条调教数据")
            
            return tuning_data_list
            
        except Exception as e:
            logger.error(f"解析调教数据失败: {str(e)}", exc_info=True)
            raise ParserError(f"解析调教数据失败: {str(e)}")
    
    def _extract_from_javascript(self, html: str) -> List[TuningData]:
        """从JavaScript代码中提取调教数据
        
        Args:
            html: HTML内容
            
        Returns:
            调教数据列表
        """
        tuning_data_list = []
        
        try:
            # 查找 const db = [...] 数组
            db_pattern = r'const\s+db\s*=\s*\[([\s\S]*?)\];'
            match = re.search(db_pattern, html)
            
            if not match:
                logger.error("未找到 const db 数组")
                return []
            
            db_content = match.group(1)
            logger.info(f"找到 db 数组，长度: {len(db_content)}")
            
            # 解析每个车辆对象
            # 匹配整个对象: {...}
            object_pattern = r'\{[^}]+\}'
            objects = re.findall(object_pattern, db_content)
            
            logger.info(f"找到 {len(objects)} 个车辆对象")
            
            for obj_str in objects:
                # 提取name
                name_match = re.search(r'name:\s*[\'"]([^\'"]+)[\'"]', obj_str)
                # 提取type
                type_match = re.search(r'type:\s*[\'"]([^\'"]+)[\'"]', obj_str)
                # 提取tune
                tune_match = re.search(r'tune:\s*[\'"]([^\'"]+)[\'"]', obj_str)
                
                if name_match and type_match and tune_match:
                    vehicle_name = name_match.group(1)
                    vehicle_type = type_match.group(1)
                    tune_value = tune_match.group(1)
                    
                    # 清理车辆名称中的多余标记
                    vehicle_name = self._clean_vehicle_name(vehicle_name)
                    
                    # type='mix' 表示0阶，type='gold5' 表示5阶
                    if vehicle_type == 'mix':
                        tier = 0
                    elif vehicle_type == 'gold5':
                        tier = 5
                    else:
                        continue  # 跳过其他类型
                    
                    # 解析调教参数
                    parameters = self._parse_tune_value(tune_value)
                    
                    if parameters:
                        tuning_data = TuningData(
                            vehicle_name=vehicle_name,
                            tier=tier,
                            parameters=parameters
                        )
                        tuning_data_list.append(tuning_data)
            
            logger.info(f"从JavaScript中提取到 {len(tuning_data_list)} 条调教数据")
            return tuning_data_list
            
        except Exception as e:
            logger.error(f"从JavaScript提取数据失败: {str(e)}", exc_info=True)
            return []
    
    def _clean_vehicle_name(self, name: str) -> str:
        """清理车辆名称中的多余标记
        
        Args:
            name: 原始车辆名称
            
        Returns:
            清理后的车辆名称
        """
        # 移除常见的后缀标记
        suffixes_to_remove = [
            ' New',
            ' new',
            ' NEW',
            ' 加强重测',
            ' 已重测',
            ' 重测',
            ' 加强',
        ]
        
        cleaned_name = name
        for suffix in suffixes_to_remove:
            if cleaned_name.endswith(suffix):
                cleaned_name = cleaned_name[:-len(suffix)]
        
        cleaned_name = cleaned_name.strip()
        
        # 名称映射表：调教数据中的名称 -> 圈速数据中的名称
        name_mapping = {
            'MINI JCW GP': 'MINI John Cooper Works GP',
            '兰博基尼 Reventon': '兰博基尼 Reventon',  # 保持一致
            '奥迪A3 飞驰人生版': '奥迪 A3 飞驰人生版',
            '宝马M4 CSL(G82)': '宝马 M4 CSL (G82)',
            '梅赛德斯-AMG A45s 4MATIC+': '梅赛德斯-AMG A45s',
        }
        
        # 如果在映射表中，使用映射后的名称
        if cleaned_name in name_mapping:
            return name_mapping[cleaned_name]
        
        return cleaned_name
    
    def _parse_tune_value(self, tune_value: str) -> Dict[str, str]:
        """解析调教值字符串
        
        Args:
            tune_value: 调教值字符串，如 '23332' 或 '漂23332 抓12332'
            
        Returns:
            参数字典
        """
        parameters = {}
        
        try:
            # 处理特殊格式：'漂 抓都是21232'
            if '都是' in tune_value:
                # 提取数字部分
                numbers_match = re.search(r'(\d+)', tune_value)
                if numbers_match:
                    numbers = numbers_match.group(1)
                    # 提取所有前缀（在"都是"之前的中文字符）
                    prefixes = re.findall(r'([\u4e00-\u9fff]+)', tune_value.split('都是')[0])
                    if prefixes:
                        # 为每个前缀创建一个条目
                        for prefix in prefixes:
                            parameters[f'{prefix}调教'] = numbers
                    else:
                        # 如果没有前缀，使用默认键名
                        parameters['调教'] = numbers
                return parameters
            
            # 处理包含多种调教的情况（如 '漂23332 抓12332' 或 '13232 23232'）
            if ' ' in tune_value:
                parts = tune_value.split()
                scheme_index = 1  # 用于无前缀方案的序号
                
                for part in parts:
                    # 提取前缀和数字
                    match = re.match(r'([\u4e00-\u9fff]*)(\d+)', part)
                    if match:
                        prefix = match.group(1)
                        numbers = match.group(2)
                        
                        if prefix:
                            # 有前缀：使用前缀作为键名
                            parameters[f'{prefix}调教'] = numbers
                        else:
                            # 无前缀：使用序号区分
                            parameters[f'调教{scheme_index}'] = numbers
                            scheme_index += 1
            else:
                # 单一调教值
                # 提取数字部分
                numbers = re.findall(r'\d+', tune_value)
                if numbers:
                    parameters['调教'] = numbers[0]
        
        except Exception as e:
            logger.error(f"解析调教值失败: {str(e)}", exc_info=True)
        
        return parameters
    
    def extract_tier_0_data(self, html: str) -> List[TuningData]:
        """提取0阶调教数据
        
        Args:
            html: HTML内容
            
        Returns:
            0阶调教数据列表
        """
        all_data = self._extract_from_javascript(html)
        return [data for data in all_data if data.tier == 0]
    
    def extract_tier_5_data(self, html: str) -> List[TuningData]:
        """提取5阶调教数据
        
        Args:
            html: HTML内容
            
        Returns:
            5阶调教数据列表
        """
        all_data = self._extract_from_javascript(html)
        return [data for data in all_data if data.tier == 5]
