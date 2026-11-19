"""
ReelLore AI — PDF Generator Alias / Bridge
===========================================
Re-exports generate_production_pdf from src.pdf_export for backwards compatibility.
"""

from src.pdf_export import generate_production_pdf, sanitize_text, markdown_to_clean_html

__all__ = ["generate_production_pdf", "sanitize_text", "markdown_to_clean_html"]
