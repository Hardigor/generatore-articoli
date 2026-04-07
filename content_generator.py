import os
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# Configura la tua API Key di Gemini (verrà letta dai Secrets di GitHub)
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Usa il modello più recente e veloce per testo e immagini
model = genai.GenerativeModel('gemini-2.5-flash')

INPUT_DIR = "input"
OUTPUT_DIR = "output"

# Crea le directory se non esistono
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Estrae il testo da un file PDF."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Errore nella lettura del PDF {pdf_path}: {e}")
    return text

def extract_text_from_docx(docx_path):
    """Estrae il testo da un file Word."""
    try:
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Errore nella lettura del file Word {docx_path}: {e}")
        return ""

def generate_content(file_path, file_extension):
    """Invia il contenuto a Gemini e richiede l'articolo e il calendario."""
    
    # Prompt di sistema basato sulle tue rigorose linee guida editoriali
    system_prompt = """
    Sei un estrattore di dati e formattatore automatico. Il tuo unico scopo è prendere le informazioni dal file fornito e inserirle in due schemi RIGIDI copiando pedissequamente gli ESEMPI REALI che ti verranno forniti qui sotto.

    REGOLA FONDAMENTALE SUI CONTENUTI:
    - NON INVENTARE NULLA. Zero dettagli aggiuntivi e zero frasi di contorno.
    - DIVIETO ASSOLUTO: Non usare formule come "Non X, ma Y" o "Pubblicato nel...". Nessuna creatività testuale, usa solo i fatti.

    IL TUO OUTPUT DEVE ESSERE DIVISO ESCLUSIVAMENTE IN DUE PARTI, SEGUENDO AL MILLIMETRO I SEGUENTI SCHEMI:

    PARTE 1: ARTICOLO WORDPRESS
    Proponi prima 3 titoli AIOSEO in formato normale (non tutto maiuscolo). Dopodiché, genera l'articolo rispettando RIGOROSAMENTE questa formattazione, inclusi gli spazi e gli a capo esatti:

    --- ESEMPIO REALE DA COPIARE PER LA PARTE 1 ---
    Racconti d'Autunno: Serata con l'autore Marco Rossi

    LIBRERIA "IL SEGNALIBRO" – MILANO (MI)

    Giovedì 26 Ottobre alle ore 18:30 presso Libreria "Il Segnalibro", Via Roma 10, Milano, si terrà l'appuntamento dal titolo "Racconti d'Autunno: Serata con l'autore Marco Rossi".

    Con:

    Marco Rossi – Autore 
    Laura Bianchi – Moderatrice

    Info: 02 12345678 – info@ilsegnalibro.it
    --- FINE ESEMPIO PARTE 1 ---


    PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
    Per il calendario devi formattare il testo copiando AL MILLIMETRO gli spazi, i maiuscoli/minuscoli e le interruzioni di riga di questo esempio reale. Fai molta attenzione a come "Info:" è attaccato all'ultima riga dei nomi.

    --- ESEMPIO REALE DA COPIARE PER LA PARTE 2 ---
    26/10/2023 – RACCONTI D'AUTUNNO: SERATA CON L'AUTORE MARCO ROSSI

    Libreria "Il Segnalibro" – Milano (MI)

    Giovedì 26 Ottobre alle ore 18:30 presso Libreria "Il Segnalibro", Via Roma 10, Milano, si terrà l'appuntamento dal titolo "Racconti d'Autunno: Serata con l'autore Marco Rossi".

    Con: 

    Marco Rossi – Autore 
    Laura Bianchi – Moderatrice
    Info: 02 12345678 – info@ilsegnalibro.it
    --- FINE ESEMPIO PARTE 2 ---
    """

    content_parts = [system_prompt]

    # Gestione in base al tipo di file
    if file_extension == '.pdf':
        print(f"Estrazione testo da PDF: {file_path}")
        text = extract_text_from_pdf(file_path)
        content_parts.append(f"Materiale di base:\n{text}")
        
    elif file_extension in ['.doc', '.docx']:
        print(f"Estrazione testo da Word: {file_path}")
        text = extract_text_from_docx(file_path)
        content_parts.append(f"Materiale di base:\n{text}")
        
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        print(f"Analisi immagine: {file_path}")
        image = Image.open(file_path)
        content_parts.append("Materiale di base (Immagine allegata):")
        content_parts.append(image)
    else:
        print(f"Formato non supportato: {file_extension}")
        return None

    # Chiamata all'API
    try:
        print("Generazione del contenuto in corso...")
        response = model.generate_content(content_parts)
        return response.text
    except Exception as e:
        print(f"Errore durante la generazione API: {e}")
        return None

def main():
    # Cerca file nella cartella di input
    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
    
    if not files:
        print("Nessun file trovato nella cartella 'input'.")
        return

    for filename in files:
        # Ignora file nascosti
        if filename.startswith('.'): continue
            
        file_path = os.path.join(INPUT_DIR, filename)
        name, ext = os.path.splitext(filename)
        
        print(f"\n--- Elaborazione di: {filename} ---")
        result = generate_content(file_path, ext.lower())
        
        if result:
            output_filename = f"{name}_WP_Ready.md"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Successo! Output salvato in: {output_path}")

if __name__ == "__main__":
    if not API_KEY:
        print("ERRORE: GEMINI_API_KEY non trovata nelle variabili d'ambiente.")
    else:
        main()
