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
    Sei un giornalista musicale e copywriter esperto. Basandoti sul materiale fornito, devi generare il contenuto richiesto applicando in modo rigoroso le mie regole editoriali e di formattazione.
    
    REGOLE STILISTICHE ASSOLUTE:
    - Varia l'inizio di ogni singola frase. Evita assolutamente ripetizioni di concetti, sostantivi e verbi vicini tra loro.
    - DIVIETO ASSOLUTO: Non usare MAI la formula retorica "Non X, ma Y" (es. "Questo non è un semplice disco, ma un capolavoro").
    - DIVIETO ASSOLUTO: Evita formule come "Pubblicato nel [anno], questo lavoro...".
    - Usa un linguaggio originale, fresco, non prevedibile e mantieni il tono dell'IA al minimo storico. Deve sembrare scritto da un umano, con stile giornalistico.
    - Contestualizza con dettagli per appassionati (es. hard rock/heavy metal o del genere di riferimento).
    
    Il tuo output deve essere diviso ESCLUSIVAMENTE in DUE parti, formattate ESATTAMENTE come segue:
    
    PARTE 1: ARTICOLO WORDPRESS (News Singola)
    Proponi 3 titoli accattivanti ottimizzati per un alto punteggio AIOSEO. I TITOLI DEVONO ESSERE SCRITTI IN FORMATO NORMALE/MINUSCOLO (con solo l'iniziale maiuscola), dopodiché genera l'articolo rispettando questa esatta struttura Markdown (ispirata al layout ufficiale):
    
    # [Inserisci qui il Titolo Scelto in formato normale]
    [Data estrapolata in formato: gg mese aaaa] - [Autore o Fondazione/Redazione]
    
    **[Luogo o Teatro - Città]** (Attenzione: scrivi in formato normale, NON usare il tutto maiuscolo)
    
    [Paragrafo descrittivo dell'evento, con data estesa, luogo esatto e informazioni sull'esibizione. Applica le regole stilistiche.]
    
    Info: [Sito web o link estrapolato, es. nomesito.it]
    
    PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
    Genera la voce per la pagina listato del Calendario. DEVI RISPETTARE RIGOROSAMENTE IL SEGUENTE SCHEMA TESTUALE, inclusi gli a capo e la punteggiatura. IL TITOLO NELLA PRIMA RIGA DEVE ESSERE IN TUTTO MAIUSCOLO, mentre nel corpo del testo in formato normale:
    
    [GG/MM/AAAA] – [TITOLO EVENTO IN TUTTO MAIUSCOLO]
    [Eventuale dicitura di Patrocinio o Sottotitolo, es. Patrocinio Fondazione Fabrizio De André]
    
    [Nome Location] – [Città] ([Provincia])
    [Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Location completa con indirizzo e città], si terrà l'appuntamento dal titolo "[Titolo Evento in formato normale]"
    
    Con:
    [Nome Artista/Relatore] – [Ruolo/Strumento]
    [Nome Artista/Relatore] – [Ruolo/Strumento]
    
    Info: [Telefono] – [Email]
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
