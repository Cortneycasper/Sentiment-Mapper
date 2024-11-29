from flask import Flask, render_template, request, jsonify
import tweepy
from textblob import TextBlob
import geopandas as gpd
from shapely.geometry import Point
import folium
import os

app = Flask(__name__)

# Load Twitter API keys from config
from config import TWITTER_API_KEY, TWITTER_API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

# Twitter API Authentication
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    tweets = api.search_tweets(q=query, lang="en", count=100, tweet_mode='extended')
    sentiment_data = []

    for tweet in tweets:
        text = tweet.full_text
        analysis = TextBlob(text)
        sentiment = "Positive" if analysis.sentiment.polarity > 0 else "Negative" if analysis.sentiment.polarity < 0 else "Neutral"

        if tweet.geo:
            latitude, longitude = tweet.geo['coordinates']
            sentiment_data.append({"text": text, "sentiment": sentiment, "location": Point(longitude, latitude)})

    if sentiment_data:
        df = gpd.GeoDataFrame(sentiment_data)
        m = folium.Map(location=[0, 0], zoom_start=2)

        for _, row in df.iterrows():
            color = "green" if row["sentiment"] == "Positive" else "red" if row["sentiment"] == "Negative" else "gray"
            folium.CircleMarker(location=[row['location'].y, row['location'].x], radius=5, color=color, fill=True).add_to(m)

        map_path = "static/map.html"
        m.save(map_path)
        return jsonify({"status": "success", "map": map_path})

    return jsonify({"status": "error", "message": "No geotagged tweets found!"})

if __name__ == "__main__":
    app.run(debug=True)
