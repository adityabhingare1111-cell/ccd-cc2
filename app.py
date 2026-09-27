"""Student Attendance System.

A small Flask app built for CCA 2 of Cloud Computing and DevOps (CSE30040).
All data lives in memory (Python dicts), so it resets whenever the app restarts.
"""
import os

from flask import Flask, jsonify, render_template

app = Flask(__name__)

# A student whose attendance is below this percentage is a "defaulter".
MIN_ATTENDANCE = 75.0


# ---------------------------------------------------------------------------
# 1. In-memory storage
# ---------------------------------------------------------------------------

# students maps roll number -> name, e.g. {"CE101": "Aarav Kulkarni"}
students = {}

# attendance maps a date string -> {roll number: True if present, False if absent}
# e.g. {"2025-07-01": {"CE101": True, "CE102": False}}
attendance = {}

SAMPLE_STUDENTS = [
    ("CE101", "Aarav Kulkarni"),
    ("CE102", "Ishita Deshmukh"),
    ("CE103", "Rohan Patil"),
    ("CE104", "Sneha Joshi"),
    ("CE105", "Kabir Shaikh"),
]

# Four past lectures so the home page has something to show on first load.
# Each date lists only the students who were PRESENT.
SAMPLE_ATTENDANCE = {
    "2025-07-01": ["CE101", "CE102", "CE103", "CE104", "CE105"],
    "2025-07-02": ["CE101", "CE102", "CE104"],
    "2025-07-03": ["CE101", "CE102", "CE103", "CE104"],
    "2025-07-04": ["CE101", "CE104"],
}


def reset_data():
    """Clear everything and load the sample data. Tests call this before each test."""
    students.clear()
    attendance.clear()
    for roll_no, name in SAMPLE_STUDENTS:
        students[roll_no] = name
    for day, present_rolls in SAMPLE_ATTENDANCE.items():
        attendance[day] = {roll_no: roll_no in present_rolls for roll_no in students}


# ---------------------------------------------------------------------------
# 2. Helper functions
# ---------------------------------------------------------------------------

def get_commit():
    """Return the 7-character commit ID of the running code.

    Render sets RENDER_GIT_COMMIT automatically. Our Docker image sets GIT_SHA
    (passed as a build arg in CI). If neither exists we are running locally.
    """
    sha = os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("GIT_SHA") or "local"
    return sha[:7]


def student_summary(roll_no):
    """Work out classes attended, total classes and percentage for one student."""
    # Only count dates on which this student was on the register.
    total = sum(1 for day in attendance.values() if roll_no in day)
    attended = sum(1 for day in attendance.values() if day.get(roll_no))
    percentage = round(attended * 100 / total, 1) if total else 0.0
    return {
        "roll_no": roll_no,
        "name": students[roll_no],
        "attended": attended,
        "total": total,
        "percentage": percentage,
        # A brand-new student with no classes yet is not counted as a defaulter.
        "defaulter": total > 0 and percentage < MIN_ATTENDANCE,
    }


def all_summaries():
    """Summaries for every student, sorted by roll number."""
    return [student_summary(roll_no) for roll_no in sorted(students)]


def render_home(error=None, status=200):
    """Render the home page. Used for normal views and for showing form errors."""
    page = render_template(
        "index.html",
        rows=all_summaries(),
        error=error,
        roster=sorted(students.items()),
        days_marked=len(attendance),
        min_attendance=MIN_ATTENDANCE,
    )
    return page, status


@app.context_processor
def inject_commit():
    """Make {{ commit }} available in every template (used by the footer)."""
    return {"commit": get_commit()}


# ---------------------------------------------------------------------------
# 3. Web pages and form handlers
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_home()


# ---------------------------------------------------------------------------
# 4. JSON API and health check
# ---------------------------------------------------------------------------

@app.route("/api/students")
def api_students():
    rows = all_summaries()
    return jsonify({"count": len(rows), "students": rows})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "commit": get_commit()})


# Load the sample data once when the app starts.
reset_data()

if __name__ == "__main__":
    # Local development server. In Docker/Render, gunicorn runs the app instead.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
