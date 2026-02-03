import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from src.services.line_service import line_service
from src.services.task_processor import task_processor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["line"])


async def process_message_background(user_input: str, user_id: str):
    """Background task to process LINE message."""
    try:
        await task_processor.process_task(
            user_input=user_input,
            source="line"
        )
    except Exception as e:
        logger.error(f"Background task failed: {e}", exc_info=True)


@router.post("/webhook/line")
async def line_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    LINE Webhook endpoint.

    Flow:
    1. Verify signature
    2. Parse events
    3. Reply immediately with "收到，處理中"
    4. Process task in background
    """
    # Get signature from header
    signature = request.headers.get("X-Line-Signature", "")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")

    # Parse the webhook body manually to extract events
    import json
    try:
        body_json = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Verify signature
    try:
        # We need to verify signature manually since we're not using the handler
        import hashlib
        import hmac
        import base64
        from src.config import settings

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

    # Process events
    events = body_json.get("events", [])

    for event in events:
        # Only handle text messages
        if event.get("type") != "message":
            continue
        if event.get("message", {}).get("type") != "text":
            continue

        reply_token = event.get("replyToken")
        user_id = event.get("source", {}).get("userId")
        user_input = event.get("message", {}).get("text", "")

        if not user_input:
            continue

        logger.info(f"Received message from {user_id}: {user_input[:50]}...")

        # Reply immediately
        try:
            await line_service.reply_message(
                reply_token=reply_token,
                message="📝 收到，處理中..."
            )
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

        # Add background task
        background_tasks.add_task(
            process_message_background,
            user_input=user_input,
            user_id=user_id
        )

    return {"status": "ok"}
