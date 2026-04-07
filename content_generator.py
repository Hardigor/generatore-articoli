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
    Sei un estrattore di dati e formattatore automatico. Il tuo compito è LEGGERE IL FILE FORNITO, estrarre le informazioni reali dell'evento (date, luoghi, nomi, contatti) e INSERIRLE NEI DUE SCHEMI RIGIDI riportati qui sotto.

    REGOLA FONDAMENTALE SUI CONTENUTI E SULLA FORMATTAZIONE:
    - ESTRAI I DATI REALI DAL FILE. Non inventare nulla, usa solo i fatti.
    - Zero dettagli aggiuntivi e zero frasi di contorno.
    - DIVIETO ASSOLUTO: Non usare formule come "Non X, ma Y" o "Pubblicato nel...". 
    - DIVIETO ASSOLUTO MAIUSCOLE: Non inserire MAI parole in TUTTO MAIUSCOLO nel corpo del testo (né per l'articolo WP, né per i luoghi/città). Usa sempre il formato normale (iniziale maiuscola e resto minuscolo). L'UNICA eccezione consentita è il TITOLO dell'evento nella Parte 2 (Calendario).

    IL TUO OUTPUT DEVE ESSERE DIVISO ESCLUSIVAMENTE IN DUE PARTI, MANTENENDO AL MILLIMETRO GLI SPAZI E GLI "A CAPO" DEI SEGUENTI SCHEMI, MA USANDO I DATI ESTRATTI DAL FILE:

    PARTE 1: ARTICOLO WORDPRESS
    Proponi prima 3 titoli AIOSEO in formato normale. Dopodiché, genera l'articolo rispettando RIGOROSAMENTE questa formattazione, senza usare il maiuscolo per le location:

    [Titolo dell'evento estratto dal file in formato normale]

    [Nome della location estratta dal file in formato normale] – [Città in formato normale] ([Provincia in formato normale])

    [Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Location completa con indirizzo e città estratta dal file in formato normale], si terrà l'appuntamento dal titolo "[Titolo Evento in formato normale]".

    Con:

    [Nome Artista/Relatore 1 dal file] – [Ruolo/Strumento]
    [Nome Artista/Relatore 2 dal file] – [Ruolo/Strumento]
    (inserisci qui tutti i partecipanti trovati nel file)

    Info: [Telefono dal file] – [Email dal file]


    PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
    Genera la formattazione per il calendario rispettando i maiuscoli/minuscoli e le interruzioni di riga esatte di questo schema (Attenzione: la riga "Info" è attaccata all'ultimo nome). USA I DATI DEL FILE.

    [Data estratta in formato GG/MM/AAAA] – [TITOLO DELL'EVENTO IN TUTTO MAIUSCOLO]

    [Nome della location estratta dal file in formato normale] – [Città in formato normale] ([Provincia in formato normale])

    [Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Location completa con indirizzo e città in formato normale], si terrà l'appuntamento dal titolo "[Titolo Evento in formato normale]".

    Con: 

    [Nome Artista/Relatore 1 dal file] – [Ruolo/Strumento]
    [Nome Artista/Relatore 2 dal file] – [Ruolo/Strumento]
    Info: [Telefono dal file] – [Email dal file]
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
