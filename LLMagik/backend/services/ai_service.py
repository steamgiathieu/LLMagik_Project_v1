"""
services/ai_service.py

Xử lý AI cho 2 tác vụ:
  1. analyze()  — phân tích văn bản theo mode reader/writer
  2. rewrite()  — viết lại một đoạn văn theo mục tiêu

Provider chọn qua AI_PROVIDER trong .env:
  mock | openai | anthropic
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────

# Language name map for prompts
LANGUAGE_NAMES = {
    "vi": "Tiếng Việt (Vietnamese)",
    "en": "English",
    "zh": "中文 (Chinese)",
    "ja": "日本語 (Japanese)",
    "fr": "Français (French)",
}

def _lang_instruction(language: str) -> str:
    """Return a language instruction string for AI prompts."""
    lang_name = LANGUAGE_NAMES.get(language, "Tiếng Việt (Vietnamese)")
    return f"QUAN TRỌNG: Toàn bộ nội dung trong JSON (summary, main_idea, notes, v.v.) PHẢI được viết bằng {lang_name}."


def build_reader_system(language: str = "vi") -> str:
    return f"""Bạn là chuyên gia phân tích văn bản từ góc độ người đọc.
Nhiệm vụ: phân tích văn bản và trả về JSON theo đúng schema. Không thêm text ngoài JSON.
{_lang_instruction(language)}"""

def build_writer_system(language: str = "vi") -> str:
    return f"""Bạn là biên tập viên chuyên nghiệp, phân tích văn bản từ góc độ người viết.
Nhiệm vụ: đánh giá kỹ thuật viết và đề xuất cải thiện, trả về JSON theo đúng schema. Không thêm text ngoài JSON.
{_lang_instruction(language)}"""

def build_rewrite_system(language: str = "vi") -> str:
    return f"""Bạn là biên tập viên chuyên nghiệp. Nhiệm vụ: viết lại MỘT đoạn văn theo mục tiêu cho trước.
Trả về JSON hợp lệ, không có markdown, không có giải thích ngoài JSON.
{_lang_instruction(language)}"""

# Keep backward-compat constants
READER_SYSTEM = build_reader_system("vi")
WRITER_SYSTEM = build_writer_system("vi")
REWRITE_SYSTEM = build_rewrite_system("vi")


def build_analyze_prompt(mode: str, paragraphs: list[dict], language: str = "vi") -> str:
    numbered = "\n\n".join(f"[{p['id']}] {p['text']}" for p in paragraphs)
    schema = json.dumps(_analysis_schema(mode), ensure_ascii=False, indent=2)
    lang_note = _lang_instruction(language)
    return f"""Phân tích văn bản sau theo chế độ "{mode}".

=== VĂN BẢN ===
{numbered}

=== YÊU CẦU OUTPUT ===
{lang_note}
Trả về JSON hợp lệ theo schema (không markdown, không giải thích):
{schema}"""


def build_rewrite_prompt(paragraph_id: str, original_text: str, goal: str, language: str = "vi") -> str:
    schema = json.dumps({
        "rewritten_text": "<rewritten paragraph>",
        "explanation": "<brief explanation of changes>",
    }, ensure_ascii=False, indent=2)
    lang_note = _lang_instruction(language)
    return f"""Viết lại đoạn văn [{paragraph_id}] theo mục tiêu: "{goal}"

=== ĐOẠN VĂN GỐC ===
{original_text}

=== YÊU CẦU ===
- Chỉ viết lại đoạn này, không thay đổi nội dung cốt lõi
- Đạt mục tiêu: {goal}
- {lang_note}
- Trả về JSON theo schema:
{schema}"""


def _analysis_schema(mode: str) -> dict:
    base: dict = {
        "summary": "<tóm tắt 2-3 câu>",
        "tone_analysis": {
            "overall_tone": "<formal|informal|neutral|persuasive|narrative>",
            "sentiment": "<positive|neutral|negative>",
            "confidence_score": 0.85,
        },
        "paragraph_analyses": [{"paragraph_id": "P1", "main_idea": "...", "notes": "..."}],
    }
    if mode == "reader":
        base["key_takeaways"] = ["<điểm cốt lõi 1>", "<điểm cốt lõi 2>"]
        base["reading_difficulty"] = "<easy|medium|hard>"
        base["logic_issues"] = [{"paragraph_id": "P1", "issue": "<vấn đề logic>"}]
    else:
        base["style_issues"] = [{"paragraph_id": "P1", "issue": "...", "severity": "low|medium|high"}]
        base["rewrite_suggestions"] = [{"paragraph_id": "P1", "original": "...", "suggestion": "..."}]
        base["overall_score"] = {"clarity": 7, "coherence": 8, "style": 6, "note": "..."}
    return base


# ─────────────────────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────────────────────

class BaseAIProvider(ABC):
    @abstractmethod
    async def analyze(self, mode: str, paragraphs: list[dict], language: str = "vi") -> dict[str, Any]:
        """Phân tích danh sách đoạn văn, trả về dict."""

    @abstractmethod
    async def rewrite(self, paragraph_id: str, original_text: str, goal: str, language: str = "vi") -> dict[str, Any]:
        """Viết lại một đoạn văn theo mục tiêu, trả về {rewritten_text, explanation}."""

    @abstractmethod
    async def chat(
        self,
        question: str,
        paragraphs: list[dict],
        history: list[dict],
        language: str = "vi",
    ) -> dict[str, Any]:
        """Trả lời câu hỏi dựa trên văn bản, trả về {answer, referenced_paragraphs, confidence, out_of_scope}."""


# ─────────────────────────────────────────────────────────────
# Mock
# ─────────────────────────────────────────────────────────────

class MockAIProvider(BaseAIProvider):

    async def analyze(self, mode: str, paragraphs: list[dict], language: str = "vi") -> dict[str, Any]:
        await _fake_latency()
        para_analyses = [
            {
                "paragraph_id": p["id"],
                "main_idea": f"Ý chính của {p['id']}: {p['text'][:60].rstrip()}...",
                "notes": random.choice([
                    "Đoạn rõ ràng, súc tích.",
                    "Cần thêm ví dụ minh họa.",
                    "Lập luận chặt chẽ, dễ theo dõi.",
                    "Chuyển tiếp sang đoạn sau còn đột ngột.",
                ]),
            }
            for p in paragraphs
        ]
        result: dict[str, Any] = {
            "summary": (
                "Văn bản trình bày một chủ đề với cấu trúc rõ ràng, lập luận logic "
                "và ngôn ngữ phù hợp với đối tượng mục tiêu. [MOCK]"
            ),
            "tone_analysis": {
                "overall_tone": random.choice(["formal", "neutral", "persuasive"]),
                "sentiment": random.choice(["positive", "neutral"]),
                "confidence_score": round(random.uniform(0.70, 0.95), 2),
            },
            "paragraph_analyses": para_analyses,
        }
        if mode == "reader":
            result["key_takeaways"] = [
                "Văn bản có cấu trúc mạch lạc.",
                "Các luận điểm được trình bày tuần tự.",
                "Kết luận rõ ràng và nhất quán.",
            ]
            result["reading_difficulty"] = random.choice(["easy", "medium"])
            result["logic_issues"] = (
                [{"paragraph_id": paragraphs[0]["id"], "issue": "Thiếu dẫn chứng cụ thể."}]
                if paragraphs and random.random() > 0.6 else []
            )
        else:
            result["style_issues"] = [
                {
                    "paragraph_id": p["id"],
                    "issue": random.choice([
                        "Câu quá dài, nên tách thành 2 câu.",
                        "Lặp từ nhiều lần trong đoạn.",
                        "Dùng bị động quá nhiều.",
                    ]),
                    "severity": random.choice(["low", "medium"]),
                }
                for p in paragraphs[:2]
            ]
            result["rewrite_suggestions"] = [
                {
                    "paragraph_id": paragraphs[0]["id"],
                    "original": paragraphs[0]["text"][:80] + "...",
                    "suggestion": "Phiên bản cải thiện: " + paragraphs[0]["text"][:80] + "... [đã chỉnh sửa]",
                }
            ] if paragraphs else []
            result["overall_score"] = {
                "clarity": random.randint(6, 9),
                "coherence": random.randint(6, 9),
                "style": random.randint(5, 8),
                "note": "Văn bản đạt yêu cầu cơ bản. Cần cải thiện tính mạch lạc giữa các đoạn.",
            }
        return result

    async def rewrite(self, paragraph_id: str, original_text: str, goal: str, language: str = "vi") -> dict[str, Any]:
        await _fake_latency()
        g = goal.lower()

        if any(w in g for w in ["trung lập", "khách quan", "neutral"]):
            rewritten = re.sub(
                r"\b(rõ ràng là|chắc chắn|tuyệt vời|hoàn toàn|nhất định)\b",
                "có thể",
                original_text,
            )
            explanation = "Đã thay thế các từ khẳng định mạnh bằng ngôn ngữ trung lập, khách quan hơn."

        elif any(w in g for w in ["rõ ràng", "súc tích", "clear", "concise"]):
            sentences = re.split(r"(?<=[.!?])\s+", original_text.strip())
            cleaned = [s.strip() for s in sentences if len(s.strip()) > 8]
            rewritten = " ".join(cleaned)
            explanation = "Đã loại bỏ cụm từ thừa, rút gọn câu để tăng tính rõ ràng và súc tích."

        elif any(w in g for w in ["trang trọng", "formal", "chuyên nghiệp"]):
            rewritten = (
                original_text
                .replace("bạn", "quý vị")
                .replace("mình", "chúng tôi")
                .replace("tôi", "chúng tôi")
            )
            explanation = "Đã điều chỉnh xưng hô và từ ngữ sang văn phong trang trọng, chuyên nghiệp."

        elif any(w in g for w in ["thân thiện", "gần gũi", "informal", "casual"]):
            rewritten = (
                original_text
                .replace("quý vị", "bạn")
                .replace("chúng tôi", "mình")
            )
            explanation = "Đã chuyển sang giọng văn thân thiện, gần gũi hơn với người đọc."

        elif any(w in g for w in ["ngắn", "short", "tóm tắt", "brief"]):
            words = original_text.split()
            half = max(15, len(words) // 2)
            rewritten = " ".join(words[:half]) + "..."
            explanation = f"Đã rút ngắn đoạn văn từ {len(words)} từ xuống còn ~{half} từ."

        elif any(w in g for w in ["chi tiết", "mở rộng", "expand", "elaborate"]):
            rewritten = (
                original_text.rstrip(".")
                + ". Để hiểu rõ hơn, cần xem xét thêm các khía cạnh liên quan "
                "và bối cảnh cụ thể của vấn đề này."
            )
            explanation = "Đã thêm câu mở rộng để làm rõ và phát triển ý tưởng chính."

        else:
            rewritten = original_text
            explanation = (
                f"Đã xử lý theo mục tiêu '{goal}'. "
                "[MOCK — kết nối AI provider thực để có kết quả viết lại chính xác]"
            )

        return {
            "rewritten_text": rewritten,
            "explanation": explanation + " [MOCK RESPONSE]",
        }


    async def chat(
        self,
        question: str,
        paragraphs: list[dict],
        history: list[dict],
        language: str = "vi",
    ) -> dict[str, Any]:
        await _fake_latency()

        q = question.lower()
        # Simple keyword matching for mock
        matched = [
            p for p in paragraphs
            if any(word in p["text"].lower() for word in q.split() if len(word) > 3)
        ]
        if not matched:
            matched = paragraphs[:2]  # fallback: first 2 paragraphs

        ref_ids = [p["id"] for p in matched[:3]]
        snippet = matched[0]["text"][:120] if matched else ""

        # Detect clearly out-of-scope questions
        out_of_scope_keywords = ["thời tiết", "giá vàng", "bóng đá", "weather", "stock", "recipe"]
        is_oos = any(kw in q for kw in out_of_scope_keywords)

        if is_oos:
            return {
                "answer": "Câu hỏi này không liên quan đến nội dung văn bản đang phân tích. Vui lòng đặt câu hỏi về nội dung tài liệu.",
                "referenced_paragraphs": [],
                "confidence": "high",
                "out_of_scope": True,
            }

        return {
            "answer": (
                f"Dựa trên văn bản (đặc biệt {', '.join(ref_ids)}), "
                f"nội dung liên quan đến câu hỏi là: \"{snippet}...\" "
                f"Đây là câu trả lời mock — kết nối AI provider thực để có phân tích chính xác hơn."
            ),
            "referenced_paragraphs": ref_ids,
            "confidence": random.choice(["high", "medium"]),
            "out_of_scope": False,
        }


async def _fake_latency():
    await asyncio.sleep(random.uniform(0.3, 0.8))


# ─────────────────────────────────────────────────────────────
# OpenAI
# ─────────────────────────────────────────────────────────────

class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        except ImportError:
            raise RuntimeError("Cài đặt openai: pip install openai")

    async def analyze(self, mode: str, paragraphs: list[dict], language: str = "vi") -> dict[str, Any]:
        system = build_reader_system(language) if mode == "reader" else build_writer_system(language)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": build_analyze_prompt(mode, paragraphs, language)},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return _safe_parse(response.choices[0].message.content or "{}")

    async def rewrite(self, paragraph_id: str, original_text: str, goal: str, language: str = "vi") -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": build_rewrite_system(language)},
                {"role": "user", "content": build_rewrite_prompt(paragraph_id, original_text, goal, language)},
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
        )
        return _safe_parse(response.choices[0].message.content or "{}")

    async def chat(
        self,
        question: str,
        paragraphs: list[dict],
        history: list[dict],
        language: str = "vi",
    ) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": build_chat_system(language)},
                {"role": "user", "content": build_chat_prompt(question, paragraphs, history, language)},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return _safe_parse(response.choices[0].message.content or "{}")


# ─────────────────────────────────────────────────────────────
# Anthropic
# ─────────────────────────────────────────────────────────────

class AnthropicProvider(BaseAIProvider):
    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        except ImportError:
            raise RuntimeError("Cài đặt anthropic: pip install anthropic")

    async def analyze(self, mode: str, paragraphs: list[dict], language: str = "vi") -> dict[str, Any]:
        system = build_reader_system(language) if mode == "reader" else build_writer_system(language)
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": build_analyze_prompt(mode, paragraphs, language)}],
        )
        raw = message.content[0].text if message.content else "{}"
        return _safe_parse(raw)

    async def rewrite(self, paragraph_id: str, original_text: str, goal: str, language: str = "vi") -> dict[str, Any]:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=build_rewrite_system(language),
            messages=[{"role": "user", "content": build_rewrite_prompt(paragraph_id, original_text, goal, language)}],
        )
        raw = message.content[0].text if message.content else "{}"
        return _safe_parse(raw)

    async def chat(
        self,
        question: str,
        paragraphs: list[dict],
        history: list[dict],
        language: str = "vi",
    ) -> dict[str, Any]:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=build_chat_system(language),
            messages=[{"role": "user", "content": build_chat_prompt(question, paragraphs, history, language)}],
        )
        raw = message.content[0].text if message.content else "{}"
        return _safe_parse(raw)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _safe_parse(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "AI trả về JSON không hợp lệ", "raw": raw[:500]}


# ─────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────

_provider_cache: BaseAIProvider | None = None


def get_provider() -> BaseAIProvider:
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache
    name = os.getenv("AI_PROVIDER", "mock").lower()
    if name == "openai":
        _provider_cache = OpenAIProvider()
    elif name == "anthropic":
        _provider_cache = AnthropicProvider()
    else:
        _provider_cache = MockAIProvider()
    return _provider_cache

# ─────────────────────────────────────────────────────────────
# Chat prompt builder (shared)
# ─────────────────────────────────────────────────────────────

# Keep backward-compat constant
CHAT_SYSTEM = """Bạn là trợ lý phân tích văn bản. Quy tắc bắt buộc:
1. Chỉ trả lời dựa trên nội dung văn bản được cung cấp — không dùng kiến thức bên ngoài.
2. Nếu câu hỏi không liên quan đến văn bản, hãy nói rõ điều đó.
3. Trích dẫn cụ thể đoạn nào (P1, P2...) là cơ sở cho câu trả lời.
4. Trả về JSON hợp lệ, không có markdown, không có text ngoài JSON."""


def build_chat_system(language: str = "vi") -> str:
    return f"""Bạn là trợ lý phân tích văn bản. Quy tắc bắt buộc:
1. Chỉ trả lời dựa trên nội dung văn bản được cung cấp — không dùng kiến thức bên ngoài.
2. Nếu câu hỏi không liên quan đến văn bản, hãy nói rõ điều đó.
3. Trích dẫn cụ thể đoạn nào (P1, P2...) là cơ sở cho câu trả lời.
4. Trả về JSON hợp lệ, không có markdown, không có text ngoài JSON.
5. {_lang_instruction(language)}"""


def build_chat_prompt(question: str, paragraphs: list[dict], history: list[dict], language: str = "vi") -> str:
    context = "\n\n".join(f"[{p['id']}] {p['text']}" for p in paragraphs)
    lang_note = _lang_instruction(language)

    history_block = ""
    if history:
        lines = []
        for turn in history[-6:]:          # tối đa 6 turns gần nhất
            role = "Người dùng" if turn["role"] == "user" else "Trợ lý"
            lines.append(f"{role}: {turn['content']}")
        history_block = "\n=== LỊCH SỬ HỘI THOẠI ===\n" + "\n".join(lines)

    schema = json.dumps({
        "answer": "<answer based on the document, 2-5 sentences>",
        "referenced_paragraphs": ["P1", "P2"],
        "confidence": "<high|medium|low>",
        "out_of_scope": False,
    }, ensure_ascii=False, indent=2)

    return f"""Văn bản được phân tích:
=== NỘI DUNG VĂN BẢN ==={history_block}
{context}

=== CÂU HỎI ===
{question}

=== YÊU CẦU OUTPUT ===
{lang_note}
Trả về JSON theo schema (không markdown, không giải thích):
{schema}

Lưu ý:
- referenced_paragraphs: danh sách ID đoạn thực sự được dùng làm cơ sở trả lời
- out_of_scope: true nếu câu hỏi nằm ngoài phạm vi văn bản
- Nếu out_of_scope là true, answer phải giải thích tại sao không trả lời được"""
