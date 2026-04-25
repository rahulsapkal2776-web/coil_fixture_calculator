import math
import tkinter as tk
from tkinter import messagebox, ttk

root = tk.Tk()
root.title("LNP ENTERPRISES - Magnetiser Design Software")
root.geometry("1380x820")
root.configure(bg="#e9edf2")

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
        poles = get_float(job_entries, "No. of Poles")
        gauss = get_float(job_entries, "Required Gauss")

        voltage = get_float(machine_entries, "Max Voltage (V)")
        current_ka = get_float(machine_entries, "Max Current (kA)")
        cycle_time = get_float(machine_entries, "Cycle Time (sec)")
        single_cap_uf = get_float(machine_entries, "Single Capacitor Value (µF)", 4700)
        single_cap_voltage = get_float(machine_entries, "Single Capacitor Voltage (V)", voltage)

        if od <= 0 or poles <= 0 or voltage <= 0:
            messagebox.showwarning(
                "Input Missing", "Please enter Magnet OD, No. of Poles and Max Voltage."
            )
            return

        if single_cap_uf <= 0 or single_cap_voltage <= 0:
            messagebox.showwarning(
                "Input Missing",
                "Please enter valid single capacitor value (µF) and voltage (V).",
            )
            return

        # Basic estimated energy logic
        # This is first-stage practical estimation, later we will improve with material database.
        required_energy = gauss * poles * 0.65
        required_uf = (2 * required_energy / (voltage**2)) * 1_000_000

        # Capacitor bank sizing from chosen capacitor part
        series_per_string = math.ceil(voltage / single_cap_voltage)
        effective_string_uf = single_cap_uf / series_per_string
        parallel_strings = math.ceil(required_uf / effective_string_uf) if effective_string_uf > 0 else 0
        no_of_caps = series_per_string * parallel_strings

        # Coil suggestion
        if poles <= 4:
            turns = 6
        elif poles <= 12:
            turns = 4
        else:
            turns = 3

        peak_current_a = current_ka * 1000
        ampere_turns = peak_current_a * turns

        # Basic fixture geometry
        pole_pitch = (math.pi * od) / poles
        pole_width = pole_pitch * 0.55
        slot_width = pole_pitch * 0.25
        air_gap = 0.2
        fixture_od = od - (2 * air_gap)
        fixture_id = id_ + (2 * air_gap) if id_ > 0 else 0

        # Output fill
        set_value(coil_entries, "Recommended Turns", turns)
        set_value(coil_entries, "Wire / Strip Size", "As per current density")
        set_value(coil_entries, "Resistance (mΩ)", "To be calculated")
        set_value(coil_entries, "Inductance (µH)", "To be calculated")
        set_value(coil_entries, "Peak Current (kA)", current_ka)
        set_value(coil_entries, "Pulse Width (ms)", "To be tested")
        set_value(coil_entries, "Ampere Turns", round(ampere_turns))

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
header.pack(fill="x")

tk.Label(
    header,
    text="LNP ENTERPRISES  |  Magnetiser / Demagnetiser Coil & Fixture Design Software",
    bg="#003366",
    fg="white",
    font=("Segoe UI", 15, "bold"),
).pack(pady=12)

# ===================== MAIN FRAME =====================
main = tk.Frame(root, bg="#e9edf2")
main.pack(fill="both", expand=True, padx=10, pady=10)

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
    "Part Name",
    "Magnet Type",
    "Magnet OD (mm)",
    "Magnet ID (mm)",
    "Height / Width (mm)",
    "No. of Poles",
    "Required Gauss",
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
    "Max Current (kA)",
    "Cycle Time (sec)",
    "Available Space (mm)",
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

# ======================================================
# CENTER PANEL = AUTO CALCULATED RESULTS
# ======================================================
center = tk.Frame(main, bg="#e9edf2")
center.pack(side="left", fill="both", expand=True, padx=8)

coil = ttk.LabelFrame(center, text="3. Auto Coil Design Results", padding=12)
coil.pack(fill="x", pady=5)

coil_fields = [
    "Recommended Turns",
    "Wire / Strip Size",
    "Resistance (mΩ)",
    "Inductance (µH)",
    "Peak Current (kA)",
    "Pulse Width (ms)",
    "Ampere Turns",
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
# BOTTOM BUTTONS
# ======================================================
bottom = tk.Frame(root, bg="#e9edf2")
bottom.pack(fill="x", pady=8)

ttk.Button(bottom, text="Calculate Design", command=calculate_design).pack(side="left", padx=10)
ttk.Button(bottom, text="Generate Drawing", command=generate_drawing).pack(side="left", padx=10)
ttk.Button(bottom, text="Save Project", command=save_project).pack(side="left", padx=10)
ttk.Button(bottom, text="Export PDF Report", command=export_pdf).pack(side="left", padx=10)
ttk.Button(bottom, text="Exit", command=root.destroy).pack(side="right", padx=10)

root.mainloop()
