import os
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# Configurazione API
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    print("❌ ERRORE CRITICO: La chiave GEMINI_API_KEY non è stata trovata nei Secrets!")
else:
    print("✅ Chiave API trovata, procedo alla configurazione.")
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
    model_name='gemini-2.5-flash',
    system_instruction=instruction
)

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate(file_path, ext):
    print(f"⏳ Inizio elaborazione del file: {file_path}")
    
    # È cruciale fornire SEMPRE un prompt di testo insieme al file/immagine
    parts = ["Estrai i dati da questo documento/immagine e compila ESATTAMENTE i due schemi richiesti."]
    
    try:
        if ext == '.pdf':
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages: 
                    text += page.extract_text() or ""
            if not text.strip(): 
                print("⚠️ Il PDF non contiene testo leggibile. Riprova usando una versione in formato JPG o PNG.")
                return None
            parts.append(text)
            print("📄 Testo estratto dal PDF con successo.")
            
        elif ext in ['.jpg', '.jpeg', '.png']:
            img = Image.open(file_path)
            parts.append(img)
            print("🖼️ Immagine caricata con successo.")
            
        elif ext in ['.doc', '.docx']:
            text = "\n".join([p.text for p in docx.Document(file_path).paragraphs])
            parts.append(text)
            print("📝 Testo estratto dal file Word con successo.")
            
        else: 
            print(f"🚫 Formato non supportato: {ext}")
            return None

        print("🤖 Invio richiesta a Gemini...")
        res = model.generate_content(parts)
        print("✅ Risposta ricevuta da Gemini!")
        return res.text
        
    except Exception as e: 
        print(f"❌ ERRORE API o DI SISTEMA: {e}")
        return None

def main():
    print("🚀 Avvio dello script principale...")
    files = [f for f in os.listdir(INPUT_DIR) if not f.startswith('.')]
    
    if not files:
        print("📁 Nessun file trovato nella cartella 'input'.")
        return

    for f in files:
        path = os.path.join(INPUT_DIR, f)
        ext = os.path.splitext(f)[1].lower()
        output = generate(path, ext)
        
        if output:
            out_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(f)[0]}_WP.md")
            with open(out_file, "w", encoding="utf-8") as out:
                out.write(output.strip())
            print(f"💾 File salvato con successo: {out_file}")
        else:
            print(f"⚠️ Impossibile generare contenuto per {f}")
            
    print("🏁 Elaborazione terminata.")

if __name__ == "__main__":
    main()
