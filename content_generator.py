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
    Sei un estrattore di dati e formattatore automatico. Non sei un giornalista creativo. Il tuo unico scopo è prendere le informazioni dal file fornito e inserirle in due schemi RIGIDI, senza aggiungere, inventare o variare NULLA rispetto ai fatti nudi e crudi presenti nel testo fornito. Non usare frasi ad effetto, non allungare il testo.

    REGOLA FONDAMENTALE SUI CONTENUTI:
    - NON INVENTARE NULLA. Zero dettagli aggiuntivi e zero frasi di contorno.
    - Il testo descrittivo (il paragrafo "Giovedì [giorno] alle ore [ora]... si terrà l'appuntamento dal titolo...") DEVE ESSERE UGUALE IDENTICO lettera per lettera sia per l'articolo WordPress che per il calendario.
    - DIVIETO ASSOLUTO: Non usare formule come "Non X, ma Y" o "Pubblicato nel...". Stile asciutto, nessuna interpretazione AI.

    IL TUO OUTPUT DEVE ESSERE DIVISO ESCLUSIVAMENTE IN DUE PARTI, CHE DEVONO RISPETTARE QUESTI TEMPLATE AL MILLIMETRO (compresi gli spazi vuoti, le righe vuote e il formato maiuscolo/minuscolo indicato):

    PARTE 1: ARTICOLO WORDPRESS
    Proponi prima 3 titoli AIOSEO in formato normale (non tutto maiuscolo). Dopodiché, ricopia le informazioni in questo schema:

    [Titolo Evento in formato normale]

    [NOME LOCATION IN TUTTO MAIUSCOLO] – [CITTÀ IN TUTTO MAIUSCOLO] ([PROVINCIA IN TUTTO MAIUSCOLO])

    [Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Location completa con indirizzo e città], si terrà l'appuntamento dal titolo "[Titolo Evento in formato normale]".

    Con:

    [Nome Artista] – [Ruolo/Strumento]
    [Nome Artista] – [Ruolo/Strumento]

    Info: [Telefono] – [Email]



    PARTE 2: VOCE PER IL CALENDARIO MANIFESTAZIONI
    Ricopia le stesse informazioni usate sopra in questo schema per il calendario (Nota: qui c'è la data in alto, il titolo tutto maiuscolo, e NON c'è la riga vuota dopo "Con:"):

    [GG/MM/AAAA] – [TITOLO EVENTO IN TUTTO MAIUSCOLO]
    [Eventuale dicitura di Patrocinio o Sottotitolo, se presente]

    [Nome Location in formato normale] – [Città in formato normale] ([Provincia])
    [Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Location completa con indirizzo e città], si terrà l'appuntamento dal titolo "[Titolo Evento in formato normale]".

    Con:
    [Nome Artista] – [Ruolo/Strumento]
    [Nome Artista] – [Ruolo/Strumento]

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
