from flask import Flask, request, session, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, User, Recipe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'super_secret_key'

CORS(app, supports_credentials=True)
db.init_app(app)
migrate = Migrate(app, db)

# === SIGNUP ===
@app.post('/signup')
def signup():
    data = request.get_json()

    try:
        new_user = User(
            username=data['username'],
            bio=data.get('bio', ''),
            image_url=data.get('image_url', '')
        )
        new_user.password_hash = data['password']

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 422


# === LOGIN ===
@app.post('/login')
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if user and user.authenticate(data.get('password')):
        session['user_id'] = user.id
        return jsonify(user.to_dict()), 200

    return jsonify({'error': 'Invalid username or password'}), 401


# === CHECK SESSION ===
@app.get('/check_session')
def check_session():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return jsonify(user.to_dict()), 200
    return jsonify({'error': 'Unauthorized'}), 401


# === LOGOUT ===
@app.delete('/logout')
def logout():
    if session.get('user_id'):
        session.pop('user_id')
        return '', 204
    return jsonify({'error': 'Unauthorized'}), 401


# === RECIPES (GET, POST) ===
@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        recipes = Recipe.query.all()
        return jsonify([r.to_dict() for r in recipes]), 200

    if request.method == 'POST':
        data = request.get_json()
        try:
            new_recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()
            return jsonify(new_recipe.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 422


# === Run Server ===
if __name__ == '__main__':
    app.run(port=5555, debug=True)
