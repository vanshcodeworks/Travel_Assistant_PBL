from flask import Flask, render_template, request, jsonify
import folium
import pandas as pd
import numpy as np
import json
import random
import datetime
from math import radians, sin, cos, sqrt, atan2
from recommender import SmartTransportRecommender

app = Flask(__name__)
recommender = SmartTransportRecommender()

# City coordinates for maps and calculations
CITY_COORDS = {
    'Delhi': (28.6139, 77.2090),
    'Mumbai': (19.0760, 72.8777),
    'Bangalore': (12.9716, 77.5946),
    'Kolkata': (22.5726, 88.3639),
    'Chennai': (13.0827, 80.2707),
    'Hyderabad': (17.3850, 78.4867),
    'Pune': (18.5204, 73.8567),
    'Agra': (27.1767, 78.0081),
    'Jaipur': (26.9124, 75.7873),
    'Ahmedabad': (23.0225, 72.5714),
    'Goa': (15.2993, 74.1240)
}

# Main route
@app.route('/')
def index():
    cities = sorted(recommender.cities)
    return render_template('index.html', cities=cities)

# Search route for finding transportation options
@app.route('/search', methods=['POST'])
def search():
    source = request.form.get('source')
    destination = request.form.get('destination')
    date = request.form.get('date')
    
    if source == destination:
        return render_template('error.html', message="Source and destination cannot be the same")
    
    # Get recommendations from recommender
    direct_options = recommender.recommend(source, destination, date=date)
    
    # Filter options by mode directly in Python code instead of in the template
    flight_options = [opt for opt in direct_options if opt.get('mode') == 'flight']
    train_options = [opt for opt in direct_options if opt.get('mode') == 'train']
    bus_options = [opt for opt in direct_options if opt.get('mode') == 'bus']
    
    # Create placeholder price data for trends
    yesterday_prices = {'bus': 1200, 'train': 1800, 'flight': 3500}
    today_prices = {'bus': 1300, 'train': 1850, 'flight': 3800}
    tomorrow_prices = {'bus': 1250, 'train': 1750, 'flight': 3600}
    
    # Calculate distance
    distance = calculate_distance(source, destination)
    
    # Generate route map
    map_html = generate_route_map(source, destination)
    
    # Get weather data for destination
    weather = get_weather_forecast(destination)
    
    # Get attractions for destination
    attractions = get_local_attractions(destination)
    
    return render_template(
        'results.html',
        source=source,
        destination=destination,
        distance=distance,
        direct=direct_options,
        flight_options=flight_options,
        train_options=train_options,
        bus_options=bus_options,
        yesterday_prices=yesterday_prices,
        today_prices=today_prices,
        tomorrow_prices=tomorrow_prices,
        map_html=map_html,
        weather=weather,
        attractions=attractions[:3]  # Limit to top 3
    )

# API endpoint for price trends
@app.route('/api/price_trends/<source>/<destination>')
def price_trends(source, destination):
    # Generate sample data for demonstration
    dates = pd.date_range(start='2023-10-01', end='2023-10-30', freq='D')
    
    # Create random price data with patterns
    np.random.seed(42)
    base_price = 2000
    
    flight_prices = base_price * 2 + np.random.normal(0, 200, len(dates))
    for i, date in enumerate(dates):
        if date.dayofweek >= 4:  # Fri, Sat, Sun
            flight_prices[i] += 500
    
    train_prices = base_price * 0.8 + np.random.normal(0, 100, len(dates))
    bus_prices = base_price * 0.5 + np.random.normal(0, 50, len(dates))
    
    data = {
        'dates': [d.strftime('%Y-%m-%d') for d in dates],
        'flight': flight_prices.tolist(),
        'train': train_prices.tolist(),
        'bus': bus_prices.tolist()
    }
    
    return jsonify(data)

# API endpoint for filtering results
@app.route('/api/filter', methods=['POST'])
def filter_results():
    data = request.json
    
    # Filters would be applied to results here
    # Simulating filtered results
    return jsonify({"success": True})

# Weather forecast page
@app.route('/weather/<city>')
def weather(city):
    forecast = get_weather_forecast(city)
    return render_template('weather.html', city=city, forecast=forecast)

# Attractions page
@app.route('/attractions/<city>')
def attractions(city):
    attractions_list = get_local_attractions(city)
    return render_template('attractions.html', city=city, attractions=attractions_list)

# Map page
@app.route('/map/<source>/<destination>')
def map_view(source, destination):
    map_html = generate_route_map(source, destination)
    return render_template('map.html', source=source, destination=destination, map_html=map_html)

# Helper functions
def calculate_distance(source, destination):
    """Calculate distance between two cities using their coordinates"""
    if source in CITY_COORDS and destination in CITY_COORDS:
        lat1, lon1 = CITY_COORDS[source]
        lat2, lon2 = CITY_COORDS[destination]
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        R = 6371  # Earth's radius in km
        
        return int(R * c)  # Distance in km
    else:
        return 1000  # Default fallback distance

def generate_route_map(source, destination):
    """Generate a Folium map for the route"""
    if source in CITY_COORDS and destination in CITY_COORDS:
        src_lat, src_lon = CITY_COORDS[source]
        dst_lat, dst_lon = CITY_COORDS[destination]
        center_lat = (src_lat + dst_lat) / 2
        center_lon = (src_lon + dst_lon) / 2
        
        # Create the map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
        
        # Add markers for source and destination
        folium.Marker(
            [src_lat, src_lon],
            popup=source,
            tooltip=source,
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        
        folium.Marker(
            [dst_lat, dst_lon],
            popup=destination,
            tooltip=destination,
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
        
        # Add different routes for different transport modes
        # Flight route (straight line)
        folium.PolyLine(
            [(src_lat, src_lon), (dst_lat, dst_lon)],
            color='blue',
            weight=3,
            opacity=0.7,
            dash_array='10',
            tooltip="Flight Route"
        ).add_to(m)
        
        # Train route (with waypoints)
        train_waypoint1 = (src_lat + (dst_lat - src_lat) * 0.33 + 0.5, src_lon + (dst_lon - src_lon) * 0.33 - 0.5)
        train_waypoint2 = (src_lat + (dst_lat - src_lat) * 0.66 - 0.5, src_lon + (dst_lon - src_lon) * 0.66 + 0.5)
        train_route = [(src_lat, src_lon), train_waypoint1, train_waypoint2, (dst_lat, dst_lon)]
        
        folium.PolyLine(
            train_route,
            color='red',
            weight=3,
            opacity=0.7,
            tooltip="Train Route"
        ).add_to(m)
        
        # Bus route (with different waypoints)
        bus_waypoint1 = (src_lat + (dst_lat - src_lat) * 0.4 - 0.3, src_lon + (dst_lon - src_lon) * 0.4 + 0.3)
        bus_waypoint2 = (src_lat + (dst_lat - src_lat) * 0.7 + 0.3, src_lon + (dst_lon - src_lon) * 0.7 - 0.3)
        bus_route = [(src_lat, src_lon), bus_waypoint1, bus_waypoint2, (dst_lat, dst_lon)]
        
        folium.PolyLine(
            bus_route,
            color='green',
            weight=3,
            opacity=0.7,
            tooltip="Bus Route"
        ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; 
                    border: 2px solid grey; z-index: 9999; font-size: 14px;
                    background-color: white; padding: 10px; border-radius: 5px;">
          <p><span style="color: blue; font-weight: bold;">———</span> Flight Route</p>
          <p><span style="color: red; font-weight: bold;">———</span> Train Route</p>
          <p><span style="color: green; font-weight: bold;">———</span> Bus Route</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m._repr_html_()
    else:
        return "<p>Map not available: city coordinates not found.</p>"

def get_weather_forecast(city, days=5):
    """Generate weather forecast for destination city (simulated)"""
    weather_types = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Heavy Rain", "Thunderstorm", "Windy"]
    weather_icons = {
        "Sunny": "☀️", 
        "Partly Cloudy": "⛅", 
        "Cloudy": "☁️", 
        "Light Rain": "🌦️", 
        "Heavy Rain": "🌧️", 
        "Thunderstorm": "⛈️", 
        "Windy": "💨"
    }
    
    # City temperature ranges (min, max) in Celsius
    city_temps = {
        "Delhi": (15, 35),
        "Mumbai": (24, 33),
        "Bangalore": (18, 28),
        "Hyderabad": (20, 32),
        "Chennai": (24, 35),
        "Kolkata": (22, 33),
        "Pune": (18, 30),
        "Jaipur": (18, 32),
        "Ahmedabad": (22, 36),
        "Agra": (15, 35)
    }
    
    # Use default temperature range if city not in dictionary
    temp_range = city_temps.get(city, (20, 30))
    
    # Generate forecast for the specified number of days
    forecast = []
    today = datetime.datetime.now()
    
    for i in range(days):
        date = today + datetime.timedelta(days=i)
        weather = random.choice(weather_types)
        temp_min = random.randint(temp_range[0], temp_range[0] + 5)
        temp_max = random.randint(temp_range[1] - 5, temp_range[1])
        
        forecast.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%A'),
            'weather': weather,
            'weather_icon': weather_icons[weather],
            'temp_min': temp_min,
            'temp_max': temp_max,
            'humidity': random.randint(40, 90),
            'wind': random.randint(5, 25)
        })
    
    return forecast

def get_local_attractions(city):
    """Get local attraction suggestions for the destination city"""
    attractions = {
        "Delhi": [
            {"name": "Red Fort", "type": "Historical", "rating": 4.5, "description": "UNESCO World Heritage site and iconic symbol of India's heritage", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Red_Fort_in_Delhi_03-2016_img3.jpg/800px-Red_Fort_in_Delhi_03-2016_img3.jpg"},
            {"name": "Qutub Minar", "type": "Historical", "rating": 4.4, "description": "UNESCO site with the world's tallest brick minaret", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Qutb_Minar_wide_lense.jpg/800px-Qutb_Minar_wide_lense.jpg"},
            {"name": "India Gate", "type": "Monument", "rating": 4.6, "description": "War memorial honoring Indian soldiers who died in WWI", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/India_Gate_in_New_Delhi_03-2016_img3.jpg/800px-India_Gate_in_New_Delhi_03-2016_img3.jpg"},
        ],
        "Mumbai": [
            {"name": "Gateway of India", "type": "Monument", "rating": 4.5, "description": "Historic monument overlooking the Arabian Sea", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Mumbai_Aug_2018_%2843397784544%29.jpg/800px-Mumbai_Aug_2018_%2843397784544%29.jpg"},
            {"name": "Marine Drive", "type": "Scenic", "rating": 4.7, "description": "Iconic seaside promenade known as the 'Queen's Necklace'", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Marine_Drive_Mumbai_Evening.jpg/800px-Marine_Drive_Mumbai_Evening.jpg"},
            {"name": "Elephanta Caves", "type": "Historical", "rating": 4.3, "description": "Ancient cave temples dedicated to Lord Shiva", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Elephanta_Caves_Trimurti.jpg/800px-Elephanta_Caves_Trimurti.jpg"},
        ]
    }
    
    # Default attractions for cities not in the list
    default_attractions = [
        {"name": "City Center", "type": "Urban", "rating": 4.0, "description": "Explore the heart of the city", "image_url": "https://via.placeholder.com/300x200?text=City+Center"},
        {"name": "Local Museum", "type": "Cultural", "rating": 4.1, "description": "Learn about the local history and culture", "image_url": "https://via.placeholder.com/300x200?text=Local+Museum"},
        {"name": "City Park", "type": "Nature", "rating": 4.2, "description": "Relax amid beautiful natural surroundings", "image_url": "https://via.placeholder.com/300x200?text=City+Park"},
    ]
    
    return attractions.get(city, default_attractions)

if __name__ == '__main__':
    app.run(debug=True)
