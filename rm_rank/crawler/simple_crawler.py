"""简单的 HTTP 爬虫（不需要浏览器）"""
import re
import json
from typing import List
import urllib.request
import urllib.error

from rm_rank.models.data_models import VehicleData
from rm_rank.validator import DataValidator
from rm_rank.exceptions import CrawlerError
from rm_rank.config import DATA_SOURCE_URL
from rm_rank.logger import logger


class SimpleCrawler:
    """使用 urllib 的简单爬虫，不需要浏览器驱动"""
    
    def __init__(self, url: str = DATA_SOURCE_URL):
        self.url = url
        self.validator = DataValidator()
    
    def fetch_all_vehicles(self) -> List[VehicleData]:
        """爬取所有车辆数据
        
        Returns:
            车辆数据列表
            
        Raises:
            CrawlerError: 网站不可访问或解析失败
        """
        try:
            logger.info(f"正在访问 {self.url}")
            
            # 发送 HTTP 请求
            req = urllib.request.Request(
                self.url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')
            
            # 从 HTML 中提取 ALL_DATA 变量
            vehicles_data = self._parse_html(html)
            
            if not vehicles_data:
                raise CrawlerError("未能从网页中提取到数据")
            
            # 验证数据
            validation_result = self.validator.validate_batch(vehicles_data)
            
            if validation_result.errors:
                logger.warning(f"数据验证发现 {len(validation_result.errors)} 个错误")
                for error in validation_result.errors[:5]:
                    logger.warning(error)
            
            logger.info(f"成功获取 {validation_result.valid_count} 条有效数据")
            return validation_result.valid_data
            
        except urllib.error.URLError as e:
            raise CrawlerError(f"网络连接失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取失败: {str(e)}", exc_info=True)
            raise CrawlerError(f"数据更新失败: {str(e)}")
    
    def _parse_html(self, html: str) -> List[dict]:
        """从 HTML 中解析数据
        
        Args:
            html: HTML 内容
            
        Returns:
            车辆数据字典列表
        """
        vehicles_data = []
        
        try:
            # 查找 ALL_DATA 变量
            # 匹配模式: const ALL_DATA = {...} 或 var ALL_DATA = {...}
            pattern = r'(?:const|var|let)\s+ALL_DATA\s*=\s*(\{.+?\});'
            match = re.search(pattern, html, re.DOTALL)
            
            if match:
                js_str = match.group(1)
                
                # 使用更安全的方式：直接解析 JavaScript 对象结构
                # 而不是转换为 JSON
                all_data = self._parse_js_object(js_str)
                
                if not all_data:
                    logger.error("无法解析 JavaScript 对象")
                    return []
                
                logger.info("成功找到并解析 ALL_DATA 变量")
                
                # 组别映射
                group_mapping = {
                    'standard': '运动组',
                    'sport': '性能组',
                    'extreme': '极限组'
                }
                
                # 解析每个组别的数据
                for group_key, group_name in group_mapping.items():
                    if group_key in all_data:
                        group_data = all_data[group_key]
                        logger.info(f"处理 {group_name}，共 {len(group_data)} 辆车")
                        
                        for car_name, lap_times in group_data.items():
                            # lap_times 是一个数组，包含 0-5 阶的圈速
                            if isinstance(lap_times, list):
                                for tier in range(0, 6):  # 0-5 阶
                                    if tier < len(lap_times):
                                        vehicle = {
                                            "name": car_name,
                                            "category": group_name,
                                            "tier": tier,
                                            "lap_time": lap_times[tier]
                                        }
                                        vehicles_data.append(vehicle)
                
                if vehicles_data:
                    logger.info(f"成功提取 {len(vehicles_data)} 条车辆配置数据")
                    return vehicles_data
            
            logger.warning("未找到 ALL_DATA 变量")
            
        except Exception as e:
            logger.error(f"解析 HTML 时出错: {e}", exc_info=True)
        
        return []
    
    def _parse_js_object(self, js_str: str) -> dict:
        """解析 JavaScript 对象（不转换为 JSON）
        
        Args:
            js_str: JavaScript 对象字符串
            
        Returns:
            解析后的字典
        """
        try:
            # 移除注释
            js_str = re.sub(r'//.*?$', '', js_str, flags=re.MULTILINE)
            js_str = re.sub(r'/\*.*?\*/', '', js_str, flags=re.DOTALL)
            
            # 使用 eval 解析（在受控环境中是安全的）
            # 将 JavaScript 对象语法转换为 Python 字典语法
            # 1. 将无引号的键名转换为字符串
            # 2. 保持字符串值不变
            
            # 简单的方法：使用 ast.literal_eval 的变体
            # 但首先需要将 JS 对象转换为 Python 字典格式
            
            # 更简单的方法：直接使用正则表达式提取数据
            result = {}
            
            # 匹配每个组别: group_name: { ... }
            group_pattern = r'(\w+):\s*\{([^}]+(?:\{[^}]+\}[^}]*)*)\}'
            for group_match in re.finditer(group_pattern, js_str):
                group_name = group_match.group(1)
                group_content = group_match.group(2)
                
                # 解析组别内的车辆数据
                # 匹配: "车名": [数字, 数字, ...]
                vehicle_pattern = r'"([^"]+)":\s*\[([^\]]+)\]'
                vehicles = {}
                
                for vehicle_match in re.finditer(vehicle_pattern, group_content):
                    car_name = vehicle_match.group(1)
                    lap_times_str = vehicle_match.group(2)
                    
                    # 解析圈速数组
                    lap_times = [float(x.strip()) for x in lap_times_str.split(',')]
                    vehicles[car_name] = lap_times
                
                result[group_name] = vehicles
            
            return result
            
        except Exception as e:
            logger.error(f"解析 JavaScript 对象失败: {e}", exc_info=True)
            return {}
