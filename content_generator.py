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

    IL TUO OUTPUT DEVE ESSERE DIVISO ESCLUSIVAMENTE IN DUE PARTI:

    PARTE 1: ARTICOLO WORDPRESS
    Proponi prima 3 titoli AIOSEO in formato normale (non tutto maiuscolo). Dopodiché, genera l'articolo rispettando RIGOROSAMENTE questa struttura e questi a capo:

    [Titolo Evento in formato normale]

    [NOME LOCATION IN TUTTO MAIUSCOLO] – [CITTÀ IN TUTTO MAIUSCOLO] ([PROVINCIA IN TUTTO MAIUSCOLO])

    [Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Location completa con indirizzo e città], si terrà l'appuntamento dal titolo "[Titolo Evento in formato normale]". (Se ci sono informazioni aggiuntive sull'evento riportale testualmente qui, senza inventare nulla)

    Con:

    [Nome Artista] – [Ruolo/Strumento]
    [Nome Artista] – [Ruolo/Strumento]

    Info: [Telefono] – [Email]


    PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
    Per il calendario devi formattare il testo copiando AL MILLIMETRO gli spazi, i maiuscoli/minuscoli e le interruzioni di riga di questi esempi reali. Scegli il modello più adatto al testo in input (se è un evento singolo usa il Modello A, se è un raggruppamento per mese usa il Modello B, se ci sono relatori o presentatori usa il Modello C).

    --- INIZIO MODELLO A (Evento Singolo Standard) ---
    05/03/2026 – FINALMENTE SCEGLIERAI – FABER, BOCCA DI ROSA E LE ALTRE…
    Patrocinio Fondazione Fabrizio De André

    Sala Ariston – Camposanto (MO)
    Giovedì 5 marzo alle ore 20:45 presso la Sala Ariston di Via Roma 6 a Camposanto, si terrà l’appuntamento dal titolo “Finalmente sceglierai – Faber, Bocca di Rosa e le altre…”

    Con:
    Germano Salsi – chitarra e voce
    Michaela Bilkova Bozzato – violino
    Francesca Cavazzuti – testi e voce narrante

    Info: 3485503202 – info@cordecordiali.it
    --- FINE MODELLO A ---

    --- INIZIO MODELLO B (Raggruppamento Eventi per Mese) ---
    MARZO 2026 – FABER EXPERIENCE IN CONCERTO

    Varie località

    Questi gli appuntamenti di marzo per Faber Experience, Tributo a Fabrizio De André:

    8 marzo – Teatro Villoresi di Monza
    26 marzo – Teatro Ambra di Poggio a Caiano (PO)
    27 marzo – Teatro Nuovo di Pisa
    28 marzo – Teatro Michelangelo di Modena

    Info: Info: faberisback.it
    --- FINE MODELLO B ---

    --- INIZIO MODELLO C (Evento con Interpreti e Presentatori) ---
    06/03/2026 – NON PER GRAZIA RICEVUTA – LE VOCI DELLE DONNE PER FABER TRA FATICA, LOTTE, RESISTENZA E DIGNITÁ
    Patrocinio Fondazione Fabrizio De André

    Savona
    Venerdì 6 marzo alle ore 16:00 presso la Sala della Sibilla (Fortezza del Priamar) a Savona, si terrà l’appuntamento dal titolo “Non per grazia ricevuta – Le voci delle donne per Faber tra fatica, lotte, resistenza e dignità”.

    Interpretazioni musicali di:
    Chiara Effe e Federico Sirianni
    cantautori e interpreti della scuola genovese in dialogo con l’opera di Fabrizio De André

    Presenta:

    Giulia Stella, segreteria Spi di Savona
    Giuliana Parodi, segretaria regionale Spi Cgil
    Andrea Pasa, segretario generale Camera del Lavoro di Savona
    --- FINE MODELLO C ---
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
