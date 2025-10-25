# app.py
import os
import uuid
import base64
from datetime import datetime, timedelta, timezone
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_from_directory, abort)
from models import init_db, get_conn, create_user, verify_user

# ---- Configuration ----
UPLOAD_IMG = "uploads/proctor_images"
UPLOAD_AUDIO = "uploads/proctor_audio"
os.makedirs(UPLOAD_IMG, exist_ok=True)
os.makedirs(UPLOAD_AUDIO, exist_ok=True)

# limit uploads to 6 MB (safety)
MAX_MB = 6
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "replace-with-a-secure-random-key")
app.config['MAX_CONTENT_LENGTH'] = MAX_MB * 1024 * 1024

# Demo hard-coded admin credentials (fallback) - remove in production
ADMIN_USERNAME = os.environ.get("DEMO_ADMIN_USER", "admin123")
ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASS", "admin_123@45")

# initialize DB
init_db()

# Ensure demo admin exists in DB (best-effort)
def ensure_demo_admin():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
        if not cur.fetchone():
            create_user(ADMIN_USERNAME, ADMIN_PASSWORD, is_admin=1)
        conn.close()
    except Exception:
        pass

ensure_demo_admin()

# ----------------- Helpers -----------------
def parse_iso_datetime(s: str) -> datetime:
    """
    Parse an ISO datetime string and return a timezone-aware UTC datetime.
    If s is naive, assume UTC.
    """
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s)
    except Exception:
        # fallback formats
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                d = datetime.strptime(s, fmt)
                break
            except Exception:
                d = None
        if d is None:
            # as ultimate fallback, return None
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d

# ------------------ AUTH ------------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")

        user = verify_user(uname, pwd)
        if user and user.get("is_admin"):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = True
            return redirect(url_for("admin_dashboard"))

        # fallback demo credentials
        if uname == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            try:
                conn = get_conn(); cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
                row = cur.fetchone()
                conn.close()
                if row:
                    session['user_id'] = row['id']
                    session['username'] = row['username']
                    session['is_admin'] = True
                else:
                    session['user_id'] = 0
                    session['username'] = ADMIN_USERNAME
                    session['is_admin'] = True
            except Exception:
                session['user_id'] = 0
                session['username'] = ADMIN_USERNAME
                session['is_admin'] = True

            flash("Logged in as admin (demo)", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials", "danger")
    return render_template("admin_login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")
        if not uname or not pwd:
            flash("Provide username and password", "danger")
            return redirect(url_for("register"))
        try:
            create_user(uname, pwd, is_admin=0)
            flash("Account created. Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash("Error creating user: " + str(e), "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")
        user = verify_user(uname, pwd)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for("admin_dashboard") if session['is_admin'] else url_for("student_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------ ADMIN DASHBOARD ------------------
@app.route("/admin")
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for("admin_login"))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()
    cur.execute("""SELECT a.*, u.username AS username, e.title AS exam_title
                   FROM attempts a
                   LEFT JOIN users u ON u.id=a.user_id
                   LEFT JOIN exams e ON e.id=a.exam_id
                   ORDER BY a.start_time DESC LIMIT 50""")
    attempts = cur.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", exams=exams, attempts=attempts)

# ------------------ STUDENT DASHBOARD ------------------
@app.route("/")
@app.route("/student")
def student_dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for("login"))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()
    cur.execute("""SELECT a.*, e.title FROM attempts a
                   JOIN exams e ON e.id=a.exam_id
                   WHERE a.user_id=?
                   ORDER BY a.start_time DESC""", (session['user_id'],))
    attempts = cur.fetchall()
    conn.close()
    return render_template("student_dashboard.html", exams=exams, attempts=attempts)

# ------------------ ADMIN: CREATE EXAM ------------------
@app.route("/admin/create_exam", methods=["GET", "POST"])
def create_exam():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        title = request.form.get("title")
        duration = int(request.form.get("duration") or 60)
        max_q = min(50, int(request.form.get("max_questions") or 50))
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO exams (title, duration_minutes, max_questions) VALUES (?,?,?)",
                    (title, duration, max_q))
        exam_id = cur.lastrowid
        for i in range(1, max_q + 1):
            q = request.form.get(f"q{i}")
            if not q:
                continue
            a = request.form.get(f"a{i}"); b = request.form.get(f"b{i}")
            c = request.form.get(f"c{i}"); d = request.form.get(f"d{i}")
            corr = request.form.get(f"corr{i}")
            cur.execute("""INSERT INTO questions (exam_id, q_index, question, option_a, option_b, option_c, option_d, correct)
                           VALUES (?,?,?,?,?,?,?,?)""", (exam_id, i, q, a, b, c, d, corr))
        conn.commit(); conn.close()
        flash("Exam created", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("create_exam.html")

# ------------------ ADMIN: EDIT EXAM ------------------
@app.route("/admin/edit/<int:exam_id>", methods=["GET", "POST"])
def edit_exam(exam_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for("admin_login"))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM exams WHERE id=?", (exam_id,))
    exam = cur.fetchone()
    if not exam:
        conn.close(); abort(404)
    if request.method == "POST":
        title = request.form.get("title")
        duration = int(request.form.get("duration") or exam['duration_minutes'])
        max_q = min(50, int(request.form.get("max_questions") or exam['max_questions']))
        cur.execute("UPDATE exams SET title=?, duration_minutes=?, max_questions=? WHERE id=?",
                    (title, duration, max_q, exam_id))
        cur.execute("DELETE FROM questions WHERE exam_id=?", (exam_id,))
        for i in range(1, max_q + 1):
            q = request.form.get(f"q{i}")
            if not q:
                continue
            a = request.form.get(f"a{i}"); b = request.form.get(f"b{i}")
            c = request.form.get(f"c{i}"); d = request.form.get(f"d{i}")
            corr = request.form.get(f"corr{i}")
            cur.execute("""INSERT INTO questions (exam_id, q_index, question, option_a, option_b, option_c, option_d, correct)
                           VALUES (?,?,?,?,?,?,?,?)""", (exam_id, i, q, a, b, c, d, corr))
        conn.commit(); conn.close()
        flash("Exam updated", "success")
        return redirect(url_for("admin_dashboard"))
    cur.execute("SELECT * FROM questions WHERE exam_id=? ORDER BY q_index", (exam_id,))
    questions = cur.fetchall()
    conn.close()
    return render_template("edit_exam.html", exam=exam, questions=questions)

# ------------------ START EXAM (STUDENT) ------------------
@app.route("/start_exam/<int:exam_id>")
def start_exam(exam_id):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for("login"))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM exams WHERE id=?", (exam_id,))
    exam = cur.fetchone()
    if not exam:
        conn.close(); flash("Exam not found", "danger"); return redirect(url_for("student_dashboard"))
    start = datetime.now(timezone.utc)
    allowed_until = start + timedelta(minutes=exam['duration_minutes'])
    cur.execute("INSERT INTO attempts (user_id, exam_id, start_time, allowed_until) VALUES (?,?,?,?)",
                (session['user_id'], exam_id, start.isoformat(), allowed_until.isoformat()))
    attempt_id = cur.lastrowid
    cur.execute("SELECT * FROM questions WHERE exam_id=? ORDER BY q_index LIMIT ?", (exam_id, exam['max_questions']))
    questions = cur.fetchall()
    conn.commit(); conn.close()
    allowed_until_iso = allowed_until.isoformat()
    return render_template("exam.html", exam=exam, questions=questions, attempt_id=attempt_id, allowed_until=allowed_until_iso)

# ------------------ AUTOSAVE ANSWER ------------------
@app.route("/save_answer", methods=["POST"])
def save_answer():
    data = request.get_json()
    attempt_id = data.get("attempt_id")
    question_id = data.get("question_id")
    selected = data.get("selected")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,))
    if not cur.fetchone():
        conn.close(); return jsonify({"status":"error", "msg":"attempt not found"}), 404
    cur.execute("SELECT * FROM answers WHERE attempt_id=? AND question_id=?", (attempt_id, question_id))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE answers SET selected=? WHERE id=?", (selected, existing["id"]))
    else:
        cur.execute("INSERT INTO answers (attempt_id, question_id, selected) VALUES (?,?,?)",
                    (attempt_id, question_id, selected))
    conn.commit(); conn.close()
    return jsonify({"status":"ok"})

# ------------------ PROCTOR: UPLOAD IMAGE ------------------
@app.route("/proctor/upload_image", methods=["POST"])
def proctor_upload_image():
    attempt_id = request.form.get("attempt_id")
    imgdata = request.form.get("image")
    if not imgdata:
        return jsonify({"status":"error","msg":"no image"}), 400
    try:
        header, encoded = imgdata.split(",", 1)
    except Exception:
        return jsonify({"status":"error","msg":"invalid image data"}), 400
    try:
        data = base64.b64decode(encoded)
    except Exception:
        return jsonify({"status":"error","msg":"bad base64"}), 400
    # Save file (filename as uuid)
    fname = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(UPLOAD_IMG, fname)
    with open(path, "wb") as f:
        f.write(data)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO proctor_images (attempt_id, filename, timestamp) VALUES (?,?,?)",
                (attempt_id, fname, datetime.now(timezone.utc).isoformat()))
    conn.commit(); conn.close()
    return jsonify({"status":"ok"})

# ------------------ PROCTOR: UPLOAD AUDIO ------------------
@app.route("/proctor/upload_audio", methods=["POST"])
def proctor_upload_audio():
    attempt_id = request.form.get("attempt_id")
    audio = request.files.get("audio")
    if not audio:
        return jsonify({"status":"error","msg":"no audio"}), 400
    try:
        fname = f"{uuid.uuid4().hex}.webm"
        path = os.path.join(UPLOAD_AUDIO, fname)
        # Ensure the audio file is saved correctly
        try:
            if not os.path.exists(UPLOAD_AUDIO):
                os.makedirs(UPLOAD_AUDIO, exist_ok=True)
            audio.save(path)
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                raise ValueError("Failed to save audio file or file is empty")
        except Exception as e:
            print(f"Error saving audio file: {str(e)}")
            return jsonify({"status":"error","msg":"failed to save audio"}), 500

        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO proctor_audio (attempt_id, filename, timestamp) VALUES (?,?,?)",
                    (attempt_id, fname, datetime.now(timezone.utc).isoformat()))
        conn.commit(); conn.close()
        return jsonify({"status":"ok"})
    except Exception as e:
        print(f"Audio upload error: {str(e)}")
        return jsonify({"status":"error","msg":"server error"}), 500

# ------------------ PROCTOR: LOG EVENT ------------------
@app.route("/proctor/log_event", methods=["POST"])
def proctor_log_event():
    data = request.get_json()
    attempt_id = data.get("attempt_id")
    ev = data.get("event")
    detail = data.get("detail", "")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO proctor_events (attempt_id, event_type, detail, timestamp) VALUES (?,?,?,?)",
                (attempt_id, ev, detail, datetime.now(timezone.utc).isoformat()))
    conn.commit(); conn.close()
    return jsonify({"status":"ok"})

# ------------------ SUBMIT EXAM (STUDENT) ------------------
@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    attempt_id = request.form.get("attempt_id")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,))
    att = cur.fetchone()
    if not att:
        conn.close(); flash("Attempt not found", "danger"); return redirect(url_for("student_dashboard"))
    now = datetime.now(timezone.utc)
    allowed_until = parse_iso_datetime(att['allowed_until'])
    if allowed_until is None:
        time_exceeded = 1
    else:
        time_exceeded = 1 if now > allowed_until else 0

    cur.execute("SELECT e.max_questions FROM exams e WHERE e.id=?", (att['exam_id'],))
    max_q_row = cur.fetchone()
    max_q = max_q_row['max_questions'] if max_q_row else 50

    cur.execute("SELECT q.id, q.correct FROM questions q WHERE q.exam_id=? ORDER BY q.q_index LIMIT ?",
                (att['exam_id'], max_q))
    qrows = cur.fetchall()
    score = 0
    total = len(qrows)
    for q in qrows:
        cur.execute("SELECT selected FROM answers WHERE attempt_id=? AND question_id=?", (attempt_id, q['id']))
        ans = cur.fetchone()
        if ans and ans['selected'] and ans['selected'] == q['correct']:
            score += 1
    # Store percentage score (0-100)
    percentage = round((score / total * 100), 1) if total > 0 else 0
    cur.execute("UPDATE attempts SET score=?, end_time=?, submitted=1, time_exceeded=? WHERE id=?",
                (percentage, now.isoformat(), time_exceeded, attempt_id))
    conn.commit(); conn.close()
    flash("Exam submitted. Results will be visible to admin only.", "success")
    return redirect(url_for("student_dashboard"))

# ------------------ ADMIN: VIEW RESULTS ------------------
@app.route("/admin/results")
def admin_results():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for("admin_login"))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""SELECT a.*, u.username AS username, e.title AS exam_title, e.max_questions
                   FROM attempts a
                   LEFT JOIN users u ON u.id=a.user_id
                   LEFT JOIN exams e ON e.id=a.exam_id
                   ORDER BY (a.score IS NULL) ASC, a.score DESC, a.start_time DESC""")
    attempts_raw = cur.fetchall()
    attempts = []
    for a in attempts_raw:
        # Get actual total questions for this attempt (in case exam was edited)
        cur.execute("SELECT COUNT(*) FROM questions WHERE exam_id=?", (a['exam_id'],))
        total_questions = cur.fetchone()[0]
        attempt = dict(a)
        attempt['total_questions'] = total_questions
        attempts.append(attempt)
    conn.close()
    return render_template("admin_results.html", attempts=attempts)

# ------------------ ADMIN: VIEW ATTEMPT DETAIL ------------------
@app.route("/admin/attempt/<int:attempt_id>")
def admin_attempt_detail(attempt_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for("admin_login"))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""SELECT a.*, u.username AS username, e.title AS exam_title
                   FROM attempts a
                   LEFT JOIN users u ON u.id=a.user_id
                   LEFT JOIN exams e ON e.id=a.exam_id
                   WHERE a.id=?""", (attempt_id,))
    att = cur.fetchone()
    if not att:
        conn.close(); abort(404)
    cur.execute("SELECT * FROM proctor_images WHERE attempt_id=? ORDER BY timestamp", (attempt_id,))
    images = cur.fetchall()
    cur.execute("SELECT * FROM proctor_audio WHERE attempt_id=? ORDER BY timestamp", (attempt_id,))
    audios = cur.fetchall()
    cur.execute("SELECT * FROM proctor_events WHERE attempt_id=? ORDER BY timestamp", (attempt_id,))
    events = cur.fetchall()
    cur.execute("""SELECT q.q_index, q.question, q.option_a, q.option_b, q.option_c, q.option_d, q.correct, a.selected
                   FROM questions q
                   LEFT JOIN answers a ON q.id=a.question_id AND a.attempt_id=?
                   WHERE q.exam_id = ? ORDER BY q.q_index""", (attempt_id, att['exam_id']))
    q_and_a = cur.fetchall()
    conn.close()
    return render_template("admin_attempt.html", att=att, images=images, audios=audios, events=events, q_and_a=q_and_a)

# ------------------ SERVE UPLOADS ------------------
@app.route("/uploads/proctor_images/<path:fname>")
def serve_image(fname):
    return send_from_directory(UPLOAD_IMG, fname)

@app.route("/uploads/proctor_audio/<path:fname>")
def serve_audio(fname):
    return send_from_directory(UPLOAD_AUDIO, fname)

# ------------------ API: Admin Stats ------------------
@app.route("/api/admin/stats")
def api_admin_stats():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({"error":"unauthorized"}), 401
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM exams")
    exams_count = cur.fetchone()[0] if cur.fetchone is None else cur.execute("SELECT COUNT(*) FROM exams").fetchone()[0]
    # Re-execute safely to fetch counts
    cur.execute("SELECT COUNT(*) FROM exams"); exams_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attempts"); attempts_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attempts WHERE submitted=1"); submitted_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attempts WHERE submitted=0"); active_attempts = cur.fetchone()[0]
    cur.execute("""
        SELECT AVG(score) 
        FROM attempts 
        WHERE score IS NOT NULL 
        AND submitted=1
    """); 
    avg = cur.fetchone()[0]
    avg_score = round(avg, 1) if avg is not None else None
    conn.close()
    return jsonify({
        "exams": exams_count,
        "attempts": attempts_count,
        "submitted": submitted_count,
        "active_attempts": active_attempts,
        "avg_score": avg_score
    })

# ------------------ API: Student Stats ------------------
@app.route("/api/student/stats")
def api_student_stats():
    if 'user_id' not in session or session.get('is_admin'):
        return jsonify({"error":"unauthorized"}), 401
    uid = session['user_id']
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attempts"); total_exams = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attempts WHERE user_id=?", (uid,)); attempts_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attempts WHERE user_id=? AND submitted=0", (uid,)); pending_count = cur.fetchone()[0]
    cur.execute("""
        SELECT AVG(score) 
        FROM attempts 
        WHERE user_id=? 
        AND score IS NOT NULL 
        AND submitted=1
    """, (uid,))
    avg = cur.fetchone()[0]
    avg_score = round(avg, 1) if avg is not None else None
    conn.close()
    return jsonify({
        "total_exams": total_exams,
        "attempts": attempts_count,
        "pending": pending_count,
        "avg_score": avg_score
    })


if __name__ == "__main__":
    app.run(debug=True)
