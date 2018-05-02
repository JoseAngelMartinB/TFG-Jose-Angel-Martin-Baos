# Import modules
from flask import Blueprint, render_template, redirect, url_for, request, make_response

index = Blueprint('index', __name__, url_prefix='/', template_folder='templates')

@index.route('')
@index.route('index.html')
def main():
    """
    Render / web page.
    """
    return redirect(url_for('about.About'))
