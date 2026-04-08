import os
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# 1. Recupero API KEY
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    print("❌ ERRORE CRITICO: La GEMINI_API_KEY non è configurata!")
else:
    genai.configure(api_key=API_KEY)

# 2. Istruzioni di Sistema (Il "Cervello" del Bot)
system_instruction = """
Sei un assistente editoriale automatico. Il tuo compito è estrarre i dati dal materiale fornito e inserirli in due schemi rigidi. 

REGOLE TASSATIVE:
1. NON CONVERSARE: Restituisci SOLO i due schemi. Non dire "Ecco i file" o "Sono pronto".
2. NON INVENTARE: Usa solo i dati presenti. Se mancano artisti o contatti, elimina quelle righe.
3. FORMATTAZIONE: 
   - Niente TUTTO MAIUSCOLO nel corpo del testo o nei luoghi.
   - SOLO il titolo della PARTE 2 (Calendario) deve essere in TUTTO MAIUSCOLO.
4. SCHEMA ARTICOLO WP: Titolo normale, Luogo normale, paragrafo descrittivo asciutto, lista "Con:" (se presente), "Info:".
5. SCHEMA CALENDARIO: [Data] - [TITOLO MAIUSCOLO], Luogo normale, stesso paragrafo dell'articolo, "Con:" e "Info:" attaccati.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-preview-09-2025',
    system_instruction=system_instruction
)

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_content(file_path, ext):
    print(f"🔍 Analisi file: {os.path.basename(file_path)}")
    content_parts = []
    
    try:
        if ext == '.pdf':
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            
            if not text.strip():
                print("⚠️ ATTENZIONE: Il PDF è un'immagine/scansione. Non posso leggere il testo interno.")
                print("💡 Suggerimento: Carica la locandina come file .JPG o .PNG per risultati migliori.")
                return None
            content_parts.append(f"DATI ESTRATTI DAL PDF:\n{text}")
            
        elif ext in ['.jpg', '.jpeg', '.png']:
            img = Image.open(file_path)
            content_parts.append("Estrai i dati da questa immagine per i due schemi:")
            content_parts.append(img)
            
        elif ext in ['.doc', '.docx']:
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            content_parts.append(f"DATI ESTRATTI DA WORD:\n{text}")
        else: return None

        print("🤖 Interrogazione Gemini in corso...")
        response = model.generate_content(content_parts)
        return response.text

    except Exception as e:
        print(f"❌ Errore: {e}")
        return None

def main():
    files = [f for f in os.listdir(INPUT_DIR) if not f.startswith('.')]
    if not files:
        print("📁 Cartella input vuota.")
        return

    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        result = generate_content(file_path, ext)
        
        if result and len(result.strip()) > 10:
            out_name = f"{os.path.splitext(filename)[0]}_WP_Ready.md"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(result.strip())
            print(f"✅ Articolo generato: {out_name}")

if __name__ == "__main__":
    main()
