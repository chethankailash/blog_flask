# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize PyMongo
mongo = PyMongo(app)

###########################################
#           Helper Functions              #
###########################################
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Admin access required.")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

###########################################
#           Routes: Home & Blog           #
###########################################
@app.route('/')
def index():
    # Convert the PyMongo cursor to a list so we can use the length filter in the template.
    blogs = list(mongo.db.blogs.find())
    return render_template('index.html', blogs=blogs)

@app.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        blog_data = {
            'title': title,
            'content': content,
            'author': session.get('username')
        }
        mongo.db.blogs.insert_one(blog_data)
        flash("Blog post created successfully!")
        return redirect(url_for('index'))
    return render_template('blog_create.html')

@app.route('/blog/edit/<blog_id>', methods=['GET', 'POST'])
@login_required
def edit_blog(blog_id):
    blog = mongo.db.blogs.find_one({'_id': ObjectId(blog_id)})
    if blog['author'] != session.get('username'):
        flash("You are not authorized to edit this post.")
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mongo.db.blogs.update_one(
            {'_id': ObjectId(blog_id)},
            {'$set': {'title': title, 'content': content}}
        )
        flash("Blog post updated!")
        return redirect(url_for('index'))
    return render_template('blog_edit.html', blog=blog)

@app.route('/blog/delete/<blog_id>')
@login_required
def delete_blog(blog_id):
    blog = mongo.db.blogs.find_one({'_id': ObjectId(blog_id)})
    if blog['author'] != session.get('username'):
        flash("You are not authorized to delete this post.")
        return redirect(url_for('index'))
    mongo.db.blogs.delete_one({'_id': ObjectId(blog_id)})
    flash("Blog post deleted!")
    return redirect(url_for('index'))

# New route for full blog details
@app.route('/blog/<blog_id>')
def blog_detail(blog_id):
    blog = mongo.db.blogs.find_one({'_id': ObjectId(blog_id)})
    if not blog:
        flash("Blog post not found!")
        return redirect(url_for('index'))
    return render_template('blog_detail.html', blog=blog)

###########################################
#        Routes: User Authentication      #
###########################################
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if mongo.db.users.find_one({'username': username}):
            flash("Username already exists!")
            return redirect(url_for('register'))
        hash_pass = generate_password_hash(password, method='pbkdf2:sha256')
        # For the first user, assign admin role; otherwise, default to user.
        role = 'admin' if mongo.db.users.count_documents({'role': 'admin'}) == 0 else 'user'
        user_data = {
            'username': username,
            'password': hash_pass,
            'role': role
        }
        mongo.db.users.insert_one(user_data)
        flash("Registration successful. Please login!")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            flash("Logged in successfully!")
            return redirect(url_for('index'))
        flash("Invalid username or password!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out!")
    return redirect(url_for('login'))

###########################################
#          Routes: Admin Panel            #
###########################################
@app.route('/admin')
@admin_required
def admin():
    users = mongo.db.users.find()
    return render_template('admin.html', users=users)

@app.route('/admin/user/edit/<user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role')
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'username': username, 'role': role}}
        )
        flash("User updated successfully!")
        return redirect(url_for('admin'))
    return render_template('edit_user.html', user=user)

@app.route('/admin/user/delete/<user_id>')
@admin_required
def delete_user(user_id):
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    flash("User deleted successfully!")
    return redirect(url_for('admin'))

###########################################
#               Run App                   #
###########################################
if __name__ == '__main__':
    app.run(debug=True)
