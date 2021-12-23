#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from flask.globals import session
from sqlalchemy.sql.elements import and_
from sqlalchemy.sql.expression import false
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler, error
from flask_wtf import Form
from forms import *
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

app.config['SQLALCHEMY_DATABASE_URI']
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
from models import db, Venue, Artist, Show



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  #Query the venue table and get distinct cities with theirs states 
  city_state = db.session.query(Venue.city.distinct().label('city'), Venue.state.label('state'))
  venue = Venue.query.all()
  return render_template('pages/venues.html', venue = venue, city_state = city_state);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # ilike is used to match the search term with the name of the venue case-insensitively
  search_term=request.form.get('search_term', '')
  response = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # get venue with the venue id then look through the show table for upcoming and past shows
  # datetime is used to get the current date (now) and time to compare it with the show start time 
  # if the start time is greater then now then this show is upcoming and if it's less than now
  # then it's a past show
  venue = Venue.query.get(venue_id)
  upcoming_shows = Show.query.filter(and_(Show.venue_id == venue_id, Show.start_time > datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))).all()
  past_shows = Show.query.filter(and_(Show.venue_id == venue_id, Show.start_time <= datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))).all()
  return render_template('pages/show_venue.html', venue=venue, upcoming_shows= upcoming_shows, past_shows=past_shows)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    fb = request.form.get('facebook_link')
    image = request.form.get('image_link')
    website = request.form.get('website_link')
    seeking = bool(request.form.get('seeking_talent'))
    seeking_description = request.form.get('seeking_description')
    venue = Venue(name=name,city=city,state=state, address=address, phone=phone,
    genres=genres, facebook_link=fb, image_link=image, website_link=website,
    seeking=seeking, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if(error):
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    name = venue.name
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Venue ' + name + ' can\'t be deleted, please try again!')
    return jsonify({ 'success': False })
  else:
    flash('Venue ' + name + ' was successfully deleted!')
    return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term', '')
  response = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  upcoming_shows = Show.query.filter(and_(Show.artist_id == artist_id, Show.start_time > datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))).all()
  past_shows = Show.query.filter(and_(Show.artist_id == artist_id, Show.start_time <= datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))).all()
  return render_template('pages/show_artist.html', artist=artist, upcoming_shows=upcoming_shows, past_shows=past_shows)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # use current artist data as placeholder in input fields
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form.get('facebook_link')
    artist.image_link = request.form.get('image_link')
    artist.website_link = request.form.get('website_link')
    artist.seeking = bool(request.form.get('seeking_venue'))
    artist.seeking_description = request.form.get('seeking_description')
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Artist ' + request.form['name'] + ' wasn\'t successfully edited, please try again!')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.address = request.form.get('address')
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form.get('facebook_link')
    venue.image_link = request.form.get('image_link')
    venue.website_link = request.form.get('website_link')
    venue.seeking = bool(request.form.get('seeking_talent'))
    venue.seeking_description = request.form.get('seeking_description')
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Venue ' + request.form['name'] + ' wasn\'t successfully edited, please try again!')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    fb = request.form.get('facebook_link')
    image = request.form.get('image_link')
    website = request.form.get('website_link')
    seeking = bool(request.form.get('seeking_venue'))
    seeking_description = request.form.get('seeking_description')
    artist = Artist(name=name,city=city,state=state, phone=phone,
    genres=genres, facebook_link=fb, image_link=image, website_link=website,
    seeking=seeking, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if(error):
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = Show.query.all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')
    show = Show(artist_id = artist_id, venue_id = venue_id, start_time = start_time)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if(error):
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show was successfully listed!')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
