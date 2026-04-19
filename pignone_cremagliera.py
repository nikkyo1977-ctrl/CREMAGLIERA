import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from matplotlib.ticker import MultipleLocator
from matplotlib.figure import Figure
from dataclasses import dataclass, field

def inv(alpha):
    return np.tan(alpha) - alpha

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

def add_fillet_to_paths(A, B, R):
    if R < 1e-4 or len(A) < 2 or len(B) < 2:
        return A + B[1:]
    Pc = np.array(A[-1])
    
    L_A = np.linalg.norm(np.array(A[0]) - Pc)
    L_B = np.linalg.norm(np.array(B[-1]) - Pc)
    
    def get_dir(path, reverse=False):
        step = -1 if not reverse else 1
        curr = len(path)-1 if not reverse else 0
        for _ in range(min(25, len(path)-1)):
            d = np.linalg.norm(np.array(path[curr]) - Pc)
            if d > R/3.0 + 1e-4: break
            curr += step
        vec = np.array(path[curr]) if 0 <= curr < len(path) else np.array(path[0])
        vec = vec - Pc
        n = np.linalg.norm(vec)
        if n > 0: return vec/n
        vec = np.array(path[-2 if not reverse else 1]) - Pc
        n = np.linalg.norm(vec)
        return vec/n if n > 0 else np.array([1.0, 0.0])
        
    vA = get_dir(A, reverse=False)
    vB = get_dir(B, reverse=True)
    dot_val = np.clip(np.dot(vA, vB), -1.0, 1.0)
    theta = np.arccos(dot_val)
    if theta < 1e-3 or theta > np.pi - 1e-3: return A + B[1:]
    
    t = R / np.tan(theta/2)
    # Protezione matematica contro raccordi che consumano l'intero dente
    if L_A < t or L_B < t:
        t = min(t, L_A * 0.9, L_B * 0.9)
        R = t * np.tan(theta/2)
        
    TA = Pc + t * vA
    TB = Pc + t * vB
    center_dir = vA + vB
    n_dir = np.linalg.norm(center_dir)
    if n_dir < 1e-5: return A + B[1:]
    C = Pc + center_dir / n_dir * (R / np.sin(theta/2))
    angA = np.arctan2(TA[1]-C[1], TA[0]-C[0])
    angB = np.arctan2(TB[1]-C[1], TB[0]-C[0])
    d_ang = (angB - angA) % (2*np.pi)
    if d_ang > np.pi: d_ang -= 2*np.pi
    arc_angs = angA + np.linspace(0, d_ang, max(6, int(abs(d_ang)*15)))
    arc_pts = [(C[0] + R*np.cos(a), C[1] + R*np.sin(a)) for a in arc_angs]
    
    catA = A[:]
    for i in range(len(A)-1, -1, -1):
        if np.linalg.norm(np.array(A[i]) - Pc) >= t:
            catA = A[:i+1]
            break
            
    catB = B[:]
    for i in range(0, len(B)):
        if np.linalg.norm(np.array(B[i]) - Pc) >= t:
            catB = B[i:]
            break
            
    return catA + arc_pts + catB

class RackPinionVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tool di Analisi e Ottimizzazione Pignone-Cremagliera")
        self.geometry("1400x900")
        
        self.create_widgets()
        self.update_plot()
        
    def create_widgets(self):
        ctrl_frame = ttk.LabelFrame(self, text="Parametri di Progetto")
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        self.vars = {
            'm': tk.DoubleVar(value=1.0),
            'z': tk.IntVar(value=8),
            'alpha_sx': tk.DoubleVar(value=20.0),
            'alpha_dx': tk.DoubleVar(value=20.0),
            'x': tk.DoubleVar(value=-0.08),
            'ha_cr_coeff': tk.DoubleVar(value=0.39),
            'c_coeff': tk.DoubleVar(value=0.25),
            'delta_s': tk.DoubleVar(value=0.0),
            'rot_deg': tk.DoubleVar(value=0.0),
            'rho_ap_coeff': tk.DoubleVar(value=0.1),
            'rho_fp_coeff': tk.DoubleVar(value=0.2),
            'rho_ac_coeff': tk.DoubleVar(value=0.1),
            'rho_fc_coeff': tk.DoubleVar(value=0.2)
        }
        
        sliders = [
            ('Modulo (m) [mm]', 'm', 0.5, 5.0, 0.1),
            ('Numero Denti (z)', 'z', 4, 40, 1),
            ('Angolo Pressione Sx α_L (°)', 'alpha_sx', 10.0, 35.0, 0.5),
            ('Angolo Pressione Dx α_R (°)', 'alpha_dx', 10.0, 35.0, 0.5),
            ('Spostamento Profilo (x)', 'x', -1.5, 1.5, 0.01),
            ('Alto Testa Crem. (ha_cr/m)', 'ha_cr_coeff', 0.1, 1.5, 0.01),
            ('Gioco di fondo (c/m)', 'c_coeff', 0.1, 0.5, 0.01),
            ('Racc. Testa Pignone (ρ_ap/m)', 'rho_ap_coeff', 0.0, 0.4, 0.01),
            ('Racc. Fondo Pignone (ρ_fp/m)', 'rho_fp_coeff', 0.0, 0.4, 0.01),
            ('Racc. Testa Crem. (ρ_ac/m)', 'rho_ac_coeff', 0.0, 0.4, 0.01),
            ('Racc. Fondo Crem. (ρ_fc/m)', 'rho_fc_coeff', 0.0, 0.4, 0.01),
            ('Var. Spessore Cordale (Δs) [mm]', 'delta_s', -1.0, 1.0, 0.01),
            ('Rotazione (°)', 'rot_deg', 0, 360, 1)
        ]
        
        row = 0
        self.scales = {}
        for label, var_name, vmin, vmax, step in sliders:
            ttk.Label(ctrl_frame, text=label).grid(row=row, column=0, sticky='w', pady=5, padx=5)
            
            scale = ttk.Scale(ctrl_frame, variable=self.vars[var_name], from_=vmin, to=vmax, orient=tk.HORIZONTAL, command=lambda e: self.update_plot())
            scale.grid(row=row, column=1, padx=5)
            self.scales[var_name] = scale
            
            entry = ttk.Entry(ctrl_frame, textvariable=self.vars[var_name], width=8)
            entry.grid(row=row, column=2, padx=5)
            entry.bind('<Return>', lambda e: self.update_plot())
            entry.bind('<FocusOut>', lambda e: self.update_plot())
            
            row += 1
            
        btn_frame = ttk.Frame(ctrl_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=15)
        ttk.Button(btn_frame, text="Carica Setup 1 (Standard)", command=self.preset_standard).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Carica Setup 2 (Ottimizzato Plastica)", command=self.preset_optimized).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Avvia/Ferma Animazione", command=self.toggle_animation).pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Esporta DXF", command=self.export_dxf).pack(side=tk.TOP, fill=tk.X, pady=2)
        self.is_animating = False
            
        res_frame = ttk.LabelFrame(ctrl_frame, text="Analisi Cinematica e Geometrica")
        res_frame.grid(row=row+1, column=0, columnspan=3, sticky='ew', pady=10, padx=5)
        
        self.res_labels = {}
        res_items = [
            'Interasse di montaggio (H)', 
            'Ricoprimento (ε_α) [SX | DX]', 
            'Tratto Accesso (ga) [SX | DX]', 
            'Tratto Recesso (gf) [SX | DX]', 
            'Asimmetria (gf/ga) [SX | DX]',
            'Spostamento lineare per giro (L)', 
            'Diametro Esterno Pignone (da)', 
            'Diametro Base (db) [SX | DX]',
            'Spessore Pignone Pitch (sp)',
            'Spessore Crem. Datum (scr)'
        ]
        
        for i, item in enumerate(res_items):
            ttk.Label(res_frame, text=item + ":", font=('Arial', 9, 'bold')).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            self.res_labels[item] = ttk.Label(res_frame, text="0.0")
            self.res_labels[item].grid(row=i, column=1, sticky='e', padx=5, pady=3)
            
        plot_frame = tk.Frame(self)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(12, 7), dpi=100)
        self.ax = self.fig.add_subplot(1, 2, 1)
        self.ax_zoom = self.fig.add_subplot(1, 2, 2)
        
        self.fig.patch.set_facecolor('#fafafa')
        for a in [self.ax, self.ax_zoom]:
            a.set_facecolor('#ffffff')
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def preset_standard(self):
        self.vars['m'].set(1.0)
        self.vars['z'].set(10)
        self.vars['alpha_sx'].set(20.0)
        self.vars['alpha_dx'].set(20.0)
        self.vars['x'].set(0.5)
        self.vars['ha_cr_coeff'].set(1.0)
        self.vars['c_coeff'].set(0.25)
        self.vars['delta_s'].set(0.0)
        self.vars['rho_ap_coeff'].set(0.1)
        self.vars['rho_fp_coeff'].set(0.2)
        self.vars['rho_ac_coeff'].set(0.1)
        self.vars['rho_fc_coeff'].set(0.2)
        self.update_plot()

    def preset_optimized(self):
        self.vars['m'].set(1.0)
        self.vars['z'].set(8)
        self.vars['alpha_sx'].set(20.0)
        self.vars['alpha_dx'].set(14.0)
        self.vars['x'].set(-0.08)
        self.vars['ha_cr_coeff'].set(0.39)
        self.vars['c_coeff'].set(0.25)
        self.vars['delta_s'].set(0.15)
        self.vars['rho_ap_coeff'].set(0.1)
        self.vars['rho_fp_coeff'].set(0.25)
        self.vars['rho_ac_coeff'].set(0.1)
        self.vars['rho_fc_coeff'].set(0.25)
        self.update_plot()
        
    def toggle_animation(self):
        self.is_animating = not self.is_animating
        if self.is_animating:
            self.animate_step()
            
    def animate_step(self):
        if self.is_animating:
            curr = self.vars['rot_deg'].get()
            self.vars['rot_deg'].set((curr + 1) % 360)
            self.update_plot()
            self.after(25, self.animate_step)
            
    def update_plot(self, *args):
        try:
            m = self.vars['m'].get()
            z = self.vars['z'].get()
            alpha_sx = np.radians(self.vars['alpha_sx'].get())
            alpha_dx = np.radians(self.vars['alpha_dx'].get())
            x = self.vars['x'].get()
            ha_cr = self.vars['ha_cr_coeff'].get() * m
            c = self.vars['c_coeff'].get() * m
            delta_s = self.vars['delta_s'].get()
            rot = np.radians(self.vars['rot_deg'].get())
            
            rho_ap = self.vars['rho_ap_coeff'].get() * m
            rho_fp = self.vars['rho_fp_coeff'].get() * m
            rho_ac = self.vars['rho_ac_coeff'].get() * m
            rho_fc = self.vars['rho_fc_coeff'].get() * m
        except tk.TclError:
            return  
            
        r = m * z / 2.0
        rb_sx = r * np.cos(alpha_sx)
        rb_dx = r * np.cos(alpha_dx)
        hap = (1.0 + x) * m
        ra = r + hap
        da = 2 * ra
        hfp = ha_cr + c - x * m
        rf = r - hfp
        
        H = r + x * m
        
        ga_sx = ha_cr / np.sin(alpha_sx) if alpha_sx != 0 else 0
        gf_sx = np.sqrt(ra**2 - rb_sx**2) - r * np.sin(alpha_sx) if ra > rb_sx else 0
        pb_sx = np.pi * m * np.cos(alpha_sx)
        eps_alpha_sx = (ga_sx + gf_sx) / pb_sx if pb_sx != 0 else 0

        ga_dx = ha_cr / np.sin(alpha_dx) if alpha_dx != 0 else 0
        gf_dx = np.sqrt(ra**2 - rb_dx**2) - r * np.sin(alpha_dx) if ra > rb_dx else 0
        pb_dx = np.pi * m * np.cos(alpha_dx)
        eps_alpha_dx = (ga_dx + gf_dx) / pb_dx if pb_dx != 0 else 0
        
        L = np.pi * m * z
        sp = m * (np.pi / 2.0 + x * np.tan(alpha_sx) + x * np.tan(alpha_dx)) - delta_s
        scr = m * np.pi / 2.0 + delta_s
        
        self.res_labels['Interasse di montaggio (H)'].config(text=f"{H:.3f} mm")
        self.res_labels['Ricoprimento (ε_α) [SX | DX]'].config(text=f"{eps_alpha_sx:.3f} | {eps_alpha_dx:.3f}")
        color_eps = 'red' if (eps_alpha_sx < 1.0 or eps_alpha_dx < 1.0) else 'forestgreen'
        self.res_labels['Ricoprimento (ε_α) [SX | DX]'].config(foreground=color_eps)
        self.res_labels['Tratto Accesso (ga) [SX | DX]'].config(text=f"{ga_sx:.3f} | {ga_dx:.3f} mm")
        self.res_labels['Tratto Recesso (gf) [SX | DX]'].config(text=f"{gf_sx:.3f} | {gf_dx:.3f} mm")
        asym_sx = gf_sx/ga_sx if ga_sx!=0 else 0
        asym_dx = gf_dx/ga_dx if ga_dx!=0 else 0
        self.res_labels['Asimmetria (gf/ga) [SX | DX]'].config(text=f"{asym_sx:.3f} | {asym_dx:.3f}")
        self.res_labels['Spostamento lineare per giro (L)'].config(text=f"{L:.3f} mm")
        self.res_labels['Diametro Esterno Pignone (da)'].config(text=f"{da:.3f} mm")
        self.res_labels['Diametro Base (db) [SX | DX]'].config(text=f"{2*rb_sx:.3f} | {2*rb_dx:.3f} mm")
        self.res_labels['Spessore Pignone Pitch (sp)'].config(text=f"{sp:.3f} mm")
        self.res_labels['Spessore Crem. Datum (scr)'].config(text=f"{scr:.3f} mm")
        
        for a in [self.ax, self.ax_zoom]:
            a.clear()
            
            # Griglia millimetrata: Major 1mm, Minor 0.1mm
            a.xaxis.set_major_locator(MultipleLocator(1.0))
            a.xaxis.set_minor_locator(MultipleLocator(0.1))
            a.yaxis.set_major_locator(MultipleLocator(1.0))
            a.yaxis.set_minor_locator(MultipleLocator(0.1))
            
            a.grid(which='major', linestyle='-', alpha=0.3, color='#bbbbbb')
            a.grid(which='minor', linestyle=':', alpha=0.2, color='#cccccc')

            la_len = 1.5 * r
            la_x_sx = [-la_len * np.cos(alpha_sx), la_len * np.cos(alpha_sx)]
            la_y_sx = [-la_len * np.sin(alpha_sx) - r, la_len * np.sin(alpha_sx) - r]
            a.plot(la_x_sx, la_y_sx, '-', color='orange', alpha=0.5, label='Retta d\'Az. sx')

            la_x_dx = [-la_len * np.cos(alpha_dx), la_len * np.cos(alpha_dx)]
            la_y_dx = [la_len * np.sin(alpha_dx) - r, -la_len * np.sin(alpha_dx) - r]
            a.plot(la_x_dx, la_y_dx, '-', color='gold', alpha=0.5, label='Retta d\'Az. dx')
            
            theta = np.linspace(0, 2*np.pi, 200)
            a.plot(r * np.cos(theta), r * np.sin(theta), 'g--', alpha=0.4, label='Primitiva (r)')
            a.plot(ra * np.cos(theta), ra * np.sin(theta), 'r--', alpha=0.2, label='Esterna (ra)')
            a.plot(rb_sx * np.cos(theta), rb_sx * np.sin(theta), 'b:', alpha=0.3, label='Base sx (rb_L)')
            a.plot(rb_dx * np.cos(theta), rb_dx * np.sin(theta), 'c:', alpha=0.3, label='Base dx (rb_R)')
            
            self.draw_pinion(a, m, z, alpha_sx, alpha_dx, x, delta_s, rf, ra, rot, rho_ap, rho_fp)
            linear_disp = r * rot
            self.draw_rack(a, m, z, alpha_sx, alpha_dx, H, ha_cr, c, delta_s, linear_disp, rho_ac, rho_fc)
            
            a.set_aspect('equal')
            a.legend(loc='upper right', fontsize='xx-small', framealpha=0.6)
        
        # Limiti Vista Principale (Focalizzata sul Pignone)
        limit_p = ra + 2*m
        self.ax.set_xlim(-limit_p, limit_p)
        self.ax.set_ylim(-H - 2*m, ra + m)
        self.ax.set_title("Dettaglio Pignone", fontsize=10, fontweight='bold')

        # Limiti Vista Zoom (centrata sul punto di contatto teorico in basso)
        zoom_w = 4.0 * m
        self.ax_zoom.set_xlim(-zoom_w/2, zoom_w/2)
        self.ax_zoom.set_ylim(-r - zoom_w/2, -r + zoom_w/2)
        self.ax_zoom.set_title(f"Dettaglio Contatto (Zoom {zoom_w}x{zoom_w}mm)", fontsize=10, fontweight='bold')
        
        self.fig.tight_layout()
        
        # Identificazione Punti di Contatto (Proximity Detection)
        contacts = []
        if hasattr(self, 'poly_pinion') and hasattr(self, 'poly_rack'):
            p_pts = np.array(self.poly_pinion)
            r_pts = np.array(self.poly_rack)
            
            # Filtro spaziale per velocizzare: consideriamo solo la zona di mesh
            mask_p = (np.abs(p_pts[:,0]) < 2.5*m) & (np.abs(p_pts[:,1] + r) < 2.5*m)
            mask_r = (np.abs(r_pts[:,0]) < 2.5*m) & (np.abs(r_pts[:,1] + r) < 2.5*m)
            p_mesh = p_pts[mask_p]
            r_mesh = r_pts[mask_r]
            
            if len(p_mesh) > 0 and len(r_mesh) > 0:
                # Calcolo distanze reciproche per trovare sovrapposizioni
                # Usiamo una soglia stretta per i punti di contatto reali
                for pt in p_mesh:
                    dists = np.linalg.norm(r_mesh - pt, axis=1)
                    if np.min(dists) < 0.015 * m:
                        contacts.append(pt)
        
        if contacts:
            cx = [p[0] for p in contacts]
            cy = [p[1] for p in contacts]
            # Disegna i punti di contatto attivi nello zoom
            self.ax_zoom.plot(cx, cy, 'ro', markersize=5, label='Contatto', zorder=10)
            # Opzionale: anche nella vista globale
            self.ax.plot(cx, cy, 'r.', markersize=3, zorder=10)

        # Traccia il punto di pitch teorico (0, -r)
        for a in [self.ax, self.ax_zoom]:
            a.plot(0, -r, 'k+', markersize=10, alpha=0.5)

        self.canvas.draw()
        
    def draw_pinion(self, ax, m, z, alpha_sx, alpha_dx, x, delta_s, rf, ra, rot, rho_ap, rho_fp):
        r = m * z / 2.0
        sp = m * (np.pi / 2.0 + x * np.tan(alpha_sx) + x * np.tan(alpha_dx)) - delta_s
        if sp <= 0: return 
        
        def rotate_pts(x_arr, y_arr, ang):
            return x_arr * np.cos(ang) - y_arr * np.sin(ang), x_arr * np.sin(ang) + y_arr * np.cos(ang)
        
        rb_sx = r * np.cos(alpha_sx)
        t_max_sx = np.sqrt(ra**2 / rb_sx**2 - 1) if ra > rb_sx else 0
        t_sx = np.linspace(0, t_max_sx, 30)
        inv_x_sx = rb_sx * (np.cos(t_sx) + t_sx * np.sin(t_sx))
        inv_y_sx = -rb_sx * (np.sin(t_sx) - t_sx * np.cos(t_sx))
        theta_pitch_sx = (np.pi * m / 4.0 - delta_s / 2.0 + x * m * np.tan(alpha_sx)) / r
        offset_ang_sx = theta_pitch_sx + inv(alpha_sx)
        left_x, left_y = rotate_pts(inv_x_sx, inv_y_sx, offset_ang_sx)

        rb_dx = r * np.cos(alpha_dx)
        t_max_dx = np.sqrt(ra**2 / rb_dx**2 - 1) if ra > rb_dx else 0
        t_dx = np.linspace(0, t_max_dx, 30)
        inv_x_dx = rb_dx * (np.cos(t_dx) + t_dx * np.sin(t_dx))
        inv_y_dx = rb_dx * (np.sin(t_dx) - t_dx * np.cos(t_dx))
        theta_pitch_dx = (np.pi * m / 4.0 - delta_s / 2.0 + x * m * np.tan(alpha_dx)) / r
        offset_ang_dx = -theta_pitch_dx - inv(alpha_dx)
        right_x, right_y = rotate_pts(inv_x_dx, inv_y_dx, offset_ang_dx)

        pitch_angle = 2 * np.pi / z
        rf_draw = min(rf, rb_sx, rb_dx)

        segments = []
        for k in range(z):
            ang = k * pitch_angle + rot + np.pi/2
            lx, ly = rotate_pts(left_x, left_y, ang)
            rx, ry = rotate_pts(right_x, right_y, ang)
            
            rx_pts = list(zip(rx, ry))
            # Extend rx_pts down to rf_draw if needed
            ang_rx_base = np.arctan2(ry[0], rx[0])
            if np.linalg.norm(np.array(rx_pts[0])) > rf_draw + 1e-5:
                rx_pts.insert(0, (rf_draw * np.cos(ang_rx_base), rf_draw * np.sin(ang_rx_base)))
                
            lx_pts = list(zip(lx[::-1], ly[::-1]))
            # Extend lx_pts down to rf_draw if needed
            ang_lx_base = np.arctan2(ly[0], lx[0])
            if np.linalg.norm(np.array(lx_pts[-1])) > rf_draw + 1e-5:
                lx_pts.append((rf_draw * np.cos(ang_lx_base), rf_draw * np.sin(ang_lx_base)))
            
            ang_tip_r = np.arctan2(ry[-1], rx[-1])
            ang_tip_l = np.arctan2(ly[-1], lx[-1])
            if ang_tip_l < ang_tip_r: ang_tip_l += 2*np.pi
            tip_pts = [(ra * np.cos(a), ra * np.sin(a)) for a in np.linspace(ang_tip_r, ang_tip_l, 10)]
            
            ang_next = ((k + 1) % z) * pitch_angle + rot + np.pi/2
            rx_next, ry_next = rotate_pts(right_x, right_y, ang_next)
            ang1 = np.arctan2(ry_next[0], rx_next[0])
            if ang1 < ang_lx_base: ang1 += 2*np.pi
            root_pts = [(rf_draw * np.cos(a), rf_draw * np.sin(a)) for a in np.linspace(ang_lx_base, ang1, 15)]
            
            p1 = add_fillet_to_paths(rx_pts, tip_pts, rho_ap)
            p2 = add_fillet_to_paths(p1, lx_pts, rho_ap)
            segments.append((p2, root_pts))
            
        pinion_poly = []
        for k in range(z):
            tooth_poly, root_pts = segments[k]
            p3 = add_fillet_to_paths(tooth_poly, root_pts, rho_fp)
            if len(pinion_poly) == 0:
                pinion_poly = p3
            else:
                pinion_poly = add_fillet_to_paths(pinion_poly, p3, rho_fp)
                
        if len(pinion_poly) > 60:
            wrap_A = pinion_poly[-30:]
            wrap_B = pinion_poly[:30]
            wrap_fillet = add_fillet_to_paths(wrap_A, wrap_B, rho_fp)
            pinion_poly = pinion_poly[:-30] + wrap_fillet + pinion_poly[30:]
            
        if len(pinion_poly) > 0:
            pinion_poly.append(pinion_poly[0])
            all_x = [p[0] for p in pinion_poly]
            all_y = [p[1] for p in pinion_poly]
            ax.plot(all_x, all_y, '-', color='#0052cc', linewidth=1.5)
            ax.fill(all_x, all_y, color='#0052cc', alpha=0.2, label='Pignone in Metallo')
            if ax == self.ax:
                self.poly_pinion = pinion_poly

    def draw_rack(self, ax, m, z, alpha_sx, alpha_dx, H, ha_cr, c, delta_s, linear_disp, rho_ac, rho_fc):
        pitch = np.pi * m
        num_teeth = z + 4  
        startX = linear_disp % pitch - (num_teeth * pitch) / 2.0 + pitch / 2.0
        
        y_datum = -H
        y_add = y_datum + ha_cr
        y_ded = y_datum - (1.0 * m + c) 
        
        w_datum = pitch / 2.0 + delta_s
        if w_datum >= pitch: return 
        
        dx_add_L = ha_cr * np.tan(alpha_sx)
        dx_ded_L = abs(y_datum - y_ded) * np.tan(alpha_sx)
        dx_add_R = ha_cr * np.tan(alpha_dx)
        dx_ded_R = abs(y_datum - y_ded) * np.tan(alpha_dx)
        
        rack_poly = []
        for i in range(num_teeth):
            x_center = startX + i * pitch
            x_d_l = x_center - w_datum / 2.0
            x_d_r = x_center + w_datum / 2.0
            x_a_l = x_d_l + dx_add_L
            x_ded_l = x_d_l - dx_ded_L
            x_a_r = x_d_r - dx_add_R
            x_ded_r = x_d_r + dx_ded_R
            next_x_center = startX + (i+1) * pitch
            next_x_d_l = next_x_center - w_datum / 2.0
            next_x_ded_l = next_x_d_l - dx_ded_L
            
            left_flank = [(x_ded_l, y_ded), (x_a_l, y_add)]
            top_land = [(x_a_l, y_add), (x_a_r, y_add)]
            right_flank = [(x_a_r, y_add), (x_ded_r, y_ded)]
            bottom_land = [(x_ded_r, y_ded), (next_x_ded_l, y_ded)]
            
            p1 = add_fillet_to_paths(left_flank, top_land, rho_ac)
            p2 = add_fillet_to_paths(p1, right_flank, rho_ac)
            p3 = add_fillet_to_paths(p2, bottom_land, rho_fc)
            
            if len(rack_poly) == 0:
                rack_poly = p3
            else:
                rack_poly = add_fillet_to_paths(rack_poly, p3, rho_fc)
                
        if len(rack_poly) > 0:
            xs = [p[0] for p in rack_poly]
            ys = [p[1] for p in rack_poly]
            xs_poly = [xs[0]] + xs + [xs[-1], xs[0]]
            ys_poly = [y_ded - 1.5*m] + ys + [y_ded - 1.5*m, y_ded - 1.5*m]
            
            ax.plot(xs, ys, '-', color='#cc0052', linewidth=1.5)
            ax.fill(xs_poly, ys_poly, color='#cc0052', alpha=0.2, label='Cremagliera in Plastica')
            if ax == self.ax:
                self.poly_rack = list(zip(xs_poly, ys_poly))

    def export_dxf(self):
        if not hasattr(self, 'poly_pinion') or not hasattr(self, 'poly_rack'):
            return
            
        import tkinter.filedialog as fd
        filepath = fd.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF file", "*.dxf")])
        if not filepath: return
            
        with open(filepath, 'w') as f:
            f.write("0\nSECTION\n2\nENTITIES\n")
            def write_poly(poly, layer):
                if len(poly) < 2: return
                f.write("0\nPOLYLINE\n8\n%s\n66\n1\n" % layer)
                f.write("70\n1\n") 
                for pt in poly:
                    f.write("0\nVERTEX\n8\n%s\n" % layer)
                    f.write("10\n{:.4f}\n20\n{:.4f}\n30\n0.0\n".format(pt[0], pt[1]))
                f.write("0\nSEQEND\n8\n%s\n" % layer)
                
            write_poly(self.poly_pinion, "PIGNONE")
            write_poly(self.poly_rack, "CREMAGLIERA")
            f.write("0\nENDSEC\n0\nEOF\n")
            
        import tkinter.messagebox as mb
        mb.showinfo("Export DXF", f"File salvato correttamente in:\n{filepath}")

if __name__ == "__main__":
    app = RackPinionVisualizer()
    app.mainloop()
