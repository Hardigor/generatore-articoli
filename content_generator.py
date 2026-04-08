import os
import sys
import time
import google.generativeai as genai
import docx
import PyPDF2
from PIL import Image

# Configurazione API
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    print("❌ ERRORE CRITICO: La chiave GEMINI_API_KEY non è stata trovata nei Secrets!")
    sys.exit(1) # Ferma l'automazione con pallino rosso
else:
    print("✅ Chiave API trovata, procedo alla configurazione.")
    genai.configure(api_key=API_KEY)

# Istruzioni Rigide per il Modello
instruction = """
Sei un estrattore di dati. Leggi il file fornito e compila i due schemi seguenti.
NON aggiungere commenti. NON dire 'Ecco i risultati'. Restituisci SOLO gli schemi esatti qui sotto.

REGOLE TASSATIVE:
1. Nomi e Luoghi nella Parte 1 DEVONO essere in formato normale (es: Teatro Ariston). NO TUTTO MAIUSCOLO.
2. SOLO il Titolo Evento della Parte 2 (dopo la data) deve essere in TUTTO MAIUSCOLO.
3. Se mancano gli artisti/musicisti nel testo, NON inventarli e NON inserire la parola "Con:". Elimina semplicemente quella sezione.
4. Sostituisci [GG/MM/AAAA] con la data corretta (es. 28/03/2026), se l'anno non è specificato deduci quello corrente.
5. I link web e gli indirizzi email devono ESSERE SEMPRE IN MINUSCOLO (es. www.sito.it), anche se nell'originale appaiono in maiuscolo.

Copia testualmente questa formattazione Markdown, rispettando rigorosamente le righe vuote e i grassetti (**testo**):

**ARTICOLO WORDPRESS**

**[Titolo Evento in formato normale]**

[Nome Location] – [Città] ([Provincia])

[Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Nome Location completa], appuntamento concerto dal titolo "[Titolo Evento in formato normale]".

(INSERISCI LA PAROLA "Con:" E L'ELENCO DEGLI ARTISTI QUI SOLO SE SONO PRESENTI NEL FILE, ALTRIMENTI OMETTI QUESTE RIGHE)

Info e biglietti: [Link o email rigorosamente in minuscolo]


**ARTICOLO CALENDARIO MANIFESTAZIONI**

**[GG/MM/AAAA] – [TITOLO EVENTO IN TUTTO MAIUSCOLO]**
(INSERISCI QUI EVENTUALE PATROCINIO SE PRESENTE, ALTRIMENTI OMETTI)

[Nome Location] – [Città] ([Provincia]) 

[Giorno della settimana] [Giorno] [Mese] alle ore [Ora] presso [Nome Location completa], appuntamento concerto dal titolo "[Titolo Evento in formato normale]".

(INSERISCI LA PAROLA "Con:" E L'ELENCO DEGLI ARTISTI QUI SOLO SE SONO PRESENTI NEL FILE, ALTRIMENTI OMETTI QUESTE RIGHE)

Info e biglietti: [Link o email rigorosamente in minuscolo]
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
        
        # --- NUOVO MECCANISMO ANTI-BLOCCO (RETRY) ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = model.generate_content(parts)
                
                if not res.candidates:
                    print("❌ ERRORE: Gemini ha bloccato la risposta o non ha trovato dati validi.")
                    return None
                    
                print("✅ Risposta ricevuta da Gemini!")
                return res.text
                
            except Exception as api_err:
                error_msg = str(api_err)
                # Verifica se abbiamo superato la quota gratuita dei 5 RPM
                if "429" in error_msg or "quota" in error_msg.lower() or "ResourceExhausted" in error_msg:
                    print(f"⚠️ Errore 429: Limite richieste superato. Tentativo {attempt + 1} di {max_retries}.")
                    if attempt < max_retries - 1:
                        attesa = 35 # Pausa di 35 secondi per far ricaricare i contatori di Google
                        print(f"⏳ Mi metto in pausa per {attesa} secondi. Abbi pazienza, riprovo da solo...")
                        time.sleep(attesa)
                    else:
                        print("❌ ERRORE CRITICO: Quota API esaurita anche dopo le pause. Riprova tra 1-2 minuti.")
                        return None
                else:
                    print(f"❌ ERRORE API: {error_msg}")
                    return None
        # --------------------------------------------
        
    except Exception as e: 
        print(f"❌ ERRORE DI SISTEMA: {e}")
        return None

def main():
    print("🚀 Avvio dello script principale...")
    
    if not os.path.exists(INPUT_DIR):
        print("❌ ERRORE CRITICO: La cartella 'input' non esiste.")
        sys.exit(1)
        
    files = [f for f in os.listdir(INPUT_DIR) if not f.startswith('.')]
    
    if not files:
        print("❌ ERRORE CRITICO: Nessun file trovato nella cartella 'input'.")
        print("💡 ATTENZIONE: Assicurati di aver caricato l'immagine *DENTRO* la cartella 'input' e non nella schermata principale del progetto!")
        sys.exit(1)

    successo_totale = False
    
    for f in files:
        path = os.path.join(INPUT_DIR, f)
        ext = os.path.splitext(f)[1].lower()
        output = generate(path, ext)
        
        if output:
            out_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(f)[0]}_WP.md")
            with open(out_file, "w", encoding="utf-8") as out:
                out.write(output.strip())
            print(f"💾 File salvato con successo: {out_file}")
            successo_totale = True
        else:
            print(f"⚠️ Impossibile generare contenuto per {f}")
            
    if not successo_totale:
        print("❌ ERRORE CRITICO: Nessun file è stato generato con successo. Processo fallito.")
        sys.exit(1)
            
    print("🏁 Elaborazione terminata con successo.")

if __name__ == "__main__":
    main()
