"""
Central configuration for Splunk Zero.
Loads all settings from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)


class Config:
    """Application configuration loaded from environment variables."""

    # Splunk
    SPLUNK_HOST: str = os.getenv("SPLUNK_HOST", "localhost")
    SPLUNK_PORT: int = int(os.getenv("SPLUNK_PORT", "8089"))
    SPLUNK_TOKEN: str = os.getenv("SPLUNK_TOKEN", "")  # MCP Encrypted Token
    SPLUNK_USERNAME: str = os.getenv("SPLUNK_USERNAME", "admin")
    SPLUNK_PASSWORD: str = os.getenv("SPLUNK_PASSWORD", "")  # For REST API fallback
    SPLUNK_MCP_URL: str = os.getenv(
        "SPLUNK_MCP_URL", f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/mcp"
    )

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "")
    GITHUB_BRANCH_PREFIX: str = os.getenv("GITHUB_BRANCH_PREFIX", "splunk-zero")

    # LLM
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite")

    # App settings
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    COST_PER_GB_PER_DAY: float = float(os.getenv("COST_PER_GB_PER_DAY", "15"))
    WASTE_THRESHOLD_PCT: float = float(os.getenv("WASTE_THRESHOLD_PCT", "5"))
    MIN_SEARCH_COUNT: int = int(os.getenv("MIN_SEARCH_COUNT", "2"))
    ANALYSIS_PERIOD_DAYS: int = int(os.getenv("ANALYSIS_PERIOD_DAYS", "30"))

    @classmethod
    def validate(cls) -> list[str]:
        """Check for missing required config. Returns list of missing keys."""
        missing = []
        if not cls.SPLUNK_TOKEN:
            missing.append("SPLUNK_TOKEN")
        if not cls.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN")
        if not cls.GITHUB_REPO:
            missing.append("GITHUB_REPO")
        if not cls.GOOGLE_API_KEY:
            missing.append("GOOGLE_API_KEY")
        return missing

    @classmethod
    def print_status(cls):
        """Print config status for debugging."""
        def check(val):
            return "[OK] set" if val else "[!!] missing"

        print("=" * 50)
        print("  Splunk Zero -- Configuration Status")
        print("=" * 50)
        print(f"  Splunk Host:    {cls.SPLUNK_HOST}:{cls.SPLUNK_PORT}")
        print(f"  Splunk Token:   {check(cls.SPLUNK_TOKEN)}")
        print(f"  MCP URL:        {cls.SPLUNK_MCP_URL}")
        print(f"  GitHub Repo:    {cls.GITHUB_REPO or '[!!] missing'}")
        print(f"  GitHub Token:   {check(cls.GITHUB_TOKEN)}")
        print(f"  Google API Key: {check(cls.GOOGLE_API_KEY)}")
        print(f"  LLM Model:      {cls.LLM_MODEL}")
        print(f"  Cost/GB/Day:    ${cls.COST_PER_GB_PER_DAY}")
        print(f"  Waste Threshold: {cls.WASTE_THRESHOLD_PCT}%")
        print(f"  Analysis Period: {cls.ANALYSIS_PERIOD_DAYS} days")
        print("=" * 50)

        missing = cls.validate()
        if missing:
            print(f"\n  [WARNING] Missing: {', '.join(missing)}")
            print("  Copy .env.example to .env and fill in your values.")
        else:
            print("\n  [OK] All configuration present.")
        print()
