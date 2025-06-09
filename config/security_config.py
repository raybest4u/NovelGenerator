# config/security_config.py
"""
安全配置
"""

from typing import List, Dict, Any

# CORS配置
CORS_SETTINGS = {
    "allow_origins": ["http://localhost:3000", "http://localhost:8080"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# 速率限制配置
RATE_LIMIT_SETTINGS = {
    "default": {"calls": 100, "period": 60},  # 每分钟100次
    "chat": {"calls": 20, "period": 60},  # 聊天API每分钟20次
    "generate": {"calls": 5, "period": 300},  # 生成API每5分钟5次
}

# 安全头配置
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}

# 输入验证配置
INPUT_VALIDATION = {
    "max_string_length": 10000,
    "max_array_length": 100,
    "max_object_depth": 10,
    "forbidden_patterns": [
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload=",
        r"onerror=",
    ]
}

# 敏感数据脱敏配置
SENSITIVE_FIELDS = [
    "password", "api_key", "secret", "token",
    "private_key", "access_key", "credential"
]


def mask_sensitive_data(data: Any) -> Any:
    """脱敏敏感数据"""
    if isinstance(data, dict):
        return {
            k: "***" if any(field in k.lower() for field in SENSITIVE_FIELDS) else mask_sensitive_data(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data