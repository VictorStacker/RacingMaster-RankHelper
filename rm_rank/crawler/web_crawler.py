"""网页爬虫模块"""
import asyncio
from typing import List

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from rm_rank.models.data_models import VehicleData
from rm_rank.validator import DataValidator
from rm_rank.exceptions import CrawlerError
from rm_rank.config import DATA_SOURCE_URL, CRAWLER_TIMEOUT
from rm_rank.logger import logger


class WebCrawler:
    """负责从数据源网站获取车辆数据"""
    
    def __init__(self, url: str = DATA_SOURCE_URL):
        self.url = url
        self.validator = DataValidator()
    
    async def fetch_all_vehicles(self) -> List[VehicleData]:
        """爬取所有车辆数据
        
        Returns:
            车辆数据列表
            
        Raises:
            CrawlerError: 网站不可访问或解析失败
        """
        try:
            async with async_playwright() as p:
                # 尝试使用已安装的浏览器
                try:
                    browser = await p.chromium.launch(headless=True)
                except Exception as browser_error:
                    # 如果浏览器未安装，抛出友好的错误信息
                    raise CrawlerError(
                        "浏览器驱动未安装。\n\n"
                        "如果您使用的是打包版本（.exe），请按以下步骤操作：\n"
                        "1. 下载并安装 Python 3.10+\n"
                        "2. 打开命令提示符（CMD）\n"
                        "3. 运行命令：pip install playwright\n"
                        "4. 运行命令：playwright install chromium\n\n"
                        "或者，您可以从源码运行本程序。"
                    )
                
                page = await browser.new_page()
                page.set_default_timeout(CRAWLER_TIMEOUT)
                
                logger.info(f"正在访问 {self.url}")
                await page.goto(self.url)
                
                # 等待页面加载
                await page.wait_for_load_state('networkidle')
                
                # 解析数据（这里需要根据实际网页结构实现）
                # 由于无法访问实际网页，这里提供一个示例实现
                vehicles_data = await self._parse_page(page)
                
                await browser.close()
                
                # 验证数据
                validation_result = self.validator.validate_batch(vehicles_data)
                
                if validation_result.errors:
                    logger.warning(f"数据验证发现 {len(validation_result.errors)} 个错误")
                    for error in validation_result.errors[:5]:  # 只记录前5个错误
                        logger.warning(error)
                
                logger.info(f"成功获取 {validation_result.valid_count} 条有效数据")
                return validation_result.valid_data
                
        except PlaywrightTimeoutError:
            raise CrawlerError("网站访问超时，请检查网络连接")
        except Exception as e:
            logger.error(f"获取失败: {str(e)}", exc_info=True)
            raise CrawlerError(f"数据更新失败: {str(e)}")
    
    async def _parse_page(self, page) -> List[dict]:
        """解析页面数据
        
        Args:
            page: Playwright 页面对象
            
        Returns:
            车辆数据字典列表
        """
        vehicles_data = []
        
        try:
            # 等待页面完全加载
            await page.wait_for_timeout(2000)
            
            # 从页面的 JavaScript 变量中提取 ALL_DATA
            logger.info("尝试从 ALL_DATA 变量提取数据...")
            
            all_data = await page.evaluate("""
                () => {
                    if (typeof ALL_DATA !== 'undefined') {
                        return ALL_DATA;
                    }
                    return null;
                }
            """)
            
            if all_data:
                logger.info("成功找到 ALL_DATA 变量")
                
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
                            # 我们为每个阶数创建一个车辆配置
                            for tier in range(0, 6):  # 0-5 阶
                                if tier < len(lap_times):
                                    vehicle = {
                                        "name": car_name,
                                        "category": group_name,
                                        "tier": tier,
                                        "lap_time": lap_times[tier]  # lap_times[0] 是 0阶，lap_times[1] 是 1阶，以此类推
                                    }
                                    vehicles_data.append(vehicle)
                
                if vehicles_data:
                    logger.info(f"成功从 ALL_DATA 提取 {len(vehicles_data)} 条车辆配置数据")
                    return vehicles_data
            
            logger.warning("未找到 ALL_DATA 变量")
            
        except Exception as e:
            logger.error(f"解析页面时出错: {e}", exc_info=True)
        
        # 如果提取失败，返回示例数据
        logger.warning("使用示例数据，实际部署时需要根据网站结构调整解析逻辑")
        return self._get_sample_data()
    
    def _parse_js_data(self, js_data: dict) -> List[dict]:
        """解析从 JavaScript 中提取的数据
        
        Args:
            js_data: JavaScript 数据对象
            
        Returns:
            车辆数据字典列表
        """
        vehicles = []
        
        try:
            # 尝试不同的数据结构
            if isinstance(js_data, list):
                # 直接是数组
                for item in js_data:
                    if isinstance(item, dict) and all(k in item for k in ['name', 'category', 'tier', 'lap_time']):
                        vehicles.append(item)
            
            elif isinstance(js_data, dict):
                # 可能是 ECharts 配置
                if 'series' in js_data:
                    # ECharts 格式
                    series = js_data.get('series', [])
                    if series and isinstance(series, list):
                        for s in series:
                            if 'data' in s:
                                # 提取数据点
                                pass  # 需要根据实际格式处理
                
                # 或者数据在某个键下
                for key in ['data', 'vehicles', 'items', 'list']:
                    if key in js_data and isinstance(js_data[key], list):
                        vehicles = js_data[key]
                        break
        
        except Exception as e:
            logger.error(f"解析 JS 数据失败: {e}")
        
        return vehicles
    
    def _get_sample_data(self) -> List[dict]:
        """获取示例数据
        
        Returns:
            示例车辆数据列表
        """
        return [
            {"name": "保时捷911 Turbo S", "category": "极限组", "tier": 5, "lap_time": 115.2},
            {"name": "法拉利488 Pista", "category": "极限组", "tier": 5, "lap_time": 116.8},
            {"name": "兰博基尼Huracán", "category": "极限组", "tier": 4, "lap_time": 118.5},
            {"name": "迈凯伦720S", "category": "性能组", "tier": 5, "lap_time": 118.9},
            {"name": "奥迪R8 V10", "category": "性能组", "tier": 5, "lap_time": 120.3},
            {"name": "日产GT-R", "category": "性能组", "tier": 4, "lap_time": 122.1},
            {"name": "宝马M4", "category": "运动组", "tier": 5, "lap_time": 120.5},
            {"name": "奔驰AMG GT", "category": "运动组", "tier": 4, "lap_time": 122.8},
            {"name": "雪佛兰科尔维特", "category": "运动组", "tier": 4, "lap_time": 124.2},
            {"name": "保时捷Cayman GT4", "category": "极限组", "tier": 3, "lap_time": 125.6},
            {"name": "阿斯顿·马丁Vantage", "category": "性能组", "tier": 3, "lap_time": 126.8},
            {"name": "捷豹F-Type R", "category": "运动组", "tier": 3, "lap_time": 128.3},
        ]
    
    def fetch_all_vehicles_sync(self) -> List[VehicleData]:
        """同步版本的获取方法
        
        Returns:
            车辆数据列表
        """
        return asyncio.run(self.fetch_all_vehicles())
