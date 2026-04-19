# Cinematica Pignone-Cremagliera — Piano di Implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correggere il bug `ga`, estrarre la matematica in `compute_kinematics()`, aggiungere diagramma cinematico `u(θ)/|vs/vp|(θ)`, overlay punto contatto animato, finestra diagnostica separata.

**Architecture:** Tutto in `pignone_cremagliera.py`. La funzione pura `compute_kinematics(params) → KinResult` centralizza tutta la matematica. `update_plot()` la chiama e distribuisce i risultati ai 3 subplot (pignone, zoom+overlay, cinematica) e alla `DiagnosticWindow`. Nessun nuovo file Python.

**Tech Stack:** Python 3.x, numpy, matplotlib, tkinter, pytest

---

## Mappa dei file

| File | Ruolo |
|---|---|
| `pignone_cremagliera.py` | Unico file modificato: aggiunge dataclass `KinResult`, funzione `compute_kinematics`, classe `DiagnosticWindow`, refactor di `update_plot`, layout 1×3 subplot |
| `tests/test_kinematics.py` | Test unitari su `compute_kinematics` (matematica pura, no UI) |

---

## Task 1: Setup pytest + dataclass `KinResult`

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_kinematics.py`
- Modify: `pignone_cremagliera.py` (aggiunge import `dataclass` + `KinResult`)

- [ ] **Step 1: Installare pytest**

```bash
pip install pytest
```

Atteso: `Successfully installed pytest-...`

- [ ] **Step 2: Creare `tests/__init__.py` vuoto**

```bash
echo. > tests/__init__.py
```

(Su Windows bash: `touch tests/__init__.py` oppure creare file vuoto)

- [ ] **Step 3: Scrivere il test placeholder (deve girare, non fallire)**

Creare `tests/test_kinematics.py`:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pignone_cremagliera import compute_kinematics, KinResult


def make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0,
                x=0.0, ha_cr_coeff=1.0, c_coeff=0.25, delta_s=0.0):
    return dict(m=m, z=z, alpha_sx_deg=alpha_sx_deg, alpha_dx_deg=alpha_dx_deg,
                x=x, ha_cr_coeff=ha_cr_coeff, c_coeff=c_coeff, delta_s=delta_s)


def test_import():
    params = make_params()
    result = compute_kinematics(params)
    assert isinstance(result, KinResult)
```

- [ ] **Step 4: Verificare che il test fallisca (ImportError atteso)**

```bash
cd c:/Users/nikky/Desktop/CREMAGLIERA && python -m pytest tests/test_kinematics.py::test_import -v
```

Atteso: `FAILED` con `ImportError: cannot import name 'compute_kinematics'`

- [ ] **Step 5: Aggiungere import `dataclass` + stub `KinResult` + stub `compute_kinematics` in `pignone_cremagliera.py`**

In cima al file, dopo gli import esistenti, aggiungere:

```python
from dataclasses import dataclass, field
import numpy as np  # già presente
```

Dopo la funzione `inv` e prima di `add_fillet_to_paths`, aggiungere:

```python
@dataclass
class KinResult:
    # Geometria base
    r: float = 0.0
    ra: float = 0.0
    rf: float = 0.0
    rb_sx: float = 0.0
    rb_dx: float = 0.0
    H: float = 0.0
    da: float = 0.0
    # Tratti di contatto
    ga_sx: float = 0.0
    gf_sx: float = 0.0
    ga_dx: float = 0.0
    gf_dx: float = 0.0
    # Ricoprimento
    eps_sx: float = 0.0
    eps_dx: float = 0.0
    pb_sx: float = 0.0
    pb_dx: float = 0.0
    # Spessori
    sp: float = 0.0
    scr: float = 0.0
    L: float = 0.0
    # Cinematica adimensionale
    vs_max_tip_pin_sx: float = 0.0
    vs_max_tip_pin_dx: float = 0.0
    vs_max_tip_rack_sx: float = 0.0
    vs_max_tip_rack_dx: float = 0.0
    # Diagnostica
    z_min_sx: float = 0.0
    z_min_dx: float = 0.0
    undercut_sx: bool = False
    undercut_dx: bool = False
    interference_rack_tip_sx: bool = False
    interference_rack_tip_dx: bool = False
    # Array cinematici (un passo, 200 punti)
    theta_arr: object = field(default_factory=lambda: np.zeros(200))
    u_sx_arr: object = field(default_factory=lambda: np.zeros(200))
    u_dx_arr: object = field(default_factory=lambda: np.zeros(200))
    vs_arr: object = field(default_factory=lambda: np.zeros(200))
    n_pairs_sx_arr: object = field(default_factory=lambda: np.ones(200, dtype=int))
    n_pairs_dx_arr: object = field(default_factory=lambda: np.ones(200, dtype=int))


def compute_kinematics(params: dict) -> KinResult:
    return KinResult()
```

- [ ] **Step 6: Verificare che il test passi**

```bash
python -m pytest tests/test_kinematics.py::test_import -v
```

Atteso: `PASSED`

- [ ] **Step 7: Commit**

```bash
git add tests/__init__.py tests/test_kinematics.py pignone_cremagliera.py
git commit -m "feat: add KinResult dataclass and compute_kinematics stub with tests"
```

---

## Task 2: `compute_kinematics` — geometria base + fix bug `ga`

**Files:**
- Modify: `pignone_cremagliera.py` (implementa `compute_kinematics` — solo geometria base)
- Modify: `tests/test_kinematics.py` (aggiunge test su geometria)

- [ ] **Step 1: Aggiungere test sulla geometria base**

Aggiungere in `tests/test_kinematics.py`:

```python
import numpy as np


def test_base_geometry_standard():
    """z=10, m=1, alpha=20°, x=0: valori standard ISO."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    assert abs(k.r - 5.0) < 1e-9
    assert abs(k.ra - 6.0) < 1e-9        # r + (1+0)*m
    assert abs(k.H - 5.0) < 1e-9         # r + 0*m
    assert abs(k.da - 12.0) < 1e-9
    assert abs(k.rb_sx - 5.0 * np.cos(np.radians(20.0))) < 1e-9
    assert abs(k.rb_dx - 5.0 * np.cos(np.radians(20.0))) < 1e-9


def test_profile_shift_geometry():
    """x=0.5: ra, H, rf cambiano correttamente."""
    params = make_params(m=1.0, z=10, x=0.5)
    k = compute_kinematics(params)
    assert abs(k.ra - (5.0 + 1.5)) < 1e-9    # r + (1+0.5)*m
    assert abs(k.H - 5.5) < 1e-9             # r + 0.5*m
    assert abs(k.rf - (5.0 - (1.0 + 0.25 - 0.5))) < 1e-9  # r - (ha_cr + c - x*m)


def test_ga_bug_fix_zero_x():
    """Con x=0, ga deve coincidere con ha_cr/sin(alpha)."""
    params = make_params(m=1.0, z=12, alpha_sx_deg=20.0, x=0.0, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    expected = 1.0 / np.sin(alpha)   # ha_cr=1.0*m=1.0
    assert abs(k.ga_sx - expected) < 1e-9


def test_ga_bug_fix_positive_x():
    """Con x=0.5, ga deve essere (ha_cr - x*m)/sin(alpha)."""
    params = make_params(m=1.0, z=12, alpha_sx_deg=20.0, x=0.5, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    ha_cr = 1.0 * 1.0  # ha_cr_coeff * m
    expected = (ha_cr - 0.5 * 1.0) / np.sin(alpha)
    assert abs(k.ga_sx - expected) < 1e-9


def test_ga_bug_fix_negative_x():
    """Con x=-0.3, ga deve essere (ha_cr - x*m)/sin(alpha) > ha_cr/sin(alpha)."""
    params = make_params(m=1.0, z=12, alpha_sx_deg=20.0, x=-0.3, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    ha_cr = 1.0
    expected = (ha_cr - (-0.3) * 1.0) / np.sin(alpha)
    assert abs(k.ga_sx - expected) < 1e-9


def test_gf_formula():
    """gf = sqrt(ra^2 - rb^2) - r*sin(alpha)."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    ra = 5.0 + 1.5  # r + (1+x)*m
    rb = 5.0 * np.cos(alpha)
    r = 5.0
    expected = np.sqrt(ra**2 - rb**2) - r * np.sin(alpha)
    assert abs(k.gf_sx - expected) < 1e-9


def test_contact_ratio():
    """eps = (ga + gf) / pb."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5, ha_cr_coeff=1.0)
    k = compute_kinematics(params)
    expected = (k.ga_sx + k.gf_sx) / k.pb_sx
    assert abs(k.eps_sx - expected) < 1e-9


def test_linear_displacement():
    """L = pi * m * z."""
    params = make_params(m=2.0, z=15)
    k = compute_kinematics(params)
    assert abs(k.L - np.pi * 2.0 * 15) < 1e-9


def test_tooth_thickness_symmetric():
    """sp = m*(pi/2 + x*(tan_sx + tan_dx)) - delta_s."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, alpha_dx_deg=20.0,
                         x=0.5, delta_s=0.05)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    expected = 1.0 * (np.pi / 2 + 0.5 * (np.tan(alpha) + np.tan(alpha))) - 0.05
    assert abs(k.sp - expected) < 1e-9
```

- [ ] **Step 2: Verificare che i test falliscano**

```bash
python -m pytest tests/test_kinematics.py -k "geometry or ga_bug or gf_formula or contact_ratio or linear or tooth" -v
```

Atteso: tutti `FAILED` (il metodo stub ritorna `KinResult()` con valori 0)

- [ ] **Step 3: Implementare `compute_kinematics` — geometria base**

Sostituire lo stub `compute_kinematics` in `pignone_cremagliera.py`:

```python
def compute_kinematics(params: dict) -> KinResult:
    m = params['m']
    z = params['z']
    alpha_sx = np.radians(params['alpha_sx_deg'])
    alpha_dx = np.radians(params['alpha_dx_deg'])
    x = params['x']
    ha_cr = params['ha_cr_coeff'] * m
    c = params['c_coeff'] * m
    delta_s = params['delta_s']

    r = m * z / 2.0
    rb_sx = r * np.cos(alpha_sx)
    rb_dx = r * np.cos(alpha_dx)
    hap = (1.0 + x) * m
    ra = r + hap
    da = 2.0 * ra
    hfp = ha_cr + c - x * m
    rf = r - hfp
    H = r + x * m

    # Tratto accesso CORRETTO: (ha_cr - x*m) / sin(alpha)
    ga_sx = (ha_cr - x * m) / np.sin(alpha_sx) if alpha_sx > 1e-6 else 0.0
    ga_dx = (ha_cr - x * m) / np.sin(alpha_dx) if alpha_dx > 1e-6 else 0.0

    # Tratto recesso
    gf_sx = (np.sqrt(ra**2 - rb_sx**2) - r * np.sin(alpha_sx)
             if ra > rb_sx else 0.0)
    gf_dx = (np.sqrt(ra**2 - rb_dx**2) - r * np.sin(alpha_dx)
             if ra > rb_dx else 0.0)

    pb_sx = np.pi * m * np.cos(alpha_sx)
    pb_dx = np.pi * m * np.cos(alpha_dx)
    eps_sx = (ga_sx + gf_sx) / pb_sx if pb_sx > 1e-9 else 0.0
    eps_dx = (ga_dx + gf_dx) / pb_dx if pb_dx > 1e-9 else 0.0

    L = np.pi * m * z
    sp = m * (np.pi / 2.0 + x * np.tan(alpha_sx) + x * np.tan(alpha_dx)) - delta_s
    scr = m * np.pi / 2.0 + delta_s

    # Velocità scorrimento adimensionale massima = |u_max| / r
    vs_max_tip_pin_sx = abs(gf_sx) / r if r > 1e-9 else 0.0
    vs_max_tip_pin_dx = abs(gf_dx) / r if r > 1e-9 else 0.0
    vs_max_tip_rack_sx = abs(ga_sx) / r if r > 1e-9 else 0.0
    vs_max_tip_rack_dx = abs(ga_dx) / r if r > 1e-9 else 0.0

    return KinResult(
        r=r, ra=ra, rf=rf, rb_sx=rb_sx, rb_dx=rb_dx, H=H, da=da,
        ga_sx=ga_sx, gf_sx=gf_sx, ga_dx=ga_dx, gf_dx=gf_dx,
        eps_sx=eps_sx, eps_dx=eps_dx, pb_sx=pb_sx, pb_dx=pb_dx,
        sp=sp, scr=scr, L=L,
        vs_max_tip_pin_sx=vs_max_tip_pin_sx,
        vs_max_tip_pin_dx=vs_max_tip_pin_dx,
        vs_max_tip_rack_sx=vs_max_tip_rack_sx,
        vs_max_tip_rack_dx=vs_max_tip_rack_dx,
    )
```

- [ ] **Step 4: Verificare che i test passino**

```bash
python -m pytest tests/test_kinematics.py -k "geometry or ga_bug or gf_formula or contact_ratio or linear or tooth" -v
```

Atteso: tutti `PASSED`

- [ ] **Step 5: Commit**

```bash
git add pignone_cremagliera.py tests/test_kinematics.py
git commit -m "fix: corretto bug ga=(ha_cr-x*m)/sin(alpha) e implementata geometria base in compute_kinematics"
```

---

## Task 3: `compute_kinematics` — array cinematici `u(θ)`, `|vs/vp|(θ)`, `n_pairs(θ)`

**Files:**
- Modify: `pignone_cremagliera.py` (completa `compute_kinematics` con array)
- Modify: `tests/test_kinematics.py`

- [ ] **Step 1: Aggiungere test sugli array cinematici**

```python
def test_kinematic_arrays_shape():
    """Gli array hanno 200 punti, theta da 0 a un passo."""
    params = make_params(m=1.0, z=10, x=0.0)
    k = compute_kinematics(params)
    pitch_angle = 2 * np.pi / 10
    assert len(k.theta_arr) == 200
    assert abs(k.theta_arr[0]) < 1e-9
    assert abs(k.theta_arr[-1] - pitch_angle) < 1e-9
    assert len(k.u_sx_arr) == 200
    assert len(k.vs_arr) == 200
    assert len(k.n_pairs_sx_arr) == 200


def test_u_sx_range():
    """u_sx va da -ga_sx a -ga_sx + pb_sx in un passo."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    assert abs(k.u_sx_arr[0] - (-k.ga_sx)) < 1e-9
    assert abs(k.u_sx_arr[-1] - (-k.ga_sx + k.pb_sx)) < 1e-6


def test_vs_zero_at_pitch_point():
    """vs = 0 quando u = 0 (punto primitivo)."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    # Trovare l'indice dove u_sx è più vicino a zero
    idx = np.argmin(np.abs(k.u_sx_arr))
    assert abs(k.vs_arr[idx]) < 0.01  # tolleranza per la discretizzazione


def test_n_pairs_double_contact_zone():
    """La zona di doppio contatto ha lunghezza (eps-1)*pitch_angle."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    pitch_angle = 2 * np.pi / 10
    double_len_expected = (k.eps_sx - 1) * pitch_angle
    double_theta = k.theta_arr[k.n_pairs_sx_arr == 2]
    if len(double_theta) > 0:
        measured = double_theta[-1] - double_theta[0]
        assert abs(measured - double_len_expected) < 0.05 * pitch_angle


def test_n_pairs_minimum_one():
    """n_pairs è sempre >= 1 quando eps >= 1."""
    params = make_params(m=1.0, z=10, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    if k.eps_sx >= 1.0:
        assert np.all(k.n_pairs_sx_arr >= 1)
```

- [ ] **Step 2: Verificare che i test falliscano**

```bash
python -m pytest tests/test_kinematics.py -k "arrays or u_sx or vs_zero or n_pairs" -v
```

Atteso: `FAILED` (gli array sono tutti zeros dallo stub)

- [ ] **Step 3: Aggiungere calcolo array cinematici in `compute_kinematics`**

Nel corpo di `compute_kinematics`, prima del `return KinResult(...)`, aggiungere:

```python
    # Array cinematici su un passo (200 punti)
    N = 200
    pitch_angle = 2.0 * np.pi / z
    theta_arr = np.linspace(0.0, pitch_angle, N)

    # u(theta) = rb * theta - ga  (posizione contatto lungo LoA dal pitch point)
    u_sx_arr = rb_sx * theta_arr - ga_sx
    u_dx_arr = rb_dx * theta_arr - ga_dx

    # |v_s/v_p|(theta) = max(|u_sx|, |u_dx|) / r
    vs_arr = np.maximum(np.abs(u_sx_arr), np.abs(u_dx_arr)) / r if r > 1e-9 else np.zeros(N)

    # n_pairs: zona doppio contatto = [0, (eps-1)*pitch_angle]
    def _n_pairs(eps, pa):
        if eps < 1.0:
            return np.ones(N, dtype=int)   # eps < 1 = gap, ma non blocchiamo
        double_theta = max(0.0, (eps - 1.0) * pa)
        return np.where(theta_arr < double_theta, 2, 1).astype(int)

    n_pairs_sx_arr = _n_pairs(eps_sx, pitch_angle)
    n_pairs_dx_arr = _n_pairs(eps_dx, pitch_angle)
```

E aggiornare il `return KinResult(...)` aggiungendo i campi array:

```python
    return KinResult(
        r=r, ra=ra, rf=rf, rb_sx=rb_sx, rb_dx=rb_dx, H=H, da=da,
        ga_sx=ga_sx, gf_sx=gf_sx, ga_dx=ga_dx, gf_dx=gf_dx,
        eps_sx=eps_sx, eps_dx=eps_dx, pb_sx=pb_sx, pb_dx=pb_dx,
        sp=sp, scr=scr, L=L,
        vs_max_tip_pin_sx=vs_max_tip_pin_sx,
        vs_max_tip_pin_dx=vs_max_tip_pin_dx,
        vs_max_tip_rack_sx=vs_max_tip_rack_sx,
        vs_max_tip_rack_dx=vs_max_tip_rack_dx,
        theta_arr=theta_arr,
        u_sx_arr=u_sx_arr,
        u_dx_arr=u_dx_arr,
        vs_arr=vs_arr,
        n_pairs_sx_arr=n_pairs_sx_arr,
        n_pairs_dx_arr=n_pairs_dx_arr,
    )
```

- [ ] **Step 4: Verificare che i test passino**

```bash
python -m pytest tests/test_kinematics.py -k "arrays or u_sx or vs_zero or n_pairs" -v
```

Atteso: tutti `PASSED`

- [ ] **Step 5: Commit**

```bash
git add pignone_cremagliera.py tests/test_kinematics.py
git commit -m "feat: aggiunta curva cinematica u(theta), vs/vp(theta), n_pairs(theta) in compute_kinematics"
```

---

## Task 4: `compute_kinematics` — diagnostica (undercut, interferenza)

**Files:**
- Modify: `pignone_cremagliera.py`
- Modify: `tests/test_kinematics.py`

- [ ] **Step 1: Aggiungere test diagnostica**

```python
def test_undercut_detection():
    """z=4, x=0, alpha=20°: deve rilevare sottosquadro (z < z_min)."""
    params = make_params(m=1.0, z=4, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    alpha = np.radians(20.0)
    z_min_expected = 2.0 * (1.0 - 0.0) / np.sin(alpha)**2
    assert abs(k.z_min_sx - z_min_expected) < 1e-6
    assert k.undercut_sx is True


def test_no_undercut_with_positive_shift():
    """x=0.5 su z=8 deve eliminare il rischio di undercut."""
    params = make_params(m=1.0, z=8, alpha_sx_deg=20.0, x=0.5)
    k = compute_kinematics(params)
    assert k.undercut_sx is False


def test_interference_rack_tip():
    """ga > r*sin(alpha): interferenza della testa cremagliera."""
    # Forzare ga grande con ha_cr elevato e alpha piccolo
    params = make_params(m=1.0, z=6, alpha_sx_deg=10.0, x=-0.5, ha_cr_coeff=1.5)
    k = compute_kinematics(params)
    alpha = np.radians(10.0)
    r = 1.0 * 6 / 2.0
    limit = r * np.sin(alpha)
    if k.ga_sx > limit:
        assert k.interference_rack_tip_sx is True


def test_no_interference_standard():
    """Setup standard z=20, m=1, alpha=20°, x=0: nessuna interferenza."""
    params = make_params(m=1.0, z=20, alpha_sx_deg=20.0, x=0.0)
    k = compute_kinematics(params)
    assert k.interference_rack_tip_sx is False
    assert k.undercut_sx is False
```

- [ ] **Step 2: Verificare che i test falliscano**

```bash
python -m pytest tests/test_kinematics.py -k "undercut or interference" -v
```

Atteso: `FAILED`

- [ ] **Step 3: Aggiungere calcolo diagnostica in `compute_kinematics`**

Dopo il calcolo di `vs_arr` e prima di `return KinResult`, aggiungere:

```python
    # Diagnostica undercut: z < 2*(1-x)/sin^2(alpha)
    z_min_sx = 2.0 * (1.0 - x) / np.sin(alpha_sx)**2 if alpha_sx > 1e-6 else 0.0
    z_min_dx = 2.0 * (1.0 - x) / np.sin(alpha_dx)**2 if alpha_dx > 1e-6 else 0.0
    undercut_sx = z < z_min_sx
    undercut_dx = z < z_min_dx

    # Interferenza testa cremagliera: ga > r*sin(alpha) (rack tip oltre cerchio base)
    interference_rack_tip_sx = ga_sx > r * np.sin(alpha_sx)
    interference_rack_tip_dx = ga_dx > r * np.sin(alpha_dx)
```

Aggiornare `return KinResult(...)` con i nuovi campi:

```python
        z_min_sx=z_min_sx, z_min_dx=z_min_dx,
        undercut_sx=undercut_sx, undercut_dx=undercut_dx,
        interference_rack_tip_sx=interference_rack_tip_sx,
        interference_rack_tip_dx=interference_rack_tip_dx,
```

- [ ] **Step 4: Verificare che i test passino**

```bash
python -m pytest tests/test_kinematics.py -v
```

Atteso: tutti `PASSED`

- [ ] **Step 5: Commit**

```bash
git add pignone_cremagliera.py tests/test_kinematics.py
git commit -m "feat: aggiunta diagnostica undercut e interferenza in compute_kinematics"
```

---

## Task 5: Refactor `update_plot` — usa `compute_kinematics`

**Files:**
- Modify: `pignone_cremagliera.py`

Nessun test nuovo (UI); verificare visivamente che i valori nel pannello risultati siano invariati rispetto a prima (ad eccezione di `ga` che ora è corretto).

- [ ] **Step 1: Aggiungere metodo helper `_params_from_vars` in `RackPinionVisualizer`**

Aggiungere in cima ai metodi della classe, dopo `create_widgets`:

```python
def _params_from_vars(self) -> dict:
    return dict(
        m=self.vars['m'].get(),
        z=self.vars['z'].get(),
        alpha_sx_deg=self.vars['alpha_sx'].get(),
        alpha_dx_deg=self.vars['alpha_dx'].get(),
        x=self.vars['x'].get(),
        ha_cr_coeff=self.vars['ha_cr_coeff'].get(),
        c_coeff=self.vars['c_coeff'].get(),
        delta_s=self.vars['delta_s'].get(),
    )
```

- [ ] **Step 2: Sostituire i calcoli all'inizio di `update_plot` con una chiamata a `compute_kinematics`**

Nella funzione `update_plot`, sostituire il blocco che va dal `try:` fino all'assegnazione di `scr` con:

```python
def update_plot(self, *args):
    try:
        params = self._params_from_vars()
        rot = np.radians(self.vars['rot_deg'].get())
        rho_ap = self.vars['rho_ap_coeff'].get() * params['m']
        rho_fp = self.vars['rho_fp_coeff'].get() * params['m']
        rho_ac = self.vars['rho_ac_coeff'].get() * params['m']
        rho_fc = self.vars['rho_fc_coeff'].get() * params['m']
    except tk.TclError:
        return

    kin = compute_kinematics(params)
    m, z = params['m'], params['z']
    r, ra, rf, H = kin.r, kin.ra, kin.rf, kin.H
    rb_sx, rb_dx = kin.rb_sx, kin.rb_dx
    alpha_sx = np.radians(params['alpha_sx_deg'])
    alpha_dx = np.radians(params['alpha_dx_deg'])
    x = params['x']
    delta_s = params['delta_s']
    ha_cr = params['ha_cr_coeff'] * m
    c = params['c_coeff'] * m
```

- [ ] **Step 3: Aggiornare le label dei risultati usando `kin`**

Nel corpo di `update_plot`, sostituire le righe `self.res_labels[...].config(...)` con:

```python
    self.res_labels['Interasse di montaggio (H)'].config(text=f"{kin.H:.3f} mm")
    self.res_labels['Ricoprimento (ε_α) [SX | DX]'].config(
        text=f"{kin.eps_sx:.3f} | {kin.eps_dx:.3f}")
    color_eps = 'red' if (kin.eps_sx < 1.0 or kin.eps_dx < 1.0) else 'forestgreen'
    self.res_labels['Ricoprimento (ε_α) [SX | DX]'].config(foreground=color_eps)
    self.res_labels['Tratto Accesso (ga) [SX | DX]'].config(
        text=f"{kin.ga_sx:.3f} | {kin.ga_dx:.3f} mm")
    self.res_labels['Tratto Recesso (gf) [SX | DX]'].config(
        text=f"{kin.gf_sx:.3f} | {kin.gf_dx:.3f} mm")
    asym_sx = kin.gf_sx / kin.ga_sx if kin.ga_sx > 1e-9 else 0.0
    asym_dx = kin.gf_dx / kin.ga_dx if kin.ga_dx > 1e-9 else 0.0
    self.res_labels['Asimmetria (gf/ga) [SX | DX]'].config(
        text=f"{asym_sx:.3f} | {asym_dx:.3f}")
    self.res_labels['Spostamento lineare per giro (L)'].config(
        text=f"{kin.L:.3f} mm")
    self.res_labels['Diametro Esterno Pignone (da)'].config(
        text=f"{kin.da:.3f} mm")
    self.res_labels['Diametro Base (db) [SX | DX]'].config(
        text=f"{2*kin.rb_sx:.3f} | {2*kin.rb_dx:.3f} mm")
    self.res_labels['Spessore Pignone Pitch (sp)'].config(
        text=f"{kin.sp:.3f} mm")
    self.res_labels['Spessore Crem. Datum (scr)'].config(
        text=f"{kin.scr:.3f} mm")
```

- [ ] **Step 4: Aggiornare le chiamate a `draw_pinion` e `draw_rack` usando variabili `kin`**

Le chiamate restano identiche, usano le stesse variabili (`r`, `ra`, `rf`, `H`, etc.) ora derivate da `kin`:

```python
    self.draw_pinion(a, m, z, alpha_sx, alpha_dx, x, delta_s, rf, ra, rot, rho_ap, rho_fp)
    linear_disp = r * rot
    self.draw_rack(a, m, z, alpha_sx, alpha_dx, H, ha_cr, c, delta_s, linear_disp, rho_ac, rho_fc)
```

- [ ] **Step 5: Avviare l'app e verificare visivamente**

```bash
python pignone_cremagliera.py
```

Controllare:
- I valori nel pannello risultati appaiono corretti
- L'animazione funziona
- Con x=0.5, `ga` è ora più piccolo di quello precedente (bug corretto)
- Con x=0, `ga` è uguale al vecchio valore (nessuna regressione)

- [ ] **Step 6: Commit**

```bash
git add pignone_cremagliera.py
git commit -m "refactor: update_plot usa compute_kinematics, rimosso calcolo duplicato"
```

---

## Task 6: Layout 1×3 + diagramma cinematico `ax_kinem`

**Files:**
- Modify: `pignone_cremagliera.py`

- [ ] **Step 1: Aggiornare la creazione della figura da 1×2 a 1×3**

In `create_widgets`, sostituire:

```python
self.fig = Figure(figsize=(12, 7), dpi=100)
self.ax = self.fig.add_subplot(1, 2, 1)
self.ax_zoom = self.fig.add_subplot(1, 2, 2)
```

con:

```python
self.fig = Figure(figsize=(18, 7), dpi=100)
self.ax = self.fig.add_subplot(1, 3, 1)
self.ax_zoom = self.fig.add_subplot(1, 3, 2)
self.ax_kinem = self.fig.add_subplot(1, 3, 3)
```

E aggiornare il loop di inizializzazione della griglia:

```python
self.fig.patch.set_facecolor('#fafafa')
for a in [self.ax, self.ax_zoom, self.ax_kinem]:
    a.set_facecolor('#ffffff')
```

- [ ] **Step 2: Aggiungere metodo `_draw_kinematic_diagram(self, kin, rot)`**

Aggiungere come nuovo metodo della classe, prima di `draw_pinion`:

```python
def _draw_kinematic_diagram(self, kin: KinResult, rot: float):
    ax = self.ax_kinem
    ax.clear()
    ax.set_facecolor('#ffffff')

    # Asse x: spostamento REALE cremagliera = r * theta (NON rb * theta)
    # In un passo completo (theta da 0 a 2pi/z), la cremagliera avanza di pi*m
    disp = kin.r * kin.theta_arr      # [mm], va da 0 a pi*m
    disp_end = disp[-1]               # = pi*m = passo circolare

    # u_sx = 0 (pitch point) quando rb_sx * theta = ga_sx -> theta = ga_sx/rb_sx
    # -> rack displacement = r * (ga_sx/rb_sx) = ga_sx / cos(alpha_sx)
    alpha_sx_rad = np.arccos(max(kin.rb_sx / kin.r, 0.0)) if kin.r > 1e-9 else 0.0
    alpha_dx_rad = np.arccos(max(kin.rb_dx / kin.r, 0.0)) if kin.r > 1e-9 else 0.0
    zero_disp_sx = kin.ga_sx / np.cos(alpha_sx_rad) if np.cos(alpha_sx_rad) > 1e-9 else disp_end / 2

    # Sfondo zone accesso/recesso
    ax.axvspan(0, min(zero_disp_sx, disp_end), alpha=0.12, color='#ff8888', label='Accesso (ga)')
    ax.axvspan(min(zero_disp_sx, disp_end), disp_end, alpha=0.12, color='#88cc88', label='Recesso (gf)')

    # Curva u_sx(theta) e u_dx(theta): posizione contatto lungo LoA
    ax.plot(disp, kin.u_sx_arr, '-', color='#0052cc', linewidth=1.8, label='u_sx(θ) [mm]')
    ax.plot(disp, kin.u_dx_arr, '--', color='#cc0052', linewidth=1.2, label='u_dx(θ) [mm]')
    ax.axhline(0, color='gray', linewidth=0.8, linestyle=':')

    # Asse Y destro: |vs/vp|
    ax2 = ax.twinx()
    ax2.plot(disp, kin.vs_arr, '-', color='#cc6600', linewidth=1.2, alpha=0.7,
             label='|vs/vp|')
    ax2.set_ylabel('|vs/vp| [-]', fontsize=8, color='#cc6600')
    ax2.tick_params(axis='y', labelcolor='#cc6600', labelsize=7)
    ax2.set_ylim(bottom=0)

    # Zona doppio contatto sx (sfondo grigio)
    # Termina a rack_disp = r * (eps_sx - 1) * pitch_angle
    pitch_angle_rad = kin.theta_arr[-1]   # = 2*pi/z
    if kin.eps_sx > 1.0:
        double_disp_end = kin.r * (kin.eps_sx - 1.0) * pitch_angle_rad
        ax.axvspan(0, min(double_disp_end, disp_end), alpha=0.15, color='gray',
                   label=f'Doppio contatto ({(kin.eps_sx-1)*100:.0f}%)')

    # Linea verticale = posizione angolare corrente
    rot_mod = rot % pitch_angle_rad if pitch_angle_rad > 1e-9 else 0.0
    current_disp = kin.r * rot_mod
    ax.axvline(current_disp, color='black', linewidth=1.5, linestyle='--', alpha=0.7)

    ax.set_xlabel('Spostamento cremagliera [mm]', fontsize=8)
    ax.set_ylabel('u — pos. contatto lungo LoA [mm]', fontsize=8)
    ax.set_title(f'Cinematica 1 Passo  ε_sx={kin.eps_sx:.3f} | ε_dx={kin.eps_dx:.3f}',
                 fontsize=9, fontweight='bold')
    ax.legend(loc='lower right', fontsize='xx-small', framealpha=0.6)
    ax.set_xlim(0, disp_end)
    ax.tick_params(labelsize=7)
    ax.xaxis.set_major_locator(MultipleLocator(max(0.1, round(disp_end / 5, 1))))
    ax.grid(which='major', linestyle='--', alpha=0.3)
```

- [ ] **Step 3: Chiamare `_draw_kinematic_diagram` da `update_plot`**

In `update_plot`, prima di `self.fig.tight_layout()`, aggiungere:

```python
    self._draw_kinematic_diagram(kin, rot)
```

- [ ] **Step 4: Avviare l'app e verificare il terzo subplot**

```bash
python pignone_cremagliera.py
```

Verificare:
- Tre subplot visibili
- Il diagramma cinematico mostra u_sx (blu), u_dx (rosso tratteggiato), |vs/vp| (arancio)
- La linea verticale nera si muove durante l'animazione
- Il punto zero di u coincide con il cambio accesso/recesso
- Le zone di sfondo sono corrette (rosa = accesso, verde = recesso)

- [ ] **Step 5: Commit**

```bash
git add pignone_cremagliera.py
git commit -m "feat: aggiunto diagramma cinematico ax_kinem con u(theta), vs/vp, n_pairs"
```

---

## Task 7: Overlay punto di contatto su `ax_zoom`

**Files:**
- Modify: `pignone_cremagliera.py`

- [ ] **Step 1: Aggiungere metodo `_draw_contact_overlay(self, ax, kin, rot)`**

```python
def _draw_contact_overlay(self, ax, kin: KinResult, rot: float):
    """Disegna segmento retta d'azione attiva e punto di contatto istantaneo."""
    r = kin.r
    alpha_sx = np.arccos(kin.rb_sx / r) if r > 1e-9 else 0.0
    alpha_dx = np.arccos(kin.rb_dx / r) if r > 1e-9 else 0.0

    # Coordinata del punto a distanza u lungo la LoA sx: (u*cos(alpha), -r + u*sin(alpha))
    # Coordinata del punto a distanza u lungo la LoA dx: (-u*cos(alpha), -r + u*sin(alpha))

    # Segmento zona attiva sx (arancio = accesso, verde = recesso)
    def loa_point_sx(u):
        return u * np.cos(alpha_sx), -r + u * np.sin(alpha_sx)

    def loa_point_dx(u):
        return -u * np.cos(alpha_dx), -r + u * np.sin(alpha_dx)

    # Tratto accesso sx: da u=-ga_sx a u=0
    if kin.ga_sx > 1e-6:
        p_start = loa_point_sx(-kin.ga_sx)
        p_pitch = loa_point_sx(0.0)
        ax.plot([p_start[0], p_pitch[0]], [p_start[1], p_pitch[1]],
                '-', color='orange', linewidth=2.5, alpha=0.8, zorder=8)

    # Tratto recesso sx: da u=0 a u=gf_sx
    if kin.gf_sx > 1e-6:
        p_pitch = loa_point_sx(0.0)
        p_end = loa_point_sx(kin.gf_sx)
        ax.plot([p_pitch[0], p_end[0]], [p_pitch[1], p_end[1]],
                '-', color='limegreen', linewidth=2.5, alpha=0.8, zorder=8)

    # Tratto accesso dx (speculare)
    if kin.ga_dx > 1e-6:
        p_start = loa_point_dx(-kin.ga_dx)
        p_pitch = loa_point_dx(0.0)
        ax.plot([p_start[0], p_pitch[0]], [p_start[1], p_pitch[1]],
                '-', color='orange', linewidth=2.5, alpha=0.5, zorder=8)

    if kin.gf_dx > 1e-6:
        p_pitch = loa_point_dx(0.0)
        p_end = loa_point_dx(kin.gf_dx)
        ax.plot([p_pitch[0], p_end[0]], [p_pitch[1], p_end[1]],
                '-', color='limegreen', linewidth=2.5, alpha=0.5, zorder=8)

    # Punto di contatto istantaneo
    pitch_angle = kin.theta_arr[-1]
    rot_mod = rot % pitch_angle if pitch_angle > 1e-9 else 0.0

    u_sx_now = kin.rb_sx * rot_mod - kin.ga_sx
    if -kin.ga_sx <= u_sx_now <= kin.gf_sx:
        cx, cy = loa_point_sx(u_sx_now)
        ax.plot(cx, cy, 'o', color='limegreen', markersize=8,
                markeredgecolor='darkgreen', zorder=15)

    u_dx_now = kin.rb_dx * rot_mod - kin.ga_dx
    if -kin.ga_dx <= u_dx_now <= kin.gf_dx:
        cx, cy = loa_point_dx(u_dx_now)
        ax.plot(cx, cy, 'o', color='limegreen', markersize=8,
                markeredgecolor='darkgreen', zorder=15, alpha=0.7)
```

- [ ] **Step 2: Chiamare `_draw_contact_overlay` in `update_plot` per `ax_zoom`**

Dopo il loop `for a in [self.ax, self.ax_zoom]:` e dopo aver impostato i limiti di `ax_zoom`, aggiungere:

```python
    self._draw_contact_overlay(self.ax_zoom, kin, rot)
```

- [ ] **Step 3: Avviare l'app e verificare l'overlay**

```bash
python pignone_cremagliera.py
```

Verificare nella vista zoom:
- Segmento arancio dal punto d'accesso al pitch point
- Segmento verde dal pitch point al punto di recesso
- Punto verde che scorre lungo la LoA durante l'animazione
- Il punto è visibile solo quando il dente è in presa
- Con `rot_deg=0` il punto è all'inizio dell'accesso

- [ ] **Step 4: Commit**

```bash
git add pignone_cremagliera.py
git commit -m "feat: overlay punto contatto animato e zona attiva su ax_zoom"
```

---

## Task 8: `DiagnosticWindow` — finestra separata

**Files:**
- Modify: `pignone_cremagliera.py` (aggiunge classe `DiagnosticWindow` prima di `RackPinionVisualizer`)

- [ ] **Step 1: Aggiungere la classe `DiagnosticWindow`**

Prima della definizione di `class RackPinionVisualizer`, aggiungere:

```python
class DiagnosticWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Diagnostica Cinematica")
        self.geometry("500x540")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        # Blocco 1: Limiti geometrici
        f1 = ttk.LabelFrame(self, text="Limiti Geometrici")
        f1.pack(fill=tk.X, padx=10, pady=5)
        headers = ["Parametro", "Valore", "Limite", "Margine", "Stato"]
        for c, h in enumerate(headers):
            ttk.Label(f1, text=h, font=('Arial', 8, 'bold')).grid(
                row=0, column=c, padx=4, pady=2)
        self._g1_rows = {}
        row_defs = [
            ('z_min_sx', 'z min sx (undercut)'),
            ('z_min_dx', 'z min dx (undercut)'),
            ('ga_sx',    'ga sx [mm]'),
            ('ga_dx',    'ga dx [mm]'),
        ]
        for i, (key, label) in enumerate(row_defs, start=1):
            ttk.Label(f1, text=label, font=('Arial', 8)).grid(
                row=i, column=0, sticky='w', padx=4)
            cells = {}
            for j, col in enumerate(['val', 'lim', 'mar', 'sta']):
                lbl = ttk.Label(f1, text='—', font=('Arial', 8), width=10)
                lbl.grid(row=i, column=j+1, padx=4)
                cells[col] = lbl
            self._g1_rows[key] = cells

        # Blocco 2: Check interferenza
        f2 = ttk.LabelFrame(self, text="Check Interferenza")
        f2.pack(fill=tk.X, padx=10, pady=5)
        self._interf_labels = {}
        interf_defs = [
            ('rack_tip_sx', 'Testa cremagliera → pignone sx'),
            ('rack_tip_dx', 'Testa cremagliera → pignone dx'),
            ('ra_rb_sx',    'ra > rb sx'),
            ('ra_rb_dx',    'ra > rb dx'),
        ]
        for i, (key, label) in enumerate(interf_defs):
            ttk.Label(f2, text=label, font=('Arial', 8)).grid(
                row=i, column=0, sticky='w', padx=4, pady=2)
            lbl = ttk.Label(f2, text='—', font=('Arial', 9, 'bold'), width=6)
            lbl.grid(row=i, column=1, padx=8)
            self._interf_labels[key] = lbl

        # Blocco 3: Grandezze cinematiche
        f3 = ttk.LabelFrame(self, text="Grandezze Cinematiche")
        f3.pack(fill=tk.X, padx=10, pady=5)
        self._kin_labels = {}
        kin_defs = [
            ('zona_sx',       'Zona attiva sx [mm]'),
            ('zona_dx',       'Zona attiva dx [mm]'),
            ('vs_tip_pin_sx', '|vs/vp|_max tip pignone sx'),
            ('vs_tip_pin_dx', '|vs/vp|_max tip pignone dx'),
            ('vs_tip_rack_sx','|vs/vp|_max tip cremagliera sx'),
            ('vs_tip_rack_dx','|vs/vp|_max tip cremagliera dx'),
            ('doppio_sx',     'Zona doppio contatto sx [mm]'),
            ('doppio_dx',     'Zona doppio contatto dx [mm]'),
        ]
        for i, (key, label) in enumerate(kin_defs):
            ttk.Label(f3, text=label, font=('Arial', 8)).grid(
                row=i, column=0, sticky='w', padx=4, pady=2)
            lbl = ttk.Label(f3, text='—', font=('Arial', 8))
            lbl.grid(row=i, column=1, sticky='e', padx=8)
            self._kin_labels[key] = lbl

    def _status(self, ok: bool, margin_pct: float = None):
        """Restituisce (testo, colore) per un check booleano."""
        if not ok:
            return '✗', '#cc0000'
        if margin_pct is not None and margin_pct < 10.0:
            return '⚠', '#cc6600'
        return '✓', '#006600'

    def refresh(self, kin: KinResult, z: int):
        """Aggiorna tutti i valori dalla finestra principale."""
        # Blocco 1
        def _set_row(key, val, lim, margin, ok, margin_pct=None):
            cells = self._g1_rows[key]
            cells['val'].config(text=f"{val:.3f}")
            cells['lim'].config(text=f"{lim:.3f}")
            cells['mar'].config(text=f"{margin:.3f}")
            txt, col = self._status(ok, margin_pct)
            cells['sta'].config(text=txt, foreground=col)

        margin_z_sx = z - kin.z_min_sx
        margin_z_dx = z - kin.z_min_dx
        _set_row('z_min_sx', kin.z_min_sx, z, margin_z_sx,
                 not kin.undercut_sx, margin_z_sx / max(z, 1) * 100)
        _set_row('z_min_dx', kin.z_min_dx, z, margin_z_dx,
                 not kin.undercut_dx, margin_z_dx / max(z, 1) * 100)

        ga_sx_limit = kin.r * np.sin(np.arccos(kin.rb_sx / kin.r)) if kin.r > 1e-9 else 0.0
        ga_dx_limit = kin.r * np.sin(np.arccos(kin.rb_dx / kin.r)) if kin.r > 1e-9 else 0.0
        _set_row('ga_sx', kin.ga_sx, ga_sx_limit, ga_sx_limit - kin.ga_sx,
                 not kin.interference_rack_tip_sx,
                 (ga_sx_limit - kin.ga_sx) / max(ga_sx_limit, 1e-9) * 100)
        _set_row('ga_dx', kin.ga_dx, ga_dx_limit, ga_dx_limit - kin.ga_dx,
                 not kin.interference_rack_tip_dx,
                 (ga_dx_limit - kin.ga_dx) / max(ga_dx_limit, 1e-9) * 100)

        # Blocco 2
        def _set_interf(key, ok):
            txt, col = self._status(ok)
            self._interf_labels[key].config(text=txt, foreground=col)

        _set_interf('rack_tip_sx', not kin.interference_rack_tip_sx)
        _set_interf('rack_tip_dx', not kin.interference_rack_tip_dx)
        _set_interf('ra_rb_sx', kin.ra > kin.rb_sx)
        _set_interf('ra_rb_dx', kin.ra > kin.rb_dx)

        # Blocco 3
        def _set_kin(key, val, unit=''):
            self._kin_labels[key].config(text=f"{val:.4f}{unit}")

        _set_kin('zona_sx',       kin.ga_sx + kin.gf_sx, ' mm')
        _set_kin('zona_dx',       kin.ga_dx + kin.gf_dx, ' mm')
        _set_kin('vs_tip_pin_sx', kin.vs_max_tip_pin_sx)
        _set_kin('vs_tip_pin_dx', kin.vs_max_tip_pin_dx)
        _set_kin('vs_tip_rack_sx',kin.vs_max_tip_rack_sx)
        _set_kin('vs_tip_rack_dx',kin.vs_max_tip_rack_dx)
        doppio_sx = max(0.0, (kin.eps_sx - 1.0) * kin.pb_sx)
        doppio_dx = max(0.0, (kin.eps_dx - 1.0) * kin.pb_dx)
        _set_kin('doppio_sx', doppio_sx, ' mm')
        _set_kin('doppio_dx', doppio_dx, ' mm')
```

- [ ] **Step 2: Avviare l'app, verificare che nessun errore appaia**

```bash
python pignone_cremagliera.py
```

Atteso: l'app si apre normalmente (la finestra diagnostica non è ancora visibile, verrà agganciata nel Task 9).

- [ ] **Step 3: Commit**

```bash
git add pignone_cremagliera.py
git commit -m "feat: aggiunta classe DiagnosticWindow con blocchi geometria, interferenza, cinematica"
```

---

## Task 9: Wiring bottone + integrazione `update_plot`

**Files:**
- Modify: `pignone_cremagliera.py`

- [ ] **Step 1: Aggiungere l'attributo `diag_win` e il bottone nel `__init__`**

In `RackPinionVisualizer.__init__`, prima di `self.create_widgets()`, aggiungere:

```python
self.diag_win = None
```

In `create_widgets`, nel `btn_frame`, aggiungere dopo il bottone "Esporta DXF":

```python
ttk.Button(btn_frame, text="Diagnostica Cinematica",
           command=self.open_diagnostics).pack(side=tk.TOP, fill=tk.X, pady=2)
```

- [ ] **Step 2: Aggiungere il metodo `open_diagnostics`**

```python
def open_diagnostics(self):
    if self.diag_win is not None and self.diag_win.winfo_exists():
        self.diag_win.lift()
    else:
        self.diag_win = DiagnosticWindow(self)
    # Aggiornare subito con i valori correnti
    try:
        params = self._params_from_vars()
        kin = compute_kinematics(params)
        self.diag_win.refresh(kin, params['z'])
    except Exception:
        pass
```

- [ ] **Step 3: Chiamare `diag_win.refresh` da `update_plot`**

In `update_plot`, dopo `self._draw_kinematic_diagram(kin, rot)`, aggiungere:

```python
    if self.diag_win is not None and self.diag_win.winfo_exists():
        self.diag_win.refresh(kin, z)
```

- [ ] **Step 4: Test finale completo**

```bash
python pignone_cremagliera.py
```

Eseguire questi check manuali:
1. Aprire la finestra diagnostica → appare con valori corretti
2. Muovere lo slider `z` a 4 → `z_min_sx` passa in rosso (undercut)
3. Muovere `alpha_sx` a 10° con `ha_cr=1.5` e `x=-0.5` → interferenza rack tip in rosso
4. Setup standard (z=10, alpha=20°, x=0.5) → tutti i check verdi
5. Avviare animazione → punto di contatto si muove su ax_zoom, linea verticale si muove su ax_kinem
6. Modificare alpha_sx ≠ alpha_dx → i valori sx e dx divergono correttamente
7. Chiudere e riaprire la finestra diagnostica → funziona senza errori

- [ ] **Step 5: Run suite test finale**

```bash
python -m pytest tests/ -v
```

Atteso: tutti `PASSED`

- [ ] **Step 6: Commit finale**

```bash
git add pignone_cremagliera.py
git commit -m "feat: wiring bottone diagnostica e aggiornamento automatico da update_plot"
```

---

## Riepilogo commit

| Task | Commit message |
|---|---|
| 1 | `feat: add KinResult dataclass and compute_kinematics stub with tests` |
| 2 | `fix: corretto bug ga=(ha_cr-x*m)/sin(alpha) e implementata geometria base in compute_kinematics` |
| 3 | `feat: aggiunta curva cinematica u(theta), vs/vp(theta), n_pairs(theta)` |
| 4 | `feat: aggiunta diagnostica undercut e interferenza in compute_kinematics` |
| 5 | `refactor: update_plot usa compute_kinematics, rimosso calcolo duplicato` |
| 6 | `feat: aggiunto diagramma cinematico ax_kinem` |
| 7 | `feat: overlay punto contatto animato e zona attiva su ax_zoom` |
| 8 | `feat: aggiunta classe DiagnosticWindow` |
| 9 | `feat: wiring bottone diagnostica e aggiornamento automatico da update_plot` |
