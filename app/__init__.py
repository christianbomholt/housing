from flask import Flask, jsonify, render_template
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(env=None):
    from app.db_util import init_db_command, tranform_command, scrape_command,scrape_hist_command
    from app.model import House

    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "app.sqlite"),
        SQLALCHEMY_TRACK_MODIFICATIONS = False
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"+app.config['DATABASE']
    db.init_app(app)
    
    app.cli.add_command(init_db_command)
    app.cli.add_command(tranform_command)
    app.cli.add_command(scrape_command)
    app.cli.add_command(scrape_hist_command)

    @app.route('/map')
    def map():
        return render_template("map.html")

    @app.route('/hist')
    def hist():
        return render_template("hist_w.html")

    @app.route('/histo')
    def hist0():
        return render_template("hist.html")

    @app.route("/")
    def index():
        houses = House.query.filter(
            House.favorite)\
            .all()
        return render_template("index.html",houses=houses)

    @app.route('/add/<guid>', methods=['GET','POST'])
    def add(guid):

        house = House.query.filter(House.guid==guid).first()
        house.favorite = True
        db.session.add(house)
        db.session.commit()
        return render_template('map.html')

    return app
