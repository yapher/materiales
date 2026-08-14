from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__, template_folder='templates')

@home_bp.route('/')
@home_bp.route('/inicio')
def index():
    return render_template('home/index.html')
