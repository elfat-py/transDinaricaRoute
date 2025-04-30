import os
import folium
import gpxpy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.distance import geodesic
from folium.plugins import HeatMap, MarkerCluster
import numpy as np
from sklearn.cluster import DBSCAN
import requests
import json
from folium.plugins import HeatMapWithTime
import branca.colormap as cm
from matplotlib.colors import to_hex
from folium import IFrame
from folium.plugins import MeasureControl
import matplotlib.patches as mpatches
import base64
from io import BytesIO
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import math

# Set working directory
working_project = "YOUR_PATH_HERE"

# GPX files to analyze
gpx_files = [
    'TransDinarica_-_2024.gpx',
    'TransDinarica_-_Dan_1.gpx',
    'TransDinarica_-_Dan_2.gpx',
    'TransDinarica_-_Dan_3.gpx',
    'Transdinarica_-_predlog_1_(onako_grubo).gpx',
    'Transdinarica.gpx'
]

# Define the countries in the TransDinarica region with their approximate bounding boxes
countries_info = {
    "Slovenia": {"bounds": [45.4, 46.9, 13.4, 16.6], "color": "#1f77b4"},
    "Croatia": {"bounds": [42.3, 46.5, 13.5, 19.4], "color": "#ff7f0e"},
    "Bosnia and Herzegovina": {"bounds": [42.5, 45.3, 15.7, 19.6], "color": "#2ca02c"},
    "Montenegro": {"bounds": [41.8, 43.6, 18.4, 20.4], "color": "#d62728"},
    "Albania": {"bounds": [39.6, 42.7, 19.2, 21.1], "color": "#9467bd"},
    "Kosovo": {"bounds": [41.8, 43.3, 20.0, 21.8], "color": "#8c564b"},
    "North Macedonia": {"bounds": [40.8, 42.4, 20.4, 23.0], "color": "#e377c2"},
    "Serbia": {"bounds": [42.2, 46.2, 18.8, 23.0], "color": "#7f7f7f"}
}

# Define challenges and opportunities
challenges_opportunities = [
    {"type": "challenge", "name": "Steep Terrain", "indicator": "slope > 15%", "color": "#d62728"},
    {"type": "challenge", "name": "Remote Areas", "indicator": "distance from settlements > 10km", "color": "#ff9896"},
    {"type": "challenge", "name": "Border Crossings", "indicator": "international borders", "color": "#9467bd"},
    {"type": "challenge", "name": "High Elevation", "indicator": "elevation > 1800m", "color": "#c5b0d5"},
    {"type": "opportunity", "name": "Scenic Views", "indicator": "elevation changes & vista points",
     "color": "#1f77b4"},
    {"type": "opportunity", "name": "Cultural Sites", "indicator": "proximity to heritage", "color": "#aec7e8"},
    {"type": "opportunity", "name": "Trail Connectivity", "indicator": "intersection with other trails",
     "color": "#2ca02c"},
    {"type": "opportunity", "name": "Local Infrastructure", "indicator": "proximity to services", "color": "#98df8a"}
]


# Function to load GPX files
def load_gpx_files(file_list, base_path):
    """Load GPX files and extract route information"""
    routes = []

    for file in file_list:
        file_path = os.path.join(base_path, file)
        try:
            with open(file_path, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                for track in gpx.tracks:
                    for segment in track.segments:
                        points = [(point.latitude, point.longitude, point.elevation) for point in segment.points]
                        if points:  # Only add if there are points
                            routes.append({'file': file, 'points': points})
        except Exception as e:
            print(f"Error loading {file}: {e}")

    return routes


# Function to calculate route distance
def route_distance(points):
    """Calculate the total distance of a route in kilometers"""
    distance = 0.0
    for i in range(1, len(points)):
        p1 = (points[i - 1][0], points[i - 1][1])
        p2 = (points[i][0], points[i][1])
        distance += geodesic(p1, p2).kilometers
    return distance


# Function to calculate slope between consecutive points
def calculate_slope(p1, p2):
    """Calculate the slope percentage between two points"""
    if p1[2] is None or p2[2] is None:
        return 0

    # Calculate distance in meters
    dist = geodesic((p1[0], p1[1]), (p2[0], p2[1])).meters
    if dist == 0:
        return 0

    # Calculate elevation change in meters
    elev_change = p2[2] - p1[2]

    # Calculate slope as percentage
    slope_pct = (elev_change / dist) * 100

    return slope_pct


# Function to identify country for a point
def identify_country(lat, lon, countries_info):
    """Identify which country a point belongs to based on bounding boxes"""
    for country, info in countries_info.items():
        bounds = info["bounds"]
        # Check if point is within bounds (lat_min, lat_max, lon_min, lon_max)
        if bounds[0] <= lat <= bounds[1] and bounds[2] <= lon <= bounds[3]:
            return country
    return "Unknown"


# Function to simulate points of interest (since we don't have actual POI data)
def generate_simulated_pois(routes, countries_info):
    """Generate simulated points of interest near the routes"""
    all_points = []
    for route in routes:
        for point in route['points']:
            all_points.append((point[0], point[1]))

    # Create a centroid of all route points
    if not all_points:
        return []

    avg_lat = sum(p[0] for p in all_points) / len(all_points)
    avg_lon = sum(p[1] for p in all_points) / len(all_points)

    pois = []
    poi_types = [
        {"type": "cultural", "name": "Historic Site", "icon": "info-sign", "color": "blue"},
        {"type": "infrastructure", "name": "Accommodation", "icon": "home", "color": "green"},
        {"type": "infrastructure", "name": "Food & Water", "icon": "cutlery", "color": "green"},
        {"type": "scenic", "name": "Vista Point", "icon": "camera", "color": "purple"},
        {"type": "trail", "name": "Trail Junction", "icon": "random", "color": "orange"}
    ]

    # Generate POIs near route points with some randomness
    np.random.seed(42)  # for reproducibility
    num_pois = min(len(all_points) // 10, 50)  # Limit to reasonable number

    selected_indices = np.random.choice(len(all_points), num_pois, replace=False)

    for idx in selected_indices:
        base_point = all_points[idx]

        # Add some random variation
        lat_variation = np.random.uniform(-0.01, 0.01)
        lon_variation = np.random.uniform(-0.01, 0.01)

        lat = base_point[0] + lat_variation
        lon = base_point[1] + lon_variation

        # Randomly select a POI type
        poi_type = np.random.choice(poi_types)

        country = identify_country(lat, lon, countries_info)

        pois.append({
            "lat": lat,
            "lon": lon,
            "type": poi_type["type"],
            "name": f"{poi_type['name']} ({country})",
            "icon": poi_type["icon"],
            "color": poi_type["color"],
            "country": country
        })

    return pois


# Function to analyze challenges and opportunities
def analyze_challenges_opportunities(routes, pois, countries_info):
    """Analyze routes for challenges and opportunities"""
    results = []

    # Process routes
    for route_idx, route in enumerate(routes):
        points = route['points']
        for i in range(1, len(points)):
            p1 = points[i - 1]
            p2 = points[i]

            # Check for steep terrain (challenge)
            slope = calculate_slope(p1, p2)

            # Check for high elevation (challenge)
            high_elevation = p1[2] > 1800 if p1[2] is not None else False

            # Calculate midpoint for this segment
            mid_lat = (p1[0] + p2[0]) / 2
            mid_lon = (p1[1] + p2[1]) / 2

            # Identify country
            country1 = identify_country(p1[0], p1[1], countries_info)
            country2 = identify_country(p2[0], p2[1], countries_info)

            # Check for border crossing (challenge)
            border_crossing = country1 != country2 and country1 != "Unknown" and country2 != "Unknown"

            # Find nearest POI (opportunity)
            nearest_poi_dist = float('inf')
            nearest_poi_type = None

            for poi in pois:
                dist = geodesic((mid_lat, mid_lon), (poi['lat'], poi['lon'])).kilometers
                if dist < nearest_poi_dist:
                    nearest_poi_dist = dist
                    nearest_poi_type = poi['type']

            # Remote area simulation (challenge)
            # If no infrastructure POI within 10km
            remote_area = not any(
                poi['type'] == 'infrastructure' and
                geodesic((mid_lat, mid_lon), (poi['lat'], poi['lon'])).kilometers < 10
                for poi in pois
            )

            # Trail connectivity (opportunity)
            # If near a trail junction
            trail_connectivity = any(
                poi['type'] == 'trail' and
                geodesic((mid_lat, mid_lon), (poi['lat'], poi['lon'])).kilometers < 2
                for poi in pois
            )

            # Scenic views (opportunity)
            # If high elevation and significant view (simplified simulation)
            scenic_view = (p1[2] > 1200 if p1[2] is not None else False) and abs(slope) > 5

            # Cultural site proximity (opportunity)
            cultural_proximity = any(
                poi['type'] == 'cultural' and
                geodesic((mid_lat, mid_lon), (poi['lat'], poi['lon'])).kilometers < 5
                for poi in pois
            )

            # Local infrastructure (opportunity)
            local_infrastructure = any(
                poi['type'] == 'infrastructure' and
                geodesic((mid_lat, mid_lon), (poi['lat'], poi['lon'])).kilometers < 5
                for poi in pois
            )

            # Store the results
            results.append({
                'route_id': route_idx,
                'file': route['file'],
                'segment': i,
                'lat': mid_lat,
                'lon': mid_lon,
                'country': country1,
                'next_country': country2,
                'elevation': p1[2],
                'slope': slope,
                'challenges': {
                    'steep_terrain': abs(slope) > 15,
                    'remote_area': remote_area,
                    'border_crossing': border_crossing,
                    'high_elevation': high_elevation
                },
                'opportunities': {
                    'scenic_view': scenic_view,
                    'cultural_proximity': cultural_proximity,
                    'trail_connectivity': trail_connectivity,
                    'local_infrastructure': local_infrastructure
                }
            })

    return results


# Function to create a challenges/opportunities heatmap
def create_challenge_opportunity_map(analysis_results):
    """Create heatmap visualizations for challenges and opportunities"""
    # Create base map
    m = folium.Map(location=[44.0, 17.5], zoom_start=7, tiles='CartoDB positron')

    # Add measure control for distance calculation
    m.add_child(MeasureControl())

    # Filter points for challenges and opportunities
    challenge_points = []
    opportunity_points = []

    for result in analysis_results:
        lat, lon = result['lat'], result['lon']

        # Count challenges at this point
        challenge_score = sum(1 for _, is_present in result['challenges'].items() if is_present)
        if challenge_score > 0:
            challenge_points.append([lat, lon, challenge_score])

        # Count opportunities at this point
        opportunity_score = sum(1 for _, is_present in result['opportunities'].items() if is_present)
        if opportunity_score > 0:
            opportunity_points.append([lat, lon, opportunity_score])

    # Create heatmap layers
    if challenge_points:
        challenge_layer = HeatMap(
            challenge_points,
            name='Challenges Heatmap',
            radius=12,
            max_zoom=13,
            gradient={0.4: 'blue', 0.65: 'yellow', 1: 'red'}
        )
        challenge_layer.add_to(m)

    if opportunity_points:
        opportunity_layer = HeatMap(
            opportunity_points,
            name='Opportunities Heatmap',
            radius=12,
            max_zoom=13,
            gradient={0.4: 'green', 0.65: 'yellow', 1: 'red'}
        )
        opportunity_layer.add_to(m)

    # Add country polygons as simplified boundaries
    for country, info in countries_info.items():
        bounds = info["bounds"]
        color = info["color"]

        # Create polygon from bounds
        coords = [
            [bounds[0], bounds[2]],  # SW
            [bounds[0], bounds[3]],  # SE
            [bounds[1], bounds[3]],  # NE
            [bounds[1], bounds[2]],  # NW
            [bounds[0], bounds[2]]  # SW again to close
        ]

        folium.Polygon(
            locations=coords,
            color=color,
            weight=2,
            fill=True,
            fill_opacity=0.1,
            fill_color=color,
            tooltip=country
        ).add_to(m)

    # Add routes as polylines
    for route_idx, route in enumerate(routes):
        points = [(p[0], p[1]) for p in route['points']]
        folium.PolyLine(
            points,
            color='blue',
            weight=3,
            opacity=0.7,
            tooltip=f"Route: {route['file']}"
        ).add_to(m)

    # Add POIs
    poi_cluster = MarkerCluster(name="Points of Interest").add_to(m)
    for poi in pois:
        folium.Marker(
            location=[poi['lat'], poi['lon']],
            tooltip=poi['name'],
            icon=folium.Icon(color=poi['color'], icon=poi['icon'])
        ).add_to(poi_cluster)

    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; right: 50px; width: 220px; 
                border:2px solid grey; z-index:9999; background-color:white;
                padding: 10px; border-radius: 5px;">
      <p><b>TransDinarica Analysis</b></p>
      <hr>
      <p><b>Challenges:</b></p>
      <p><i style="background: red; width: 15px; height: 15px; display: inline-block;"></i> High Challenge Density</p>
      <p><i style="background: yellow; width: 15px; height: 15px; display: inline-block;"></i> Medium Challenge Density</p>
      <hr>
      <p><b>Opportunities:</b></p>
      <p><i style="background: green; width: 15px; height: 15px; display: inline-block;"></i> High Opportunity Density</p>
      <p><i style="background: yellow; width: 15px; height: 15px; display: inline-block;"></i> Medium Opportunity Density</p>
      <hr>
      <p><i class="fa fa-info-sign" style="color: blue"></i> Cultural Site</p>
      <p><i class="fa fa-home" style="color: green"></i> Accommodation</p>
      <p><i class="fa fa-cutlery" style="color: green"></i> Food & Water</p>
      <p><i class="fa fa-camera" style="color: purple"></i> Vista Point</p>
      <p><i class="fa fa-random" style="color: orange"></i> Trail Junction</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add layer control
    folium.LayerControl().add_to(m)

    # Add title
    title_html = '''
    <h3 align="center" style="font-size:16px"><b>TransDinarica Route: Challenges & Opportunities</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    return m


# Function to create detailed statistics for each country
def create_country_statistics(analysis_results, pois):
    """Calculate and visualize statistics for each country"""
    country_stats = {}

    # Initialize stats
    for country in countries_info.keys():
        country_stats[country] = {
            'segment_count': 0,
            'total_distance': 0,
            'elevation_gain': 0,
            'elevation_loss': 0,
            'challenges': {
                'steep_terrain': 0,
                'remote_area': 0,
                'border_crossing': 0,
                'high_elevation': 0
            },
            'opportunities': {
                'scenic_view': 0,
                'cultural_proximity': 0,
                'trail_connectivity': 0,
                'local_infrastructure': 0
            },
            'poi_count': {
                'cultural': 0,
                'infrastructure': 0,
                'scenic': 0,
                'trail': 0
            }
        }

    # Count POIs by country
    for poi in pois:
        country = poi['country']
        if country in country_stats:
            poi_type = poi['type']
            if poi_type in country_stats[country]['poi_count']:
                country_stats[country]['poi_count'][poi_type] += 1

    # Process route segments
    for result in analysis_results:
        country = result['country']
        if country in country_stats:
            # Basic stats
            country_stats[country]['segment_count'] += 1

            # Challenges
            for challenge, is_present in result['challenges'].items():
                if is_present:
                    country_stats[country]['challenges'][challenge] += 1

            # Opportunities
            for opportunity, is_present in result['opportunities'].items():
                if is_present:
                    country_stats[country]['opportunities'][opportunity] += 1

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(18, 16))

    # Challenge count by country
    challenge_data = []
    for country, stats in country_stats.items():
        challenge_sum = sum(stats['challenges'].values())
        challenge_data.append({'country': country, 'challenge_count': challenge_sum})

    challenge_df = pd.DataFrame(challenge_data)
    challenge_df = challenge_df.sort_values('challenge_count', ascending=False)

    sns.barplot(data=challenge_df, x='country', y='challenge_count', ax=axes[0, 0])
    axes[0, 0].set_title('Challenges by Country')
    axes[0, 0].set_xlabel('Country')
    axes[0, 0].set_ylabel('Number of Challenges')
    axes[0, 0].tick_params(axis='x', rotation=45)

    # Opportunity count by country
    opportunity_data = []
    for country, stats in country_stats.items():
        opportunity_sum = sum(stats['opportunities'].values())
        opportunity_data.append({'country': country, 'opportunity_count': opportunity_sum})

    opportunity_df = pd.DataFrame(opportunity_data)
    opportunity_df = opportunity_df.sort_values('opportunity_count', ascending=False)

    sns.barplot(data=opportunity_df, x='country', y='opportunity_count', ax=axes[0, 1])
    axes[0, 1].set_title('Opportunities by Country')
    axes[0, 1].set_xlabel('Country')
    axes[0, 1].set_ylabel('Number of Opportunities')
    axes[0, 1].tick_params(axis='x', rotation=45)

    # POI distribution by country
    poi_data = []
    for country, stats in country_stats.items():
        for poi_type, count in stats['poi_count'].items():
            poi_data.append({'country': country, 'poi_type': poi_type, 'count': count})

    poi_df = pd.DataFrame(poi_data)

    sns.barplot(data=poi_df, x='country', y='count', hue='poi_type', ax=axes[1, 0])
    axes[1, 0].set_title('POI Distribution by Country')
    axes[1, 0].set_xlabel('Country')
    axes[1, 0].set_ylabel('Number of POIs')
    axes[1, 0].tick_params(axis='x', rotation=45)

    # Challenge/opportunity ratio
    ratio_data = []
    for country, stats in country_stats.items():
        challenge_sum = sum(stats['challenges'].values())
        opportunity_sum = sum(stats['opportunities'].values())

        # Avoid division by zero
        ratio = challenge_sum / opportunity_sum if opportunity_sum > 0 else float('inf')
        if ratio == float('inf'):
            ratio = 5  # Cap for visualization purposes

        ratio_data.append({'country': country, 'ratio': ratio})

    ratio_df = pd.DataFrame(ratio_data)
    ratio_df = ratio_df.sort_values('ratio', ascending=False)

    sns.barplot(data=ratio_df, x='country', y='ratio', ax=axes[1, 1])
    axes[1, 1].set_title('Challenge to Opportunity Ratio by Country')
    axes[1, 1].set_xlabel('Country')
    axes[1, 1].set_ylabel('Ratio (Challenges / Opportunities)')
    axes[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig('country_statistics.png')

    return country_stats, fig


# Function to create a combined challenge and opportunity map with layers
def create_detailed_heatmap(routes, analysis_results, pois):
    """Create a detailed heatmap with separate layers for each challenge and opportunity"""
    # Create base map
    m = folium.Map(location=[44.0, 17.5], zoom_start=7, tiles='CartoDB positron')

    # Add measure control
    m.add_child(MeasureControl())

    # Add route layers
    route_group = folium.FeatureGroup(name="Routes", show=True)
    for route in routes:
        points = [(p[0], p[1]) for p in route['points']]
        folium.PolyLine(
            points,
            color='blue',
            weight=3,
            opacity=0.7,
            tooltip=f"Route: {route['file']}"
        ).add_to(route_group)
    route_group.add_to(m)

    # Create separate layers for each challenge
    challenge_types = ['steep_terrain', 'remote_area', 'border_crossing', 'high_elevation']
    challenge_names = ['Steep Terrain', 'Remote Areas', 'Border Crossings', 'High Elevation']
    challenge_colors = ['red', 'purple', 'blue', 'orange']

    for idx, challenge_type in enumerate(challenge_types):
        challenge_name = challenge_names[idx]
        challenge_color = challenge_colors[idx]

        # Extract points with this challenge
        points = []
        for result in analysis_results:
            if result['challenges'][challenge_type]:
                points.append([result['lat'], result['lon'], 1])

        if points:
            challenge_layer = HeatMap(
                points,
                name=f"Challenge: {challenge_name}",
                radius=12,
                max_zoom=13,
                gradient={0.4: 'blue', 0.65: 'yellow', 1: challenge_color},
                show=False
            )
            challenge_layer.add_to(m)

    # Create separate layers for each opportunity
    opportunity_types = ['scenic_view', 'cultural_proximity', 'trail_connectivity', 'local_infrastructure']
    opportunity_names = ['Scenic Views', 'Cultural Sites', 'Trail Connectivity', 'Local Infrastructure']
    opportunity_colors = ['green', 'lightblue', 'yellow', 'teal']

    for idx, opportunity_type in enumerate(opportunity_types):
        opportunity_name = opportunity_names[idx]
        opportunity_color = opportunity_colors[idx]

        # Extract points with this opportunity
        points = []
        for result in analysis_results:
            if result['opportunities'][opportunity_type]:
                points.append([result['lat'], result['lon'], 1])

        if points:
            opportunity_layer = HeatMap(
                points,
                name=f"Opportunity: {opportunity_name}",
                radius=12,
                max_zoom=13,
                gradient={0.4: 'green', 0.65: 'yellow', 1: opportunity_color},
                show=False
            )
            opportunity_layer.add_to(m)

    # Add POI clusters by type
    poi_types = set(poi['type'] for poi in pois)
    for poi_type in poi_types:
        poi_group = folium.FeatureGroup(name=f"POI: {poi_type.capitalize()}", show=False)
        for poi in pois:
            if poi['type'] == poi_type:
                folium.Marker(
                    location=[poi['lat'], poi['lon']],
                    tooltip=poi['name'],
                    icon=folium.Icon(color=poi['color'], icon=poi['icon'])
                ).add_to(poi_group)
        poi_group.add_to(m)

    # Add country boundaries
    for country, info in countries_info.items():
        bounds = info["bounds"]
        color = info["color"]

        # Create polygon from bounds
        coords = [
            [bounds[0], bounds[2]],  # SW
            [bounds[0], bounds[3]],  # SE
            [bounds[1], bounds[3]],  # NE
            [bounds[1], bounds[2]],  # NW
            [bounds[0], bounds[2]]  # SW again to close
        ]

        folium.Polygon(
            locations=coords,
            color=color,
            weight=2,
            fill=True,
            fill_opacity=0.1,
            fill_color=color,
            tooltip=country
        ).add_to(m)

    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; right: 50px; width: 220px; 
                border:2px solid grey; z-index:9999; background-color:white;
                padding: 10px; border-radius: 5px;">
      <p><b>TransDinarica Analysis</b></p>
      <hr>
      <p><b>Challenges:</b></p>
      <p><i style="background: red; width: 15px; height: 15px; display: inline-block;"></i> Steep Terrain</p>
      <p><i style="background: purple; width: 15px; height: 15px; display: inline-block;"></i> Remote Areas</p>
      <p><i style="background: blue; width: 15px; height: 15px; display: inline-block;"></i> Border Crossings</p>
      <p><i style="background: orange; width: 15px; height: 15px; display: inline-block;"></i> High Elevation</p>
      <hr>
      <p><b>Opportunities:</b></p>
      <p><i style="background: green; width: 15px; height: 15px; display: inline-block;"></i> Scenic Views</p>
      <p><i style="background: lightblue; width: 15px; height: 15px; display: inline-block;"></i> Cultural Sites</p>
      <p><i style="background: yellow; width: 15px; height: 15px; display: inline-block;"></i> Trail Connectivity</p>
      <p><i style="background: teal; width: 15px; height: 15px; display: inline-block;"></i> Local Infrastructure</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add layer control
    folium.LayerControl().add_to(m)

    # Add title
    title_html = '''
    <h3 align="center" style="font-size:16px"><b>TransDinarica Route: Detailed Analysis</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    return m



# Main function to run the entire analysis
def analyze_transdinarica():
    """Main function to run the full TransDinarica route analysis"""
    print("Starting TransDinarica route analysis...")

    # Load GPX files
    routes = load_gpx_files(gpx_files, working_project)
    print(f"Loaded {len(routes)} route segments from {len(gpx_files)} GPX files")

    # Generate POIs
    pois = generate_simulated_pois(routes, countries_info)
    print(f"Generated {len(pois)} simulated points of interest")

    # Analyze challenges and opportunities
    analysis_results = analyze_challenges_opportunities(routes, pois, countries_info)
    print(f"Analyzed {len(analysis_results)} route segments for challenges and opportunities")

    # Create visualizations
    print("Creating visualizations...")

    # Challenge/opportunity heatmap
    challenge_map = create_challenge_opportunity_map(analysis_results)
    challenge_map.save('transdinarica_challenge_opportunity_map.html')
    print("Created challenge/opportunity heatmap")

    # Country statistics
    country_stats, stats_fig = create_country_statistics(analysis_results, pois)
    print("Created country statistics visualization")

    # Detailed heatmap with layers
    detailed_map = create_detailed_heatmap(routes, analysis_results, pois)
    detailed_map.save('transdinarica_detailed_map.html')
    print("Created detailed interactive map")

    # Summary statistics
    summary_stats = create_summary_stats(routes, analysis_results, country_stats)
    print("Generated summary statistics")

    print("\nSummary of TransDinarica Route Analysis:")
    print(summary_stats)

    print("\nAnalysis complete! Output files:")
    print("- transdinarica_challenge_opportunity_map.html")
    print("- transdinarica_detailed_map.html")
    print("- country_statistics.png")
    print("- challenge_opportunity_ratio.png")

    return {
        'routes': routes,
        'pois': pois,
        'analysis_results': analysis_results,
        'country_stats': country_stats,
        'summary_stats': summary_stats
    }


def create_summary_stats(routes, analysis_results, country_stats):
    """Create high-level summary statistics for the entire TransDinarica route"""
    # Calculate basic route statistics
    total_distance = sum(route_distance(route['points']) for route in routes)

    elevation_gains = []
    elevation_losses = []
    max_elevations = []
    min_elevations = []

    for route in routes:
        points = route['points']
        if not points:
            continue

        elevations = [p[2] for p in points if p[2] is not None]
        if not elevations:
            continue

        # Calculate elevation changes
        gain = 0
        loss = 0
        for i in range(1, len(elevations)):
            diff = elevations[i] - elevations[i - 1]
            if diff > 0:
                gain += diff
            else:
                loss += abs(diff)

        elevation_gains.append(gain)
        elevation_losses.append(loss)
        max_elevations.append(max(elevations))
        min_elevations.append(min(elevations))

    # Calculate challenge and opportunity statistics
    challenge_counts = {
        'steep_terrain': 0,
        'remote_area': 0,
        'border_crossing': 0,
        'high_elevation': 0
    }

    opportunity_counts = {
        'scenic_view': 0,
        'cultural_proximity': 0,
        'trail_connectivity': 0,
        'local_infrastructure': 0
    }

    country_segment_counts = {}

    for result in analysis_results:
        # Count challenges
        for challenge, is_present in result['challenges'].items():
            if is_present:
                challenge_counts[challenge] += 1

        # Count opportunities
        for opportunity, is_present in result['opportunities'].items():
            if is_present:
                opportunity_counts[opportunity] += 1

        # Count country segments
        country = result['country']
        if country != 'Unknown':
            country_segment_counts[country] = country_segment_counts.get(country, 0) + 1

    # Create summary statistics dataframe
    summary = {
        'Total Distance (km)': total_distance,
        'Total Elevation Gain (m)': sum(elevation_gains),
        'Total Elevation Loss (m)': sum(elevation_losses),
        'Maximum Elevation (m)': max(max_elevations) if max_elevations else 0,
        'Minimum Elevation (m)': min(min_elevations) if min_elevations else 0,
        'Number of Countries': len([c for c, count in country_segment_counts.items() if count > 0]),
        'Total Border Crossings': challenge_counts['border_crossing'],
        'Steep Terrain Sections': challenge_counts['steep_terrain'],
        'Remote Areas': challenge_counts['remote_area'],
        'High Elevation Sections': challenge_counts['high_elevation'],
        'Scenic View Spots': opportunity_counts['scenic_view'],
        'Cultural Sites': opportunity_counts['cultural_proximity'],
        'Trail Junctions': opportunity_counts['trail_connectivity'],
        'Infrastructure Access Points': opportunity_counts['local_infrastructure']
    }

    summary_df = pd.DataFrame(list(summary.items()), columns=['Metric', 'Value'])

    # Create a summary plot
    plt.figure(figsize=(10, 6))

    challenge_ratio = sum(challenge_counts.values()) / (sum(opportunity_counts.values()) or 1)

    # Create a pie chart showing ratio of challenges to opportunities
    labels = ['Challenges', 'Opportunities']
    sizes = [sum(challenge_counts.values()), sum(opportunity_counts.values())]
    colors = ['#ff9999', '#66b3ff']
    explode = (0.1, 0)  # explode the 1st slice (Challenges)

    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(f'Challenge to Opportunity Ratio: {challenge_ratio:.2f}')

    plt.savefig('challenge_opportunity_ratio.png')

    return summary_df


# Function to create a high-level summary
# Run analysis if script is executed directly
if __name__ == "__main__":
    analyze_transdinarica()
