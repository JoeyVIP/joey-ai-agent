from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LINE Bot
    line_channel_secret: str = Field(..., description="LINE Channel Secret")
    line_channel_access_token: str = Field(..., description="LINE Channel Access Token")
    joey_line_user_id: str = Field(..., description="Joey's LINE User ID for push notifications")

    # Notion
    notion_api_key: str = Field(..., description="Notion Integration Token")
    notion_inbox_db_id: str = Field(..., description="Notion Inbox Database ID")
    notion_review_db_id: str = Field(..., description="Notion Review Database ID")
    notion_memory_db_id: str = Field(..., description="Notion Memory Database ID")

    # Anthropic
    anthropic_api_key: str = Field(..., description="Anthropic API Key")
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use"
    )

    # Claude Code
    claude_code_oauth_token: str = Field(
        default="",
        description="Claude Code OAuth Token for headless/SSH execution"
    )

    # External Service Tokens (used by MCP servers)
    github_token: str = Field(
        default="",
        description="GitHub Personal Access Token"
    )
    railway_token: str = Field(
        default="",
        description="Railway API Token (deprecated, use Render)"
    )
    render_api_key: str = Field(
        default="",
        description="Render API Key for deployment"
    )

    # Database
    database_url: str = Field(
        default="sqlite:///./joey_ai_agent.db",
        description="Database connection URL"
    )

    # GitHub OAuth (for Web Frontend)
    github_oauth_client_id: str = Field(
        default="",
        description="GitHub OAuth App Client ID"
    )
    github_oauth_client_secret: str = Field(
        default="",
        description="GitHub OAuth App Client Secret"
    )
    nextauth_secret: str = Field(
        default="",
        description="NextAuth.js secret key"
    )
    nextauth_url: str = Field(
        default="http://localhost:3000",
        description="NextAuth.js app URL"
    )

    # App
    app_env: str = Field(default="development", description="Application environment")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        description="Comma-separated CORS allowed origins"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore any extra env vars not defined here


settings = Settings()
