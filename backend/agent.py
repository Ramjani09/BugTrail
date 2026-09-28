import os
import json
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from backend.models import BugReport, MemoryItem, InvestigationResult

logger = logging.getLogger("bugtrail.agent")

class BugTrailAgent:
    def __init__(self):
        self.api_key = ""
        self.client = None
        self._reload_and_init()

    def _reload_and_init(self):
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None
        else:
            self.client = None

    def is_gemini_connected(self) -> bool:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        current_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if current_key != self.api_key or (current_key and not self.client):
            self._reload_and_init()

        return self.client is not None

    def investigate(self, bug: BugReport, memories: List[MemoryItem], hindsight_connected: bool) -> InvestigationResult:
        hindsight_status_str = "Connected" if hindsight_connected else "Not Connected"

        # Try using Gemini if API key is present
        if self.is_gemini_connected():
            try:
                return self._investigate_with_gemini(bug, memories, hindsight_status_str)
            except Exception as e:
                logger.error(f"Gemini investigation failed ({e}), falling back to Demo Mode reasoning engine.")

        # Fallback to Demo Mode reasoning engine
        return self._investigate_demo_fallback(bug, memories, hindsight_status_str)

    def _investigate_with_gemini(self, bug: BugReport, memories: List[MemoryItem], hindsight_status: str) -> InvestigationResult:
        memories_text = ""
        if memories:
            memories_text = "RECALLED PREVIOUS BUG EXPERIENCES FROM HINDSIGHT:\n"
            for i, mem in enumerate(memories, 1):
                memories_text += f"{i}. INCIDENT: {mem.incident}\n   ROOT CAUSE: {mem.root_cause}\n   FIX: {mem.fix}\n   LESSON/CONTEXT: {mem.context}\n\n"
        else:
            memories_text = "RECALLED PREVIOUS BUG EXPERIENCES FROM HINDSIGHT: None found.\n"

        prompt = f"""You are BugTrail, an expert AI bug-investigation memory agent.
Your mission: Investigate the software bug using both current bug details and relevant past bug memories recalled from Hindsight.

CURRENT BUG REPORT:
Title: {bug.title}
Description: {bug.description}
Environment: {bug.environment}
Recent Change: {bug.recent_change}
Error/Log Details: {bug.error_logs}

{memories_text}

INSTRUCTIONS:
1. If relevant past bug memories are present above, weigh them HEAVILY in your analysis. Your recommendations MUST explicitly reference past successful fixes and prioritize investigation steps that align with past lessons learned.
2. If no past memories exist, provide standard investigation steps based on general engineering heuristics.
3. You MUST respond with ONLY a valid JSON object matching this exact structure:
{{
  "probable_cause": "Detailed summary of the most likely root cause",
  "investigation_steps": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "recommended_first_check": "The single highest priority action or check to execute first",
  "why_recommendation_made": "Clear explanation of why this check is recommended (explicitly state if past Hindsight memory influenced this)",
  "confidence_explanation": "High / Medium / Low with reasoning",
  "memory_influenced": true_or_false
}}
"""
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        parsed = json.loads(response_text)
        return InvestigationResult(
            probable_cause=parsed.get("probable_cause", "Likely post-deployment configuration or service error."),
            investigation_steps=parsed.get("investigation_steps", ["Inspect recent deployment diffs", "Check application logs"]),
            recommended_first_check=parsed.get("recommended_first_check", "Check recent database configuration modifications."),
            why_recommendation_made=parsed.get("why_recommendation_made", "Based on recent changes and error symptoms."),
            confidence_explanation=parsed.get("confidence_explanation", "High confidence based on LLM analysis."),
            memory_influenced=bool(parsed.get("memory_influenced", len(memories) > 0)),
            memories_recalled=memories,
            ai_mode="Gemini AI",
            hindsight_status=hindsight_status
        )

    def _investigate_demo_fallback(self, bug: BugReport, memories: List[MemoryItem], hindsight_status: str) -> InvestigationResult:
        has_memory = len(memories) > 0

        if has_memory:
            ref_mem = memories[0]
            return InvestigationResult(
                probable_cause=f"Likely recurring issue matching prior incident '{ref_mem.incident}'. Root cause previously identified: {ref_mem.root_cause}",
                investigation_steps=[
                    f"1. Check {ref_mem.root_cause.lower()} as identified in past incident.",
                    f"2. Apply fix: {ref_mem.fix}",
                    "3. Verify network access and credentials between API container and target service.",
                    "4. Compare deployment configuration diff against prior working release."
                ],
                recommended_first_check=f"Apply proven fix from memory: {ref_mem.fix}",
                why_recommendation_made=f"Recalled previous resolved incident '{ref_mem.incident}' from Hindsight where fixing '{ref_mem.root_cause}' resolved the issue. Lesson: {ref_mem.context or 'Follow prior resolution path.'}",
                confidence_explanation="High (95%) - Recalled matching resolution experience from Hindsight memory bank.",
                memory_influenced=True,
                memories_recalled=memories,
                ai_mode="Demo Mode",
                hindsight_status=hindsight_status
            )
        else:
            # Baseline heuristic response when no memories are present
            return InvestigationResult(
                probable_cause="Generic post-deployment service initialization failure or configuration mismatch.",
                investigation_steps=[
                    "1. Review recent deployment changes and configuration file diffs.",
                    "2. Inspect application server stdout/stderr logs for unhandled connection exceptions.",
                    "3. Verify database connectivity and environment variables in the production environment."
                ],
                recommended_first_check="Inspect recent deployment configuration changes and DB connection error logs.",
                why_recommendation_made="General engineering heuristic: HTTP 500 errors following recent deployment configuration changes indicate a setup or environment mismatch.",
                confidence_explanation="Moderate (65%) - Baseline heuristic analysis (no prior bug memories found in Hindsight).",
                memory_influenced=False,
                memories_recalled=[],
                ai_mode="Demo Mode",
                hindsight_status=hindsight_status
            )

agent = BugTrailAgent()
