import math
import tkinter as tk
from tkinter import messagebox, ttk

root = tk.Tk()
root.title("LNP ENTERPRISES - Magnetiser Design Software")
root.geometry("1380x820")
root.minsize(1100, 700)
root.configure(bg="#e9edf2")
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# ===================== STYLE =====================
style = ttk.Style()
style.theme_use("clam")

style.configure("TLabelframe", background="white", borderwidth=1, relief="solid")
style.configure(
    "TLabelframe.Label",
    font=("Segoe UI", 11, "bold"),
    foreground="#003366",
    background="white",
)
style.configure("TLabel", background="white", font=("Segoe UI", 10))
style.configure("TEntry", padding=4)
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)

# ===================== DATA STORAGE =====================
job_entries = {}
machine_entries = {}
coil_entries = {}
cap_entries = {}
fixture_entries = {}

def set_value(entry_dict, key, value):
    entry_dict[key].delete(0, tk.END)
    entry_dict[key].insert(0, str(value))


def get_float(entry_dict, key, default=0):
    try:
        return float(entry_dict[key].get())
    except Exception:
        return default


def calculate_design():
    try:
        od = get_float(job_entries, "Magnet OD (mm)")
        id_ = get_float(job_entries, "Magnet ID (mm)")
        height_mm = get_float(job_entries, "Height / Width (mm)", 20.0)
        poles = get_float(job_entries, "No. of Poles")
        gauss = get_float(job_entries, "Required Gauss")
        turns_per_pole = get_float(job_entries, "Turns per Pole", 10)
        pole_face_width_mm = get_float(job_entries, "Pole Face Width (mm)", 10)
        pole_face_depth_mm = get_float(job_entries, "Pole Face Depth (mm)", 10)
        magnetic_path_length_mm = get_float(job_entries, "Magnetic Path Length (mm)", 100)
        safety_factor = get_float(job_entries, "Safety Factor", 1.3)

        voltage = get_float(machine_entries, "Max Voltage (V)")
        cycle_time = get_float(machine_entries, "Cycle Time (sec)")
        single_cap_uf = get_float(machine_entries, "Single Capacitor Value (µF)", 4700)
        single_cap_voltage = get_float(machine_entries, "Single Capacitor Voltage (V)", voltage)
        cooling_type = machine_entries["Cooling Type"].get().strip().lower()

        if od <= 0 or poles <= 0 or voltage <= 0 or turns_per_pole <= 0:
            messagebox.showwarning(
                "Input Missing", "Please enter Magnet OD, No. of Poles, Turns per Pole and Max Voltage."
            )
            return

        if single_cap_uf <= 0 or single_cap_voltage <= 0:
            messagebox.showwarning(
                "Input Missing",
                "Please enter valid single capacitor value (µF) and voltage (V).",
            )
            return
        if cycle_time <= 0 or magnetic_path_length_mm <= 0 or pole_face_width_mm <= 0 or height_mm <= 0:
            messagebox.showwarning(
                "Input Missing",
                "Please enter valid Cycle Time, Pole Width, Height, and Magnetic Path Length.",
            )
            return

        # -------- Magnetic-design-first approach --------
        h_required = 200000  # A/m for ferrite
        magnetic_path_m = magnetic_path_length_mm / 1000
        mmf = h_required * magnetic_path_m
        at_required_per_pole = mmf * safety_factor
        current_a = at_required_per_pole / turns_per_pole
        current_a = max(5000, min(30000, current_a))  # clamp 5kA..30kA
        # Distributed winding: per-pole turns, total ampere-turns across poles
        ampere_turns_per_pole = current_a * turns_per_pole
        ampere_turns_total = ampere_turns_per_pole * poles

        b_tesla = gauss / 10000
        pole_area_m2 = (pole_face_width_mm * height_mm) * 1e-6
        flux_per_pole_wb = b_tesla * pole_area_m2
        flux_per_pole_gauss = (flux_per_pole_wb / pole_area_m2) * 10000 if pole_area_m2 > 0 else 0
        steel_utilization_pct = (b_tesla / 1.7) * 100 if 1.7 > 0 else 0

        if b_tesla > 1.7:
            messagebox.showerror("Steel Saturation", "Increase pole area")
            return

        current_density = 10000 if "water" in cooling_type else 5000
        wire_area_mm2 = current_a / current_density

        # Basic estimated energy logic (kept for capacitor design)
        required_energy = gauss * poles * 0.65
        required_uf = (2 * required_energy / (voltage**2)) * 1_000_000

        # Capacitor bank sizing from chosen capacitor part
        series_per_string = math.ceil(voltage / single_cap_voltage)
        effective_string_uf = single_cap_uf / series_per_string
        parallel_strings = math.ceil(required_uf / effective_string_uf) if effective_string_uf > 0 else 0
        no_of_caps = series_per_string * parallel_strings

        area_m2 = wire_area_mm2 * 1e-6
        resistivity_cu = 1.724e-8  # ohm*m
        density_cu = 8960  # kg/m³
        cp_cu = 385  # J/kgK

        # Coil DC resistance estimate
        mean_diameter_mm = ((od + id_) / 2) if id_ > 0 else (od * 0.7)
        mean_turn_length_m = math.pi * mean_diameter_mm / 1000
        total_conductor_length_m = mean_turn_length_m * turns_per_pole
        resistance_ohm = (resistivity_cu * total_conductor_length_m / area_m2) if area_m2 > 0 else 0
        resistance_mohm = resistance_ohm * 1000

        # Coil inductance estimate (single-layer equivalent, first-stage)
        mu0 = 4 * math.pi * 1e-7
        effective_length_m = max(height_mm / 1000, 0.005)
        magnetic_area_m2 = (math.pi / 4) * max((od**2) - (id_**2), od**2 * 0.25) * 1e-6
        inductance_h = mu0 * (turns_per_pole**2) * magnetic_area_m2 / effective_length_m
        inductance_uh = inductance_h * 1e6

        # Actual pulse current and pulse width from RLC discharge
        capacitance_f = required_uf * 1e-6
        alpha = resistance_ohm / (2 * inductance_h) if inductance_h > 0 else 0
        natural_omega_sq = (1 / (inductance_h * capacitance_f)) if inductance_h > 0 and capacitance_f > 0 else 0
        damped_omega_sq = natural_omega_sq - (alpha**2)

        if damped_omega_sq > 0:
            omega_d = math.sqrt(damped_omega_sq)
            t_peak = math.atan(omega_d / alpha) / omega_d if alpha > 0 else (math.pi / (2 * omega_d))
            i_peak_calc_a = (voltage / (inductance_h * omega_d)) * math.exp(-alpha * t_peak) * math.sin(
                omega_d * t_peak
            )
            pulse_width_s = math.pi / omega_d  # half-cycle discharge pulse width
        else:
            # Overdamped fallback
            tau = inductance_h / resistance_ohm if resistance_ohm > 0 else 0
            t_peak = tau
            i_peak_calc_a = voltage / resistance_ohm if resistance_ohm > 0 else 0
            pulse_width_s = 5 * tau if tau > 0 else 0.003

        peak_current_a = min(i_peak_calc_a, current_a)
        pulse_width_ms = pulse_width_s * 1000
        ampere_turns = peak_current_a * turns_per_pole

        shots_per_min = 60 / cycle_time
        duty_fraction = ((pulse_width_ms / 1000) * shots_per_min) / 60
        duty_reference = 0.02  # 2% pulse-duty baseline
        thermal_index = duty_fraction
        duty_cycle_correction = math.sqrt(max(thermal_index / duty_reference, 1.0))

        # Copper temperature-rise estimate from I²R heat in copper volume using actual peak current
        pulse_current_density = peak_current_a / wire_area_mm2 if wire_area_mm2 > 0 else 0
        j_a_m2 = peak_current_a / area_m2 if area_m2 > 0 else 0
        power_density_w_m3 = (j_a_m2**2) * resistivity_cu
        energy_per_min_j_m3 = power_density_w_m3 * pulse_width_s * shots_per_min
        copper_temp_rise_c = energy_per_min_j_m3 / (density_cu * cp_cu) if area_m2 > 0 else 0

        # Basic fixture geometry
        pole_pitch = (math.pi * od) / poles
        pole_width = pole_pitch * 0.55
        slot_width = pole_pitch * 0.25
        air_gap = 0.2
        fixture_od = od - (2 * air_gap)
        fixture_id = id_ + (2 * air_gap) if id_ > 0 else 0

        # Output fill
        set_value(coil_entries, "Current (kA)", round(peak_current_a / 1000, 3))
        set_value(coil_entries, "Ampere Turns", round(ampere_turns))
        set_value(coil_entries, "Flux per Pole (Gauss)", round(flux_per_pole_gauss, 2))
        set_value(coil_entries, "Steel Utilization (%)", round(steel_utilization_pct, 1))
        set_value(coil_entries, "Recommended Wire Area (mm²)", round(wire_area_mm2, 3))
        set_value(
            coil_entries,
            "Recommended Wire Size",
            f"{round(wire_area_mm2, 2)} mm² ({'Water' if 'water' in cooling_type else 'Air'} cooled)",
        )
        set_value(coil_entries, "Resistance (mΩ)", round(resistance_mohm, 4))
        set_value(coil_entries, "Inductance (µH)", round(inductance_uh, 2))
        set_value(coil_entries, "Pulse Width (ms)", round(pulse_width_ms, 3))
        set_value(coil_entries, "Pulse Current Density (A/mm²)", round(pulse_current_density, 1))
        set_value(coil_entries, "Duty Cycle Correction", round(duty_cycle_correction, 2))
        set_value(coil_entries, "Copper Temperature Rise (°C/min)", round(copper_temp_rise_c, 2))

        set_value(cap_entries, "Required Energy (J)", round(required_energy, 2))
        set_value(cap_entries, "Suggested Voltage (V)", round(voltage, 2))
        set_value(cap_entries, "Required µF", round(required_uf, 2))
        set_value(cap_entries, "Series per String", series_per_string)
        set_value(cap_entries, "Parallel Strings", parallel_strings)
        set_value(cap_entries, "No. of Capacitors", no_of_caps)
        set_value(cap_entries, "Recharge Time (sec)", cycle_time)

        set_value(fixture_entries, "Pole Pitch (mm)", round(pole_pitch, 2))
        set_value(fixture_entries, "Pole Width (mm)", round(pole_width, 2))
        set_value(fixture_entries, "Slot Width (mm)", round(slot_width, 2))
        set_value(fixture_entries, "Air Gap (mm)", air_gap)
        set_value(fixture_entries, "Fixture OD (mm)", round(fixture_od, 2))
        set_value(fixture_entries, "Fixture ID (mm)", round(fixture_id, 2))

        draw_fixture_preview(poles)

    except Exception as e:
        messagebox.showerror("Error", str(e))


def draw_fixture_preview(poles):
    canvas.delete("all")
    canvas.create_text(160, 15, text="Fixture Top View", font=("Segoe UI", 10, "bold"))

    cx, cy = 160, 140
    outer_r = 95
    inner_r = 45

    canvas.create_oval(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r, width=2)
    canvas.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, width=2)

    if poles > 0:
        for p in range(int(poles)):
            angle = 2 * math.pi * p / poles
            x1 = cx + inner_r * math.cos(angle)
            y1 = cy + inner_r * math.sin(angle)
            x2 = cx + outer_r * math.cos(angle)
            y2 = cy + outer_r * math.sin(angle)
            canvas.create_line(x1, y1, x2, y2)


def generate_drawing():
    messagebox.showinfo("Generate Drawing", "Drawing generation will be added in next step.")


def save_project():
    messagebox.showinfo("Save Project", "Project save function will be added in next step.")


def export_pdf():
    messagebox.showinfo("Export PDF", "PDF report export will be added in next step.")


# ===================== HEADER =====================
header = tk.Frame(root, bg="#003366", height=55)
header.grid(row=0, column=0, sticky="ew")

tk.Label(
    header,
    text="LNP ENTERPRISES  |  Magnetiser / Demagnetiser Coil & Fixture Design Software",
    bg="#003366",
    fg="white",
    font=("Segoe UI", 15, "bold"),
).pack(pady=12)

# ===================== SCROLLABLE CONTENT =====================
content_container = tk.Frame(root, bg="#e9edf2")
content_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
content_container.grid_rowconfigure(0, weight=1)
content_container.grid_columnconfigure(0, weight=1)

content_canvas = tk.Canvas(content_container, bg="#e9edf2", highlightthickness=0)
content_canvas.grid(row=0, column=0, sticky="nsew")

vscroll = ttk.Scrollbar(content_container, orient="vertical", command=content_canvas.yview)
vscroll.grid(row=0, column=1, sticky="ns")
content_canvas.configure(yscrollcommand=vscroll.set)

main = tk.Frame(content_canvas, bg="#e9edf2")
main_window = content_canvas.create_window((0, 0), window=main, anchor="nw")


def _on_main_configure(event):
    content_canvas.configure(scrollregion=content_canvas.bbox("all"))


def _on_canvas_configure(event):
    content_canvas.itemconfig(main_window, width=event.width)


main.bind("<Configure>", _on_main_configure)
content_canvas.bind("<Configure>", _on_canvas_configure)

# ======================================================
# LEFT PANEL = USER INPUTS
# ======================================================
left = tk.Frame(main, bg="#e9edf2")
left.pack(side="left", fill="y", padx=(0, 8))

job = ttk.LabelFrame(left, text="1. Job & Magnet Input", padding=12)
job.pack(fill="x", pady=5)

ttk.Label(job, text="Application Type").grid(row=0, column=0, sticky="w", pady=4, padx=5)

application_type = ttk.Combobox(
    job,
    values=["Magnetiser", "Pulse Demagnetiser", "AC Conveyor Demagnetiser"],
    width=25,
    state="readonly",
)
application_type.grid(row=0, column=1, pady=4, padx=5)
application_type.current(0)

job_fields = [
    "Customer Name",
    "Magnet Type",
    "Magnet OD (mm)",
    "Magnet ID (mm)",
    "Height / Width (mm)",
    "No. of Poles",
    "Required Gauss",
    "Turns per Pole",
    "Pole Face Width (mm)",
    "Pole Face Depth (mm)",
    "Magnetic Path Length (mm)",
    "Steel Type",
    "Safety Factor",
]

for i, f in enumerate(job_fields):
    ttk.Label(job, text=f).grid(row=i + 1, column=0, sticky="w", pady=4, padx=5)
    ent = ttk.Entry(job, width=28)
    ent.grid(row=i + 1, column=1, pady=4, padx=5)
    job_entries[f] = ent

machine = ttk.LabelFrame(left, text="2. Machine Limits + Capacitor Input", padding=12)
machine.pack(fill="x", pady=5)

machine_fields = [
    "Max Voltage (V)",
    "Cycle Time (sec)",
    "Cooling Type",
    "Single Capacitor Value (µF)",
    "Single Capacitor Voltage (V)",
]

for i, f in enumerate(machine_fields):
    ttk.Label(machine, text=f).grid(row=i, column=0, sticky="w", pady=4, padx=5)
    ent = ttk.Entry(machine, width=28)
    ent.grid(row=i, column=1, pady=4, padx=5)
    machine_entries[f] = ent

set_value(machine_entries, "Single Capacitor Value (µF)", 4700)
set_value(machine_entries, "Cooling Type", "Air Cooled")
set_value(job_entries, "Magnet Type", "Ferrite")
set_value(job_entries, "Turns per Pole", 10)
set_value(job_entries, "Steel Type", "MS")
set_value(job_entries, "Safety Factor", 1.3)

# ======================================================
# CENTER PANEL = AUTO CALCULATED RESULTS
# ======================================================
center = tk.Frame(main, bg="#e9edf2")
center.pack(side="left", fill="both", expand=True, padx=8)

coil = ttk.LabelFrame(center, text="3. Auto Coil Design Results", padding=12)
coil.pack(fill="x", pady=5)

coil_fields = [
    "Current (kA)",
    "Ampere Turns",
    "Flux per Pole (Gauss)",
    "Steel Utilization (%)",
    "Recommended Wire Area (mm²)",
    "Recommended Wire Size",
    "Resistance (mΩ)",
    "Inductance (µH)",
    "Pulse Width (ms)",
    "Pulse Current Density (A/mm²)",
    "Duty Cycle Correction",
    "Copper Temperature Rise (°C/min)",
]

for i, f in enumerate(coil_fields):
    ttk.Label(coil, text=f).grid(row=i, column=0, sticky="w", pady=4, padx=5)
    ent = ttk.Entry(coil, width=25)
    ent.grid(row=i, column=1, pady=4, padx=5)
    coil_entries[f] = ent

cap = ttk.LabelFrame(center, text="4. Capacitor Bank Design", padding=12)
cap.pack(fill="x", pady=5)

cap_fields = [
    "Required Energy (J)",
    "Suggested Voltage (V)",
    "Required µF",
    "Series per String",
    "Parallel Strings",
    "No. of Capacitors",
    "Recharge Time (sec)",
]

for i, f in enumerate(cap_fields):
    ttk.Label(cap, text=f).grid(row=i, column=0, sticky="w", pady=4, padx=5)
    ent = ttk.Entry(cap, width=25)
    ent.grid(row=i, column=1, pady=4, padx=5)
    cap_entries[f] = ent

# ======================================================
# RIGHT PANEL = FIXTURE + DRAWING
# ======================================================
right = tk.Frame(main, bg="#e9edf2")
right.pack(side="right", fill="y", padx=(8, 0))

fixture = ttk.LabelFrame(right, text="5. Fixture Design Output", padding=12)
fixture.pack(fill="x", pady=5)

fixture_fields = [
    "Pole Pitch (mm)",
    "Pole Width (mm)",
    "Slot Width (mm)",
    "Air Gap (mm)",
    "Fixture OD (mm)",
    "Fixture ID (mm)",
]

for i, f in enumerate(fixture_fields):
    ttk.Label(fixture, text=f).grid(row=i, column=0, sticky="w", pady=4, padx=5)
    ent = ttk.Entry(fixture, width=22)
    ent.grid(row=i, column=1, pady=4, padx=5)
    fixture_entries[f] = ent

draw = ttk.LabelFrame(right, text="6. Design Preview", padding=10)
draw.pack(fill="both", expand=True, pady=5)

canvas = tk.Canvas(draw, width=320, height=260, bg="white")
canvas.pack()

canvas.create_oval(50, 40, 270, 240, width=2)
canvas.create_oval(95, 85, 225, 195, width=2)
canvas.create_text(160, 15, text="Fixture Top View")

# ======================================================
# BOTTOM BUTTONS (always visible)
# ======================================================
bottom = tk.Frame(root, bg="#e9edf2")
bottom.grid(row=2, column=0, sticky="ew", pady=8)

ttk.Button(bottom, text="Calculate Design", command=calculate_design).pack(side="left", padx=10)
ttk.Button(bottom, text="Generate Drawing", command=generate_drawing).pack(side="left", padx=10)
ttk.Button(bottom, text="Save Project", command=save_project).pack(side="left", padx=10)
ttk.Button(bottom, text="Export PDF Report", command=export_pdf).pack(side="left", padx=10)
ttk.Button(bottom, text="Exit", command=root.destroy).pack(side="right", padx=10)

root.mainloop()
