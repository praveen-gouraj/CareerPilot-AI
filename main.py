from flask import Blueprint, flash, render_template, request

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    return render_template("landing.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Thanks for reaching out. Our team will respond shortly.", "success")
    return render_template("contact.html")
