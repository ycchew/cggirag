import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from pypdf import PdfReader
import pandas as pd

logger = logging.getLogger(__name__)


class CGGIDocumentProcessor:
    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.documents = []

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""

    def extract_text_from_txt(self, txt_path: Path) -> str:
        """Extract text content from a TXT file with multiple encoding attempts"""
        encodings = [
            "utf-8",
            "utf-16",
            "utf-16-le",
            "cp1252",
            "latin-1",
            "windows-1252",
        ]
        for encoding in encodings:
            try:
                with open(txt_path, "r", encoding=encoding) as f:
                    text = f.read()
                if text.strip():
                    logger.info(
                        f"Successfully read {txt_path.name} with encoding: {encoding}"
                    )
                    return text
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.warning(
                    f"Encoding {encoding} failed for {txt_path.name}: {str(e)}"
                )
                continue
            except Exception as e:
                logger.error(f"Error extracting text from {txt_path}: {str(e)}")
                return ""
        logger.error(f"All encoding attempts failed for {txt_path.name}")
        return ""

    def chunk_text(
        self, text: str, chunk_size: int = 512, overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Ensure we don't go beyond text length
            if end > len(text):
                end = len(text)

            chunk_text = text[start:end]

            chunk = {
                "content": chunk_text,
                "start_pos": start,
                "end_pos": end,
                "metadata": {
                    "length": len(chunk_text),
                    "start_char": start,
                    "end_char": end,
                },
            }

            chunks.append(chunk)

            # Move start position forward by chunk_size - overlap
            start += chunk_size - overlap

            # If we're near the end, break to avoid infinite loop
            if start >= len(text):
                break

        return chunks

    async def process_cggi_reports(self) -> List[Dict[str, Any]]:
        """Process all CGGI reports in the source directory (PDF files only)"""
        logger.info(f"Processing CGGI reports from {self.source_dir}")

        pdf_files = list(self.source_dir.glob("*.pdf"))
        pdf_files = [
            f for f in pdf_files if any(str(y) in f.name for y in range(2021, 2026))
        ]
        logger.info(
            f"Found {len(pdf_files)} PDF files to process: {[f.name for f in pdf_files]}"
        )

        all_chunks = []

        for pdf_file in pdf_files:
            logger.info(f"Processing PDF: {pdf_file.name}")
            text_content = self.extract_text_from_pdf(pdf_file)

            if not text_content.strip():
                logger.warning(f"No text content extracted from {pdf_file.name}")
                continue

            year = self._extract_year_from_filename(pdf_file.name)
            chunks = self.chunk_text(text_content)

            for i, chunk in enumerate(chunks):
                chunk["metadata"].update(
                    {
                        "source_file": pdf_file.name,
                        "year": year,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "file_type": "pdf",
                    }
                )
                all_chunks.append(chunk)

        logger.info(f"Processed {len(all_chunks)} total chunks from CGGI reports")
        return all_chunks

    def _extract_year_from_filename(self, filename: str) -> int:
        """Extract year from CGGI report filename"""
        # Filename format: "YYYY-Chandler-Good-Government-Index-Report.pdf"
        try:
            year_str = filename.split("-")[0]
            return int(year_str)
        except (ValueError, IndexError):
            logger.warning(f"Could not extract year from filename: {filename}")
            return 0  # Return 0 if year extraction fails


# Example usage
async def main():
    processor = CGGIDocumentProcessor("D:\\dev\\CGGI\\docs\\source\\")
    chunks = await processor.process_cggi_reports()

    # Print first few chunks as example
    for i, chunk in enumerate(chunks[:3]):
        print(
            f"Chunk {i + 1}: {len(chunk['content'])} chars from {chunk['metadata']['source_file']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
