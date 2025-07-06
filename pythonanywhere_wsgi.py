import sys
import os

# ---- PythonAnywhere WSGI configuration file ----
# This file contains the WSGI configuration required to serve your
# web application from PythonAnywhere.

# +++++++++++ VIRTUALENV +++++++++++
# If you have a virtualenv for this web app, add the path to it here
# so that Python can find your packages.
# For example:
# path = '/home/YourUsername/.virtualenvs/my-virtualenv/bin'
# if path not in sys.path:
#     sys.path.insert(0, path)

# +++++++++++ PROJECT PATH +++++++++++
# Add your project's directory to the Python path.
# IMPORTANT: Replace 'YourUsername' with your PythonAnywhere username.
# The project directory name 'Cerebrova' should match the folder you upload.
project_home = u'..'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# It's also a good idea to change the working directory to your project's directory.
os.chdir(project_home)

# +++++++++++ FLASK APPLICATION +++++++++++
# Import the Flask app object from your app.py file.
# The 'application' variable is what the PythonAnywhere server looks for.
from app import app as application
