from fastapi import HTTPException, Header, Request
from typing import Optional
import os
from dotenv import load_dotenv
from app.utils.logger import logger
from app.manager.model_manager import model_manager



# 获取配置文件中的 API Key
def get_api_key():
    """从配置文件中获取 API Key"""
    system_config = model_manager.config.get("system", {})
    api_key = system_config.get("api_key")
    
    # 打印API密钥的前4位用于调试
    logger.info(f"Loaded API key from config: {api_key[:4] if len(api_key) >= 4 else api_key}")
    
    return api_key


async def verify_api_key(authorization: Optional[str] = Header(None)) -> None:
    """验证API密钥

    Args:
        authorization (Optional[str], optional): Authorization header中的API密钥. Defaults to Header(None).

    Raises:
        HTTPException: 当Authorization header缺失或API密钥无效时抛出401错误
    """
    if authorization is None:
        logger.warning("请求缺少Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    # 获取最新的 API Key
    current_api_key = get_api_key()
    
    api_key = authorization.replace("Bearer ", "").strip()
    if api_key != current_api_key:
        logger.warning(f"无效的API密钥: {api_key}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    logger.info("API密钥验证通过")
