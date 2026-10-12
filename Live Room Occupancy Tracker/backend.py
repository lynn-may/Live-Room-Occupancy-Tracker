import sqlite3
from datetime import datetime

DB_NAME = "ustp_rooms.db"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# USTP campus buildings
BUILDINGS = [
    "Bldg. 1: Arts and Culture Building",
    "Bldg. 3: College of Medicine",
    "Bldg. 5: Old Engineering Building",
    "Bldg. 9: ICT Building",
    "Bldg. 18: Culinary Building",
    "Bldg. 19: NSTP Building",
    "Bldg. 23: Learning Resource Center",
    "Bldg. 24: Girl's Trade Building",
    "Bldg. 28: Old Science Building",
    "Bldg. 35: Old Education Building",
    "Bldg. 36: Old Student Center",
    "Bldg. 41: Science Complex",
    "Bldg. 42: Engineering Complex I (Right Wing)",
    "Bldg. 43: Engineering Complex II (Left Wing)",
    "Bldg. 44: Student Center & Education Complex",
    "Bldg. 45: Mechanical Laboratory Shop",
    "Bldg. 47: Technology Building",
    "Bldg. 50: Faculty Learning Resource Center",
    "Bldg. 51: Dormitory",
    "Bldg. 52: FAB LAB Building",
]

FLOOR_LABELS = ["1st Floor", "2nd Floor", "3rd Floor", "4th Floor"]
ROOMS_PER_FLOOR = 9  # 101-109, 201-209, 301-309, 401-409

# Capacity of a normal classroom
DEFAULT_CAPACITY = 50

# Buildings that have a different room capacity
BUILDING_CAPACITY = {
    "Bldg. 9: ICT Building": 45,
    "Bldg. 47: Technology Building": 45,
    "Bldg. 45: Mechanical Laboratory Shop": 30,
    "Bldg. 23: Learning Resource Center": 10,
}

# Big venues (building, room name, capacity)
SPECIAL_VENUES = [
    ("Bldg. 44: Student Center & Education Complex", "Performing Arts Theater (PAT)", 300),
    ("Bldg. 1: Arts and Culture Building", "Auditorium", 500),
    ("Bldg. 16: Gymnasium / DRER Memorial Hall", "Gymnasium", 3000),
]


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_time_now():
    return datetime.now().strftime(TIME_FORMAT)

def get_building_number(building_name):
    first_part = building_name.split(":")[0]
    number = first_part.replace("Bldg. ", "")
    return int(number)

def sort_rooms(room):
    return (get_building_number(room["building"]), room["room_name"])

# makes rooms 101-109, 201-209, 301-309, 401-409 for every building
def generate_rooms():
    all_rooms = []
    for building in BUILDINGS:
        capacity = BUILDING_CAPACITY.get(building, DEFAULT_CAPACITY)
        for floor in range(1, len(FLOOR_LABELS) + 1):
            for number in range(1, ROOMS_PER_FLOOR + 1):
                room_name = "Room " + str(floor * 100 + number)
                all_rooms.append((building, room_name, capacity))
    for venue in SPECIAL_VENUES:
        all_rooms.append(venue)
    return all_rooms

# Creates the tables and puts the buildings and rooms in the database
def init_db():
    conn = connect_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            building  TEXT NOT NULL,
            room_name TEXT NOT NULL,
            capacity  INTEGER NOT NULL DEFAULT 50,
            UNIQUE (building, room_name)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS occupancy_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id     INTEGER NOT NULL,
            occupied_by TEXT NOT NULL,
            purpose     TEXT,
            start_time  TEXT NOT NULL,
            end_time    TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE
        )
        """
    )

    all_rooms = generate_rooms()
    for room in all_rooms:
        building = room[0]
        room_name = room[1]
        capacity = room[2]
        conn.execute(
            "INSERT OR IGNORE INTO rooms (building, room_name, capacity) "
            "VALUES (?, ?, ?)",
            (building, room_name, capacity),
        )
        conn.execute(
            "UPDATE rooms SET capacity = ? WHERE building = ? AND room_name = ?",
            (capacity, building, room_name),
        )
    conn.commit()
    conn.close()

# Rooms
def get_buildings():
    conn = connect_db()
    rows = conn.execute("SELECT DISTINCT building FROM rooms").fetchall()
    conn.close()

    building_list = []
    for row in rows:
        building_list.append(row["building"])
    building_list.sort(key=get_building_number)
    return building_list


# Gets all rooms and their status (Occupied or Vacant)
def get_rooms_with_status(building=None, search="", floor=None):
    sql = """
        SELECT r.id, r.building, r.room_name, r.capacity,
               l.occupied_by, l.purpose, l.start_time AS since
        FROM rooms r
        LEFT JOIN occupancy_log l
               ON l.room_id = r.id AND l.end_time IS NULL
        WHERE 1 = 1
    """
    values = []
    if building and building != "All Buildings":
        sql += " AND r.building = ?"
        values.append(building)
    if floor in FLOOR_LABELS:
        floor_number = FLOOR_LABELS.index(floor) + 1
        sql += " AND r.room_name LIKE ?"
        values.append("Room " + str(floor_number) + "%")
    if search:
        sql += " AND (r.room_name LIKE ? OR r.building LIKE ?)"
        values.append("%" + search + "%")
        values.append("%" + search + "%")

    conn = connect_db()
    rows = conn.execute(sql, values).fetchall()
    conn.close()

    room_list = []
    for row in rows:
        room = dict(row)
        room["status"] = "Occupied" if room["since"] else "Vacant"
        room_list.append(room)
    room_list.sort(key=sort_rooms)
    return room_list


# Occupancy
def occupy_room(room_id, occupied_by, purpose=""):
    occupied_by = occupied_by.strip()
    if occupied_by == "":
        return False, "Please enter who is using the room."

    conn = connect_db()
    open_session = conn.execute(
        "SELECT id FROM occupancy_log WHERE room_id = ? AND end_time IS NULL",
        (room_id,),
    ).fetchone()
    if open_session:
        conn.close()
        return False, "This room is already occupied."

    conn.execute(
        "INSERT INTO occupancy_log (room_id, occupied_by, purpose, start_time) "
        "VALUES (?, ?, ?, ?)",
        (room_id, occupied_by, purpose.strip(), get_time_now()),
    )
    conn.commit()
    conn.close()
    return True, "Room marked as occupied."

def vacate_room(room_id):
    conn = connect_db()
    cursor = conn.execute(
        "UPDATE occupancy_log SET end_time = ? "
        "WHERE room_id = ? AND end_time IS NULL",
        (get_time_now(), room_id),
    )
    conn.commit()
    changed = cursor.rowcount
    conn.close()

    if changed == 0:
        return False, "This room is already vacant."
    return True, "Room marked as vacant."


# Summary
def get_summary():
    conn = connect_db()
    total = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    occupied = conn.execute(
        "SELECT COUNT(DISTINCT room_id) FROM occupancy_log WHERE end_time IS NULL"
    ).fetchone()[0]
    conn.close()
    return total, occupied, total - occupied

# Gives a time like "1h 25m" between two timestamps
def format_duration(start_text, end_text=None):
    start = datetime.strptime(start_text, TIME_FORMAT)
    if end_text:
        end = datetime.strptime(end_text, TIME_FORMAT)
    else:
        end = datetime.now()

    total_minutes = int((end - start).total_seconds() // 60)
    if total_minutes < 0:
        total_minutes = 0
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        return str(hours) + "h " + str(minutes) + "m"
    return str(minutes) + "m"

# Past and current sessions, newest first
def get_history(room_id=None, limit=200):
    sql = """
        SELECT l.id, r.building, r.room_name, l.occupied_by, l.purpose,
               l.start_time, l.end_time
        FROM occupancy_log l
        JOIN rooms r ON r.id = l.room_id
    """
    values = []
    if room_id:
        sql += " WHERE l.room_id = ?"
        values.append(room_id)
    sql += " ORDER BY l.start_time DESC LIMIT ?"
    values.append(limit)

    conn = connect_db()
    rows = conn.execute(sql, values).fetchall()
    conn.close()

    history_list = []
    for row in rows:
        record = dict(row)
        record["duration"] = format_duration(record["start_time"], record["end_time"])
        history_list.append(record)
    return history_list