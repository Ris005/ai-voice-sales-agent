"""Central configuration. Everything is overridable via environment variables
so the same build runs locally and on Render with zero code changes."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"
STATIC_DIR = BASE_DIR / "static"

# Excel CRM location. On Render, point this at a mounted disk to persist edits.
CRM_PATH = Path(os.getenv("CRM_PATH", DATA_DIR / "leads.xlsx"))
KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_PATH", DATA_DIR / "knowledge_base.md"))
SYSTEM_PROMPT_PATH = Path(os.getenv("SYSTEM_PROMPT_PATH", PROMPTS_DIR / "system_prompt.txt"))

# LLM. If OPENAI_API_KEY is unset, the agent transparently falls back to a
# built-in rule-based sales brain so the app runs with zero configuration.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

COMPANY_NAME = os.getenv("COMPANY_NAME", "Nimbus CRM")
AGENT_NAME = os.getenv("AGENT_NAME", "Aria")
