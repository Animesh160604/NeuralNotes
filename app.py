"""Run the NeuralNotes desktop prototype with Python 3.10+."""
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from study_pack import ENGINE_NAME, generate, markdown, preview, source_lines

SAMPLE = """A stack is a last-in, first-out data structure.
A queue is a first-in, first-out data structure.
Push means adding an item to the top of a stack.
Pop means removing the top item from a stack.
Enqueue means adding an item to the back of a queue."""


class StudyApp:
    def __init__(self, root):
        self.root = root
        self.pack = None
        self.lines = {}
        self.view = tk.StringVar(value="Full pack")

        root.title("NeuralNotes | Study workspace")
        root.geometry("1180x760")
        root.minsize(980, 680)
        root.configure(bg="#eef2f7")

        self.colors = {
            "nav": "#132238", "nav_text": "#cbd8e7", "canvas": "#eef2f7",
            "card": "#ffffff", "border": "#dde5ef", "primary": "#4f46e5",
            "primary_dark": "#3730a3", "text": "#172033", "muted": "#65748b",
            "success": "#138a72", "soft": "#f7f9fc",
        }

        self.configure_styles()
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        self.build_sidebar()
        self.build_main()

    def configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Nav.TFrame", background=self.colors["nav"])
        style.configure("Canvas.TFrame", background=self.colors["canvas"])
        style.configure("Card.TFrame", background=self.colors["card"])
        style.configure("Nav.TButton", font=("Segoe UI", 10), foreground=self.colors["nav_text"],
                        background=self.colors["nav"], borderwidth=0, padding=(14, 10), anchor="w")
        style.map("Nav.TButton", background=[("active", "#22344e")])
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"),
                        foreground="#ffffff", background=self.colors["primary"],
                        borderwidth=0, padding=(14, 9))
        style.map("Primary.TButton", background=[
            ("active", self.colors["primary_dark"]), ("disabled", "#a5adbb")])
        style.configure("Secondary.TButton", font=("Segoe UI", 10),
                        foreground=self.colors["text"], background="#ffffff",
                        borderwidth=1, relief="solid", padding=(12, 8))

    def build_sidebar(self):
        sidebar = ttk.Frame(self.root, style="Nav.TFrame", width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = tk.Frame(sidebar, bg=self.colors["nav"], padx=20, pady=22)
        brand.pack(fill="x")
        tk.Label(brand, text="NN", font=("Segoe UI", 16, "bold"), bg=self.colors["primary"],
                 fg="#ffffff", width=3).pack(side="left", padx=(0, 10))
        tk.Label(brand, text="NeuralNotes", font=("Segoe UI", 15, "bold"),
                 bg=self.colors["nav"], fg="#ffffff").pack(side="left")

        tk.Label(sidebar, text="WORKSPACE", font=("Segoe UI", 8, "bold"),
                 bg=self.colors["nav"], fg="#8292a8").pack(anchor="w", padx=20, pady=(12, 6))

        nav = tk.Frame(sidebar, bg=self.colors["nav"])
        nav.pack(fill="x", padx=10)
        ttk.Button(nav, text="  Study workspace", style="Nav.TButton").pack(fill="x", pady=2)
        ttk.Button(nav, text="  Saved packs", style="Nav.TButton", command=self.export).pack(fill="x", pady=2)
        ttk.Button(nav, text="  Sources", style="Nav.TButton",
                   command=lambda: self.view.set("Sources")).pack(fill="x", pady=2)

        model = tk.Frame(sidebar, bg="#1b2b44", padx=14, pady=14)
        model.pack(side="bottom", fill="x", padx=12, pady=14)
        tk.Label(model, text="ENGINE", font=("Segoe UI", 8, "bold"),
                 bg="#1b2b44", fg="#8292a8").pack(anchor="w")
        tk.Label(model, text=ENGINE_NAME, font=("Segoe UI", 10, "bold"),
                 bg="#1b2b44", fg="#ffffff").pack(anchor="w", pady=(5, 2))
        tk.Label(model, text="Google Gemini API", font=("Segoe UI", 9),
                 bg="#1b2b44", fg="#90a4bc").pack(anchor="w")

    def build_main(self):
        main = ttk.Frame(self.root, style="Canvas.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        header = ttk.Frame(main, style="Canvas.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=26, pady=(22, 14))
        tk.Label(header, text="Study workspace", font=("Segoe UI", 21, "bold"),
                 bg=self.colors["canvas"], fg=self.colors["text"]).pack(side="left")
        self.status = tk.StringVar(value="Ready")
        tk.Label(header, textvariable=self.status, font=("Segoe UI", 9),
                 bg="#e6edf6", fg=self.colors["muted"], padx=12, pady=6).pack(side="right")

        metrics = ttk.Frame(main, style="Canvas.TFrame")
        metrics.grid(row=1, column=0, sticky="ew", padx=26, pady=(0, 14))
        metrics.columnconfigure((0, 1, 2, 3), weight=1, uniform="metric")
        self.metric_values = {}
        for index, (label, key) in enumerate((
            ("Words", "words"), ("Source lines", "lines"),
            ("Key terms", "terms"), ("Questions", "questions"))):
            card = tk.Frame(metrics, bg=self.colors["card"], highlightthickness=1,
                            highlightbackground=self.colors["border"], padx=14, pady=12)
            card.grid(row=0, column=index, sticky="ew", padx=(0, 10 if index < 3 else 0))
            tk.Label(card, text=label.upper(), font=("Segoe UI", 8, "bold"),
                     bg=self.colors["card"], fg=self.colors["muted"], anchor="w").pack(fill="x")
            value = tk.Label(card, text="0", font=("Segoe UI", 16, "bold"),
                             bg=self.colors["card"], fg=self.colors["text"], anchor="w")
            value.pack(fill="x", pady=(4, 0))
            self.metric_values[key] = value

        pipeline = ttk.Frame(main, style="Canvas.TFrame")
        pipeline.grid(row=2, column=0, sticky="ew", padx=26, pady=(0, 12))
        tk.Label(pipeline, text="PIPELINE", font=("Segoe UI", 8, "bold"),
                 bg=self.colors["canvas"], fg=self.colors["muted"]).pack(side="left", padx=(0, 12))
        self.pipeline_labels = {}
        for name in ("Evidence", "Draft", "Review"):
            label = tk.Label(pipeline, text=f"○  {name}", font=("Segoe UI", 9, "bold"),
                             bg="#e7edf5", fg=self.colors["muted"], padx=10, pady=5)
            label.pack(side="left", padx=(0, 7))
            self.pipeline_labels[name] = label

        workspace = ttk.Frame(main, style="Canvas.TFrame")
        workspace.grid(row=3, column=0, sticky="nsew", padx=26, pady=(0, 22))
        workspace.columnconfigure((0, 1), weight=1, uniform="panel")
        workspace.rowconfigure(0, weight=1)

        source_card = self.card(workspace, "1  Lecture notes")
        source_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.notes = self.editor(source_card)
        self.notes.bind("<<Modified>>", self.update_metrics)

        controls = tk.Frame(source_card, bg=self.colors["card"])
        controls.pack(fill="x", pady=(10, 0))
        tk.Button(controls, text="Load example", command=self.load_sample, font=("Segoe UI", 9),
                  bg="#ffffff", fg=self.colors["text"], relief="solid", bd=1, padx=10, pady=5).pack(side="left")
        tk.Button(controls, text="Open TXT", command=self.open_file, font=("Segoe UI", 9),
                  bg="#ffffff", fg=self.colors["text"], relief="solid", bd=1, padx=10, pady=5).pack(side="left", padx=6)
        self.mode = tk.StringVar(value="AI · v3 chain")
        ttk.Combobox(controls, state="readonly", textvariable=self.mode, width=17,
                     values=("AI · v3 chain", "Offline preview")).pack(side="left", padx=6)
        self.run_button = ttk.Button(controls, text="Generate pack", style="Primary.TButton", command=self.run)
        self.run_button.pack(side="right")

        output_card = self.card(workspace, "2  Generated study pack")
        output_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        toolbar = tk.Frame(output_card, bg=self.colors["card"])
        toolbar.pack(fill="x")
        for name in ("Full pack", "Summary", "Key terms", "Questions", "Sources"):
            tk.Radiobutton(toolbar, text=name, variable=self.view, value=name, command=self.render,
                           indicatoron=False, selectcolor="#e9edff", activebackground="#f0f2ff",
                           bg=self.colors["card"], fg=self.colors["muted"],
                           font=("Segoe UI", 8, "bold"), padx=7, pady=5, relief="flat",
                           borderwidth=0).pack(side="left")
        self.answers = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_card, text="Show answers", variable=self.answers,
                        command=self.render).pack(anchor="e", pady=(5, 0))
        self.output = self.editor(output_card)
        self.output.config(state="disabled")
        footer = tk.Frame(output_card, bg=self.colors["card"])
        footer.pack(fill="x", pady=(8, 0))
        self.export_button = ttk.Button(footer, text="Export Markdown", style="Secondary.TButton",
                                        command=self.export, state="disabled")
        self.export_button.pack(side="right")
        self.update_metrics()

    def card(self, parent, title):
        card = tk.Frame(parent, bg=self.colors["card"], highlightthickness=1,
                        highlightbackground=self.colors["border"], padx=14, pady=14)
        tk.Label(card, text=title, font=("Segoe UI", 12, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"], anchor="w").pack(fill="x", pady=(0, 10))
        return card

    def editor(self, panel):
        frame = tk.Frame(panel, bg=self.colors["soft"], highlightthickness=1,
                         highlightbackground=self.colors["border"])
        frame.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        widget = tk.Text(frame, wrap="word", font=("Segoe UI", 10), bg=self.colors["soft"],
                         fg="#26364e", relief="flat", padx=12, pady=10,
                         yscrollcommand=scroll.set, width=36, height=11,
                         insertbackground=self.colors["primary"])
        widget.pack(fill="both", expand=True)
        scroll.configure(command=widget.yview)
        return widget

    def replace_notes(self, value):
        self.notes.delete("1.0", "end")
        self.notes.insert("1.0", value)
        self.notes.edit_modified(False)
        self.update_metrics()

    def update_metrics(self, event=None):
        text = self.notes.get("1.0", "end-1c")
        self.metric_values["words"].config(text=str(len(text.split())))
        try:
            lines = source_lines(text)
        except ValueError:
            lines = {}
        self.metric_values["lines"].config(text=str(len(lines)))
        if self.pack:
            self.metric_values["terms"].config(text=str(len(self.pack.get("terms", []))))
            self.metric_values["questions"].config(text=str(len(self.pack.get("questions", []))))
        else:
            self.metric_values["terms"].config(text="0")
            self.metric_values["questions"].config(text="0")
        if event is not None:
            self.notes.edit_modified(False)

    def set_pipeline(self, active=None, complete=False):
        for name, label in self.pipeline_labels.items():
            if complete:
                label.config(text=f"●  {name}", bg="#dff3ed", fg=self.colors["success"])
            elif name == active:
                label.config(text=f"◉  {name}", bg="#e4e7ff", fg=self.colors["primary"])
            else:
                label.config(text=f"○  {name}", bg="#e7edf5", fg=self.colors["muted"])

    def load_sample(self):
        self.replace_notes(SAMPLE)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All files", "*.*")])
        if path:
            try:
                self.replace_notes(Path(path).read_text(encoding="utf-8-sig"))
                self.status.set(Path(path).name)
            except (OSError, UnicodeError) as error:
                self.status.set(str(error))

    def run(self):
        notes = self.notes.get("1.0", "end-1c")
        self.pack = None
        self.export_button.config(state="disabled")
        self.display("")
        self.update_metrics()
        try:
            self.lines = source_lines(notes)
        except ValueError as error:
            self.status.set(str(error))
            self.set_pipeline()
            return

        self.run_button.config(state="disabled")
        offline = self.mode.get() == "Offline preview"
        if offline:
            self.set_pipeline("Evidence")
            self.status.set("Generating offline preview…")
            self.compute(notes, True)
        else:
            self.set_pipeline("Evidence")
            self.status.set(f"Running extraction with {ENGINE_NAME}…")
            threading.Thread(target=self.compute, args=(notes, False), daemon=True).start()

    def compute(self, notes, offline):
        try:
            pack = preview(notes) if offline else generate(notes)
        except (ValueError, OSError, KeyError, TypeError) as error:
            self.root.after(0, self.finish, None, str(error))
        else:
            label = "Offline preview" if offline else f"AI study pack · {ENGINE_NAME}"
            self.root.after(0, self.finish, pack, f"{label} · {len(pack['questions'])} practice questions")

    def finish(self, pack, message):
        self.pack = pack
        self.status.set(message)
        self.run_button.config(state="normal")
        if pack:
            self.export_button.config(state="normal")
            self.set_pipeline(complete=True)
        else:
            self.set_pipeline()
        self.update_metrics()
        self.render()

    def display(self, text):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.config(state="disabled")

    def document(self):
        if not self.pack:
            return ""
        sections = []
        if self.view.get() in ("Full pack", "Summary"):
            sections.append("## Summary")
            sections.extend(f"- {row['text']} [{', '.join(row['refs'])}]"
                            for row in self.pack["summary"])
        if self.view.get() in ("Full pack", "Key terms"):
            sections.append("## Key terms")
            sections.extend(f"- **{row['term']}** — {row['definition']} [{', '.join(row['refs'])}]"
                            for row in self.pack["terms"])
        if self.view.get() in ("Full pack", "Questions"):
            sections.append("## Practice questions")
            for index, row in enumerate(self.pack["questions"], 1):
                sections.append(f"{index}. {row['question']} [{', '.join(row['refs'])}]")
                if self.answers.get():
                    sections.append(f"   Answer: {row['answer']}")
        if self.view.get() in ("Full pack", "Sources"):
            sections.append("## Source lines")
            sections.extend(f"- [{ref}] {line}" for ref, line in self.lines.items())
        if self.pack["warnings"]:
            sections.append("## Review notes")
            sections.extend(f"- {warning}" for warning in self.pack["warnings"])
        return "\n\n".join(sections) + "\n"

    def render(self):
        self.display(self.document())

    def export(self):
        if not self.pack:
            self.status.set("Generate a study pack before exporting.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if path:
            try:
                document = markdown(self.pack, self.answers.get()) + "\n## Source lines\n\n" + "\n".join(
                    f"- [{ref}] {line}" for ref, line in self.lines.items()) + "\n"
                Path(path).write_text(document, encoding="utf-8")
                self.status.set("Saved " + Path(path).name)
            except OSError as error:
                self.status.set(str(error))


if __name__ == "__main__":
    window = tk.Tk()
    StudyApp(window)
    window.mainloop()
