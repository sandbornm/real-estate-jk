import matplotlib.pyplot as plt
import geopandas

def load_data():
    # create a dictionary of {city_name: (latitude, longitude)} from the file called largest_metros.txt
    fpath = "./largest_metros.txt"
    with open(fpath, 'r') as f:
        # load lines from file
        data = f.readlines()
        # filter data by separating city and coords
        clean_data = [d.strip().split("-") for d in data]

    # init dictionary to hold our data { city : (lat, lon) }
    geo_df = {}
    for entry in clean_data:
        # add city name and latitude (N) and longitude (W) to the dictionary
        city_name = entry[0].strip()
        city_lat = float(entry[1].split(",")[0].strip())
        city_long = float(entry[1].split(",")[1].strip())
        geo_df[city_name] = (city_lat, city_long)
    print(geo_df)


def run():
    # read largest_metros.txt into a dictionary
    # of { city name :
    pass

if __name__ == "__main__": 
    load_data()
    states = geopandas.read_file('data/usa-states-census-2014.shp')
    type(states)
    states = states.to_crs("EPSG:3395")
    states.boundary.plot()
    plt.show()