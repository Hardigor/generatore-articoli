import os
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# Configurazione API
API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)

# Istruzioni Rigide per il Modello
instruction = """
Sei un estrattore di dati. Leggi il file fornito e compila i due schemi seguenti.
NON aggiungere commenti. NON dire 'Ecco i risultati'. Restituisci SOLO gli schemi.

REGOLE MAIUSCOLE:
- PARTE 1: Nomi e Luoghi in formato normale (es: Teatro Ariston). NO TUTTO MAIUSCOLO.
- PARTE 2: Titolo Evento in TUTTO MAIUSCOLO. Tutto il resto in formato normale.

PARTE 1: ARTICOLO WORDPRESS
(Inizia con 3 titoli AIOSEO normali)

[Titolo Evento]

[Nome Location] – [Città] ([Provincia])

[Paragrafo descrittivo: Giorno, data e ora presso location, appuntamento dal titolo "..."]

Con:
[Nome Artista] – [Strumento]

Info: [Contatti]

PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
[GG/MM/AAAA] – [TITOLO EVENTO IN MAIUSCOLO]
[Sottotitolo o Patrocinio se presente]

[Nome Location] – [Città] ([Provincia])
[Paragrafo identico alla Parte 1]

Con:
[Nome Artista] – [Strumento]
Info: [Contatti]
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-preview-09-2025',
    system_instruction=instruction
)

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate(file_path, ext):
    parts = []
    try:
        if ext == '.pdf':
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages: text += page.extract_text() or ""
            if not text.strip(): return None # PDF immagine non leggibile come testo
            parts.append(text)
        elif ext in ['.jpg', '.jpeg', '.png']:
            parts.append(Image.open(file_path))
        elif ext in ['.doc', '.docx']:
            parts.append("\n".join([p.text for p in docx.Document(file_path).paragraphs]))
        else: return None

        res = model.generate_content(parts)
        return res.text
    except: return None

def main():
    files = [f for f in os.listdir(INPUT_DIR) if not f.startswith('.')]
    for f in files:
        path = os.path.join(INPUT_DIR, f)
        ext = os.path.splitext(f)[1].lower()
        output = generate(path, ext)
        if output:
            with open(os.path.join(OUTPUT_DIR, f"{os.path.splitext(f)[0]}_WP.md"), "w", encoding="utf-8") as out:
                out.write(output.strip())

if __name__ == "__main__":
    if API_KEY: main()
