"""
Module 1: Document Parser — PTIT Edition
Hỗ trợ: PDF, Excel (.xlsx/.xls), Word (.docx), Text (.txt)
Tự động làm sạch header/footer và chuẩn hóa text tiếng Việt.
"""
from pathlib import Path
from typing import List
import re
import unicodedata

import fitz  # PyMuPDF
import pandas as pd


# ─── Patterns để loại bỏ khỏi PDF ───────────────────────────
_NOISE_PATTERNS = [
    r"Trang\s+\d+\s*/\s*\d+",       # "Trang 1/10"
    r"^\s*\d+\s*$",                  # Số trang đơn lẻ
    r"Học viện Công nghệ Bưu chính Viễn thông\s*$",  # Header lặp lại
    r"PTIT\s*[-–]\s*",               # Prefix thừa
    r"={3,}|-{3,}|_{3,}|\*{3,}",    # Đường kẻ trang trí
]


class PDFParser:
    """Parse PDF và trả về list đoạn text — mỗi đoạn là 1 trang."""

    def parse(self, path: str) -> List[str]:
        pages = []
        doc = fitz.open(path)

        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            text = self._clean(text, page_num)
            if text and len(text.split()) >= 20:  # Bỏ trang quá ngắn
                pages.append(text)

        doc.close()
        return pages

    def _clean(self, text: str, page_num: int = 0) -> str:
        # 1. Xoá các dòng noise (header, footer, số trang)
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            if self._is_noise(line):
                continue
            cleaned_lines.append(line)

        text = " ".join(cleaned_lines)

        # 2. Chuẩn hóa khoảng trắng
        text = re.sub(r"\s+", " ", text)

        # 3. Fix lỗi encoding tiếng Việt thường gặp
        text = text.replace("\u0000", "").strip()

        return text

    def _is_noise(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return True
        for pattern in _NOISE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False


class ExcelParser:
    """
    Parse Excel → chuyển từng row thành câu text tự nhiên.
    """

    # Template đặc biệt cho các cột điểm chuẩn PTIT
    SCORE_COLUMNS = {"điểm chuẩn", "diemchuan", "diem_chuan", "score", "điểm"}
    YEAR_COLUMNS = {"năm", "year", "nam"}
    MAJOR_COLUMNS = {"tên ngành", "ngành", "major", "nganh"}
    CODE_COLUMNS = {"mã ngành", "ma_nganh", "code", "mã"}
    BASE_COLUMNS = {"cơ sở", "co_so", "campus", "cs"}

    def parse(self, path: str) -> List[str]:
        """Parse tất cả sheets trong file Excel."""
        xl = pd.ExcelFile(path)
        all_rows = []

        for sheet in xl.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            df = df.dropna(how="all")
            df = df.ffill().fillna("")

            rows = self._parse_sheet(df, sheet_name=sheet)
            all_rows.extend(rows)

        return all_rows

    def _parse_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[str]:
        rows = []

        def normalize_v(s):
            if pd.isna(s): return ""
            return unicodedata.normalize("NFC", str(s).strip())

        # 1. Chuẩn hóa tên cột
        df.columns = [normalize_v(c) for c in df.columns]
        
        # 2. Dò tìm header thật sự (ASCII-based search)
        def is_major_header(s):
            s_clean = normalize_v(s).lower()
            return "nganh" in s_clean or "major" in s_clean or "tên" in s_clean

        has_major = any(is_major_header(c) for c in df.columns)
        if not has_major and len(df) > 0:
            for i, row in df.iterrows():
                if any(is_major_header(str(v)) for v in row):
                    df.columns = [normalize_v(v) for v in row]
                    df = df.iloc[i+1:].reset_index(drop=True)
                    break

        # Tìm cột ngành bằng ASCII mờ
        major_col = next((c for c in df.columns if "nganh" in normalize_v(c).lower() or "ngành" in normalize_v(c).lower()), None)
        code_col = next((c for c in df.columns if "ma" in normalize_v(c).lower() or "code" in normalize_v(c).lower()), None)
        
        # Từ khóa điểm chuẩn (ASCII fallback)
        score_keywords = ["diem", "score", "2021", "2022", "2023", "2024", "2025", "hsa", "tsa", "ielts", "dgnl", "dgtd", "to hop"]
        score_cols = [c for c in df.columns if any(k in normalize_v(c).lower() or k in normalize_v(c).lower().replace("đ", "d") for k in score_keywords)]
        
        if not major_col:
            # Last resort: first column that looks like a name
            major_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        for _, row in df.iterrows():
            major = str(row.get(major_col, "")).strip()
            code = str(row.get(code_col, "")).strip() if code_col else ""
            
            if not major or major.lower() == "nan" or "tổng" in major.lower():
                continue
            
            # A. Granular
            for s_col in score_cols:
                val = str(row.get(s_col, "")).strip()
                if val and val.lower() != "nan" and val not in ["-", "0", ""]:
                    msg = f"Nganh {major}"
                    if code: msg += f" (ma {code})"
                    msg += f" co {s_col} la {val}."
                    rows.append(msg)

            # B. Summary
            summary = [f"{k}: {v}" for k, v in row.items() if str(v).lower() != "nan" and str(v) != "-"]
            if summary:
                rows.append(f"Du lieu chi tiet nganh {major} ({code}): " + " | ".join(summary))

        return rows

    def _detect_columns(self, columns: List[str]) -> dict:
        mapping = {}
        for col in columns:
            col_l = col.lower()
            if any(k in col_l for k in self.SCORE_COLUMNS): mapping["score"] = col
            elif any(k in col_l for k in self.YEAR_COLUMNS): mapping["year"] = col
            elif any(k in col_l for k in self.MAJOR_COLUMNS): mapping["major"] = col
            elif any(k in col_l for k in self.CODE_COLUMNS): mapping["code"] = col
            elif any(k in col_l for k in self.BASE_COLUMNS): mapping["base"] = col
        return mapping


class CSVParser:
    """Parse CSV -> hỗ trợ cả trường hợp file Excel bị đổi đuôi thành .csv."""

    def parse(self, path: str) -> List[str]:
        import pandas as pd
        
        # Kiểm tra magic bytes xem có phải là file Zip (Excel) không
        with open(path, "rb") as f:
            header = f.read(4)
            if header == b"PK\x03\x04":
                df = pd.read_excel(path)
            else:
                try:
                    df = pd.read_csv(path, encoding="utf-8")
                except:
                    df = pd.read_csv(path, encoding="latin1")
        
        df = df.dropna(how="all")
        df.columns = [str(c).strip() for c in df.columns]
        
        excel_parser = ExcelParser()
        return excel_parser._parse_sheet(df, "CSV")


class TextParser:
    """Parse file .txt hoặc .md — split theo đoạn."""

    def parse(self, path: str) -> List[str]:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if len(p.split()) >= 10]


class DocxParser:
    """Parse file .docx."""

    def parse(self, path: str) -> List[str]:
        try:
            import docx2txt
            text = docx2txt.process(path)
            paragraphs = re.split(r"\n\s*\n", text)
            return [p.strip() for p in paragraphs if len(p.split()) >= 10]
        except ImportError:
            raise ImportError("Cài docx2txt: pip install docx2txt")


class DocumentParser:
    """Tự động detect loại file và dùng parser phù hợp."""

    SUPPORTED = {".pdf", ".xlsx", ".xls", ".txt", ".md", ".docx", ".csv"}

    def __init__(self):
        self._parsers = {
            ".pdf": PDFParser(),
            ".xlsx": ExcelParser(),
            ".xls": ExcelParser(),
            ".csv": CSVParser(),
            ".txt": TextParser(),
            ".md": TextParser(),
            ".docx": DocxParser(),
        }

    def parse(self, path: str) -> List[str]:
        ext = Path(path).suffix.lower()
        if ext not in self._parsers: return []
        return self._parsers[ext].parse(path)

    def parse_directory(self, dir_path: str) -> List[str]:
        all_docs = []
        dir_p = Path(dir_path)

        if not dir_p.exists(): return []

        files = [f for f in dir_p.iterdir() if f.suffix.lower() in self.SUPPORTED]

        for f in files:
            try:
                docs = self.parse(str(f))
                all_docs.extend(docs)
                print(f"  [>>] Parsed: {f.name} ({len(docs)} chunks)")
            except Exception as e:
                print(f"  [WARN] Error parsing {f.name}: {e}")

        return all_docs
