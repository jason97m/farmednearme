from flask import Flask, render_template, request
import csv
import math
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MARKETS_FILE = os.path.join(BASE_DIR, "data", "markets.csv")
ZIP_FILE = os.path.join(BASE_DIR, "data", "uszips.csv")

# ---------------------------
# Utility Functions
# ---------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Distance in miles"""
    R = 3958.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def load_zip_latlon(zip_code):
    with open(ZIP_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["zip"] == zip_code:
                return float(row["lat"]), float(row["lng"])
    return None

def load_markets():
    markets = []
    with open(MARKETS_FILE, newline='', encoding="cp1252") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            # Clean lat/lon strings: remove whitespace and trailing commas
            lat_str = row.get("location_y", "").strip().rstrip(',')
            lon_str = row.get("location_x", "").strip().rstrip(',')
            
            if lat_str and lon_str:
                try:
                    markets.append({
                        "name": row.get("listing_name", "").strip(),
                        # Strip extra quotes from addresses
                        "address": row.get("location_address", "").strip().strip('"'),
                        "lat": float(lat_str),
                        "lon": float(lon_str),
                        "desc": row.get("location_desc", "").strip()
                    })
                except ValueError:
                    # Skip rows with invalid numbers
                    print(f"Skipping invalid row: {row}")
    return markets

# ---------------------------
# Routes
# ---------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    error = None

    if request.method == "POST":
        zip_code = request.form.get("zip")

        zip_location = load_zip_latlon(zip_code)
        if not zip_location:
            error = "ZIP code not found."
        else:
            zip_lat, zip_lon = zip_location
            markets = load_markets()

            for market in markets:
                distance = haversine(
                    zip_lat, zip_lon,
                    market["lat"], market["lon"]
                )
                if distance <= 25:
                    market["distance"] = round(distance, 1)
                    results.append(market)

            results.sort(key=lambda x: x["distance"])

    return render_template("index.html", results=results, error=error)

if __name__ == "__main__":
    app.run(debug=True)
