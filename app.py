from flask import Flask, render_template, request
import requests
import pandas as pd
import re

app = Flask(__name__)

API_URL = "https://www.microburbs.com.au/report_generator/api/suburb/properties"
API_KEY = "test"   


def fetch_suburb_data(suburb, property_type="all"):
    params = {
        "suburb": suburb,
        "property_type": property_type
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.get(API_URL, params=params, headers=headers, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"API error: {r.status_code}")

    data = r.json()
    results = data.get("results", [])
    return results


def flatten_results(results):
    records = []

    for r in results:
        attrs = r.get("attributes", {}) or {}
        addr = r.get("address", {}) or {}
        coords = r.get("coordinates", {}) or {}

        rec = {
            "area_name": r.get("area_name"),
            "gnaf_pid": r.get("gnaf_pid"),
            "listing_date": r.get("listing_date"),
            "price": r.get("price"),
            "property_type": r.get("property_type"),

            "bedrooms": attrs.get("bedrooms"),
            "bathrooms": attrs.get("bathrooms"),
            "garage_spaces": attrs.get("garage_spaces"),
            "building_size": attrs.get("building_size"),
            "land_size": attrs.get("land_size"),

            "sa1": addr.get("sa1"),
            "suburb": addr.get("sal"),
            "state": addr.get("state"),
            "street": addr.get("street"),

            "latitude": coords.get("latitude"),
            "longitude": coords.get("longitude"),
        }
        records.append(rec)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    return df


def to_numeric(col):
    """
    Convert a column that may contain strings like '593.0', '605 m²', 'None', 'nan'
    to numeric floats.
    """
    if col.dtype == "float" or col.dtype == "int":
        return col

    # extract first number in the string
    return (
        col.astype(str)
        .str.extract(r"([-+]?\d*\.?\d+)")[0]
        .astype(float)
    )


def analyze_data(df):
    if df.empty:
        return {}, {}, {}, {}, []

    # ensure price numeric
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"].notna()].copy()

    # numeric conversions
    for col in ["bedrooms", "bathrooms", "garage_spaces"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "building_size" in df.columns:
        df["building_size_num"] = to_numeric(df["building_size"])
    else:
        df["building_size_num"] = None

    if "land_size" in df.columns:
        df["land_size_num"] = to_numeric(df["land_size"])
    else:
        df["land_size_num"] = None

    # listing date to datetime
    if "listing_date" in df.columns:
        df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
        df["year"] = df["listing_date"].dt.year
    else:
        df["year"] = None

    # summary stats
    stats = {
        "total_listings": int(len(df)),
        "median_price": round(df["price"].median(), 2),
        "mean_price": round(df["price"].mean(), 2),
        "min_price": round(df["price"].min(), 2),
        "max_price": round(df["price"].max(), 2),
        "number of avg_bedrooms": int(round(df["bedrooms"].mean(), 2)) if "bedrooms" in df.columns else None,
        "number of avg_bathrooms": int(round(df["bathrooms"].mean(), 2)) if "bathrooms" in df.columns else None,
    }

    # yearly listings
    yearly_counts = (
        df.dropna(subset=["year"])
        .groupby("year")
        .size()
        .to_dict()
    )

    # median price by property type
    if "property_type" in df.columns:
        ptype_median = (
            df.groupby("property_type")["price"]
            .median()
            .sort_values(ascending=False)
            .to_dict()
        )
    else:
        ptype_median = {}

    # median price by bedrooms
    if "bedrooms" in df.columns:
        bed_median = (
            df.dropna(subset=["bedrooms"])
            .groupby("bedrooms")["price"]
            .median()
            .sort_values()
            .to_dict()
        )
    else:
        bed_median = {}

    # property_type counts
    if "property_type" in df.columns:
        ptype_counts = df["property_type"].value_counts().to_dict()
    else:
        ptype_counts = {}

    sample_rows = df.head(50).to_dict(orient="records")

    return stats, yearly_counts, ptype_median, bed_median, ptype_counts, sample_rows


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        suburb = request.form.get("suburb", "").strip()
        prop_type = request.form.get("property_type", "all")

        if not suburb:
            return render_template("index.html", error="Please enter a suburb name.")

        try:
            results = fetch_suburb_data(suburb, prop_type)
        except Exception as e:
            return render_template("index.html", error=str(e))

        df = flatten_results(results)

        if df.empty:
            return render_template(
                "index.html",
                error="No results returned for that suburb or property type combination."
            )

        stats, yearly_counts, ptype_median, bed_median, ptype_counts, sample_rows = analyze_data(df)

        return render_template(
            "dashboard.html",
            suburb=suburb,
            prop_type=prop_type,
            stats=stats,
            yearly_sales=yearly_counts,
            ptype_median=ptype_median,
            bed_median=bed_median,
            ptype_counts=ptype_counts,
            table_data=sample_rows,
        )

    # GET
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
