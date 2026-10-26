from flask import Blueprint, render_template

bp = Blueprint("web", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/ui-kit")
def ui_kit():
    return render_template("ui_kit.html")


@bp.get("/my-complaints")
def my_complaints():
    return render_template("my_complaints.html")


@bp.get("/track")
def track():
    return render_template("track.html")
