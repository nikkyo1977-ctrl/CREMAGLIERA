# Design: Analisi Cinematica Pignone-Cremagliera

**Data:** 2026-04-19
**Scope:** Solo cinematica del gear mesh — nessuna resistenza o analisi dei carichi.
**File target:** `pignone_cremagliera.py`

---

## 1. Bug da correggere

### 1.1 Formula `ga` errata per x ≠ 0

**Attuale (errata):**
```python
ga_sx = ha_cr / sin(alpha_sx)
ga_dx = ha_cr / sin(alpha_dx)
```

**Corretta:**
```python
ga_sx = (ha_cr - x * m) / sin(alpha_sx)
ga_dx = (ha_cr - x * m) / sin(alpha_dx)
```

**Motivazione:** Con profilo spostato `x`, la linea primitiva di lavoro si sposta di `x·m` rispetto al datum della cremagliera. La distanza dalla testa della cremagliera alla linea primitiva non è `ha_cr` ma `ha_cr - x·m`. La formula attuale sovrastima `ga` per `x > 0` e lo sottostima per `x < 0`, producendo valori errati di `ε_α`, `ga`, `gf/ga`.

**Impatto:** Tutte le grandezze derivate da `ga` (ricoprimento sx/dx, asimmetria, diagnostica interferenza) sono attualmente errate per qualsiasi valore di `x ≠ 0`.

---

## 2. Nuova funzione `compute_kinematics(params)`

Funzione pura (nessun side-effect UI) che centralizza tutti i calcoli cinematici e geometrici.

### Firma
```python
from dataclasses import dataclass
import numpy as np

@dataclass
class KinResult:
    # Geometria base
    r: float
    ra: float
    rf: float
    rb_sx: float
    rb_dx: float
    H: float
    da: float
    # Tratti di contatto (corretti)
    ga_sx: float
    gf_sx: float
    ga_dx: float
    gf_dx: float
    # Ricoprimento
    eps_sx: float
    eps_dx: float
    pb_sx: float
    pb_dx: float
    # Spessori
    sp: float
    scr: float
    # Cinematica
    L: float
    vs_max_sx: float    # |v_s/v_p|_max fianco sx (adimensionale)
    vs_max_dx: float
    # Diagnostica
    z_min_sx: float
    z_min_dx: float
    undercut_sx: bool
    undercut_dx: bool
    interference_tip_pin_sx: bool
    interference_tip_pin_dx: bool
    interference_tip_rack_sx: bool
    interference_tip_rack_dx: bool
    # Curva cinematica su un passo (array numpy)
    theta_arr: np.ndarray    # angoli [0, 2π/z]
    u_sx_arr: np.ndarray     # posizione contatto lungo retta d'azione, fianco sx [mm]
    u_dx_arr: np.ndarray     # idem fianco dx
    vs_arr: np.ndarray       # |v_s/v_p|(θ) — massimo tra i due fianchi attivi
    n_pairs_arr: np.ndarray  # numero coppie in presa (int 1 o 2)

def compute_kinematics(params: dict) -> KinResult:
    ...
```

### Formule principali

| Grandezza | Formula |
|---|---|
| Raggio primitivo | `r = m·z/2` |
| Cerchio base sx | `rb_sx = r·cos(α_sx)` |
| Cerchio base dx | `rb_dx = r·cos(α_dx)` |
| Raggio testa | `ra = r + (1 + x)·m` |
| Raggio piede | `rf = r - (ha_cr + c - x·m)` |
| Interasse | `H = r + x·m` |
| Tratto accesso (**corretto**) | `ga = (ha_cr - x·m) / sin(α)` |
| Tratto recesso | `gf = sqrt(ra² - rb²) - r·sin(α)` |
| Passo base | `pb = π·m·cos(α)` |
| Ricoprimento | `ε_α = (ga + gf) / pb` |
| Spostamento/giro | `L = π·m·z` |
| Spessore pignone | `sp = m·(π/2 + x·(tan(α_sx) + tan(α_dx))) - δs` |
| z minimo (undercut) | `z_min = 2·(1 - x) / sin²(α)` per fianco sx e dx |
| Vel. scorrimento norm. | `\|v_s/v_p\| = \|u\| / r` dove `u` = dist. dal pitch point |

### Curva cinematica `u(θ)` su un passo

Per ogni angolo `θ ∈ [0, 2π/z]` (un passo del pignone):
- La posizione del contatto lungo la retta d'azione: `u(θ) = r·θ - ga` (da inizio accesso)
- Clamp: `u ∈ [-ga, +gf]` (fuori da questo intervallo non c'è contatto)
- `n_pairs(θ)`: 2 se `u mod pb < (ga + gf - pb)`, altrimenti 1
- `|v_s/v_p|(θ) = |u(θ)| / r`

---

## 3. Modifiche a `update_plot()`

### 3.1 Layout figura
Da `Figure(1,2)` a `Figure(1,3)`:
- `ax` (subplot 1): vista pignone — invariata
- `ax_zoom` (subplot 2): zoom contatto — aggiornata con overlay
- `ax_kinem` (subplot 3): diagramma cinematico — nuova

Se il layout `1×3` risulta troppo stretto (< 400px per subplot), usare `GridSpec(2,2)` con `ax_kinem` che occupa la riga inferiore per intero.

### 3.2 Overlay su `ax_zoom`
Aggiunto dopo il disegno dei profili:

**Segmento retta d'azione attiva:**
- Tratto accesso (da pitch point verso cremagliera): arancio, spessore 2
- Tratto recesso (da pitch point verso testa pignone): verde, spessore 2
- Estremi: punti start/end della zona di contatto attiva

**Punto di contatto istantaneo:**
- Coordinata lungo la retta d'azione: `u_current = r·rot - ga_sx` (clampato)
- Convertita in coordinate cartesiane:
  ```
  x_contact = -u · cos(90° - α)  = -u · sin(α)
  y_contact = -r + u · cos(α)  [per fianco sx, approssimazione linea d'azione]
  ```
  (adattata per sx e dx)
- Disegnato come cerchio verde Ø8pt, zorder=15

### 3.3 Diagramma cinematico `ax_kinem`
Asse X: `θ · r` = spostamento cremagliera [mm] su un passo (`0 → pb = π·m`)
Asse Y sinistro: `u(θ)` [mm] — posizione contatto (linea blu)
Asse Y destro (twin_ax): `|v_s/v_p|(θ)` (linea rossa tratteggiata)

Elementi grafici:
- Sfondo rosa per zona `u < 0` (accesso), sfondo verde chiaro per `u > 0` (recesso)
- Gradino `n_pairs(θ)`: area grigia sovrapposta (scala indipendente, asse Y dx secondario)
- Linea verticale tratteggiata nera: posizione angolare corrente
- Titolo: `"Cinematica — 1 Passo (pb = {pb:.3f} mm)"`

---

## 4. Finestra Diagnostica (`DiagnosticWindow`)

### Apertura
- Nuovo bottone nel pannello controlli: `"Diagnostica Cinematica"`
- Crea `self.diag_win = DiagnosticWindow(self)` (Toplevel tkinter)
- Se già aperta, la porta in primo piano (`lift()`)
- `update_plot()` chiama `self.diag_win.refresh(kin)` se `self.diag_win` esiste ed è aperta

### Layout finestra (450×500 px)

**Blocco 1 — Limiti geometrici** (`LabelFrame`)

| Campo | Valore | Limite | Margine | Stato |
|---|---|---|---|---|
| z min sx (undercut) | `z_min_sx` | z attuale | `z - z_min_sx` | ✓/✗ |
| z min dx (undercut) | `z_min_dx` | z attuale | `z - z_min_dx` | ✓/✗ |
| ga sx | valore [mm] | `gf_sx` (max) | diff | ✓/✗ |
| ga dx | valore [mm] | `gf_dx` (max) | diff | ✓/✗ |

**Blocco 2 — Check interferenza** (`LabelFrame`)

| Check | Condizione | Stato |
|---|---|---|
| Testa pignone sx | `gf_sx ≤ ga_sx_max_rack` | ✓/✗ |
| Testa pignone dx | `gf_dx ≤ ga_dx_max_rack` | ✓/✗ |
| Testa cremagliera sx | `ga_sx ≤ gf_sx_max_pin` | ✓/✗ |
| Testa cremagliera dx | `ga_dx ≤ gf_dx_max_pin` | ✓/✗ |
| Ra > Rb sx | `ra > rb_sx` | ✓/✗ |
| Ra > Rb dx | `ra > rb_dx` | ✓/✗ |

**Blocco 3 — Grandezze cinematiche** (`LabelFrame`)

| Grandezza | Valore |
|---|---|
| Lunghezza zona attiva sx | `ga_sx + gf_sx` mm |
| Lunghezza zona attiva dx | `ga_dx + gf_dx` mm |
| `\|v_s/v_p\|_max` tip pignone sx | `gf_sx / r` |
| `\|v_s/v_p\|_max` tip pignone dx | `gf_dx / r` |
| `\|v_s/v_p\|_max` tip cremagliera sx | `ga_sx / r` |
| `\|v_s/v_p\|_max` tip cremagliera dx | `ga_dx / r` |
| Zona doppio contatto sx | `(ε_sx - 1) · pb_sx` mm |
| Zona doppio contatto dx | `(ε_dx - 1) · pb_dx` mm |

**Colori:**
- Rosso (`#cc0000`): condizione violata
- Arancio (`#cc6600`): margine < 10% del valore limite
- Verde (`#006600`): ok

---

## 5. Fuori scope

- Analisi di resistenza, Hertz, fatica, carichi — non inclusi
- Ristrutturazione UI a schede (Notebook) — non inclusa
- Modifica ai parametri/slider esistenti — nessuna
- Calcolo di errori di trasmissione per tolleranze di produzione — non incluso

---

## 6. File modificati

| File | Tipo modifica |
|---|---|
| `pignone_cremagliera.py` | Refactor + nuove funzioni |

Nessun nuovo file Python — tutto nel file esistente.
