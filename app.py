from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re
import os
import html

from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# FLASK APPLICATION
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "storyspring-development-key"
)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    "database.db"
)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS stories (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            description TEXT NOT NULL,

            category TEXT NOT NULL,

            age_group TEXT NOT NULL,

            creator TEXT NOT NULL,

            cover_image TEXT,

            content TEXT NOT NULL,

            status TEXT DEFAULT 'published'

        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT DEFAULT 'creator'

        )
    """)

    connection.commit()

    connection.close()


# ==========================================
# DEFAULT CREATOR
# ==========================================

def create_default_creator():

    connection = get_db_connection()

    existing_creator = connection.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, ("creator",)).fetchone()

    if existing_creator is None:

        hashed_password = generate_password_hash(
            "creator123"
        )

        connection.execute("""
            INSERT INTO users
            (
                username,
                password,
                role
            )

            VALUES (?, ?, ?)

        """, (
            "creator",
            hashed_password,
            "creator"
        ))

        connection.commit()

    connection.close()


# ==========================================
# DEFAULT ADMIN
# ==========================================

def create_default_admin():

    connection = get_db_connection()

    existing_admin = connection.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, ("admin",)).fetchone()

    if existing_admin is None:

        hashed_password = generate_password_hash(
            "admin123"
        )

        connection.execute("""
            INSERT INTO users
            (
                username,
                password,
                role
            )

            VALUES (?, ?, ?)

        """, (
            "admin",
            hashed_password,
            "admin"
        ))

        connection.commit()

    connection.close()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    connection = get_db_connection()

    stories = connection.execute("""
        SELECT *
        FROM stories

        WHERE status = 'published'

        ORDER BY id DESC

    """).fetchall()

    connection.close()

    return render_template(
        "index.html",
        stories=stories
    )


# ==========================================
# SEARCH
# ==========================================

@app.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    connection = get_db_connection()

    if query:

        search_pattern = f"%{query}%"

        stories = connection.execute("""
            SELECT *
            FROM stories

            WHERE status = 'published'

            AND (
                title LIKE ?
                OR description LIKE ?
                OR category LIKE ?
                OR content LIKE ?
            )

            ORDER BY id DESC

        """, (
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern
        )).fetchall()

    else:

        stories = connection.execute("""
            SELECT *
            FROM stories

            WHERE status = 'published'

            ORDER BY id DESC

        """).fetchall()

    connection.close()

    return render_template(
        "search.html",
        stories=stories,
        query=query
    )


# ==========================================
# STORY PAGE
# ==========================================

@app.route("/story/<int:story_id>")
def story(story_id):

    connection = get_db_connection()

    story = connection.execute("""
        SELECT *
        FROM stories

        WHERE id = ?

        AND status = 'published'

    """, (story_id,)).fetchone()

    connection.close()

    if story is None:

        return "Story not found", 404

    return render_template(
        "story.html",
        story=story
    )

@app.route("/about")
def about():
    return render_template("about.html")

# ==========================================
# CREATOR SIGN UP
# ==========================================

@app.route(
    "/creator/signup",
    methods=["GET", "POST"]
)
def creator_signup():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # ----------------------------------
        # VALIDATION
        # ----------------------------------

        if not username:

            flash("Please enter a username.")

            return redirect(
                url_for("creator_signup")
            )

        if len(username) < 3:

            flash(
                "Username must be at least 3 characters long."
            )

            return redirect(
                url_for("creator_signup")
            )

        if not re.match(
            r"^[A-Za-z0-9_]+$",
            username
        ):

            flash(
                "Username can only contain letters, numbers and underscores."
            )

            return redirect(
                url_for("creator_signup")
            )

        if not password:

            flash("Please enter a password.")

            return redirect(
                url_for("creator_signup")
            )

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters long."
            )

            return redirect(
                url_for("creator_signup")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match."
            )

            return redirect(
                url_for("creator_signup")
            )

        # ----------------------------------
        # CHECK USERNAME
        # ----------------------------------

        connection = get_db_connection()

        existing_user = connection.execute("""
            SELECT id
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        if existing_user:

            connection.close()

            flash(
                "That username is already taken."
            )

            return redirect(
                url_for("creator_signup")
            )

        # ----------------------------------
        # HASH PASSWORD
        # ----------------------------------

        hashed_password = generate_password_hash(
            password
        )

        # ----------------------------------
        # CREATE CREATOR
        # ----------------------------------

        connection.execute("""
            INSERT INTO users
            (
                username,
                password,
                role
            )

            VALUES (?, ?, ?)

        """, (
            username,
            hashed_password,
            "creator"
        ))

        connection.commit()

        new_user = connection.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        connection.close()

        # ----------------------------------
        # LOGIN USER
        # ----------------------------------

        session["user_id"] = new_user["id"]

        session["username"] = new_user["username"]

        session["role"] = new_user["role"]

        flash(
            "Your creator account has been created successfully!"
        )

        return redirect(
            url_for("creator_dashboard")
        )

    return render_template(
        "creator_signup.html"
    )


# ==========================================
# CREATOR LOGIN
# ==========================================

@app.route(
    "/creator/login",
    methods=["GET", "POST"]
)
def creator_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter your username and password."
            )

            return redirect(
                url_for("creator_login")
            )

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users

            WHERE username = ?

            AND role = 'creator'

        """, (username,)).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["role"] = user["role"]

            return redirect(
                url_for("creator_dashboard")
            )

        flash(
            "Invalid username or password."
        )

    return render_template(
        "creator_login.html"
    )


# ==========================================
# CREATOR DASHBOARD
# ==========================================

@app.route("/creator/dashboard")
def creator_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("creator_login")
        )

    if session.get("role") != "creator":

        return redirect(
            url_for("creator_login")
        )

    connection = get_db_connection()

    stories = connection.execute("""
        SELECT *
        FROM stories

        WHERE creator = ?

        ORDER BY id DESC

    """, (
        session["username"],
    )).fetchall()

    connection.close()

    return render_template(
        "creator_dashboard.html",
        stories=stories
    )


# ==========================================
# CREATE STORY
# ==========================================

@app.route(
    "/creator/story/create",
    methods=["GET", "POST"]
)
def create_story():

    if "user_id" not in session:

        return redirect(
            url_for("creator_login")
        )

    if session.get("role") != "creator":

        return redirect(
            url_for("creator_login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        age_group = request.form.get(
            "age_group",
            ""
        ).strip()

        content = request.form.get(
            "content",
            ""
        ).strip()

        # ----------------------------------
        # VALIDATION
        # ----------------------------------

        if not title:

            flash("Please enter a story title.")

            return redirect(
                url_for("create_story")
            )

        if not description:

            flash(
                "Please enter a story description."
            )

            return redirect(
                url_for("create_story")
            )

        if not category:

            flash(
                "Please select a category."
            )

            return redirect(
                url_for("create_story")
            )

        if not age_group:

            flash(
                "Please select an age group."
            )

            return redirect(
                url_for("create_story")
            )

        if not content:

            flash(
                "Please write your story."
            )

            return redirect(
                url_for("create_story")
            )

        # ----------------------------------
        # FORMAT STORY SAFELY
        # ----------------------------------

        paragraphs = content.split("\n\n")

        formatted_content = ""

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if paragraph:

                safe_paragraph = html.escape(
                    paragraph
                )

                formatted_content += (
                    "<p>"
                    + safe_paragraph.replace(
                        "\n",
                        "<br>"
                    )
                    + "</p>"
                )

        # ----------------------------------
        # SAVE STORY AS PENDING
        # ----------------------------------

        connection = get_db_connection()

        connection.execute("""
            INSERT INTO stories
            (
                title,
                description,
                category,
                age_group,
                creator,
                cover_image,
                content,
                status
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            title,

            description,

            category,

            age_group,

            session["username"],

            None,

            formatted_content,

            "pending"

        ))

        connection.commit()

        connection.close()

        flash(
            "Your story has been submitted for admin approval!"
        )

        return redirect(
            url_for("creator_dashboard")
        )

    return render_template(
        "create_story.html"
    )


# ==========================================
# EDIT STORY
# ==========================================

@app.route(
    "/creator/story/edit/<int:story_id>",
    methods=["GET", "POST"]
)
def edit_story(story_id):

    if "user_id" not in session:

        return redirect(
            url_for("creator_login")
        )

    if session.get("role") != "creator":

        return redirect(
            url_for("creator_login")
        )

    connection = get_db_connection()

    story = connection.execute("""
        SELECT *
        FROM stories

        WHERE id = ?

        AND creator = ?

    """, (
        story_id,
        session["username"]
    )).fetchone()

    if story is None:

        connection.close()

        return "Story not found", 404

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        age_group = request.form.get(
            "age_group",
            ""
        ).strip()

        content = request.form.get(
            "content",
            ""
        ).strip()

        # ----------------------------------
        # VALIDATION
        # ----------------------------------

        if (
            not title
            or not description
            or not category
            or not age_group
            or not content
        ):

            flash(
                "Please complete all fields."
            )

            connection.close()

            return redirect(
                url_for(
                    "edit_story",
                    story_id=story_id
                )
            )

        # ----------------------------------
        # FORMAT CONTENT SAFELY
        # ----------------------------------

        paragraphs = content.split("\n\n")

        formatted_content = ""

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if paragraph:

                safe_paragraph = html.escape(
                    paragraph
                )

                formatted_content += (
                    "<p>"
                    + safe_paragraph.replace(
                        "\n",
                        "<br>"
                    )
                    + "</p>"
                )

        # ----------------------------------
        # UPDATE STORY
        # ----------------------------------

        connection.execute("""
            UPDATE stories

            SET
                title = ?,
                description = ?,
                category = ?,
                age_group = ?,
                content = ?,
                status = 'pending'

            WHERE id = ?

            AND creator = ?

        """, (

            title,

            description,

            category,

            age_group,

            formatted_content,

            story_id,

            session["username"]

        ))

        connection.commit()

        connection.close()

        flash(
            "Story updated and sent for admin approval again."
        )

        return redirect(
            url_for("creator_dashboard")
        )

    connection.close()

    return render_template(
        "edit_story.html",
        story=story
    )


# ==========================================
# DELETE STORY
# ==========================================

@app.route(
    "/creator/story/delete/<int:story_id>",
    methods=["POST"]
)
def delete_story(story_id):

    if "user_id" not in session:

        return redirect(
            url_for("creator_login")
        )

    if session.get("role") != "creator":

        return redirect(
            url_for("creator_login")
        )

    connection = get_db_connection()

    story = connection.execute("""
        SELECT id
        FROM stories

        WHERE id = ?

        AND creator = ?

    """, (
        story_id,
        session["username"]
    )).fetchone()

    if story is None:

        connection.close()

        return "Story not found", 404

    connection.execute("""
        DELETE FROM stories

        WHERE id = ?

        AND creator = ?

    """, (
        story_id,
        session["username"]
    ))

    connection.commit()

    connection.close()

    flash(
        "Story deleted successfully."
    )

    return redirect(
        url_for("creator_dashboard")
    )


# ==========================================
# CREATOR LOGOUT
# ==========================================

@app.route("/creator/logout")
def creator_logout():

    session.clear()

    return redirect(
        url_for("creator_login")
    )


# ==========================================
# ADMIN LOGIN
# ==========================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter your username and password."
            )

            return redirect(
                url_for("admin_login")
            )

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users

            WHERE username = ?

            AND role = 'admin'

        """, (username,)).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["role"] = user["role"]

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "Invalid admin username or password."
        )

    return render_template(
        "admin_login.html"
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    if session.get("role") != "admin":

        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()

    stories = connection.execute("""
        SELECT *
        FROM stories

        ORDER BY id DESC

    """).fetchall()

    total_stories = connection.execute("""
        SELECT COUNT(*)
        FROM stories
    """).fetchone()[0]

    pending_stories = connection.execute("""
        SELECT COUNT(*)
        FROM stories

        WHERE status = 'pending'
    """).fetchone()[0]

    published_stories = connection.execute("""
        SELECT COUNT(*)
        FROM stories

        WHERE status = 'published'
    """).fetchone()[0]

    rejected_stories = connection.execute("""
        SELECT COUNT(*)
        FROM stories

        WHERE status = 'rejected'
    """).fetchone()[0]

    creators = connection.execute("""
        SELECT COUNT(*)
        FROM users

        WHERE role = 'creator'
    """).fetchone()[0]

    connection.close()

    return render_template(
        "admin_dashboard.html",

        stories=stories,

        total_stories=total_stories,

        pending_stories=pending_stories,

        published_stories=published_stories,

        rejected_stories=rejected_stories,

        creators=creators
    )


# ==========================================
# ADMIN APPROVE STORY
# ==========================================

@app.route(
    "/admin/story/approve/<int:story_id>",
    methods=["POST"]
)
def approve_story(story_id):

    if "user_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    if session.get("role") != "admin":

        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()

    connection.execute("""
        UPDATE stories

        SET status = 'published'

        WHERE id = ?

    """, (story_id,))

    connection.commit()

    connection.close()

    flash(
        "Story approved and published successfully!"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ==========================================
# ADMIN REJECT STORY
# ==========================================

@app.route(
    "/admin/story/reject/<int:story_id>",
    methods=["POST"]
)
def reject_story(story_id):

    if "user_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    if session.get("role") != "admin":

        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()

    connection.execute("""
        UPDATE stories

        SET status = 'rejected'

        WHERE id = ?

    """, (story_id,))

    connection.commit()

    connection.close()

    flash(
        "Story has been rejected."
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ==========================================
# ADMIN DELETE STORY
# ==========================================

@app.route(
    "/admin/story/delete/<int:story_id>",
    methods=["POST"]
)
def admin_delete_story(story_id):

    if "user_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    if session.get("role") != "admin":

        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM stories

        WHERE id = ?

    """, (story_id,))

    connection.commit()

    connection.close()

    flash(
        "Story deleted by administrator."
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ==========================================
# ADMIN LOGOUT
# ==========================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# ==========================================
# INITIALIZE DATABASE
# ==========================================

# This runs both when using:
#
#     python app.py
#
# and when using:
#
#     gunicorn app:app
#
# It creates the database tables if they
# do not already exist and creates the
# default admin/creator accounts if needed.

create_database()

create_default_creator()

create_default_admin()


# ==========================================
# START APPLICATION LOCALLY
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
