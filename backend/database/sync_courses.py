import csv
import os
import sqlite3


def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "coursecaddy.db")
    return sqlite3.connect(db_path)


def get_first_value(row, possible_keys):
    for key in possible_keys:
        if key in row and str(row[key]).strip() != "":
            return str(row[key]).strip()
    return ""


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


def create_18_holes_for_course(cursor, course_id):
    for hole_number in range(1, 19):
        cursor.execute("""
            INSERT INTO holes (course_id, hole_number, par, image_path)
            VALUES (?, ?, ?, ?)
        """, (course_id, hole_number, 4, ""))


def delete_removed_courses(cursor, csv_course_names):
    cursor.execute("SELECT id, name FROM courses")
    database_courses = cursor.fetchall()

    deleted_count = 0

    for course_id, course_name in database_courses:
        if course_name.strip().lower() not in csv_course_names:
            cursor.execute("""
                DELETE FROM ratings
                WHERE hole_id IN (
                    SELECT id FROM holes WHERE course_id = ?
                )
            """, (course_id,))

            cursor.execute("""
                DELETE FROM hole_photos
                WHERE hole_id IN (
                    SELECT id FROM holes WHERE course_id = ?
                )
            """, (course_id,))

            cursor.execute("""
                DELETE FROM holes
                WHERE course_id = ?
            """, (course_id,))

            cursor.execute("""
                DELETE FROM courses
                WHERE id = ?
            """, (course_id,))

            deleted_count += 1

    return deleted_count


def sync_courses():
    connection = get_connection()
    cursor = connection.cursor()

    csv_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "assets",
            "south_carolina_golf_courses.csv"
        )
    )

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        connection.close()
        return

    added = 0
    updated = 0
    csv_course_names = set()

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            course_name = get_first_value(row, ["Course", "Name", "course", "name"])

            if course_name:
                csv_course_names.add(course_name.strip().lower())

    deleted = delete_removed_courses(cursor, csv_course_names)

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
                SELECT id
                FROM courses
                WHERE LOWER(name) = LOWER(?)
            """, (course_name,))

            existing_course = cursor.fetchone()

            if existing_course:
                course_id = existing_course[0]

                cursor.execute("""
                    UPDATE courses
                    SET location = ?,
                        zip = ?,
                        yardage = ?,
                        slope = ?,
                        image_path = ?
                    WHERE id = ?
                """, (
                    location,
                    zip_code,
                    yardage,
                    slope,
                    image_path,
                    course_id
                ))

                updated += 1

            else:
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

                course_id = cursor.lastrowid
                create_18_holes_for_course(cursor, course_id)
                added += 1

    connection.commit()
    connection.close()

    print("Sync complete.")
    print(f"Added {added} new courses.")
    print(f"Updated {updated} existing courses.")
    print(f"Deleted {deleted} courses removed from CSV.")


sync_courses()