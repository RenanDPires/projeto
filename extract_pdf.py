import pypdf
import os

# Abrindo o PDF
pdf_path = r"base_teorica\Avaliacao_1\Avaliacao_1_EEL7216_semestre_2026_1.pdf"
reader = pypdf.PdfReader(pdf_path)

print(f"Total de páginas: {len(reader.pages)}\n")

# Extraindo texto de todas as páginas
full_text = ""
for i, page in enumerate(reader.pages):
    print(f"--- PÁGINA {i+1} ---")
    text = page.extract_text()
    full_text += f"\n--- PÁGINA {i+1} ---\n{text}"
    print(text[:300] if text else "[SEM TEXTO]")
    print("...")
    print()

# Salvando em arquivo temporário para análise
with open("temp_pdf_content.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print("\n\nConteúdo salvo em temp_pdf_content.txt")
print(f"Tamanho total: {len(full_text)} caracteres")
