import os
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# Configurazione API
API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)

# Configurazione del modello con istruzioni di sistema separate
system_instruction = """
Sei un assistente editoriale automatizzato. Il tuo compito è estrarre i dati dal materiale fornito e inserirli in due schemi rigidi. 

REGOLE DI COMPORTAMENTO:
1. NON CONVERSARE: Non rispondere con "Certamente", "Ecco i file" o "Sono pronto". Restituisci SOLO i due schemi.
2. NON INVENTARE: Usa solo i dati presenti nel file. Se mancano nomi di artisti o contatti, elimina quelle righe dallo schema (non lasciarle vuote e non inventarle).
3. MAIUSCOLE/MINUSCOLE: 
   - Nel corpo del testo e nei luoghi, usa SEMPRE il formato normale (iniziale maiuscola, resto minuscolo). No "TUTTO MAIUSCOLO".
   - SOLO il titolo della PARTE 2 (Calendario) deve essere in TUTTO MAIUSCOLO.
4. STILE: Giornalistico, asciutto, variare l'inizio delle frasi, evitare ripetizioni. Vietata la formula "Non X, ma Y".

STRUTTURA OUTPUT:

PARTE 1: ARTICOLO WORDPRESS
(Inizia con 3 titoli AIOSEO in formato normale, poi lo schema seguente)

[Titolo Evento]

[Nome Location] – [Città] ([Provincia])

[Paragrafo descrittivo che inizia con: Giorno della settimana, Giorno, Mese, ore... presso...]

Con:

[Nome Artista] – [Strumento]

Info: [Contatti]


PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
[GG/MM/AAAA] – [TITOLO EVENTO IN MAIUSCOLO]
[Sottotitolo o Patrocinio se presente]

[Nome Location] – [Città] ([Provincia])
[Paragrafo descrittivo identico a quello della Parte 1]

Con: 
[Nome Artista] – [Strumento]
Info: [Contatti]
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=system_instruction
)

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except: pass
    return text

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except: return ""

def generate_content(file_path, file_extension):
    content_parts = []
    
    if file_extension == '.pdf':
        text = extract_text_from_pdf(file_path)
        if not text.strip(): return None
        content_parts.append(f"ELABORA QUESTO TESTO:\n\n{text}")
    elif file_extension in ['.doc', '.docx']:
        text = extract_text_from_docx(file_path)
        if not text.strip(): return None
        content_parts.append(f"ELABORA QUESTO TESTO:\n\n{text}")
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        try:
            image = Image.open(file_path)
            content_parts.append("ELABORA QUESTA IMMAGINE:")
            content_parts.append(image)
        except: return None
    else: return None

    try:
        response = model.generate_content(content_parts)
        return response.text
    except Exception as e:
        print(f"Errore API: {e}")
        return None

def main():
    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f)) and not f.startswith('.')]
    if not files: return

    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        result = generate_content(file_path, ext)
        
        if result:
            output_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(filename)[0]}_WP_Ready.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Generato: {filename}")

if __name__ == "__main__":
    if API_KEY: main()
    else: print("Manca GEMINI_API_KEY")
