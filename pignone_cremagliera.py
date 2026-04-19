import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

def inv(alpha):
    return np.tan(alpha) - alpha

class RackPinionVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tool di Analisi e Ottimizzazione Pignone-Cremagliera")
        self.geometry("1400x900")
        
        self.create_widgets()
        self.update_plot()
        
    def create_widgets(self):
        # Frame Principale Controlli
        ctrl_frame = ttk.LabelFrame(self, text="Parametri di Progetto")
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Variabili di stato
        self.vars = {
            'm': tk.DoubleVar(value=1.0),
            'z': tk.IntVar(value=8),
            'alpha': tk.DoubleVar(value=20.0),
            'x': tk.DoubleVar(value=-0.08),
            'ha_cr_coeff': tk.DoubleVar(value=0.39),
            'c_coeff': tk.DoubleVar(value=0.25),
            'delta_s': tk.DoubleVar(value=0.0),
            'rot_deg': tk.DoubleVar(value=0.0)
        }
        
        sliders = [
            ('Modulo (m) [mm]', 'm', 0.5, 5.0, 0.1),
            ('Numero Denti Pignone (z)', 'z', 4, 40, 1),
            ('Angolo Pressione α (°)', 'alpha', 10.0, 35.0, 0.5),
            ('Spostamento Profilo (x)', 'x', -1.5, 1.5, 0.01),
            ('Alto Testa Cremagliera Stub (ha_cr/m)', 'ha_cr_coeff', 0.1, 1.5, 0.01),
            ('Gioco di fondo (c/m)', 'c_coeff', 0.1, 0.5, 0.01),
            ('Variazione Spessore Cordale (Δs) [mm]', 'delta_s', -1.0, 1.0, 0.01),
            ('Rotazione Pignone (°)', 'rot_deg', 0, 360, 1)
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
            
        # Pulsanti di Analisi e Azioni
        btn_frame = ttk.Frame(ctrl_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=15)
        ttk.Button(btn_frame, text="Carica Setup 1 (Standard)", command=self.preset_standard).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Carica Setup 2 (Ottimizzato Plastica)", command=self.preset_optimized).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Avvia/Ferma Animazione", command=self.toggle_animation).pack(side=tk.LEFT, padx=3)
        self.is_animating = False
            
        # Frame Risultati
        res_frame = ttk.LabelFrame(ctrl_frame, text="Analisi Cinematica e Geometrica")
        res_frame.grid(row=row+1, column=0, columnspan=3, sticky='ew', pady=10, padx=5)
        
        self.res_labels = {}
        res_items = [
            'Interasse di montaggio (H)', 
            'Ricoprimento Totale (ε_α)', 
            'Lunghezza Tratto Accesso (ga)', 
            'Lunghezza Tratto Recesso (gf)', 
            'Rapporto asimmetria (gf/ga)',
            'Spostamento lineare per giro (L)', 
            'Diametro Esterno Pignone (da)', 
            'Diametro Base Pignone (db)',
            'Spessore Pignone Pitch (sp)',
            'Spessore Crem. Datum (scr)'
        ]
        
        for i, item in enumerate(res_items):
            ttk.Label(res_frame, text=item + ":", font=('Arial', 9, 'bold')).grid(row=i, column=0, sticky='w', padx=5, pady=3)
            self.res_labels[item] = ttk.Label(res_frame, text="0.0")
            self.res_labels[item].grid(row=i, column=1, sticky='e', padx=5, pady=3)
            
        # Area Grafica
        plot_frame = tk.Frame(self)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(9, 9))
        self.fig.patch.set_facecolor('#fafafa')
        self.ax.set_facecolor('#ffffff')
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def preset_standard(self):
        self.vars['m'].set(1.0)
        self.vars['z'].set(10)
        self.vars['alpha'].set(20.0)
        self.vars['x'].set(0.5)
        self.vars['ha_cr_coeff'].set(1.0)
        self.vars['c_coeff'].set(0.25)
        self.vars['delta_s'].set(0.0)
        self.update_plot()

    def preset_optimized(self):
        self.vars['m'].set(1.0)
        self.vars['z'].set(8)
        self.vars['alpha'].set(20.0)
        self.vars['x'].set(-0.08)
        self.vars['ha_cr_coeff'].set(0.39)
        self.vars['c_coeff'].set(0.25)
        self.vars['delta_s'].set(0.15)
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
            alpha_deg = self.vars['alpha'].get()
            alpha = np.radians(alpha_deg)
            x = self.vars['x'].get()
            ha_cr = self.vars['ha_cr_coeff'].get() * m
            c = self.vars['c_coeff'].get() * m
            delta_s = self.vars['delta_s'].get()
            rot = np.radians(self.vars['rot_deg'].get())
        except tk.TclError:
            return  # invalid input if empty
            
        r = m * z / 2.0
        rb = r * np.cos(alpha)
        hap = (1.0 + x) * m
        ra = r + hap
        da = 2 * ra
        hfp = ha_cr + c - x * m
        rf = r - hfp
        
        H = r + x * m
        
        # Formule di ingranamento pignone-cremagliera
        ga = ha_cr / np.sin(alpha) if alpha != 0 else 0
        
        if ra > rb:
            gf = np.sqrt(ra**2 - rb**2) - r * np.sin(alpha)
        else:
            gf = 0
            
        pb = np.pi * m * np.cos(alpha)
        eps_alpha = (ga + gf) / pb if pb != 0 else 0
        
        L = np.pi * m * z
        
        # Spessori
        sp = m * (np.pi / 2.0 + 2 * x * np.tan(alpha)) - delta_s
        scr = m * np.pi / 2.0 + delta_s
        
        # Rendering Testo Risultati
        self.res_labels['Interasse di montaggio (H)'].config(text=f"{H:.3f} mm")
        self.res_labels['Ricoprimento Totale (ε_α)'].config(text=f"{eps_alpha:.3f}")
        
        # Allerta colorata se il ricoprimento scende sotto 1
        color_eps = 'red' if eps_alpha < 1.0 else 'forestgreen'
        self.res_labels['Ricoprimento Totale (ε_α)'].config(foreground=color_eps)
        
        self.res_labels['Lunghezza Tratto Accesso (ga)'].config(text=f"{ga:.3f} mm")
        self.res_labels['Lunghezza Tratto Recesso (gf)'].config(text=f"{gf:.3f} mm")
        self.res_labels['Rapporto asimmetria (gf/ga)'].config(text=f"{gf/ga if ga!=0 else 0:.3f}")
        self.res_labels['Spostamento lineare per giro (L)'].config(text=f"{L:.3f} mm")
        self.res_labels['Diametro Esterno Pignone (da)'].config(text=f"{da:.3f} mm")
        self.res_labels['Diametro Base Pignone (db)'].config(text=f"{2*rb:.3f} mm")
        self.res_labels['Spessore Pignone Pitch (sp)'].config(text=f"{sp:.3f} mm")
        self.res_labels['Spessore Crem. Datum (scr)'].config(text=f"{scr:.3f} mm")
        
        # Redraw
        self.ax.clear()
        
        # Retta d'azione
        la_len = 1.5 * r
        la_x = [-la_len * np.cos(alpha), la_len * np.cos(alpha)]
        la_y = [-la_len * np.sin(alpha) - r, la_len * np.sin(alpha) - r]
        self.ax.plot(la_x, la_y, '-', color='orange', alpha=0.5, label='Retta d\'Azione')
        
        # Circonferenze primitive e di riferimento
        theta = np.linspace(0, 2*np.pi, 200)
        self.ax.plot(r * np.cos(theta), r * np.sin(theta), 'g--', alpha=0.6, label='Circonferenza Primitiva')
        self.ax.plot(ra * np.cos(theta), ra * np.sin(theta), 'r--', alpha=0.4, label='Circonferenza Esterna')
        self.ax.plot(rb * np.cos(theta), rb * np.sin(theta), 'b--', alpha=0.4, label='Circonferenza Base')
        
        # Disegno delle geometrie
        self.draw_pinion(m, z, alpha, x, delta_s, rf, rb, ra, rot)
        linear_disp = r * rot
        self.draw_rack(m, z, alpha, H, ha_cr, c, delta_s, linear_disp)
        
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle=':', alpha=0.6)
        
        # Viewport Constraints
        limit_x = max(ra + 2*m, np.pi*m*2)
        limit_y_top = ra + m
        limit_y_bot = -H - 2.5*m
        self.ax.set_xlim(-limit_x, limit_x)
        self.ax.set_ylim(limit_y_bot, limit_y_top)
        
        self.ax.legend(loc='upper right', fontsize='small', framealpha=0.9)
        self.canvas.draw()
        
    def draw_pinion(self, m, z, alpha, x, delta_s, rf, rb, ra, rot):
        r = m * z / 2.0
        # Spessore inclusa Variazione Cordale
        sp = m * (np.pi / 2.0 + 2 * x * np.tan(alpha)) - delta_s
        if sp <= 0: return # Configurazione non fisicamente realizzabile
        
        theta_s = sp / (2*r)
        theta_inv = inv(alpha)
        
        t_max = np.sqrt(ra**2 / rb**2 - 1) if ra > rb else 0
        t = np.linspace(0, t_max, 40)
        
        inv_x = rb * (np.cos(t) + t * np.sin(t))
        inv_y = rb * (np.sin(t) - t * np.cos(t))
        
        def rotate_pts(x_arr, y_arr, ang):
            return x_arr * np.cos(ang) - y_arr * np.sin(ang), x_arr * np.sin(ang) + y_arr * np.cos(ang)
        
        # Rotazione alla posizione del mezzo dente e flip
        right_x, right_y = rotate_pts(inv_x, inv_y, -(theta_inv + theta_s))
        left_x, left_y = rotate_pts(inv_x, -inv_y, (theta_inv + theta_s))
        
        pitch_angle = 2 * np.pi / z
        all_x, all_y = [], []
        
        for k in range(z):
            ang = k * pitch_angle + rot + np.pi/2
            lx, ly = rotate_pts(left_x, left_y, ang)
            rx, ry = rotate_pts(right_x, right_y, ang)
            
            ang_next = ((k + 1) % z) * pitch_angle + rot + np.pi/2
            lx_next, ly_next = rotate_pts(left_x, left_y, ang_next)
            
            ang0_r = np.arctan2(ry[0], rx[0]) if len(ry) > 0 else 0
            ang1_l = np.arctan2(ly_next[0], lx_next[0]) if len(ly_next) > 0 else 0
            
            # Fianco Sinistro (Da base verso la punta)
            all_x.extend(lx)
            all_y.extend(ly)
            
            # Fianco Destro (Dalla punta verso la base)
            all_x.extend(rx[::-1])
            all_y.extend(ry[::-1])
            
            if rf < rb:
                all_x.append(rf * np.cos(ang0_r))
                all_y.append(rf * np.sin(ang0_r))
                
                if ang1_l < ang0_r:
                    ang1_l += 2*np.pi
                arc_angs = np.linspace(ang0_r, ang1_l, 15)
                all_x.extend(rf * np.cos(arc_angs))
                all_y.extend(rf * np.sin(arc_angs))
                
        # Chiusura poligonale e face fill
        if len(all_x) > 0:
            all_x.append(all_x[0])
            all_y.append(all_y[0])
            
        self.ax.plot(all_x, all_y, '-', color='#0052cc', linewidth=1.5)
        self.ax.fill(all_x, all_y, color='#0052cc', alpha=0.2, label='Pignone in Metallo')
        
        # Referenza rotazione
        self.ax.plot([0, r*np.cos(rot+np.pi/2)], [0, r*np.sin(rot+np.pi/2)], 'b-.', alpha=0.5)

    def draw_rack(self, m, z, alpha, H, ha_cr, c, delta_s, linear_disp):
        pitch = np.pi * m
        num_teeth = z + 4  # Numero fittizio visivo per coprire lo schermo
        
        # Allineamento sincronizzabile col rack
        startX = linear_disp % pitch - (num_teeth * pitch) / 2.0 + pitch / 2.0
        
        y_datum = -H
        y_add = y_datum + ha_cr
        y_ded = y_datum - (1.0 * m + c) # Limite dedendum imposto utensile tagliente 
        
        xs, ys = [], []
        w_datum = pitch / 2.0 + delta_s
        
        if w_datum >= pitch: return # Imbroglio geometrico
        
        for i in range(num_teeth):
            x_center = startX + i * pitch
            
            # Punti sul Datum Line
            x_d_l = x_center - w_datum / 2.0
            x_d_r = x_center + w_datum / 2.0
            
            # Punti Addendum / Top 
            dx_add = ha_cr * np.tan(alpha)
            x_a_l = x_d_l + dx_add
            x_a_r = x_d_r - dx_add
            
            # Punti Dedendum / Bottom Root
            dx_ded = abs(y_datum - y_ded) * np.tan(alpha)
            x_ded_l = x_d_l - dx_ded
            x_ded_r = x_d_r + dx_ded
            
            xs.extend([x_ded_l, x_a_l, x_a_r, x_ded_r])
            ys.extend([y_ded, y_add, y_add, y_ded])
            
        if len(xs) > 0:
            xs_poly = [xs[0]] + xs + [xs[-1], xs[0]]
            ys_poly = [y_ded - 1.5*m] + ys + [y_ded - 1.5*m, y_ded - 1.5*m]
            
            self.ax.plot(xs, ys, '-', color='#cc0052', linewidth=1.5)
            self.ax.fill(xs_poly, ys_poly, color='#cc0052', alpha=0.2, label='Cremagliera in Plastica')
        
        self.ax.axhline(-H, color='g', linestyle='-.', alpha=0.8, label='Datum / Riferimento')
        self.ax.axhline(-m*z/2.0, color='r', linestyle=':', alpha=0.8, label='Pitch / Rotolamento')

if __name__ == "__main__":
    app = RackPinionVisualizer()
    app.mainloop()
