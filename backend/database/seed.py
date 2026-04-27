import csv
import os
import sqlite3


def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "coursecaddy.db")
    return sqlite3.connect(db_path)


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            zip TEXT,
            yardage INTEGER,
            slope INTEGER,
            image_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            hole_number INTEGER NOT NULL,
            par INTEGER NOT NULL,
            image_path TEXT,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hole_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hole_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            is_featured INTEGER DEFAULT 0,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hole_id) REFERENCES holes (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hole_id INTEGER NOT NULL,
            condition_score REAL NOT NULL,
            visual_score REAL NOT NULL,
            fun_score REAL NOT NULL,
            comments TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hole_id) REFERENCES holes (id)
        )
    """)

    connection.commit()
    connection.close()


def clean_integer(value):
    if value is None:
        return None

    cleaned_value = str(value).strip().replace(",", "")

    if cleaned_value == "":
        return None

    try:
        return int(float(cleaned_value))
    except ValueError:
        return None


def get_first_value(row, possible_keys):
    for key in possible_keys:
        if key in row and str(row[key]).strip() != "":
            return str(row[key]).strip()
    return ""


def import_courses_from_csv():
    connection = get_connection()
    cursor = connection.cursor()

    csv_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "assets",
        "south_carolina_golf_courses.csv"
    )
    csv_path = os.path.abspath(csv_path)

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        connection.close()
        return

    cursor.execute("DELETE FROM ratings")
    cursor.execute("DELETE FROM hole_photos")
    cursor.execute("DELETE FROM holes")
    cursor.execute("DELETE FROM courses")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            course_name = get_first_value(row, ["Course", "Name", "course", "name"])
            city = get_first_value(row, ["City", "city"])
            state = get_first_value(row, ["State", "state"])
            zip_code = get_first_value(row, ["ZIP", "Zip", "ZipCode", "zip", "zipcode"])
            yardage = clean_integer(get_first_value(row, ["Yardage", "Yardage_Back_Tees", "yardage"]))
            slope = clean_integer(get_first_value(row, ["Slope", "Slope_Back_Tees", "slope"]))
            image_path = get_first_value(row, ["Photo", "photo", "PHOTO", "Image", "image"])

            if not course_name:
                continue

            if city and state:
                location = f"{city}, {state}"
            elif city:
                location = city
            else:
                location = ""

            cursor.execute("""
                INSERT INTO courses (name, location, zip, yardage, slope, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                course_name,
                location,
                zip_code,
                yardage,
                slope,
                image_path
            ))

    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM courses")
    course_count = cursor.fetchone()[0]

    connection.close()
    print(f"Imported {course_count} courses successfully.")


def create_18_holes_for_every_course():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM courses")
    courses = cursor.fetchall()

    total_holes_inserted = 0

    for course in courses:
        course_id = course[0]

        holes_to_insert = []
        for hole_number in range(1, 19):
            holes_to_insert.append((course_id, hole_number, 4, ""))

        cursor.executemany("""
            INSERT INTO holes (course_id, hole_number, par, image_path)
            VALUES (?, ?, ?, ?)
        """, holes_to_insert)

        total_holes_inserted += 18

    connection.commit()
    connection.close()

    print(f"Inserted {total_holes_inserted} holes successfully.")


def assign_sample_hole_images():
    connection = get_connection()
    cursor = connection.cursor()

    image_rules = [
        ("aberdeen", 1, "Aberdeen-1.png"),
        ("tpc myrtle", 9, "tpc-myrtle-9.jpg"),
        ("caledonia", 18, "caledonia.jpg"),
        ("kiawah", 10, "Kiawah-10.jpg"),
        ("legends", 17, "legends-17.jpg"),
        ("moorland", 11, "moorland-11.webp"),
        ("parkland", 15, "parkland-15.jpg"),
        ("prestwick", 13, "prestwick-13.jpg"),
        ("heathland", 1, "heathland.jpeg")
    ]

    inserted_count = 0

    cursor.execute("SELECT id, name FROM courses")
    courses = cursor.fetchall()

    for course_id, course_name in courses:
        name_lower = course_name.lower()

        for keyword, hole_number, image_file in image_rules:
            if keyword in name_lower:
                cursor.execute("""
                    SELECT id
                    FROM holes
                    WHERE course_id = ? AND hole_number = ?
                """, (course_id, hole_number))

                hole_row = cursor.fetchone()

                if hole_row:
                    hole_id = hole_row[0]

                    cursor.execute("""
                        INSERT INTO hole_photos (hole_id, image_path, is_featured)
                        VALUES (?, ?, 1)
                    """, (hole_id, image_file))

                    inserted_count += 1

    connection.commit()
    connection.close()

    print(f"Inserted {inserted_count} hole photos.")


def seed_facebook_ratings():
    connection = get_connection()
    cursor = connection.cursor()

    def find_hole_id(course_keywords, hole_number):
        cursor.execute("""
            SELECT
                h.id,
                c.name,
                h.hole_number
            FROM holes h
            JOIN courses c ON h.course_id = c.id
        """)
        rows = cursor.fetchall()

        for row in rows:
            hole_id = row[0]
            course_name = row[1].lower()
            db_hole_number = row[2]

            if db_hole_number != hole_number:
                continue

            if all(keyword in course_name for keyword in course_keywords):
                return hole_id, row[1]

        return None, None

    def add_rating(course_keywords, hole_number, comment):
        hole_id, matched_course = find_hole_id(course_keywords, hole_number)

        if hole_id:
            cursor.execute("""
                INSERT INTO ratings (hole_id, condition_score, visual_score, fun_score, comments)
                VALUES (?, ?, ?, ?, ?)
            """, (
                hole_id,
                4.0,
                4.0,
                5.0,
                comment
            ))
            return True, matched_course

        return False, None

    facebook_mentions = [
        (["caledonia"], 18, "Facebook mention: Finishing hole at Caledonia"),
        (["tpc", "myrtle"], 17, "Facebook mention: For some crazy reason I love #17 at TPC"),
        (["norman"], 10, "Facebook mention: #10 Norman"),
        (["dye"], 6, "Facebook mention: #6 Dye Club"),
        (["wachesaw"], 17, "Facebook mention: #17 Wachesaw Plantation"),
        (["wizard"], 17, "Facebook mention: I love #17 @ Wizard"),
        (["wizard"], 18, "Facebook mention: 18 is better at Wizard"),
        (["river", "club"], 18, "Facebook mention: #18 at River Club"),
        (["rivers", "edge"], 9, "Facebook mention: The ninth hole at Rivers Edge"),
        (["grande", "dunes"], 14, "Facebook mention: Favorite MB hole: Grande Dunes #14"),
        (["prestwick"], 17, "Facebook mention: #17 at Prestwick"),
        (["arrowhead"], 2, "Facebook mention: Arrowhead, Cypress Hole #2"),
        (["glen", "dornoch"], 16, "Facebook mention: #16 at Glen Dornoch"),
        (["barefoot", "norman"], 10, "Facebook mention: Barefoot Norman #10"),
        (["grande", "dunes"], 14, "Facebook mention: Grande Dunes #14"),
        (["wachesaw"], 18, "Facebook mention: Wachesaw Plantation #18"),
        (["barefoot", "norman"], 10, "Facebook mention: #10 Norman Course at Barefoot Resort & Golf"),
        (["fazio"], 5, "Facebook mention: Fazio Course Hole #5"),
        (["legends", "kings", "north"], 6, "Facebook mention: Kings North #6"),
        (["leopards"], 18, "Facebook mention: Leopards Chase #18"),
        (["prestwick"], 9, "Facebook mention: I love #9 at Prestwick"),
        (["prestwick"], 17, "Facebook mention: Prestwick #17"),
        (["eagles", "nest"], 18, "Facebook mention: Finishing hole at Eagles Nest"),
        (["rivers", "edge"], 17, "Facebook mention: #17 at Rivers Edge"),
        (["tidewater"], 4, "Facebook mention: #4 Tidewater"),
        (["glen", "dornoch"], 8, "Facebook mention: Glen Dornoch #8"),
        (["brunswick", "dogwood"], 9, "Facebook mention: Dogwood #9 at Brunswick"),
        (["heathland"], 1, "Facebook mention: Heathland #1"),
        (["moorland"], 11, "Facebook mention: Moorland #11"),
        (["parkland"], 15, "Facebook mention: Parkland #15")
    ]

    inserted = 0
    skipped = []

    for course_keywords, hole_number, comment in facebook_mentions:
        was_inserted, matched_course = add_rating(course_keywords, hole_number, comment)

        if was_inserted:
            inserted += 1
        else:
            skipped.append(comment)

    connection.commit()
    connection.close()

    print(f"Inserted {inserted} Facebook ratings.")
    print(f"Skipped {len(skipped)} Facebook mentions.")

    if skipped:
        print("Skipped mentions:")
        for item in skipped:
            print(f" - {item}")


create_tables()
import_courses_from_csv()
create_18_holes_for_every_course()
assign_sample_hole_images()
seed_facebook_ratings()