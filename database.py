from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    album = db.Column(db.String(255), nullable=False)
    artists = db.Column(db.String(255), nullable=False)
    popularity = db.Column(db.Integer)
    acousticness = db.Column(db.Float)
    danceability = db.Column(db.Float)
    energy = db.Column(db.Float)
    instrumentalness = db.Column(db.Float)
    liveness = db.Column(db.Float)
    loudness = db.Column(db.Float)
    speechiness = db.Column(db.Float)
    tempo = db.Column(db.Float)
    valence = db.Column(db.Float)
    genres = db.Column(db.String(255))

    def __repr__(self):
        return f"<Track {self.name}>"