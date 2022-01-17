from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ['API_KEY']

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Create SQLAlchemy Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
    def __repr__(self):
        return '<Movie %r>' % self.title


class MovieForm(FlaskForm):
    updated_rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    updated_review = StringField('Your Review', validators=[DataRequired()])
    done_button = SubmitField('Done')


class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    add_button = SubmitField('Add Movie')


db.create_all()


### Add a movie to the database. Comment out after complete. ###
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()

# access all of the movies and save to variable

@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    ranking = len(movies) + 1
    for movie in movies:
        ranking -= 1
        movie.ranking = ranking
    return render_template("index.html", movies=movies)

@app.route("/edit", methods=["POST", "GET"])
def edit():
    form = MovieForm()
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    if form.validate_on_submit():
        new_rating = float(form.updated_rating.data)
        new_review = form.updated_review.data
        movie_selected.rating = new_rating
        movie_selected.review = new_review
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie_selected)

@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    selected_movie = Movie.query.get(movie_id)
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["POST", "GET"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        query = form.title.data
        parameters = {
            "api_key": API_KEY,
            "query": query,
        }
        r = requests.get("https://api.themoviedb.org/3/search/movie", params=parameters)
        results = r.json()['results']
        return render_template("select.html", movies=results)
    return render_template("add.html", form=form)

@app.route("/select")
def select():
    movie_id = request.args.get('id')
    if movie_id:
        movie_db_details = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}",
                                        params={"api_key": API_KEY, "movie_id": movie_id, })
        movie_details = movie_db_details.json()
        new_movie = Movie(
            title=movie_details['title'],
            year=movie_details['release_date'].split("-")[0],
            description=movie_details['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500/{movie_details['poster_path']}",
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
