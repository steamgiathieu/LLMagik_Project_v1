"""
services/text_processor.py
Trích xuất và chuẩn hóa văn bản từ 3 nguồn: text, URL, file.
"""
import re
import unicodedata
from typing import List


# ── Paragraph normalization ────────────────────────────────────

def normalize_text(text: str) -> str:
    """Unicode NFC + collapse whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_paragraphs(text: str, min_length: int = 8) -> List[str]:
    """
    Chia văn bản thành danh sách đoạn.
    Đoạn được tách bởi dòng trống; đoạn quá ngắn bị bỏ qua.
    """
    raw_blocks = re.split(r"\n{2,}", text)
    paragraphs: List[str] = []

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue

        # Preserve explicit bullet/list lines as separate paragraphs.
        if all(re.match(r"^([-*•]|\d+[.)])\s+", ln) for ln in lines):
            paragraphs.extend(lines)
            continue

        merged = " ".join(lines)
        merged = re.sub(r"\s+", " ", merged).strip()
        if merged:
            paragraphs.append(merged)

    # Merge orphan very-short lines into the previous paragraph only when safe.
    refined: List[str] = []
    for para in paragraphs:
        if (
            refined
            and len(para) < min_length
            and not re.match(r"^([-*•]|\d+[.)])\s+", para)
            and not re.search(r"[.!?:]$", refined[-1])
        ):
            refined[-1] = f"{refined[-1]} {para}".strip()
        else:
            refined.append(para)

    return [p for p in refined if p]


def build_paragraph_list(paragraphs: List[str]) -> List[dict]:
    return [{"id": f"P{i + 1}", "text": p} for i, p in enumerate(paragraphs)]


# ── Source: plain text ─────────────────────────────────────────

def extract_from_text(raw: str) -> str:
    return normalize_text(raw)


# ── Source: URL ────────────────────────────────────────────────

def extract_from_url(url: str) -> str:
    """Fetch URL và trích xuất nội dung bằng BeautifulSoup."""
    try:
        import httpx
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        }
        resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Xóa script, style, nav, footer, ads
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "noscript", "iframe", "figure"]):
            tag.decompose()

        # Ưu tiên thẻ article / main / div.content
        content = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"class": re.compile(r"(content|body|post|article)", re.I)})
            or soup.find("body")
        )
        if content:
            chunks: List[str] = []
            for node in content.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"]):
                txt = normalize_text(node.get_text(" ", strip=True))
                if not txt:
                    continue
                # Bỏ các đoạn cực ngắn có khả năng là nhãn giao diện.
                if len(txt) < 3:
                    continue
                chunks.append(txt)

            if chunks:
                return normalize_text("\n\n".join(chunks))

        text = content.get_text(separator="\n") if content else soup.get_text(separator="\n")
        return normalize_text(text)

    except ImportError:
        # Mock nếu thiếu httpx / beautifulsoup4
        return _mock_url_content(url)

    except Exception as e:
        raise ValueError(f"Không thể tải URL: {e}")


def _mock_url_content(url: str) -> str:
    return (
        f"[MOCK] Nội dung được trích xuất từ URL: {url}\n\n"
        "Đây là đoạn văn mẫu đầu tiên được tạo bởi mock extractor. "
        "Trong môi trường thực, nội dung sẽ được fetch và parse từ trang web.\n\n"
        "Đây là đoạn văn mẫu thứ hai. Nó chứa thêm thông tin giả lập để "
        "kiểm tra chức năng chia đoạn và đánh số.\n\n"
        "Đây là đoạn văn mẫu thứ ba. Cài đặt httpx và beautifulsoup4 "
        "để lấy nội dung thực từ URL."
    )


# ── Source: PDF ────────────────────────────────────────────────

def extract_from_pdf(file_bytes: bytes) -> str:
    try:
        import io
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
        return normalize_text("\n\n".join(pages))

    except ImportError:
        return _mock_file_content("PDF")

    except Exception as e:
        raise ValueError(f"Không thể đọc PDF: {e}")


# ── Source: DOCX ───────────────────────────────────────────────

def extract_from_docx(file_bytes: bytes) -> str:
    try:
        import io
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        return normalize_text("\n\n".join(paras))

    except ImportError:
        return _mock_file_content("DOCX")

    except Exception as e:
        raise ValueError(f"Không thể đọc DOCX: {e}")


def _mock_file_content(file_type: str) -> str:
    return (
        f"[MOCK] Nội dung được trích xuất từ file {file_type}.\n\n"
        "Đây là đoạn văn mẫu đầu tiên từ tài liệu. "
        "Trong môi trường thực, văn bản sẽ được đọc trực tiếp từ file.\n\n"
        "Đây là đoạn văn mẫu thứ hai từ tài liệu. "
        "Cài đặt PyPDF2 (PDF) hoặc python-docx (DOCX) để kích hoạt tính năng này."
    )


# ── Dispatch ───────────────────────────────────────────────────

def process_input(
    source_type: str,
    text: str = None,
    url: str = None,
    file_bytes: bytes = None,
    filename: str = None,
) -> dict:
    """
    Trả về dict gồm raw_text, title, source_ref.
    """
    if source_type == "text":
        raw = extract_from_text(text or "")
        title = raw[:80] + "..." if len(raw) > 80 else raw
        source_ref = None

    elif source_type == "url":
        raw = extract_from_url(url)
        title = url
        source_ref = url

    elif source_type == "file":
        ext = (filename or "").rsplit(".", 1)[-1].lower()
        if ext == "pdf":
            raw = extract_from_pdf(file_bytes)
        elif ext in ("docx", "doc"):
            raw = extract_from_docx(file_bytes)
        else:
            raise ValueError(f"Định dạng file không hỗ trợ: .{ext}")
        title = filename
        source_ref = filename

    else:
        raise ValueError(f"source_type không hợp lệ: {source_type}")

    paragraphs = split_paragraphs(raw)
    if not paragraphs and raw.strip():
        paragraphs = [raw.strip()]

    return {
        "raw_text": raw,
        "title": title,
        "source_ref": source_ref,
        "paragraphs": build_paragraph_list(paragraphs),
    }
