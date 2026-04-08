import os
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# Configurazione API
API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)

# Configurazione del modello
system_instruction = """
Sei un assistente editoriale automatizzato. Il tuo compito è estrarre i dati dal materiale fornito (testo o immagine) e inserirli in due schemi rigidi. 

REGOLE DI COMPORTAMENTO:
1. NON CONVERSARE: Restituisci SOLO i due schemi. Nessun commento iniziale o finale.
2. NON INVENTARE: Usa solo i dati presenti. Se mancano artisti o contatti, ometti quelle righe.
3. MAIUSCOLE/MINUSCOLE: 
   - Corpo del testo e luoghi: formato normale (Es: Teatro Ariston - Sanremo).
   - SOLO il titolo della PARTE 2 (Calendario) deve essere in TUTTO MAIUSCOLO.
4. STILE: Giornalistico asciutto. Identico contenuto descrittivo per entrambi gli schemi.

STRUTTURA OUTPUT:

PARTE 1: ARTICOLO WORDPRESS
(Inizia con 3 titoli AIOSEO in formato normale)

[Titolo Evento]

[Nome Location] – [Città] ([Provincia])

[Paragrafo descrittivo: Giorno della settimana, Giorno, Mese, ore... presso...]

Con:

[Nome Artista] – [Strumento]

Info: [Contatti]


PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
[GG/MM/AAAA] – [TITOLO EVENTO IN MAIUSCOLO]
[Sottotitolo o Patrocinio se presente]

[Nome Location] – [Città] ([Provincia])
[Paragrafo descrittivo identico alla Parte 1]

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
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
    except Exception as e: print(f"Errore PDF: {e}")
    return text

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except: return ""

def generate_content(file_path, file_extension):
    content_parts = []
    print(f"--- Elaborazione file: {os.path.basename(file_path)} ---")
    
    if file_extension == '.pdf':
        text = extract_text_from_pdf(file_path)
        if not text.strip(): 
            print("⚠️ Nessun testo trovato nel PDF. Provo come immagine...")
            try:
                # Se il PDF non ha testo, Gemini può analizzarlo come immagine se passiamo il file
                # In questo ambiente semplificato, trattiamo solo testo estratto o immagini pure
                return None
            except: return None
        content_parts.append(f"DATI DA ELABORARE:\n\n{text}")
    elif file_extension in ['.doc', '.docx']:
        text = extract_text_from_docx(file_path)
        if not text.strip(): return None
        content_parts.append(f"DATI DA ELABORARE:\n\n{text}")
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        try:
            image = Image.open(file_path)
            content_parts.append("ANALIZZA QUESTA IMMAGINE ED ESTRAI I DATI PER GLI SCHEMI:")
            content_parts.append(image)
        except: return None
    else: return None

    try:
        response = model.generate_content(content_parts)
        return response.text
    except Exception as e:
        print(f"❌ Errore API: {e}")
        return None

def main():
    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f)) and not f.startswith('.')]
    if not files:
        print("Nessun file trovato in 'input'.")
        return

    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        result = generate_content(file_path, ext)
        
        if result:
            # Pulizia output da eventuali tag residui dell'AI
            clean_result = result.replace("--- INIZIO MATERIALE ---", "").replace("--- FINE MATERIALE ---", "")
            output_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(filename)[0]}_WP_Ready.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(clean_result.strip())
            print(f"✅ Articolo salvato con successo: {output_path}")

if __name__ == "__main__":
    if API_KEY: main()
    else: print("ERRORE: GEMINI_API_KEY non configurata.")
