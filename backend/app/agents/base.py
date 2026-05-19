"""Agent基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.core.logger import logger
from app.core.config import settings


class BaseAgent(ABC):
    """Agent抽象基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """初始化LLM（支持 OpenAI / DeepSeek）"""
        try:
            from langchain_openai import ChatOpenAI
        except Exception:
            logger.info(f"{self.name}: langchain_openai 未安装，使用规则引擎模式")
            return

        # 优先使用 DeepSeek
        if settings.DEEPSEEK_API_KEY:
            try:
                self.llm = ChatOpenAI(
                    model=settings.DEEPSEEK_MODEL,
                    temperature=0,
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_BASE_URL,
                )
                logger.info(f"{self.name}: DeepSeek LLM 初始化成功（模型={settings.DEEPSEEK_MODEL}）")
                return
            except Exception as e:
                logger.warning(f"{self.name}: DeepSeek 初始化失败: {e}")

        # 其次使用 OpenAI
        if settings.OPENAI_API_KEY:
            try:
                self.llm = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    temperature=0,
                    api_key=settings.OPENAI_API_KEY,
                )
                logger.info(f"{self.name}: OpenAI LLM 初始化成功")
                return
            except Exception as e:
                logger.warning(f"{self.name}: OpenAI 初始化失败: {e}")

        logger.info(f"{self.name}: 无可用LLM，使用规则引擎模式")

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent任务"""
        pass

    async def _llm_invoke(self, prompt: str) -> str:
        """调用LLM，失败时返回空字符串"""
        if not self.llm:
            return ""
        try:
            logger.info(f"{self.name}: 正在调用LLM...")
            result = await self.llm.ainvoke(prompt)
            content = result.content
            logger.info(f"{self.name}: LLM响应成功，长度={len(content)}")
            return content
        except Exception as e:
            logger.error(f"{self.name} LLM调用失败: {e}")
            return ""

    def _extract_json(self, text: str) -> dict:
        """从LLM响应中提取JSON（支持markdown代码块包裹）"""
        import json
        import re
        # 尝试从markdown代码块中提取
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        # 直接尝试解析
        try:
            return json.loads(text)
        except Exception:
            pass
        # 尝试找最外层大括号
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
        return None
