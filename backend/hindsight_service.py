import os
import logging
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv
from backend.models import BugResolution, MemoryItem

logger = logging.getLogger("bugtrail.hindsight")

HINDSIGHT_BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
MEMORY_BANK_ID = "bugtrail-memory"

class HindsightService:
    def __init__(self):
        self.api_key = ""
        self.client = None
        self._connected = False
        self._demo_memory_store: List[MemoryItem] = []
        self._reload_and_init()

    def _reload_and_init(self):
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)

        self.api_key = os.environ.get("HINDSIGHT_API_KEY", "").strip()
        if not self.api_key:
            logger.info("HINDSIGHT_API_KEY is not configured in .env. Hindsight running in local fallback memory mode.")
            self._connected = False
            self.client = None
            return

        try:
            from hindsight_client import Hindsight
            self.client = Hindsight(base_url=HINDSIGHT_BASE_URL, api_key=self.api_key)
            logger.info(f"Hindsight client initialized with base URL {HINDSIGHT_BASE_URL}.")
            self._ensure_bank()
        except Exception as e:
            logger.error(f"Failed to initialize Hindsight client: {e}")
            self._connected = False
            self.client = None

    def is_connected(self) -> bool:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        current_key = os.environ.get("HINDSIGHT_API_KEY", "").strip()

        if current_key != self.api_key or (current_key and not self.client):
            self._reload_and_init()

        return self._connected and self.client is not None

    def _ensure_bank(self):
        if not self.client:
            self._connected = False
            return

        try:
            self.client.create_bank(
                bank_id=MEMORY_BANK_ID,
                name="BugTrail Bug Memories",
                background="Stores software engineering bug reports, root cause analyses, resolutions, and lessons learned."
            )
            logger.info(f"Memory bank '{MEMORY_BANK_ID}' created successfully.")
            self._connected = True
        except Exception as e:
            err_str = str(e).lower()
            if "already exists" in err_str or "409" in err_str or "conflict" in err_str:
                logger.info(f"Memory bank '{MEMORY_BANK_ID}' already exists and is connected.")
                self._connected = True
            else:
                logger.warning(f"Hindsight bank check/create failed: {e}")
                self._connected = False

    def retain_resolution(self, resolution: BugResolution) -> Tuple[bool, str]:
        content_str = (
            f"[BUG INCIDENT]: {resolution.bug_title}\n"
            f"[ROOT CAUSE]: {resolution.root_cause}\n"
            f"[FIX APPLIED]: {resolution.fix_applied}\n"
            f"[RESULT]: {resolution.result}\n"
            f"[ADDITIONAL LESSON]: {resolution.additional_lesson}"
        )

        # 1. Store in real Hindsight Cloud if key is configured
        if self.is_connected():
            try:
                res = self.client.retain(
                    bank_id=MEMORY_BANK_ID,
                    content=content_str,
                    metadata={
                        "type": "bug_resolution",
                        "title": resolution.bug_title
                    }
                )
                logger.info(f"Successfully retained resolution to Hindsight bank '{MEMORY_BANK_ID}': {res}")
                return True, "✓ Bug experience saved to Hindsight Cloud memory"
            except Exception as e:
                logger.error(f"Error retaining resolution to Hindsight: {e}")
                return False, f"Failed to save resolution to Hindsight: {str(e)}"

        # 2. Local session memory fallback if HINDSIGHT_API_KEY is not configured
        mem_item = MemoryItem(
            incident=resolution.bug_title,
            root_cause=resolution.root_cause,
            fix=resolution.fix_applied,
            context=f"{resolution.result} {resolution.additional_lesson}".strip()
        )
        # Prevent duplicates in demo store
        if not any(m.incident == mem_item.incident for m in self._demo_memory_store):
            self._demo_memory_store.append(mem_item)
            
        return True, "✓ Bug experience saved to memory (Session Demo Store)"

    def recall_memories(self, query: str) -> List[MemoryItem]:
        # 1. Query real Hindsight Cloud if key is configured
        if self.is_connected():
            try:
                res = self.client.recall(
                    bank_id=MEMORY_BANK_ID,
                    query=query,
                    budget="mid"
                )

                memories: List[MemoryItem] = []
                if hasattr(res, 'results') and res.results:
                    for item in res.results:
                        text_content = getattr(item, 'text', '') or ''
                        context_content = getattr(item, 'context', '') or ''
                        metadata = getattr(item, 'metadata', {}) or {}
                        if text_content:
                            mem_item = self._parse_memory_text(text_content, context_content, metadata)
                            memories.append(mem_item)
                return memories
            except Exception as e:
                logger.error(f"Error recalling memories from Hindsight: {e}")
                return []

        # 2. Local session memory fallback if HINDSIGHT_API_KEY is not configured
        if self._demo_memory_store:
            return list(self._demo_memory_store)

        return []

    def _parse_memory_text(self, text: str, default_context: str = "", metadata: dict = None) -> MemoryItem:
        incident = "Past Bug Incident"
        root_cause = "Not specified"
        fix = "Not specified"
        context = default_context

        for line in text.splitlines():
            line_str = line.strip()
            if line_str.startswith("[BUG INCIDENT]:"):
                incident = line_str.replace("[BUG INCIDENT]:", "").strip()
            elif line_str.startswith("[ROOT CAUSE]:"):
                root_cause = line_str.replace("[ROOT CAUSE]:", "").strip()
            elif line_str.startswith("[FIX APPLIED]:"):
                fix = line_str.replace("[FIX APPLIED]:", "").strip()
            elif line_str.startswith("[ADDITIONAL LESSON]:"):
                context = line_str.replace("[ADDITIONAL LESSON]:", "").strip()

        if incident == "Past Bug Incident":
            if metadata and isinstance(metadata, dict) and metadata.get("title"):
                incident = metadata["title"]
            elif text:
                incident = text[:80] + "..." if len(text) > 80 else text
                context = text

        return MemoryItem(
            incident=incident,
            root_cause=root_cause,
            fix=fix,
            context=context
        )

# Global service instance
hindsight_service = HindsightService()
