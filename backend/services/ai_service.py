"""
services/ai_service.py

Xử lý AI cho 2 tác vụ:
  1. analyze()  — phân tích văn bản theo mode reader/writer
  2. rewrite()  — viết lại một đoạn văn theo mục tiêu

Provider chọn qua AI_PROVIDER trong .env:
  mock | openai | openrouter | anthropic
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

def _normalize_language(language: str | None) -> str:
    if not language:
        return "vi"
    code = language.strip().lower()
    return code if code in LANGUAGE_NAMES else "vi"


def _lang_instruction(language: str) -> str:
    """Return a language instruction string for AI prompts."""
    lang_name = LANGUAGE_NAMES.get(_normalize_language(language), "Tiếng Việt (Vietnamese)")
    return f"QUAN TRỌNG: Toàn bộ nội dung trong JSON (summary, main_idea, notes, v.v.) PHẢI được viết bằng {lang_name}."


def build_reader_system(language: str = "vi") -> str:
    language = _normalize_language(language)
    return f"""Bạn là chuyên gia phân tích văn bản từ góc độ người đọc.
Nhiệm vụ: phân tích văn bản và trả về JSON theo đúng schema. Không thêm text ngoài JSON.
{_lang_instruction(language)}"""

def build_writer_system(language: str = "vi") -> str:
    language = _normalize_language(language)
    return f"""Bạn là biên tập viên chuyên nghiệp, phân tích văn bản từ góc độ người viết.
Nhiệm vụ: đánh giá kỹ thuật viết và đề xuất cải thiện, trả về JSON theo đúng schema. Không thêm text ngoài JSON.
{_lang_instruction(language)}"""

def build_rewrite_system(language: str = "vi") -> str:
    language = _normalize_language(language)
    return f"""Bạn là biên tập viên chuyên nghiệp. Nhiệm vụ: viết lại MỘT đoạn văn theo mục tiêu cho trước.
Trả về JSON hợp lệ, không có markdown, không có giải thích ngoài JSON.
{_lang_instruction(language)}"""

# Keep backward-compat constants
READER_SYSTEM = build_reader_system("vi")
WRITER_SYSTEM = build_writer_system("vi")
REWRITE_SYSTEM = build_rewrite_system("vi")


def build_analyze_prompt(mode: str, paragraphs: list[dict], language: str = "vi") -> str:
    language = _normalize_language(language)
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
    language = _normalize_language(language)
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
        base["reading_difficulty"] = "<easy|medium|hard (legacy)>"
        base["readability_metrics"] = {
            "accessibility_score": 78,
            "accessibility_label": "<dễ tiếp cận|trung bình|chuyên sâu>",
            "avg_sentence_length_words": 17.4,
            "long_sentence_ratio": 0.22,
            "lexical_diversity": 0.48,
            "recommended_reader_profile": "<phổ thông|đại học|chuyên môn>",
            "note": "<nhận xét ngắn về mức dễ đọc dựa trên chỉ số>",
        }
        base["claim_checks"] = [{
            "paragraph_id": "P1",
            "claim": "<một phát biểu chính cần kiểm chứng>",
            "evidence_in_text": "<chứng cứ trực tiếp trong bài hoặc 'không nêu'>",
            "support_level": "<supported|weak|unsupported>",
            "risk_if_believed": "<rủi ro nếu người đọc tin ngay>",
            "verification_prompt": "<câu hỏi kiểm chứng cụ thể>",
        }]
        base["critical_reading_guard"] = {
            "persuasion_risk": "<low|medium|high>",
            "manipulation_signals": [
                "<dấu hiệu thao túng 1>",
                "<dấu hiệu thao túng 2>"
            ],
            "missing_context_flags": [
                "<điểm thiếu bối cảnh 1>"
            ],
            "fact_check_actions": [
                "<hành động kiểm chứng 1>",
                "<hành động kiểm chứng 2>"
            ],
            "alternative_views": [
                "<góc nhìn thay thế 1>"
            ],
            "do_not_conclude_yet": [
                "<điều chưa đủ cơ sở để kết luận>"
            ],
        }
        base["logic_issues"] = [{"paragraph_id": "P1", "issue": "<vấn đề logic>"}]
        base["reader_summary_breakdown"] = {
            "main_points": ["<ý chính 1>", "<ý chính 2>"],
            "figures": ["<số liệu 1 (nếu có)>"],
            "argument_flow": ["<luận điểm A>", "<suy luận B>", "<kết luận C>"],
        }
        base["deep_style_analysis"] = {
            "emotional_tone": "<calm|neutral|urgent|fearful|aggressive|inspirational>",
            "inflammatory_word_frequency": "<low|medium|high (kèm tỷ lệ ước tính)>",
            "group_bias_level": "<low|medium|high>",
            "notes": "<nhận xét ngắn về dấu hiệu kích động/thiên lệch nhóm>",
        }
        base["logic_diagnostics"] = [{
            "paragraph_id": "P1",
            "issue_type": "<fallacy|conclusion_jump|fear_appeal|spelling_grammar>",
            "description": "<mô tả vấn đề>",
            "evidence": "<trích cụm từ ngắn>",
            "severity": "<low|medium|high>",
        }]
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
# Reader heuristics for mock provider
# ─────────────────────────────────────────────────────────────

_INFLAMMATORY_WORDS = {
    "vi": ["phản bội", "thảm họa", "hủy diệt", "đáng sợ", "kinh hoàng", "khủng khiếp", "độc ác"],
    "en": ["betrayal", "disaster", "destroy", "terrifying", "horrific", "evil", "panic"],
}
_FEAR_WORDS = {
    "vi": ["đe dọa", "nguy cơ", "sợ", "hoảng loạn", "mất an toàn", "sụp đổ", "diệt vong"],
    "en": ["threat", "risk", "fear", "panic", "unsafe", "collapse", "doom"],
}
_ABSOLUTE_WORDS = {
    "vi": ["tất cả", "mọi", "không ai", "duy nhất", "chắc chắn", "luôn luôn", "không bao giờ"],
    "en": ["all", "everyone", "nobody", "only", "certainly", "always", "never"],
}
_GROUP_WORDS = {
    "vi": ["phụ nữ", "đàn ông", "người nghèo", "người giàu", "người trẻ", "người già", "dân nhập cư"],
    "en": ["women", "men", "poor", "rich", "young", "elderly", "immigrants"],
}


def _detect_language_bucket(text: str) -> str:
    return "vi" if re.search(r"[ăâđêôơư]", text.lower()) else "en"


def _extract_figures(paragraphs: list[dict]) -> list[str]:
    figures: list[str] = []
    seen: set[str] = set()
    for p in paragraphs:
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?%?\b", p["text"])
        if not numbers:
            continue
        snippet = ", ".join(numbers[:4])
        text = f"{p['id']}: {snippet}"
        if text not in seen:
            seen.add(text)
            figures.append(text)
    return figures[:8]


def _estimate_inflammatory_frequency(paragraphs: list[dict], lang_bucket: str) -> tuple[str, int, int]:
    words = re.findall(r"\w+", " ".join(p["text"].lower() for p in paragraphs))
    total = max(len(words), 1)
    triggers = _INFLAMMATORY_WORDS.get(lang_bucket, _INFLAMMATORY_WORDS["en"])
    hit = sum(1 for w in words if w in triggers)
    ratio = hit / total
    if ratio >= 0.03:
        level = "high"
    elif ratio >= 0.01:
        level = "medium"
    else:
        level = "low"
    return f"{level} ({ratio:.1%})", hit, total


def _estimate_group_bias(paragraphs: list[dict], lang_bucket: str) -> str:
    all_text = " ".join(p["text"].lower() for p in paragraphs)
    group_hits = sum(1 for w in _GROUP_WORDS.get(lang_bucket, _GROUP_WORDS["en"]) if w in all_text)
    absolute_hits = sum(1 for w in _ABSOLUTE_WORDS.get(lang_bucket, _ABSOLUTE_WORDS["en"]) if w in all_text)
    score = group_hits + absolute_hits
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _detect_emotional_tone(paragraphs: list[dict], lang_bucket: str) -> str:
    all_text = " ".join(p["text"].lower() for p in paragraphs)
    fear_hits = sum(1 for w in _FEAR_WORDS.get(lang_bucket, _FEAR_WORDS["en"]) if w in all_text)
    inflame_hits = sum(1 for w in _INFLAMMATORY_WORDS.get(lang_bucket, _INFLAMMATORY_WORDS["en"]) if w in all_text)
    if fear_hits + inflame_hits >= 3:
        return "fearful"
    if "!" in all_text:
        return "urgent"
    return random.choice(["neutral", "calm", "inspirational"])


def _build_argument_flow(paragraphs: list[dict]) -> list[str]:
    flow: list[str] = []
    for p in paragraphs[:4]:
        short = p["text"][:90].strip()
        flow.append(f"{p['id']}: {short}...")
    return flow


def _detect_logic_diagnostics(paragraphs: list[dict], lang_bucket: str) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    abs_words = _ABSOLUTE_WORDS.get(lang_bucket, _ABSOLUTE_WORDS["en"])
    fear_words = _FEAR_WORDS.get(lang_bucket, _FEAR_WORDS["en"])

    for p in paragraphs:
        txt = p["text"]
        low = txt.lower()

        if any(w in low for w in abs_words):
            diagnostics.append({
                "paragraph_id": p["id"],
                "issue_type": "fallacy",
                "description": "Có xu hướng khái quát hóa/khẳng định tuyệt đối, dễ tạo lập luận thiếu điều kiện.",
                "evidence": next((w for w in abs_words if w in low), None) or txt[:60],
                "severity": "medium",
            })

        if any(w in low for w in ["vì vậy", "do đó", "therefore", "thus", "hence"]) and not re.search(r"\d", low):
            diagnostics.append({
                "paragraph_id": p["id"],
                "issue_type": "conclusion_jump",
                "description": "Có dấu hiệu nhảy kết luận nhưng thiếu bằng chứng định lượng hoặc ví dụ cụ thể.",
                "evidence": txt[:80],
                "severity": "medium",
            })

        fear_hit = next((w for w in fear_words if w in low), None)
        if fear_hit:
            diagnostics.append({
                "paragraph_id": p["id"],
                "issue_type": "fear_appeal",
                "description": "Sử dụng ngôn từ gây sợ hãi để thuyết phục thay vì chứng cứ.",
                "evidence": fear_hit,
                "severity": "high",
            })

        if re.search(r"\s{2,}", txt) or re.search(r"[!?]{2,}", txt):
            diagnostics.append({
                "paragraph_id": p["id"],
                "issue_type": "spelling_grammar",
                "description": "Có dấu hiệu lỗi chính tả/ngữ pháp hoặc dấu câu không chuẩn.",
                "evidence": txt[:80],
                "severity": "low",
            })

    return diagnostics[:12]


def _compute_readability_metrics(paragraphs: list[dict]) -> dict[str, Any]:
    text = " ".join(p["text"] for p in paragraphs).strip()
    if not text:
        return {
            "accessibility_score": 75,
            "accessibility_label": "trung bình",
            "avg_sentence_length_words": 0.0,
            "long_sentence_ratio": 0.0,
            "lexical_diversity": 0.0,
            "recommended_reader_profile": "phổ thông",
            "note": "Thiếu dữ liệu để ước lượng chính xác, dùng mức trung tính.",
        }

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"\w+", text.lower())
    sentence_count = max(len(sentences), 1)
    total_words = max(len(words), 1)

    sentence_lengths = [len(re.findall(r"\w+", s)) for s in sentences] or [total_words]
    avg_sentence_len = sum(sentence_lengths) / len(sentence_lengths)
    long_sentence_ratio = sum(1 for n in sentence_lengths if n >= 25) / len(sentence_lengths)
    lexical_diversity = len(set(words)) / total_words

    # Heuristic readability score: higher is easier to read.
    sentence_penalty = min(max(avg_sentence_len - 14, 0) * 2.2, 35)
    long_sentence_penalty = min(long_sentence_ratio * 40, 30)
    lexical_penalty = min(max(lexical_diversity - 0.52, 0) * 35, 20)
    raw_score = 100 - sentence_penalty - long_sentence_penalty - lexical_penalty
    score = int(round(max(0, min(100, raw_score))))

    if score >= 80:
        label = "dễ tiếp cận"
        profile = "phổ thông"
    elif score >= 60:
        label = "trung bình"
        profile = "đại học"
    else:
        label = "chuyên sâu"
        profile = "chuyên môn"

    return {
        "accessibility_score": score,
        "accessibility_label": label,
        "avg_sentence_length_words": round(avg_sentence_len, 1),
        "long_sentence_ratio": round(long_sentence_ratio, 2),
        "lexical_diversity": round(lexical_diversity, 2),
        "recommended_reader_profile": profile,
        "note": "Chỉ số dựa trên độ dài câu, tỷ lệ câu dài và độ đa dạng từ vựng.",
    }


def _build_claim_checks(paragraphs: list[dict]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for p in paragraphs[:6]:
        text = p["text"].strip()
        if not text:
            continue
        has_number = bool(re.search(r"\b\d+(?:[.,]\d+)?%?\b", text))
        has_source_hint = bool(
            re.search(r"\b(theo|nguồn|source|study|research|http|www)\b", text.lower())
        )
        if has_source_hint and (has_number or "trích" in text.lower()):
            support = "supported"
            evidence = "Có nêu số liệu hoặc dấu hiệu trích nguồn trong chính văn bản."
        elif has_number:
            support = "weak"
            evidence = "Có số liệu nhưng thiếu nguồn/cách đo cụ thể."
        else:
            support = "unsupported"
            evidence = "Không thấy chứng cứ trực tiếp đi kèm phát biểu."

        claim = text[:140] + ("..." if len(text) > 140 else "")
        checks.append({
            "paragraph_id": p["id"],
            "claim": claim,
            "evidence_in_text": evidence,
            "support_level": support,
            "risk_if_believed": (
                "Có thể chấp nhận kết luận một chiều hoặc sai lệch nếu không kiểm chứng."
                if support != "supported" else
                "Rủi ro thấp hơn, nhưng vẫn cần đối chiếu nguồn gốc số liệu."
            ),
            "verification_prompt": "Nguồn gốc dữ liệu này là gì, thu thập khi nào, bởi tổ chức nào?",
        })
    return checks[:5]


def _build_critical_reading_guard(
    paragraphs: list[dict],
    diagnostics: list[dict[str, str]],
    group_bias_level: str,
    inflammatory_frequency: str,
) -> dict[str, Any]:
    all_text = " ".join(p["text"].lower() for p in paragraphs)
    signals: list[str] = []

    if any(k in all_text for k in ["chắc chắn", "duy nhất", "always", "never"]):
        signals.append("Khẳng định tuyệt đối, giảm không gian phản biện.")
    if any(k in all_text for k in ["họ", "chúng ta", "phe", "bọn", "them", "us"]):
        signals.append("Phân cực 'chúng ta - họ', dễ dẫn dắt cảm xúc nhóm.")
    if any(d.get("issue_type") == "fear_appeal" for d in diagnostics):
        signals.append("Kêu gọi nỗi sợ để thuyết phục thay vì lập luận bằng chứng.")
    if not signals:
        signals.append("Không thấy tín hiệu thao túng nổi bật, nhưng vẫn cần kiểm chứng nguồn.")

    risk_score = 0
    if group_bias_level == "high":
        risk_score += 2
    elif group_bias_level == "medium":
        risk_score += 1
    if inflammatory_frequency.startswith("high"):
        risk_score += 2
    elif inflammatory_frequency.startswith("medium"):
        risk_score += 1
    if len(diagnostics) >= 4:
        risk_score += 1

    persuasion_risk = "high" if risk_score >= 4 else "medium" if risk_score >= 2 else "low"
    return {
        "persuasion_risk": persuasion_risk,
        "manipulation_signals": signals[:4],
        "missing_context_flags": [
            "Thiếu thông tin đối chiếu từ nguồn độc lập.",
            "Chưa nêu rõ phạm vi áp dụng của kết luận.",
        ],
        "fact_check_actions": [
            "Tìm tối thiểu 2 nguồn độc lập có dữ liệu cùng chủ đề để so sánh.",
            "Tách phần 'sự kiện' và 'ý kiến' trước khi rút kết luận.",
            "Kiểm tra thời điểm dữ liệu để tránh dùng thông tin lỗi thời.",
        ],
        "alternative_views": [
            "Có cách giải thích nào khác cho cùng hiện tượng không?",
            "Nhóm bị phê phán trong bài có lập luận phản biện nào đáng xem xét?",
        ],
        "do_not_conclude_yet": [
            "Chưa đủ cơ sở để khẳng định nguyên nhân - hệ quả nếu thiếu dữ liệu kiểm chứng.",
            "Không nên suy rộng từ một vài ví dụ cá biệt sang toàn bộ nhóm.",
        ],
    }


# ─────────────────────────────────────────────────────────────
# Mock
# ─────────────────────────────────────────────────────────────

class MockAIProvider(BaseAIProvider):

    async def analyze(self, mode: str, paragraphs: list[dict], language: str = "vi") -> dict[str, Any]:
        await _fake_latency()
        full_text = " ".join(p["text"] for p in paragraphs)
        lang_bucket = _detect_language_bucket(full_text)
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
            figures = _extract_figures(paragraphs)
            argument_flow = _build_argument_flow(paragraphs)
            inflam_freq, _, _ = _estimate_inflammatory_frequency(paragraphs, lang_bucket)
            group_bias = _estimate_group_bias(paragraphs, lang_bucket)
            emotional_tone = _detect_emotional_tone(paragraphs, lang_bucket)
            diagnostics = _detect_logic_diagnostics(paragraphs, lang_bucket)
            readability = _compute_readability_metrics(paragraphs)
            claim_checks = _build_claim_checks(paragraphs)
            reading_guard = _build_critical_reading_guard(
                paragraphs=paragraphs,
                diagnostics=diagnostics,
                group_bias_level=group_bias,
                inflammatory_frequency=inflam_freq,
            )

            result["key_takeaways"] = [
                "Văn bản có cấu trúc mạch lạc.",
                "Các luận điểm được trình bày tuần tự.",
                "Kết luận rõ ràng và nhất quán.",
            ]
            result["readability_metrics"] = readability
            result["claim_checks"] = claim_checks
            result["critical_reading_guard"] = reading_guard
            result["reading_difficulty"] = (
                "easy" if readability["accessibility_score"] >= 80
                else "medium" if readability["accessibility_score"] >= 60
                else "hard"
            )
            result["logic_issues"] = (
                [{"paragraph_id": paragraphs[0]["id"], "issue": "Thiếu dẫn chứng cụ thể."}]
                if paragraphs and random.random() > 0.6 else []
            )
            result["reader_summary_breakdown"] = {
                "main_points": [p["main_idea"] for p in para_analyses[:4]],
                "figures": figures or ["Không phát hiện số liệu nổi bật trong văn bản."],
                "argument_flow": argument_flow,
            }
            result["deep_style_analysis"] = {
                "emotional_tone": emotional_tone,
                "inflammatory_word_frequency": inflam_freq,
                "group_bias_level": group_bias,
                "notes": (
                    "Tần số ngôn từ kích động và thiên lệch nhóm đang ở mức cần theo dõi."
                    if group_bias in {"medium", "high"} else
                    "Văn phong tương đối trung tính, ít dấu hiệu kích động mạnh."
                ),
            }
            result["logic_diagnostics"] = diagnostics
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
        casual_keywords = ["hello", "hi", "hey", "xin chào", "chào", "yo", "hola", "cảm ơn", "thanks"]
        if any(word in q for word in casual_keywords):
            return {
                "answer": (
                    "Chào bạn. Mình sẵn sàng hỗ trợ phân tích tài liệu, "
                    "bạn có thể hỏi về ý chính, luận điểm hoặc giọng văn của văn bản."
                ),
                "referenced_paragraphs": [],
                "confidence": "high",
                "out_of_scope": False,
            }

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
                "answer": (
                    "Mình chưa thể trả lời câu này từ tài liệu hiện tại. "
                    "Bạn có thể hỏi lại theo nội dung văn bản (ví dụ: tóm tắt, ý chính từng đoạn, điểm yếu lập luận)."
                ),
                "referenced_paragraphs": [],
                "confidence": "medium",
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
# OpenRouter (OpenAI-compatible)
# ─────────────────────────────────────────────────────────────

class OpenRouterProvider(OpenAIProvider):
    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            )
            self.model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
            self._extra_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "LLMagik"),
            }
        except ImportError:
            raise RuntimeError("Cài đặt openai SDK: pip install openai")

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
            extra_headers=self._extra_headers,
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
            extra_headers=self._extra_headers,
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
            extra_headers=self._extra_headers,
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
    elif name == "openrouter":
        _provider_cache = OpenRouterProvider()
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
    language = _normalize_language(language)
    return f"""Bạn là trợ lý phân tích văn bản. Quy tắc bắt buộc:
1. Ưu tiên trả lời dựa trên nội dung văn bản được cung cấp.
2. Nếu người dùng chào hỏi hoặc hội thoại xã giao ngắn (ví dụ: hello, hi, cảm ơn), hãy phản hồi tự nhiên, thân thiện.
3. Nếu câu hỏi nằm ngoài nội dung văn bản, hãy trả lời ngắn gọn và gợi ý quay lại nội dung tài liệu.
4. Chỉ liệt kê referenced_paragraphs khi có dùng nội dung đoạn văn cụ thể.
5. Trả về JSON hợp lệ, không có markdown, không có text ngoài JSON.
6. {_lang_instruction(language)}"""


def build_chat_prompt(question: str, paragraphs: list[dict], history: list[dict], language: str = "vi") -> str:
    language = _normalize_language(language)
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
        "answer": "<answer dựa trên tài liệu hoặc phản hồi xã giao ngắn>",
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
- out_of_scope: true nếu câu hỏi không dựa trên nội dung văn bản
- Với chào hỏi xã giao, trả lời thân thiện; đặt out_of_scope=false và referenced_paragraphs=[]
- Nếu out_of_scope là true, answer cần hữu ích và gợi ý câu hỏi liên quan tài liệu"""
