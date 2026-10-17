# Travel Assistant PBL

Recommendation system for travel attractions: a Flask-style Python service that
suggests places based on user preferences, with a notebook walking through the
model.

## Layout

```
main.py            application entrypoint
server.py          HTTP server
recommender.py     recommendation logic
Ai.ipynb           walkthrough notebook
static/css/        styles
static/js/         frontend behaviour
templates/         HTML templates (Jinja2)
```

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## How it works

`recommender.py` scores attractions against user preferences and returns the
best matches; `server.py` exposes that over HTTP and `templates/attractions.html`
renders the results. `Ai.ipynb` documents how the scoring was arrived at.

## Notes

- This is the backend half of a project-based-learning submission; there is no
  packaging and no test suite.
- The templates use Jinja2, so this is Flask-style rendering served through a
  plain `http.server`-style bootstrap rather than the Flask app object.