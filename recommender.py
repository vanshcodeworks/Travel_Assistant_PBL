import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import json
import re
from datetime import datetime

class SmartTransportRecommender:
    def __init__(self, bus_path='bus.csv', train_path='train.csv', flight_path='flight.csv'):
        self.bus_path = bus_path
        self.train_path = train_path
        self.flight_path = flight_path
        self.load_data()
        self.train_models()

    def load_data(self):
        try:
            # Load bus data
            bus = pd.read_csv(self.bus_path)
            bus_df = pd.DataFrame({
                'mode': 'bus',
                'source': bus['Source'],
                'destination': bus['Destination'],
                'price': bus['price'].astype(float),
                'distance': bus['distance'].astype(float),
                'hour': pd.to_datetime(bus['Departure Time']).dt.hour,
                # Extract numeric part from duration strings like "03hrs 40mins"
                'duration': bus['Travel Duration'].apply(self.parse_duration),
                # Convert seats to numeric, handling any non-numeric values
                'availability': bus['Seats Left'].apply(lambda x: float(x) if pd.notnull(x) and str(x).isdigit() else 20),
                'operator': bus['Operator'],
                'rating': bus['rating'].fillna(4.0)
            })

            # Load flight data
            flight = pd.read_csv(self.flight_path)
            flight_df = pd.DataFrame({
                'mode': 'flight',
                'source': flight['source_city'],
                'destination': flight['destination_city'],
                'price': flight['price'].astype(float),
                'distance': flight.apply(lambda row: self.calculate_distance(row['source_city'], row['destination_city']), axis=1),
                'hour': self.map_time_of_day(flight['departure_time']),
                'duration': flight['duration'].astype(float),
                # Set default availability for flights
                'availability': 50,
                'operator': flight['airline'],
                'rating': 4.5
            })

            # Load train data
            train = pd.read_csv(self.train_path)
            train_df = pd.DataFrame({
                'mode': 'train',
                'source': train['fromStnCode'],
                'destination': train['toStnCode'],
                'price': train['totalFare'].astype(float),
                'distance': train['distance'].astype(float),
                'hour': pd.to_datetime(train['timeStamp']).dt.hour,
                'duration': train['duration'].astype(float),
                # Extract numeric availability from complex format
                'availability': train['availability'].apply(self.parse_train_availability),
                'operator': train['trainNumber'].astype(str),
                'rating': 4.0
            })

            self.df = pd.concat([bus_df, flight_df, train_df], ignore_index=True)
            self.cities = sorted(set(self.df['source']) | set(self.df['destination']))
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.create_sample_data()

    def parse_duration(self, duration_str):
        """Parse bus duration strings like '03hrs 40mins' to hours (float)"""
        if not isinstance(duration_str, str):
            return 2.0
        
        hours = 0
        minutes = 0
        
        hr_match = re.search(r'(\d+)hrs', duration_str)
        if hr_match:
            hours = int(hr_match.group(1))
            
        min_match = re.search(r'(\d+)mins', duration_str)
        if min_match:
            minutes = int(min_match.group(1))
            
        return hours + minutes/60

    def parse_train_availability(self, avail_str):
        """Extract numeric availability from train availability data"""
        if pd.isnull(avail_str):
            return 20
            
        try:
            # If it's a JSON string containing availability data
            if isinstance(avail_str, str) and avail_str.startswith('[{'):
                avail_data = json.loads(avail_str)
                if isinstance(avail_data, list) and len(avail_data) > 0:
                    # Extract numeric part from "AVAILABLE-0090"
                    status = avail_data[0].get('status', '')
                    match = re.search(r'AVAILABLE-(\d+)', status)
                    if match:
                        return float(match.group(1))
            
            # If it contains 'RAC' or similar non-numeric values
            if isinstance(avail_str, str) and 'RAC' in avail_str:
                # Just return a reasonable value
                return 5
            
            # Try direct conversion if possible
            return float(avail_str)
        except:
            # Default value if parsing fails
            return 20

    def map_time_of_day(self, time_strings):
        """Map text time periods to hour values"""
        hour_mapping = {
            'Early_Morning': 5,
            'Morning': 9,
            'Afternoon': 13,
            'Evening': 17,
            'Night': 21
        }
        
        return time_strings.map(hour_mapping).fillna(12)

    def create_sample_data(self):
        """Create sample data if loading real data fails"""
        print("Creating sample data...")
        self.df = pd.DataFrame({
            'source': ['Delhi']*3 + ['Mumbai']*3,
            'destination': ['Mumbai']*3 + ['Delhi']*3,
            'mode': ['bus', 'train', 'flight']*2,
            'price': np.random.randint(400, 2000, 6),
            'hour': [10, 12, 14, 9, 13, 15],
            'duration': [16, 12, 2, 16, 12, 2],
            'distance': [1400]*6,
            'availability': np.random.randint(10, 100, 6),
            'rating': [4.0, 4.2, 4.5, 3.9, 4.1, 4.6]
        })
        self.cities = sorted(set(self.df['source']) | set(self.df['destination']))

    def get_city_coordinates(self):
        """Return coordinates for major Indian cities"""
        return {
            'Delhi': (28.6139, 77.2090),
            'Mumbai': (19.0760, 72.8777),
            'Bangalore': (12.9716, 77.5946),
            'Kolkata': (22.5726, 88.3639),
            'Chennai': (13.0827, 80.2707),
            'Hyderabad': (17.3850, 78.4867),
            'Pune': (18.5204, 73.8567),
            'Agra': (27.1767, 78.0081),
            # Add other cities as needed
        }

    def calculate_distance(self, source, destination):
        """Calculate great-circle distance between cities"""
        from math import radians, sin, cos, sqrt, atan2

        coords = self.get_city_coordinates()
        if source not in coords or destination not in coords:
            return 500  # default distance

        lat1, lon1 = coords[source]
        lat2, lon2 = coords[destination]

        R = 6371  # Earth radius in kilometers
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return int(R * c)

    def train_models(self):
        """Train price prediction models for each mode of transport"""
        self.models = {}
        for mode in self.df['mode'].unique():
            data = self.df[self.df['mode'] == mode]
            if len(data) >= 10:  # Only train if we have enough data
                X = data[['distance', 'hour', 'availability']].values
                y = data['price'].values
                model = RandomForestRegressor(n_estimators=50, random_state=42)
                model.fit(X, y)
                self.models[mode] = model
            else:
                # Simple linear model for modes with little data
                self.models[mode] = lambda x: x[0] * 0.5 + 500

    def predict_price(self, source, dest, duration, mode, availability=50):
        """Predict price for a specific route and transport mode"""
        dist = self.calculate_distance(source, dest)
        hour = datetime.now().hour
        
        if mode in self.models:
            if isinstance(self.models[mode], RandomForestRegressor):
                input_data = np.array([[dist, hour, availability]])
                return float(self.models[mode].predict(input_data)[0])
            else:
                # Simple fallback model
                return float(self.models[mode]([dist, hour, availability]))
        
        # Default calculations if no model exists
        base_prices = {'bus': 1.0, 'train': 1.5, 'flight': 5.0}
        return dist * base_prices.get(mode, 2.0)

    def recommend(self, source, dest, date=None, hour=None):
        """Return detailed options for each mode with explanations."""
        results = []
        for mode in ['bus', 'train', 'flight']:
            mode_df = self.df[
                (self.df['source'] == source) &
                (self.df['destination'] == dest) &
                (self.df['mode'] == mode)
            ]
            if mode_df.empty:
                continue
            for _, row in mode_df.iterrows():
                result = {
                    'mode': mode,
                    'operator': row.get('operator', ''),
                    'departure_time': row.get('departure_time', ''),
                    'arrival_time': row.get('arrival_time', ''),
                    'price': row.get('price', 0),
                    'distance': row.get('distance', 0),
                    'duration': row.get('duration', 0),
                    'availability': row.get('availability', 0),
                    'rating': row.get('rating', 0),
                    'explanation': ''
                }
                # Add explanation
                if row.get('price', 0) == mode_df['price'].min():
                    result['explanation'] += 'Cheapest. '
                if row.get('duration', 0) == mode_df['duration'].min():
                    result['explanation'] += 'Fastest. '
                if row.get('rating', 0) == mode_df['rating'].max():
                    result['explanation'] += 'Highest rated. '
                results.append(result)
        # Sort by price, then duration
        results = sorted(results, key=lambda x: (x['price'], x['duration']))
        return results

    def estimate_duration(self, source, dest, mode):
        """Estimate travel duration based on distance and mode"""
        distance = self.calculate_distance(source, dest)
        speeds = {'bus': 60, 'train': 80, 'flight': 800}
        
        base_time = distance / speeds.get(mode, 60)
        
        # Add fixed overhead times
        if mode == 'flight':
            base_time += 2  # Airport procedures
        elif mode == 'train':
            base_time += 0.5  # Station procedures
        elif mode == 'bus':
            base_time += 0.3  # Bus station procedures
            
        return round(base_time * 2) / 2  # Round to nearest half hour

    def calculate_convenience(self, mode, duration, price):
        """Calculate a convenience score (higher is better)"""
        # Simple weighted score based on duration and price
        time_weight = 0.6
        price_weight = 0.4
        
        # Normalize scores (lower is better for both time and price)
        max_duration = 24  # Assume 24 hours is the max reasonable duration
        max_price = 10000  # Assume 10000 is the max reasonable price
        
        time_score = 1 - (duration / max_duration)
        price_score = 1 - (price / max_price)
        
        return (time_weight * time_score) + (price_weight * price_score)

    def get_cities(self):
        """Return list of available cities"""
        return self.cities
