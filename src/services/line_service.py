import logging

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.config import settings

logger = logging.getLogger(__name__)


class LineService:
    """LINE Messaging API 服務"""
    def __init__(self):
        self.handler = WebhookHandler(settings.line_channel_secret)
        self.configuration = Configuration(
            access_token=settings.line_channel_access_token
        )
        self.joey_user_id = settings.joey_line_user_id

    def verify_signature(self, body: str, signature: str) -> bool:
        """Verify LINE webhook signature."""
        try:
            self.handler.handle(body, signature)
            return True
        except InvalidSignatureError:
            logger.warning("LINE 簽名驗證失敗")
            return False

    async def reply_message(self, reply_token: str, message: str) -> None:
        """Reply to a LINE message."""
        try:
            with ApiClient(self.configuration) as api_client:
                api = MessagingApi(api_client)
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=message)]
                    )
                )
            logger.debug(f"LINE 回覆訊息成功: {message[:50]}...")
        except Exception as e:
            logger.error(f"LINE 回覆訊息失敗: {e}")
            raise

    async def push_message(self, user_id: str, message: str) -> None:
        """Push a message to a user."""
        try:
            with ApiClient(self.configuration) as api_client:
                api = MessagingApi(api_client)
                api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[TextMessage(text=message)]
                    )
                )
            logger.debug(f"LINE 推送訊息成功至 {user_id[:8]}...: {message[:50]}...")
        except Exception as e:
            logger.error(f"LINE 推送訊息失敗至 {user_id[:8]}...: {e}")
            raise

    async def push_to_joey(self, message: str) -> None:
        """Push a message to Joey."""
        logger.info(f"推送訊息給 Joey: {message[:50]}...")
        await self.push_message(self.joey_user_id, message)

    def get_handler(self) -> WebhookHandler:
        """Get the webhook handler for registering event handlers."""
        return self.handler


line_service = LineService()
