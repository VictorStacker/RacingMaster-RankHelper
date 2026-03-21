from uuid import uuid4
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from rm_rank.engines.ranking_engine import RankingEngine
from rm_rank.engines.recommendation_engine import RecommendationEngine
from rm_rank.io import DataExporter, DataImporter
from rm_rank.models.data_models import Category, GarageVehicleConfig, VehicleData
from rm_rank.models.db_models import Base, init_database
from rm_rank.repositories import (
    AccountRepository,
    CombinationRepository,
    GarageRepository,
    VehicleRepository,
)
from rm_rank.ui.recommendation_view import build_display_rows
from rm_rank.validator import DataValidator


TEST_TEMP_ROOT = Path(__file__).resolve().parent / ".test_temp"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)


def create_repositories(session):
    vehicle_repo = VehicleRepository(session)
    garage_repo = GarageRepository(session)
    combination_repo = CombinationRepository(session)
    account_repo = AccountRepository(session)
    return vehicle_repo, garage_repo, combination_repo, account_repo


def seed_account(account_repo: AccountRepository, name: str = "主账号"):
    account = account_repo.create_account(name)
    account_repo.set_active_account(account.id)
    return account


def seed_vehicle(vehicle_repo: VehicleRepository, name: str, category: Category, tier: int, lap_time: float):
    vehicle_repo.save_vehicles(
        [
            VehicleData(
                name=name,
                category=category,
                tier=tier,
                lap_time=lap_time,
            )
        ]
    )


def test_garage_repository_persists_resting_status_per_account(test_db):
    vehicle_repo, garage_repo, _, account_repo = create_repositories(test_db)
    seed_vehicle(vehicle_repo, "A车", Category.EXTREME, 5, 300.0)
    seed_vehicle(vehicle_repo, "B车", Category.EXTREME, 5, 301.0)

    first_account = seed_account(account_repo, "账号1")
    garage_repo.add_vehicle("A车", 5)
    garage_repo.add_vehicle("B车", 5)
    garage_repo.set_vehicle_resting_status("A车", 5, True)

    first_account_garage = {
        (vehicle.name, vehicle.tier): vehicle.is_resting
        for vehicle in garage_repo.get_all_garage_vehicles()
    }
    assert first_account_garage == {("A车", 5): True, ("B车", 5): False}

    second_account = account_repo.create_account("账号2")
    account_repo.set_active_account(second_account.id)
    garage_repo.add_vehicle("A车", 5)

    second_account_garage = garage_repo.get_all_garage_vehicles()
    assert len(second_account_garage) == 1
    assert second_account_garage[0].is_resting is False

    garage_repo.set_account_id(first_account.id)
    restored_first_account_garage = {
        (vehicle.name, vehicle.tier): vehicle.is_resting
        for vehicle in garage_repo.get_all_garage_vehicles()
    }
    assert restored_first_account_garage[("A车", 5)] is True


def test_recommendation_engine_keeps_original_recommendation_order():
    engine = RecommendationEngine(RankingEngine(vehicle_repo=None))
    garage = [
        GarageVehicleConfig(
            id=1,
            name="休息快车",
            category=Category.EXTREME,
            tier=5,
            lap_time=300.0,
            is_resting=True,
        ),
        GarageVehicleConfig(
            id=2,
            name="主力1",
            category=Category.EXTREME,
            tier=5,
            lap_time=301.0,
            is_resting=False,
        ),
        GarageVehicleConfig(
            id=3,
            name="主力2",
            category=Category.EXTREME,
            tier=5,
            lap_time=302.0,
            is_resting=False,
        ),
    ]

    result = engine.recommend_optimal_combination(garage, category="极限组", limit=3)
    assert [vehicle.vehicle.name for vehicle in result.vehicles] == [
        "休息快车",
        "主力1",
        "主力2",
    ]
    assert [vehicle.rank for vehicle in result.vehicles] == [1, 2, 3]

    display_rows = build_display_rows(result.vehicles)
    assert [row["ranked_vehicle"].vehicle.name for row in display_rows] == [
        "主力1",
        "主力2",
        "休息快车",
    ]
    assert [row["ranked_vehicle"].rank for row in display_rows] == [2, 3, 1]
    assert [row["category_rank"] for row in display_rows] == [2, 3, 1]


def test_export_and_import_garage_preserves_resting_status():
    source_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(source_engine)
    source_session = sessionmaker(bind=source_engine)()
    source_vehicle_repo, source_garage_repo, source_combination_repo, source_account_repo = create_repositories(source_session)

    seed_vehicle(source_vehicle_repo, "A车", Category.EXTREME, 5, 300.0)
    seed_vehicle(source_vehicle_repo, "B车", Category.PERFORMANCE, 5, 310.0)
    seed_account(source_account_repo)
    source_garage_repo.add_vehicle("A车", 5)
    source_garage_repo.add_vehicle("B车", 5)
    source_garage_repo.set_vehicle_resting_status("A车", 5, True)

    export_path = TEST_TEMP_ROOT / f"garage_{uuid4().hex}.json"
    exporter = DataExporter(
        source_vehicle_repo,
        source_garage_repo,
        source_combination_repo,
        source_account_repo,
    )
    exporter.export_garage(export_path)

    exported_text = export_path.read_text(encoding="utf-8")
    assert '"is_resting": true' in exported_text

    target_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(target_engine)
    target_session = sessionmaker(bind=target_engine)()
    target_vehicle_repo, target_garage_repo, target_combination_repo, target_account_repo = create_repositories(target_session)
    seed_vehicle(target_vehicle_repo, "A车", Category.EXTREME, 5, 300.0)
    seed_vehicle(target_vehicle_repo, "B车", Category.PERFORMANCE, 5, 310.0)

    importer = DataImporter(
        target_vehicle_repo,
        target_garage_repo,
        target_combination_repo,
        DataValidator(),
        target_account_repo,
    )
    imported_count = importer.import_garage(export_path)

    assert imported_count == 2
    imported_account = target_account_repo.get_account_by_name("主账号")
    assert imported_account is not None

    target_garage_repo.set_account_id(imported_account.id)
    imported_garage = {
        (vehicle.name, vehicle.tier): vehicle.is_resting
        for vehicle in target_garage_repo.get_all_garage_vehicles()
    }
    assert imported_garage == {("A车", 5): True, ("B车", 5): False}


def test_init_database_adds_resting_column_for_existing_database():
    db_path = TEST_TEMP_ROOT / f"legacy_{uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL UNIQUE,
                    description VARCHAR,
                    is_active BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    tier INTEGER NOT NULL,
                    lap_time FLOAT NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE user_garage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    vehicle_id INTEGER NOT NULL,
                    added_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE current_combination (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    vehicle_id INTEGER NOT NULL,
                    position INTEGER NOT NULL
                )
                """
            )
        )

    init_database(f"sqlite:///{db_path}")

    inspector = inspect(create_engine(f"sqlite:///{db_path}"))
    account_columns = {column["name"] for column in inspector.get_columns("accounts")}
    garage_columns = {column["name"] for column in inspector.get_columns("user_garage")}

    assert "sort_order" in account_columns
    assert "is_resting" in garage_columns
