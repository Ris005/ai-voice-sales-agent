"""Loads the company knowledge base and system prompt from disk."""
from . import config


def load_knowledge() -> str:
    try:
        return config.KNOWLEDGE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "No knowledge base configured."


def load_system_prompt() -> str:
    try:
        return config.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are {agent_name}, a friendly voice sales agent for {company_name} "
            "speaking with {lead_name} from {lead_company}. Keep replies short.\n"
            "{knowledge_base}"
        )


def build_system_prompt(lead: dict) -> str:
    return load_system_prompt().format(
        agent_name=config.AGENT_NAME,
        company_name=config.COMPANY_NAME,
        lead_name=lead.get("Name", "there"),
        lead_company=lead.get("Company", "your company"),
        knowledge_base=load_knowledge(),
    )
