"""基础客户端类,定义通用接口"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

import aiohttp
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

from app.utils.logger import logger


class BaseClient(ABC):
    """基础客户端类"""

    # 默认超时设置(秒)
    # total: 总超时时间
    # connect: 连接超时时间
    # sock_read: 读取超时时间
    # TODO: 默认时间的设置涉及到模型推理速度，需要根据实际情况进行调整
    DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=600, connect=10, sock_read=500)

    def __init__(
        self,
        api_key: str,
        api_url: str,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        proxy: Optional[str] = None,
    ):
        """初始化基础客户端

        Args:
            api_key: API密钥
            api_url: API地址
            timeout: 请求超时设置,None则使用默认值
            proxy: 代理服务器地址，例如 "http://127.0.0.1:7890"
        """
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.proxy = proxy

    async def _make_request(
        self, headers: dict, data: dict, timeout: Optional[aiohttp.ClientTimeout] = None
    ) -> AsyncGenerator[bytes, None]:
        """发送请求并处理响应

        Args:
            headers: 请求头
            data: 请求数据
            timeout: 当前请求的超时设置,None则使用实例默认值

        Yields:
            bytes: 原始响应数据

        Raises:
            aiohttp.ClientError: 客户端错误
            ServerTimeoutError: 服务器超时
            Exception: 其他异常
        """
        request_timeout = timeout or self.timeout

        try:
            # 使用 connector 参数来优化连接池
            connector = aiohttp.TCPConnector(limit=100, force_close=True)
            
            # 处理代理地址格式
            proxy_url = None
            if self.proxy:
                # 如果代理地址不包含协议前缀，添加 http:// 前缀
                if self.proxy and not self.proxy.startswith(('http://', 'https://', 'socks://', 'socks5://')):
                    proxy_url = f"http://{self.proxy}"
                else:
                    proxy_url = self.proxy
                logger.info(f"使用代理: {proxy_url}")
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    self.api_url, 
                    headers=headers, 
                    json=data, 
                    timeout=request_timeout,
                    proxy=proxy_url
                ) as response:
                    # 检查响应状态
                    if not response.ok:
                        error_text = await response.text()
                        error_msg = f"API 请求失败: 状态码 {response.status}, 错误信息: {error_text}"
                        logger.error(error_msg)
                        raise ClientError(error_msg)

                    # 流式读取响应内容
                    async for chunk in response.content.iter_any():
                        if chunk:  # 过滤空chunks
                            yield chunk

        except ServerTimeoutError as e:
            error_msg = f"请求超时: {str(e)}"
            logger.error(error_msg)
            raise

        except ClientError as e:
            error_msg = f"客户端错误: {str(e)}"
            logger.error(error_msg)
            raise

        except Exception as e:
            error_msg = f"请求处理异常: {str(e)}"
            logger.error(error_msg)
            raise

    @abstractmethod
    async def stream_chat(
        self, messages: list, model: str
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话，由子类实现

        Args:
            messages: 消息列表
            model: 模型名称

        Yields:
            tuple[str, str]: (内容类型, 内容)
        """
        pass
