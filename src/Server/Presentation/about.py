# Import modules
from flask import Blueprint, render_template, redirect, url_for, request, make_response

about = Blueprint('about', __name__, url_prefix='/', template_folder='templates')

@about.route('about.html')
def About():
    """
    Render /about.html web page.
    """
    return render_template('about.html',)
