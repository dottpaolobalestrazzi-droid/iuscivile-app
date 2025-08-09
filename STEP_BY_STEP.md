
# IusCivile Pro+ — Guida passo‐passo (solo iOS, iPhone)

Questa guida è **clic per clic**: seguila nell’ordine. Tempo totale: ~30–45 minuti.

---

## 1) Avviare il backend in locale

1. Apri il Terminale e vai nella cartella:
   ```bash
   cd backend
   ```
2. Avvia con un solo comando:
   ```bash
   ./launch.sh
   ```
   - scarica le dipendenze
   - carica le **chiavi** dal file `.env` (già configurato)
   - avvia il server su **http://127.0.0.1:8000**

> **Nota**: per indicizzare nuovi PDF, usa:
> ```bash
> source .venv/bin/activate
> mkdir -p data
> python ingest.py "/percorso/al/tuo.pdf" "/percorso/ad/altro.pdf"
> ```

---

## 2) Test rapido del backend

In un nuovo Terminale:
```bash
curl -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"query":"Spiegami l'art. 2051 c.c.","history":[],"profile":"praticanteAvvocato","show_links":true,"force_web_for_cases":true}'
```
Se ottieni una risposta JSON, è ok.

Puoi testare anche i **quiz**:
```bash
curl -X POST http://127.0.0.1:8000/quiz   -H "Content-Type: application/json"   -d '{"topic":"obbligazioni","difficulty":"medio","num":5}'
```

---

## 3) Aprire il progetto iOS in Xcode (solo iPhone)

1. Apri **Xcode**, *File → Open…* e seleziona la cartella `ios/IusCivile`
2. Target dell’app → **General**:
   - **Display Name**: *IusCivile Pro+*
   - **Bundle Identifier**: qualcosa di unico (es. `it.tuonome.iuscivilepro`)
   - **Team**: il tuo team Apple Developer
   - **Signing**: lascia automatico
   - **Deployment Info → Devices:** `iPhone`
   - **Orientation**: *Portrait* (consigliato)
   - Spunta **Requires full screen**

3. In app (tab **Impostazioni**) imposta **Backend URL** a:
   - `http://127.0.0.1:8000` per test locale
   - Oppure il tuo dominio se decidi di metterlo online

---

## 4) Prova l’app sul simulatore

1. Seleziona un simulatore (es. iPhone 15 Pro)
2. Premi ▶️ (Run)
3. In app:
   - Scegli profilo (Praticante Avv., Avvocato, Praticante Notaio, Notaio, Studente)
   - Prova: *"Redigi atto di citazione ex art. 2051 c.c."*
   - Prova **Quiz**: argomento "obbligazioni", *Crea 5 domande*

---

## 5) App Store Connect — creare la scheda

1. Vai su **https://appstoreconnect.apple.com → App → +** → **Nuova App**
2. Piattaforma **iOS**; nome **IusCivile Pro+**; Bundle ID uguale a Xcode
3. **Prezzo e disponibilità**: scegli gratuita o a pagamento
4. **Informazioni app**: compila i campi (vedi `docs/APP_STORE_DESC.md`)

**Privacy (App Privacy):**
- Dichiara che l’app invia **contenuti** al tuo backend (nessun tracciamento pubblicitario)
- Collezione dati minima per *App Functionality*

---

## 6) Caricare l’app da Xcode

1. In Xcode: **Product → Archive**
2. Al termine si apre **Organizer**: seleziona l’archivio → **Distribute App**
3. Scegli **App Store Connect** → **Upload**
4. Attendi elaborazione in App Store Connect (pochi minuti)

---

## 7) Screenshot per la scheda (solo iPhone)

**Come crearli:**
1. Lancia l’app nel simulatore iPhone 6.7" (es. iPhone 15 Pro Max)
2. Vai su:
   - Chat con risposta (teoria/atto)
   - Tab **Quiz**
   - Esempio atto (notarile o processuale)
3. Fai screenshot dal menu **File → New Screenshot** nel simulatore
4. Caricali su App Store Connect (sezione *App Information → Screenshots*)

> Suggerimento: 3–5 screenshot bastano per la review.

---

## 8) Inviare in review

1. In App Store Connect → **App** → **Version** → **Add for Review**
2. Rispondi alle domande (nessun uso di *Sign in with Apple*, niente *HealthKit* ecc.)
3. Invia.

**Tempi tipici**: 24–48 ore.

---

## Domande frequenti

- **Serve un server pubblico?** Per test no; per gli utenti sì. Puoi usare un VPS e mettere Nginx + HTTPS.
- **Dove cambio i domini per le sentenze?** Nel backend, `ALLOWLIST` inside `server.py`.
- **Posso aggiungere altri PDF?** Sì: `python ingest.py "/percorso/nuovo.pdf"` poi riavvia il backend.
- **Quiz usa norme e sentenze vere?** Sì: domande generate con riferimenti essenziali.

—
Generato il: 2025-08-08T18:51:56.482676Z
