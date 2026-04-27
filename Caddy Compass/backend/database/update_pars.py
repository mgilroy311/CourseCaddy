import os
import sqlite3

def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "coursecaddy.db")
    return sqlite3.connect(db_path)

def update_hole_pars(course_name_keywords, pars):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, name FROM courses")
    courses = cursor.fetchall()

    matched_course_id = None
    matched_course_name = None

    for course_id, course_name in courses:
        name_lower = course_name.lower()
        if all(keyword in name_lower for keyword in course_name_keywords):
            matched_course_id = course_id
            matched_course_name = course_name
            break

    if matched_course_id is None:
        print(f"No course match found for keywords: {course_name_keywords}")
        connection.close()
        return

    for hole_number, par_value in enumerate(pars, start=1):
        cursor.execute("""
            UPDATE holes
            SET par = ?
            WHERE course_id = ? AND hole_number = ?
        """, (par_value, matched_course_id, hole_number))

    connection.commit()
    connection.close()
    print(f"Updated pars for {matched_course_name}")


# Fully confirmed hole-by-hole pars so far
update_hole_pars(["azalea", "sands"], [5,4,4,4,3,5,4,3,4,4,5,3,4,4,3,4,4,5])