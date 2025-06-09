
# utils/security.py
"""
安全工具和中间件
"""

import hashlib
import secrets
import jwt
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from config.settings import get_settings


class SecurityManager:
    """安全管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.failed_attempts = {}  # IP -> (count, last_attempt)
        self.blocked_ips = set()
        self.api_keys = set()  # 存储有效的API密钥

    def generate_api_key(self) -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(32)

    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_bytes(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return salt.hex() + pwdhash.hex()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """验证密码"""
        try:
            salt = bytes.fromhex(stored_hash[:64])
            stored_pwdhash = bytes.fromhex(stored_hash[64:])
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return pwdhash == stored_pwdhash
        except Exception:
            return False

    def create_access_token(self, data: Dict[str, Any],
                            expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        to_encode.update({"exp": expire})

        # 使用设置中的密钥或生成一个
        secret_key = getattr(self.settings, 'secret_key', 'your-secret-key')
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            secret_key = getattr(self.settings, 'secret_key', 'your-secret-key')
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token验证失败: {e}")
            return None

    def record_failed_attempt(self, ip: str):
        """记录失败尝试"""
        now = time.time()

        if ip in self.failed_attempts:
            count, last_attempt = self.failed_attempts[ip]

            # 如果距离上次尝试超过1小时，重置计数
            if now - last_attempt > 3600:
                count = 1
            else:
                count += 1

            self.failed_attempts[ip] = (count, now)

            # 超过5次失败，封锁IP
            if count >= 5:
                self.blocked_ips.add(ip)
                logger.warning(f"IP {ip} 因多次失败尝试被封锁")
        else:
            self.failed_attempts[ip] = (1, now)

    def is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被封锁"""
        return ip in self.blocked_ips

    def validate_request_rate(self, ip: str, limit: int = 100,
                              window: int = 3600) -> bool:
        """验证请求频率"""
        # 简单的速率限制实现
        # 实际项目中可以使用Redis等存储
        return True

    def sanitize_input(self, data: Any) -> Any:
        """输入数据清理"""
        if isinstance(data, str):
            # 移除潜在的恶意字符
            dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
            for char in dangerous_chars:
                data = data.replace(char, '')
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]

        return data


# 全局安全管理器
security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """获取安全管理器"""
    return security_manager


# FastAPI安全中间件
security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """API密钥验证"""
    token = credentials.credentials

    # 验证令牌
    payload = security_manager.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")

    return payload


async def check_rate_limit(request: Request):
    """检查速率限制"""
    client_ip = request.client.host

    # 检查IP是否被封锁
    if security_manager.is_ip_blocked(client_ip):
        logger.warning(f"被封锁的IP尝试访问: {client_ip}")
        raise HTTPException(status_code=429, detail="IP已被封锁")

    # 检查请求频率
    if not security_manager.validate_request_rate(client_ip):
        security_manager.record_failed_attempt(client_ip)
        raise HTTPException(status_code=429, detail="请求过于频繁")