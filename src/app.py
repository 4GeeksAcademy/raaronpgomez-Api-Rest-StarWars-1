"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import logging
import traceback
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Manejador global para registrar excepciones y devolver JSON (útil para debugging)


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception("Unhandled exception:")
    # En desarrollo puedes incluir traceback; quitar en producción.
    return jsonify({
        "error": "internal_server_error",
        "message": str(e),
        "trace": traceback.format_exc().splitlines()[-10:]  # últimas 10 líneas
    }), 500

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


def get_current_user():
    """Return the current user. Since there's no auth yet we pick the first user in the DB.
    Users must be created via Flask-Admin as requested."""
    user = User.query.first()
    if not user:
        raise APIException(
            "No users found. Create a user via the Flask-Admin interface.", status_code=404)
    return user


# People endpoints
@app.route('/people', methods=['GET'])
def list_people():
    people = People.query.all()
    return jsonify([p.serialize() for p in people]), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_people(people_id):
    person = People.query.get(people_id)
    if not person:
        raise APIException("People not found", status_code=404)
    return jsonify(person.serialize()), 200


# Planet endpoints
@app.route('/planets', methods=['GET'])
def list_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException("Planet not found", status_code=404)
    return jsonify(planet.serialize()), 200


# Users and favorites
@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200


@app.route('/users/favorites', methods=['GET'])
def list_current_user_favorites():
    user = get_current_user()
    favs = Favorite.query.filter_by(user_id=user.id).all()
    return jsonify([f.serialize() for f in favs]), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = get_current_user()
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException("Planet not found", status_code=404)

    # prevent duplicates
    exists = Favorite.query.filter_by(
        user_id=user.id, planet_id=planet_id).first()
    if exists:
        raise APIException("Favorite already exists", status_code=400)

    fav = Favorite(user_id=user.id, planet_id=planet_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({"msg": "Planet added to favorites", "favorite": fav.serialize()}), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    user = get_current_user()
    person = People.query.get(people_id)
    if not person:
        raise APIException("People not found", status_code=404)

    exists = Favorite.query.filter_by(
        user_id=user.id, people_id=people_id).first()
    if exists:
        raise APIException("Favorite already exists", status_code=400)

    fav = Favorite(user_id=user.id, people_id=people_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({"msg": "People added to favorites", "favorite": fav.serialize()}), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user = get_current_user()
    fav = Favorite.query.filter_by(
        user_id=user.id, planet_id=planet_id).first()
    if not fav:
        raise APIException("Favorite not found", status_code=404)
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite planet removed"}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    user = get_current_user()
    fav = Favorite.query.filter_by(
        user_id=user.id, people_id=people_id).first()
    if not fav:
        raise APIException("Favorite not found", status_code=404)
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite people removed"}), 200


# Ruta más robusta para /planets
@app.route("/planets", methods=["GET"])
def get_planets():
    try:
        planets = Planet.query.all()
        # Asegúrate de que Planet tenga un método serialize()
        result = []
        for p in planets:
            if hasattr(p, "serialize"):
                result.append(p.serialize())
            else:
                # Fallback básico si no existe serialize()
                result.append({
                    "id": getattr(p, "id", None),
                    "name": getattr(p, "name", None)
                })
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception("Error fetching /planets")
        return jsonify({"error": "internal_server_error", "message": str(e)}), 500


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
