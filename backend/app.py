import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import csv

app = Flask(__name__)
CORS(app)


def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "database", "coursecaddy.db")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection

@app.route("/api/submit_missing_hole", methods=["POST"])
def submit_missing_hole():
    data = request.json

    file_path = os.path.join(
        os.path.dirname(__file__),
        "database",
        "pending_hole_submissions.csv"
    )

    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "course_name",
                "location",
                "hole_number",
                "par",
                "yardage",
                "condition",
                "visual",
                "fun",
                "notes"
            ])

        writer.writerow([
            data.get("course_name"),
            data.get("location"),
            data.get("hole_number"),
            data.get("par"),
            data.get("yardage"),
            data.get("condition"),
            data.get("visual"),
            data.get("fun"),
            data.get("notes")
        ])

    return jsonify({"message": "Submission saved"}), 200



@app.route("/")
def home():
    return send_from_directory("..", "index.html")

@app.route("/holes.html")
def holes_page():
    return send_from_directory("..", "holes.html")

@app.route("/review.html")
def review_page():
    return send_from_directory("..", "review.html")

@app.route("/courses.html")
def courses_page():
    return send_from_directory("..", "courses.html")

@app.route("/css/<path:filename>")
def css_files(filename):
    return send_from_directory("../css", filename)

@app.route("/js/<path:filename>")
def js_files(filename):
    return send_from_directory("../js", filename)

@app.route("/assets/<path:filename>")
def asset_files(filename):
    return send_from_directory("../assets", filename)


@app.route("/api/courses")
def get_courses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, location, zip, yardage, slope, image_path
        FROM courses
        ORDER BY name
    """)
    rows = cursor.fetchall()
    connection.close()

    courses = []
    for row in rows:
        courses.append({
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "zip": row["zip"],
            "yardage": row["yardage"],
            "slope": row["slope"],
            "image": row["image_path"]
        })

    return jsonify(courses)


@app.route("/api/course-holes/<int:course_id>")
def get_course_holes(course_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            h.id,
            h.hole_number,
            h.par
        FROM holes h
        WHERE h.course_id = ?
        ORDER BY h.hole_number
    """, (course_id,))
    rows = cursor.fetchall()
    connection.close()

    holes = []
    for row in rows:
        holes.append({
            "id": row["id"],
            "hole_number": row["hole_number"],
            "par": row["par"]
        })

    return jsonify(holes)


@app.route("/api/holes")
def get_holes():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            c.name AS course_name,
            c.location,
            h.id AS hole_id,
            h.hole_number,
            h.par,
            hp.image_path,
            COALESCE(AVG(r.condition_score), 0) AS condition_avg,
            COALESCE(AVG(r.visual_score), 0) AS visual_avg,
            COALESCE(AVG(r.fun_score), 0) AS fun_avg
        FROM hole_photos hp
        JOIN holes h ON hp.hole_id = h.id
        JOIN courses c ON h.course_id = c.id
        LEFT JOIN ratings r ON r.hole_id = h.id
        WHERE hp.is_featured = 1
        GROUP BY c.name, c.location, h.id, h.hole_number, h.par, hp.image_path
        ORDER BY c.name, h.hole_number
    """)
    rows = cursor.fetchall()
    connection.close()

    holes = []
    for row in rows:
        holes.append({
            "hole_id": row["hole_id"],
            "Course": row["course_name"],
            "Hole": row["hole_number"],
            "par": row["par"],
            "photo": row["image_path"],
            "condition": round(row["condition_avg"], 1),
            "visual": round(row["visual_avg"], 1),
            "fun": round(row["fun_avg"], 1),
            "maintenance": round(row["condition_avg"], 1),
            "difficulty": 0.0,
            "city": row["location"] or "",
            "state": "",
            "postalCode": "",
            "yardage": ""
        })

    return jsonify(holes)


@app.route("/api/submit_rating", methods=["POST"])
def submit_rating():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data received."}), 400

    hole_id = data.get("hole_id")
    condition_score = data.get("condition_score")
    visual_score = data.get("visual_score")
    fun_score = data.get("fun_score")
    comments = data.get("comments", "")

    if not hole_id:
        return jsonify({"success": False, "message": "hole_id is required."}), 400

    try:
        hole_id = int(hole_id)
        condition_score = float(condition_score)
        visual_score = float(visual_score)
        fun_score = float(fun_score)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid rating values."}), 400

    for score in [condition_score, visual_score, fun_score]:
        if score < 1 or score > 5:
            return jsonify({"success": False, "message": "Scores must be between 1 and 5."}), 400

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO ratings (hole_id, condition_score, visual_score, fun_score, comments)
        VALUES (?, ?, ?, ?, ?)
    """, (
        hole_id,
        condition_score,
        visual_score,
        fun_score,
        comments.strip()
    ))

    connection.commit()
    connection.close()

    return jsonify({"success": True, "message": "Rating submitted successfully."})


if __name__ == "__main__":
    app.run(debug=True)
