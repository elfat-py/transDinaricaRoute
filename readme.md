# 🏔️ TransDinarica Route Analysis

This project analyzes the **TransDinarica** bikepacking route using real GPX data.

It provides:
# TODO
- 📊 Statistics for each route
- 📍 Interactive maps
- 📈 Elevation and distance analysis
- 🔥 Difficulty scores
- 🧗‍♂️ Identification of the toughest uphill sections
- 🌡️ Heatmaps and visualizations

---

## 📂 Project Structure

| File/Folder                   | Description |
|:------------------------------|:------------|
| `transdinarica.ipynb`         | Main Jupyter Notebook for the full analysis |
| `assets/`                     | Folder containing GPX tracks |
| `transdinarica_map.html` TODO | Interactive map generated |
| `plots/` TODO                 | Generated elevation profiles and heatmaps (optional) |
| `README.md`                   | This file |

---
# TODO
## 🛠️ How to Run

1. Install required packages:

    ```bash
    pip install gpxpy folium pandas geopy matplotlib
    ```

2. Make sure your GPX files are stored in a folder (e.g., `gpx_files/`).

3. Open and run the Jupyter Notebook:

    ```bash
    jupyter notebook Transdinarica_Analysis.ipynb
    ```

4. The notebook will:
    - Parse all `.gpx` files
    - Visualize routes on an interactive map
    - Analyze elevation and distance
    - Calculate Difficulty Index
    - Detect and plot the Toughest Sections
    - Export an HTML interactive map

---

## 📊 What the Analysis Includes

### 1. Parsing and Visualizing Routes
- Routes loaded using **gpxpy**
- Routes drawn with **Folium** map
- Color-coded sections for steepness (optional)

### 2. Statistics per Route
- Total Distance (km)
- Total Elevation Gain (m)
- Maximum and Minimum Altitude
- Difficulty Index (Elevation Gain per 100 km)

### 3. Difficulty Index
- A normalized metric of "how hard" a route is based on climbing.

### 4. Toughest Uphill Sections
- Finds the steepest continuous climb (~1 km windows)
- Highlights them on the map in **red**

### 5. Heatmaps (optional extension)
- Create heatmaps of route density or difficulty by GPS point clustering.

---

## 📌 Key Concepts

| Metric | Meaning |
|:----|:----|
| **Difficulty Index** | Elevation gain normalized per 100 km distance |
| **Toughest Sections** | Parts with the highest elevation gain over 1 km |
| **Interactive Map** | Easy to zoom and explore routes visually |
| **Heatmaps** | Show concentration or difficulty intensities |

---

## 📋 Notes

- Make sure all `.gpx` files are correctly placed in the specified folder.
- This analysis is highly extensible: you can add weather layers, surface type annotations, or points of interest (POIs) later if needed.

---

## 📬 Future Improvements

[//]: # TODO ()
- Cluster analysis for **remote vs urban** challenges
- Weather API integration for **forecast challenges**
- Segment-based scoring (per country)
- Surface roughness detection if detailed GPX is available (trail vs asphalt)

---

