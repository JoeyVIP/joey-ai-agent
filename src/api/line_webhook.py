import logging
import json
import hashlib
import hmac
import base64
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

from src.services.line_service import line_service
from src.services.task_processor import task_processor
from src.config import settings
from src.constants import (
    LINE_MESSAGE_PREVIEW_LENGTH,
    LINE_LOG_MESSAGE_LENGTH,
    LINE_FILE_LOG_MESSAGE_LENGTH,
    USER_IDS_LOG_FILENAME,
)

# 專案根目錄（從 src/api/ 往上兩層）
PROJECT_ROOT = Path(__file__).parent.parent.parent

logger = logging.getLogger(__name__)
router = APIRouter(tags=["line"])

# 總管理員（Joey）
ADMIN_USER_ID = settings.joey_line_user_id

# 授權使用者清單（ID -> 名稱）
AUTHORIZED_USERS = {
    settings.joey_line_user_id: "Joey",
    "U07923894d7eb396901da0796ee96d0c6": "Cindy",
}


async def process_message_background(user_input: str, user_id: str, user_name: str):
    """Background task to process LINE message."""
    try:
        await task_processor.process_task(
            user_input=user_input,
            source="line"
        )
    except Exception as e:
        logger.error(f"Background task failed: {e}", exc_info=True)


async def notify_admin(user_name: str, user_input: str):
    """通知管理員有使用者提出請求"""
    try:
        # 截斷過長的訊息
        preview = user_input[:LINE_MESSAGE_PREVIEW_LENGTH] + "..." if len(user_input) > LINE_MESSAGE_PREVIEW_LENGTH else user_input
        notification = f"📢 {user_name} 提出請求：\n\n{preview}"
        await line_service.push_to_joey(notification)
        logger.info(f"Admin notified about {user_name}'s request")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")


@router.post("/webhook/line")
async def line_webhook(request: Request, background_tasks: BackgroundTasks):
    """LINE Webhook endpoint with user authorization."""

    signature = request.headers.get("X-Line-Signature", "")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        body_json = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Verify signature
    try:
        channel_secret = settings.line_channel_secret
        hash_value = hmac.new(
            channel_secret.encode("utf-8"),
            body_str.encode("utf-8"),
            hashlib.sha256
        ).digest()
        computed_signature = base64.b64encode(hash_value).decode("utf-8")

        if signature != computed_signature:
            raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    events = body_json.get("events", [])

    for event in events:
        if event.get("type") != "message":
            continue
        if event.get("message", {}).get("type") != "text":
            continue

        reply_token = event.get("replyToken")
        user_id = event.get("source", {}).get("userId")
        user_input = event.get("message", {}).get("text", "")

        # Log all incoming messages
        log_file = PROJECT_ROOT / USER_IDS_LOG_FILENAME
        with open(log_file, "a") as f:
            f.write(f"User ID: {user_id}, Message: {user_input[:LINE_FILE_LOG_MESSAGE_LENGTH]}\n")

        logger.info(f"Received message from {user_id}: {user_input[:LINE_LOG_MESSAGE_LENGTH]}...")

        if not user_input:
            continue

        # 檢查使用者是否授權
        if user_id not in AUTHORIZED_USERS:
            logger.warning(f"Unauthorized user: {user_id}")
            try:
                await line_service.reply_message(
                    reply_token=reply_token,
                    message="抱歉，你目前沒有使用權限。請聯繫管理員。"
                )
            except Exception as e:
                logger.error(f"Failed to send unauthorized reply: {e}")
            continue

        # 取得使用者名稱
        user_name = AUTHORIZED_USERS[user_id]

        # 如果不是管理員，通知管理員有人提出請求
        if user_id != ADMIN_USER_ID:
            await notify_admin(user_name, user_input)

        # 授權使用者 - 回覆確認訊息
        try:
            await line_service.reply_message(
                reply_token=reply_token,
                message=f"📝 收到，{user_name}！處理中..."
            )
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

        background_tasks.add_task(
            process_message_background,
            user_input=user_input,
            user_id=user_id,
            user_name=user_name
        )

    return {"status": "ok"}
