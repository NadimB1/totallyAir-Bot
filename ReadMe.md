# Air Quality Analysis Project
This project provides an in-depth analysis of air quality, focusing on various pollutants and gases. The analysis leverages multiple data sources, including image data representing pollutant dispersion and CSV files containing gas information. The goal is to send to users prediction of the air quality of the next day in Paris

## Getting Started
Follow these steps to set up the project on your local machine for development and testing purposes.

## Prerequisites
The project is written in Python and requires the following libraries:

- **pandas**: For data manipulation and analysis, providing data structures and operations for numerical tables and time series.
- **numpy**: Supports large, multi-dimensional arrays and matrices, along with a collection of mathematical functions.
- **matplotlib**: A plotting library for creating static, animated, and interactive visualizations.
- **Pillow (PIL)**: An open-source Python Imaging Library that adds image processing capabilities.
- **geopandas**: Makes working with geospatial data in Python easier, extending pandas to allow spatial operations on geometric types.
- **rasterio**: For reading and writing geospatial raster data.
- **shapely**: For manipulating and analyzing planar geometric objects.
- **pyproj**: A Python interface to the PROJ library for cartographic projections and coordinate transformations.

You can install these packages using pip:

```pip install pandas numpy matplotlib pillow geopandas rasterio shapely pyproj```

# Running the Scripts 
The primary script for this project is main.py. This script performs the following tasks:

Downloads images of pollutants from a specified URL. 
Processes the downloaded images, 
including cropping and model training. 
Downloads and saves pollen data from a specified URL. 
Downloads and merges gas data. 
Processes gas data to extract useful information. 
Conducts image analysis on a specific image using a GeoJSON file for geographic information. 

To run the script, navigate to the directory containing main.py and use the following command:

```python main.py```

Please note that the paths and URLs used in the script are specific to the original environment. Adjust these paths and URLs as needed for your setup.

# Outputs 
The scripts generate various outputs, including:

Cropped images that shows the prediction of tomorrow. Trained models for further analysis or prediction tasks. Tomorrow's prediction for the air quality in details CSV files with data on the presence of various gases and pollen in the air. These outputs will be saved to directories specified in the scripts.

# License 
Proprietary to a collaboration between Nadim BEN KHALIFA and Sofiane OULD AMARA.

# Acknowledgments
OpenAI for their GPT-3 model, which assisted in writing the code for this project. 
The Python community for providing an excellent ecosystem for data analysis and machine learning.