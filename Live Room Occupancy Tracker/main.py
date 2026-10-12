import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

import backend

REFRESH_MS = 5000 # UI updates automatically every 5 seconds

# UI colors
USTP_BLUE = "#1a3a6b"
USTP_GOLD = "#f2b705"
OCCUPIED_BG = "#f8c9c9"
VACANT_BG = "#c9f0d3"


# Dashboard of the program
class RoomTrackerDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("USTP Live Room Occupancy Tracker")
        self.geometry("1150x640")
        self.minsize(950, 500)

        # Components and database initialization
        backend.init_db()
        self.build_header()
        self.build_summary()
        self.build_controls()
        self.build_table()
        self.build_buttons()

        # Start live loops
        self.tick_clock()
        self.auto_refresh()

    def build_header(self):
        header_frame = tk.Frame(self, bg=USTP_BLUE)
        header_frame.pack(fill="x")
        title_label = tk.Label(
            header_frame,
            text="USTP Live Room Occupancy Tracker",
            font=("Segoe UI", 18, "bold"),
            bg=USTP_BLUE,
            fg="white",
        )
        title_label.pack(side="left", padx=15, pady=10)
        self.clock_label = tk.Label(
            header_frame, font=("Segoe UI", 11), bg=USTP_BLUE, fg=USTP_GOLD
        )
        self.clock_label.pack(side="right", padx=15)

    def build_summary(self):
        summary_frame = tk.Frame(self)
        summary_frame.pack(fill="x", padx=15, pady=(10, 0))
        self.total_var = tk.StringVar()
        self.occ_var = tk.StringVar()
        self.vac_var = tk.StringVar()

        total_label = tk.Label(
            summary_frame,
            textvariable=self.total_var,
            font=("Segoe UI", 12, "bold"),
            bg="#e8ecf4",
            width=20,
            pady=8,
        )
        total_label.pack(side="left", padx=(0, 10))

        occupied_label = tk.Label(
            summary_frame,
            textvariable=self.occ_var,
            font=("Segoe UI", 12, "bold"),
            bg=OCCUPIED_BG,
            width=20,
            pady=8,
        )
        occupied_label.pack(side="left", padx=(0, 10))

        vacant_label = tk.Label(
            summary_frame,
            textvariable=self.vac_var,
            font=("Segoe UI", 12, "bold"),
            bg=VACANT_BG,
            width=20,
            pady=8,
        )
        vacant_label.pack(side="left", padx=(0, 10))

    def build_controls(self):
        controls_frame = tk.Frame(self)
        controls_frame.pack(fill="x", padx=15, pady=10)

        # Building filters
        tk.Label(controls_frame, text="Building:").pack(side="left")
        self.building_var = tk.StringVar(value="All Buildings")
        self.building_box = ttk.Combobox(
            controls_frame, textvariable=self.building_var, state="readonly", width=40
        )
        self.building_box.pack(side="left", padx=(5, 15))
        self.building_box.bind("<<ComboboxSelected>>", self.refresh)

        # Floor filters
        tk.Label(controls_frame, text="Floor:").pack(side="left")
        self.floor_var = tk.StringVar(value="All Floors")
        floor_box = ttk.Combobox(
            controls_frame,
            textvariable=self.floor_var,
            values=["All Floors"] + backend.FLOOR_LABELS,
            state="readonly",
            width=10,
        )
        floor_box.pack(side="left", padx=(5, 15))
        floor_box.bind("<<ComboboxSelected>>", self.refresh)

        # Search box
        tk.Label(controls_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=22)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<KeyRelease>", self.refresh)

        # Status filter
        self.status_var = tk.StringVar(value="All")
        tk.Label(controls_frame, text="Status:").pack(side="left", padx=(15, 0))
        status_box = ttk.Combobox(
            controls_frame,
            textvariable=self.status_var,
            values=["All", "Vacant", "Occupied"],
            state="readonly",
            width=10,
        )
        status_box.pack(side="left", padx=5)
        status_box.bind("<<ComboboxSelected>>", self.refresh)

    def build_table(self):
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=15)

        columns = ("building", "room", "capacity", "status", "by", "since", "duration")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        headings = {
            "building": ("Building", 280),
            "room": ("Room", 130),
            "capacity": ("Capacity", 70),
            "status": ("Status", 90),
            "by": ("Occupied By", 150),
            "since": ("Since", 140),
            "duration": ("Duration", 80),
        }
        for key in headings:
            self.tree.heading(key, text=headings[key][0])
            self.tree.column(key, width=headings[key][1], anchor="center")

        # Configure row colors based on status
        self.tree.tag_configure("Occupied", background=OCCUPIED_BG)
        self.tree.tag_configure("Vacant", background=VACANT_BG)

        # Add a vertical scrollbar to the treeview
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Connect the scrollbar to the treeview
        self.tree.configure(yscrollcommand=scrollbar.set)

    def build_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.pack(fill="x", padx=15, pady=10)

        occupied_button = tk.Button(
            button_frame,
            text="Mark Occupied",
            command=self.mark_occupied,
            padx=12,
            pady=5,
            bg=USTP_BLUE,
            fg="white",
            font=("Segoe UI", 10, "bold"),
        )
        occupied_button.pack(side="left", padx=(0, 8))

        vacant_button = tk.Button(
            button_frame,
            text="Mark Vacant",
            command=self.mark_vacant,
            padx=12,
            pady=5,
            bg=USTP_GOLD,
            fg="black",
            font=("Segoe UI", 10, "bold"),
        )
        vacant_button.pack(side="left", padx=(0, 8))

        history_button = tk.Button(
            button_frame,
            text="Room History",
            command=self.show_history,
            padx=12,
            pady=5,
            font=("Segoe UI", 10),
        )
        history_button.pack(side="left", padx=(0, 8))

        refresh_button = tk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh,
            padx=12,
            pady=5,
            font=("Segoe UI", 10),
        )
        refresh_button.pack(side="left", padx=(0, 8))

        self.last_update = tk.Label(button_frame, text="", fg="gray")
        self.last_update.pack(side="right")

    def selected_room(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select a room", "Please select a room first.")
            return None
        values = self.tree.item(selection[0], "values")
        return int(selection[0]), values

    def tick_clock(self):
        time_text = datetime.now().strftime("%A, %B %d, %Y  %I:%M:%S %p")
        self.clock_label.config(text=time_text)
        self.after(1000, self.tick_clock)

    def auto_refresh(self):
        self.refresh()
        self.after(REFRESH_MS, self.auto_refresh)

    # The event argument is ignored. Only included to accept Tkinter .bind() calls
    def refresh(self, event=None):
        selected = self.tree.selection()

        buildings = ["All Buildings"] + backend.get_buildings()
        self.building_box["values"] = buildings
        if self.building_var.get() not in buildings:
            self.building_var.set("All Buildings")

        rooms = backend.get_rooms_with_status(
            self.building_var.get(),
            self.search_var.get().strip(),
            self.floor_var.get(),
        )
        status_filter = self.status_var.get()

        # Clear the treeview and insert new data
        self.tree.delete(*self.tree.get_children())
        for room in rooms:
            if status_filter != "All" and room["status"] != status_filter:
                continue
            # Compute duration if occupied, else show "-"
            if room["since"]:
                duration = backend.format_duration(room["since"])
                since = room["since"]
                occupied_by = room["occupied_by"]
            else:
                duration = "-"
                since = "-"
                occupied_by = "-"
            row_values = []
            row_values.append(room["building"])
            row_values.append(room["room_name"])
            row_values.append(room["capacity"])
            row_values.append(room["status"])
            row_values.append(occupied_by)
            row_values.append(since)
            row_values.append(duration)
            self.tree.insert(
                "",
                "end",
                iid=str(room["id"]),
                values=row_values,
                tags=(room["status"],),
            )

        # Keep selected room selected after refreshing
        for iid in selected:
            if self.tree.exists(iid):
                self.tree.selection_add(iid)

        # Update summary 
        total, occupied, vacant = backend.get_summary()
        self.total_var.set("Total Rooms: " + str(total))
        self.occ_var.set("Occupied: " + str(occupied))
        self.vac_var.set("Vacant: " + str(vacant))
        self.last_update.config(
            text="Updated " + datetime.now().strftime("%I:%M:%S %p")
        )

    def mark_occupied(self):
        picked = self.selected_room()
        if not picked:
            return
        room_id = picked[0]
        values = picked[1]
        if values[3] == "Occupied":
            messagebox.showwarning("Already occupied", "This room is already occupied.")
            return

        # Ask who is using the room and the purpose
        who = simpledialog.askstring(
            "Mark Occupied",
            "Who is using " + values[1] + "?\n(Instructor / Class / Organization)",
            parent=self,
        )
        if who is None:     # User pressed cancel
            return
        purpose = simpledialog.askstring(
            "Purpose", "Purpose (optional):", parent=self
        )
        if purpose is None:
            purpose = ""

        # Update the database and refresh the table
        success, message = backend.occupy_room(room_id, who, purpose)
        if not success:
            messagebox.showerror("Error", message)
        self.refresh()

    def mark_vacant(self):
        picked = self.selected_room()
        if not picked:
            return
        room_id = picked[0]
        values = picked[1]
        if values[3] == "Vacant":
            messagebox.showinfo("Already vacant", "This room is already vacant.")
            return
        if messagebox.askyesno("Confirm", "Mark " + values[1] + " as vacant?"):
            success, message = backend.vacate_room(room_id)
            if not success:
                messagebox.showerror("Error", message)
            self.refresh()

    def show_history(self):
        picked = self.selected_room()
        if not picked:
            return
        room_id = picked[0]
        values = picked[1]

        # Create a new window to show the history of the selected room
        history_dashboard_ = tk.Toplevel(self)
        history_dashboard_.title("History - " + values[0] + " / " + values[1])
        history_dashboard_.geometry("760x380")

        columns = ("by", "purpose", "start", "end", "duration")
        history_tree = ttk.Treeview(history_dashboard_, columns=columns, show="headings")

        history_tree.heading("by", text="Occupied By")
        history_tree.column("by", width=150, anchor="center")
        history_tree.heading("purpose", text="Purpose")
        history_tree.column("purpose", width=160, anchor="center")
        history_tree.heading("start", text="Start")
        history_tree.column("start", width=140, anchor="center")
        history_tree.heading("end", text="End")
        history_tree.column("end", width=140, anchor="center")
        history_tree.heading("duration", text="Duration")
        history_tree.column("duration", width=80, anchor="center")

        # Fetch the history records from the backend
        for record in backend.get_history(room_id):
            purpose = record["purpose"] if record["purpose"] else "-"
            end_time = record["end_time"] if record["end_time"] else "In use"
            who = record["occupied_by"]
            start_text = record["start_time"]
            duration_text = record["duration"]
            history_values = (who, purpose, start_text, end_time, duration_text)
            history_tree.insert("", "end", values=history_values)
        history_tree.pack(fill="both", expand=True, padx=10, pady=10)


# Start the UI
dashboard = RoomTrackerDashboard()
dashboard.mainloop()