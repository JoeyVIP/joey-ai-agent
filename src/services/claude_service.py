import json
from pathlib import Path
from anthropic import Anthropic

from src.config import settings
from src.models.claude_response import ClaudeResponse


class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self._system_prompt = None

    @property
    def system_prompt(self) -> str:
        """Load system prompt from file (cached)."""
        if self._system_prompt is None:
            prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
            self._system_prompt = prompt_path.read_text(encoding="utf-8")
        return self._system_prompt

    async def process_task(
        self,
        user_input: str,
        memories: str
    ) -> ClaudeResponse:
        """Process a task with Claude and return structured response."""

        # Build the user message with context
        user_message = f"""## Joey 的記憶

{memories}

---

## Joey 的任務

{user_input}

---

請以 JSON 格式回應。"""

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Extract text content
        content = response.content[0].text

        # Parse JSON from response
        parsed = self._parse_json_response(content)

        return parsed

    def _parse_json_response(self, content: str) -> ClaudeResponse:
        """Parse JSON response from Claude, handling various formats."""

        # Try to find JSON in the response
        json_str = content

        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            json_str = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            json_str = content[start:end].strip()

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # If parsing fails, create a fallback response
            return ClaudeResponse(
                difficulty="simple",
                title="處理結果",
                simple_result={
                    "summary": "AI 回應（非結構化）",
                    "result": content
                },
                memory_updates=[],
                line_message="處理完成，請查看 Notion Review"
            )

        # Validate and create ClaudeResponse
        return ClaudeResponse(**data)


claude_service = ClaudeService()
