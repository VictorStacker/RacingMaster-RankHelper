"""应用程序主入口"""
import sys
from pathlib import Path

from rm_rank.models.db_models import init_database
from rm_rank.repositories import VehicleRepository, GarageRepository
from rm_rank.engines import RankingEngine, RecommendationEngine
from rm_rank.crawler import WebCrawler
from rm_rank.logger import logger
from rm_rank.config import DATABASE_PATH


class Application:
    """应用程序主类"""
    
    def __init__(self):
        # 初始化数据库
        init_database()
        logger.info("数据库初始化完成")
        
        # 初始化仓库
        self.vehicle_repo = VehicleRepository()
        self.garage_repo = GarageRepository()
        
        # 初始化引擎
        self.ranking_engine = RankingEngine(self.vehicle_repo)
        self.recommendation_engine = RecommendationEngine(self.ranking_engine)
        
        # 初始化爬虫
        self.crawler = WebCrawler()
    
    def run_cli(self):
        """运行命令行界面"""
        print("=" * 60)
        print("巅峰极速赛车数据分析和排位推荐系统")
        print("=" * 60)
        print()
        
        while True:
            print("\n请选择操作：")
            print("1. 爬取车辆数据")
            print("2. 查看排行榜")
            print("3. 管理车库")
            print("4. 获取推荐")
            print("5. 退出")
            
            choice = input("\n请输入选项 (1-5): ").strip()
            
            if choice == "1":
                self._crawl_data()
            elif choice == "2":
                self._view_ranking()
            elif choice == "3":
                self._manage_garage()
            elif choice == "4":
                self._get_recommendation()
            elif choice == "5":
                print("\n感谢使用！再见！")
                break
            else:
                print("\n无效选项，请重新选择")
    
    def _crawl_data(self):
        """爬取数据"""
        print("\n正在爬取数据...")
        try:
            vehicles = self.crawler.fetch_all_vehicles_sync()
            self.vehicle_repo.save_vehicles(vehicles)
            print(f"\n✓ 成功爬取并保存 {len(vehicles)} 条车辆数据")
        except Exception as e:
            print(f"\n✗ 爬取失败: {str(e)}")
            logger.error(f"爬取数据失败: {str(e)}", exc_info=True)
    
    def _view_ranking(self):
        """查看排行榜"""
        print("\n请选择组别：")
        print("1. 全部")
        print("2. 运动组")
        print("3. 性能组")
        print("4. 极限组")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        category_map = {"1": None, "2": "运动组", "3": "性能组", "4": "极限组"}
        category = category_map.get(choice)
        
        if category is None and choice != "1":
            print("\n无效选项")
            return
        
        try:
            ranking = self.ranking_engine.generate_ranking(category)
            
            if not ranking:
                print("\n暂无数据，请先爬取车辆数据")
                return
            
            print(f"\n{'='*80}")
            print(f"{'排名':<6} {'车型':<20} {'组别':<8} {'阶数':<6} {'圈速':<10}")
            print(f"{'='*80}")
            
            for ranked_vehicle in ranking[:20]:  # 只显示前20名
                v = ranked_vehicle.vehicle
                print(f"{ranked_vehicle.rank:<6} {v.name:<20} {v.category.value:<8} {v.tier:<6} {v.lap_time:<10.2f}")
            
            if len(ranking) > 20:
                print(f"\n... 还有 {len(ranking) - 20} 条数据")
                
        except Exception as e:
            print(f"\n✗ 查询失败: {str(e)}")
            logger.error(f"查询排行榜失败: {str(e)}", exc_info=True)
    
    def _manage_garage(self):
        """管理车库"""
        print("\n车库管理：")
        print("1. 查看车库")
        print("2. 添加车辆")
        print("3. 删除车辆")
        
        choice = input("\n请输入选项 (1-3): ").strip()
        
        if choice == "1":
            self._view_garage()
        elif choice == "2":
            self._add_to_garage()
        elif choice == "3":
            self._remove_from_garage()
        else:
            print("\n无效选项")
    
    def _view_garage(self):
        """查看车库"""
        try:
            vehicles = self.garage_repo.get_all_garage_vehicles()
            
            if not vehicles:
                print("\n车库为空")
                return
            
            print(f"\n{'='*80}")
            print(f"{'ID':<6} {'车型':<20} {'组别':<8} {'阶数':<6} {'圈速':<10}")
            print(f"{'='*80}")
            
            for v in vehicles:
                print(f"{v.id:<6} {v.name:<20} {v.category.value:<8} {v.tier:<6} {v.lap_time:<10.2f}")
                
        except Exception as e:
            print(f"\n✗ 查询失败: {str(e)}")
    
    def _add_to_garage(self):
        """添加车辆到车库"""
        name = input("\n请输入车型名称: ").strip()
        tier_str = input("请输入阶数: ").strip()
        
        try:
            tier = int(tier_str)
            vehicle = self.vehicle_repo.get_vehicle_by_name_and_tier(name, tier)
            
            if not vehicle:
                print(f"\n✗ 未找到车型 '{name}' 阶数 {tier}")
                return
            
            self.garage_repo.add_vehicle(vehicle.id)
            print(f"\n✓ 成功添加 {name} (阶数{tier}) 到车库")
            
        except ValueError:
            print("\n✗ 阶数必须是整数")
        except Exception as e:
            print(f"\n✗ 添加失败: {str(e)}")
    
    def _remove_from_garage(self):
        """从车库删除车辆"""
        vehicle_id_str = input("\n请输入要删除的车辆ID: ").strip()
        
        try:
            vehicle_id = int(vehicle_id_str)
            self.garage_repo.remove_vehicle(vehicle_id)
            print(f"\n✓ 成功删除车辆ID {vehicle_id}")
            
        except ValueError:
            print("\n✗ 车辆ID必须是整数")
        except Exception as e:
            print(f"\n✗ 删除失败: {str(e)}")
    
    def _get_recommendation(self):
        """获取推荐"""
        try:
            garage_vehicles = self.garage_repo.get_all_garage_vehicles()
            
            if not garage_vehicles:
                print("\n车库为空，请先添加车辆")
                return
            
            print("\n请选择推荐类型：")
            print("1. 全部组别")
            print("2. 运动组")
            print("3. 性能组")
            print("4. 极限组")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            category_map = {"1": None, "2": "运动组", "3": "性能组", "4": "极限组"}
            category = category_map.get(choice)
            
            if category is None and choice != "1":
                print("\n无效选项")
                return
            
            result = self.recommendation_engine.recommend_optimal_combination(
                garage_vehicles, category
            )
            
            if not result.vehicles:
                print("\n没有符合条件的车辆")
                return
            
            print(f"\n{'='*80}")
            print(f"推荐的最优组合 (共{result.count}辆车，总圈速: {result.total_lap_time:.2f})")
            print(f"{'='*80}")
            print(f"{'排名':<6} {'车型':<20} {'组别':<8} {'阶数':<6} {'圈速':<10}")
            print(f"{'='*80}")
            
            for ranked_vehicle in result.vehicles:
                v = ranked_vehicle.vehicle
                print(f"{ranked_vehicle.rank:<6} {v.name:<20} {v.category.value:<8} {v.tier:<6} {v.lap_time:<10.2f}")
                
        except Exception as e:
            print(f"\n✗ 推荐失败: {str(e)}")
            logger.error(f"获取推荐失败: {str(e)}", exc_info=True)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="巅峰极速赛车数据分析和排位推荐系统")
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="启动图形界面（默认为命令行界面）"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    import logging
    from rm_rank.logger import logger
    logger.setLevel(getattr(logging, args.log_level))
    
    try:
        if args.gui:
            # 启动图形界面
            from rm_rank.ui import MainWindow
            from PyQt6.QtWidgets import QApplication
            
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(app.exec())
        else:
            # 启动命令行界面
            app = Application()
            app.run_cli()
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}", exc_info=True)
        print(f"\n程序异常退出: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
