"""账号数据仓库"""
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from rm_rank.models.db_models import Account
from rm_rank.exceptions import DatabaseError, BusinessLogicError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class AccountRepository:
    """账号的数据访问对象"""
    
    def __init__(self, session: Session):
        """
        初始化 AccountRepository
        
        Args:
            session: SQLAlchemy 数据库会话
        """
        self.session = session
    
    def create_account(self, name: str, description: str = None) -> Account:
        """创建新账号
        
        Args:
            name: 账号名称
            description: 账号描述
            
        Returns:
            创建的账号对象
            
        Raises:
            BusinessLogicError: 账号名称已存在
            DatabaseError: 数据库操作失败
        """
        try:
            # 检查账号名称是否已存在
            existing = self.session.query(Account).filter(Account.name == name).first()
            if existing:
                raise BusinessLogicError(f"账号名称已存在: {name}")
            
            # 创建账号
            account = Account(name=name, description=description)
            self.session.add(account)
            self.session.commit()
            
            logger.info(f"创建账号: {name}")
            return account
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"创建账号失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"创建账号失败: {str(e)}")
    
    def get_all_accounts(self) -> List[Account]:
        """获取所有账号
        
        Returns:
            账号列表
        """
        try:
            return self.session.query(Account).order_by(Account.created_at).all()
        except SQLAlchemyError as e:
            logger.error(f"获取账号列表失败: {str(e)}")
            raise DatabaseError(f"获取账号列表失败: {str(e)}")
    
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """根据ID获取账号
        
        Args:
            account_id: 账号ID
            
        Returns:
            账号对象，如果不存在则返回 None
        """
        try:
            return self.session.query(Account).filter(Account.id == account_id).first()
        except SQLAlchemyError as e:
            logger.error(f"获取账号失败: {str(e)}")
            return None
    
    def get_account_by_name(self, name: str) -> Optional[Account]:
        """根据名称获取账号
        
        Args:
            name: 账号名称
            
        Returns:
            账号对象，如果不存在则返回 None
        """
        try:
            return self.session.query(Account).filter(Account.name == name).first()
        except SQLAlchemyError as e:
            logger.error(f"获取账号失败: {str(e)}")
            return None
    
    def get_active_account(self) -> Optional[Account]:
        """获取当前激活的账号
        
        Returns:
            激活的账号对象，如果没有则返回 None
        """
        try:
            return self.session.query(Account).filter(Account.is_active == True).first()
        except SQLAlchemyError as e:
            logger.error(f"获取激活账号失败: {str(e)}")
            return None
    
    def set_active_account(self, account_id: int) -> None:
        """设置激活的账号
        
        Args:
            account_id: 要激活的账号ID
            
        Raises:
            BusinessLogicError: 账号不存在
            DatabaseError: 数据库操作失败
        """
        try:
            # 检查账号是否存在
            account = self.get_account_by_id(account_id)
            if not account:
                raise BusinessLogicError(f"账号不存在: ID={account_id}")
            
            # 取消所有账号的激活状态
            self.session.query(Account).update({Account.is_active: False})
            
            # 激活指定账号
            account.is_active = True
            self.session.commit()
            
            logger.info(f"切换到账号: {account.name}")
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"设置激活账号失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"设置激活账号失败: {str(e)}")
    
    def update_account(self, account_id: int, name: str = None, description: str = None) -> None:
        """更新账号信息
        
        Args:
            account_id: 账号ID
            name: 新的账号名称（可选）
            description: 新的账号描述（可选）
            
        Raises:
            BusinessLogicError: 账号不存在或名称已被使用
            DatabaseError: 数据库操作失败
        """
        try:
            account = self.get_account_by_id(account_id)
            if not account:
                raise BusinessLogicError(f"账号不存在: ID={account_id}")
            
            # 如果要修改名称，检查新名称是否已存在
            if name and name != account.name:
                existing = self.get_account_by_name(name)
                if existing:
                    raise BusinessLogicError(f"账号名称已存在: {name}")
                account.name = name
            
            if description is not None:
                account.description = description
            
            self.session.commit()
            logger.info(f"更新账号: {account.name}")
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"更新账号失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"更新账号失败: {str(e)}")
    
    def delete_account(self, account_id: int) -> None:
        """删除账号
        
        Args:
            account_id: 账号ID
            
        Raises:
            BusinessLogicError: 账号不存在
            DatabaseError: 数据库操作失败
        """
        try:
            account = self.get_account_by_id(account_id)
            if not account:
                raise BusinessLogicError(f"账号不存在: ID={account_id}")
            
            account_name = account.name
            self.session.delete(account)
            self.session.commit()
            
            logger.info(f"删除账号: {account_name}")
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"删除账号失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"删除账号失败: {str(e)}")
    
    def ensure_default_account(self) -> Account:
        """确保存在默认账号，如果不存在则创建
        
        Returns:
            默认账号对象
        """
        try:
            # 检查是否有账号
            accounts = self.get_all_accounts()
            
            if not accounts:
                # 创建默认账号
                account = self.create_account("默认账号", "系统自动创建的默认账号")
                account.is_active = True
                self.session.commit()
                logger.info("创建默认账号")
                return account
            
            # 检查是否有激活的账号
            active_account = self.get_active_account()
            if not active_account:
                # 激活第一个账号
                first_account = accounts[0]
                first_account.is_active = True
                self.session.commit()
                logger.info(f"激活账号: {first_account.name}")
                return first_account
            
            return active_account
            
        except Exception as e:
            logger.error(f"确保默认账号失败: {str(e)}", exc_info=True)
            raise
