import os # for operating system
import subprocess
import sys

try:
    import numpy as np
except ImportError:
    print("numpy is not installed, installing now")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
    import numpy as np

try:
    import pandas as pd
except ImportError:
    print("pandas is not installed, installing now")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

try:
    import folium
except ImportError:
    print("folium is not installed, installing now")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "folium"])
    import folium


# get the coordinates of cities from the textfile
def get_metro_coords_dict():

    # ADD MORE CITIES TO THIS FOLLOW IN THE FORMAT:
    # City:N. Lat,W. Long (see largest_metros.txt) 
    metro_loc_file = "largest_metros.txt"

    print(f"creating metro name to coordinate lookup table from file {metro_loc_file}...")
    metro_coords_lines = open(metro_loc_file, 'r').readlines()

    metro_cities = [mcl.split(":")[0].strip() for mcl in metro_coords_lines]
    metro_coord_lats = [float(mcl.split(":")[1].split(",")[0].strip()) for mcl in metro_coords_lines]
    metro_coord_lons = [float(mcl.split(":")[1].split(",")[1].strip()) for mcl in metro_coords_lines]

    metro_lat_lon = [list(ll) for ll in list(zip(metro_coord_lats, metro_coord_lons))]
    metro_coords_dict = {metro_cities[i] : metro_lat_lon[i] for i in range(len(metro_cities))}

    #print(f"metro_coords_dict = {metro_coords_dict}")

    return metro_coords_dict


# read the excel to file dataframe
def read_excel_file_to_dataframe(
    filename,
    existing_lat_key,
    existing_lon_key,
    construction_lat_key,
    construction_lon_key,
    num_units_key
):
    # change the filename here and make sure that it is in the same folder as this file "driver.py"
    # the parent folder here is "real-estate-jk" and the path to the file is: ./real-estate-jk/cities_locations.xlsx
    
    # CHANGE FILENAME HERE - make sure it is in the same folder as this "driver.py" file
    # most likely you want to right click on the file name in the left panel and then click "copy path" and paste it below
    #filename = "./cities_locations.xlsx"  # replace with your filename
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    print(f"reading excel file to form dataframe from file: {filename}")
    company_name_df_dict = pd.read_excel(filepath, engine='openpyxl', sheet_name=None)  # sheet_name=None is to handle multiple sheets

    company_df_clean_dict = {}

    for company_name, property_df in company_name_df_dict.items():
        print(f"current company: {company_name}")
        #print(type(property_df))

        # set a lookup for the company data
        company_df_clean_dict[company_name] = {}

        # remove nans
        clean_property_df = property_df.dropna()
        #print(clean_property_df.head())

        # split into construction and existing properties
        clean_construction_df = clean_property_df[[construction_lat_key, construction_lon_key, num_units_key]]
        clean_existing_df = clean_property_df[[existing_lat_key, existing_lon_key]]

        # add the cleaned dataframes to the dictionary
        company_df_clean_dict[company_name]['construction'] = clean_construction_df
        company_df_clean_dict[company_name]['existing'] = clean_existing_df

    return company_df_clean_dict


def is_within_threshold(distance, threshold):
    """
    simply return whether the distance is less than or equal to threshold which is used
    as a boolean to update the counting of construction units
    """
    return distance <= threshold


def get_distance_between_points(lat1, lon1, lat2, lon2, unit='mi'):
    """
    calculate the distance in 'units' of the input coordinates given by 'lat1/2' and lon1/2'.
    If the resulting distance falls within 'threshold' then we are going to increment the
    encroach count by the number of units of the building under construction. If the units have already
    been accounted for, then the sum only increments by 1 (is correct? why?)
    """
    assert unit in ['mi', 'km'], f"unit {unit} is not valid. Must be mi or km"

    #print("in get_distance_between points")
    # calculate the distance between 2 coordinate pairs (lat N, lon W) in specified units
    import geopy.distance

    coords1 = [lat1, lon1]  # type tuple
    coords2 = [lat2, lon2]  # type tuple

    #print(f"coords1 = {coords1}")
    #print(f"coords2 = {coords2}")

    if unit == 'mi':
        distance = geopy.distance.geodesic(coords1, coords2).miles
    elif unit == 'km':
        distance = geopy.distance.geodesic(coords1, coords2).km

    #print(f"distance from {coords1} to {coords2} is {distance} {unit}")

    return distance

    

def get_city_from_coords(metro_coords, test_lat, test_lon, threshold=50):
    """
        get the name of the city that is within "threshold" miles of the location
        at test_lat, test_lon, or otherwise the closest if none are within the threshold

        iterate through the existing metro_coords_dict and find the minimum distance, look up and return city name
        based on this min
    """

    #print("in get city from coords")

    dists = []
    #inside = [False * len(metro_coords)]

    for city_name, coords in metro_coords.items():

        #print(f"city_name = {city_name}")
        metro_lat, metro_lon = coords
        #print(f"metro_lat = {metro_lat}")
        #print(f"metro_lon = {metro_lon}")
        distance = get_distance_between_points(test_lat, test_lon, metro_lat, metro_lon)

        dists.append(distance)

        # falls_within = is_within_threshold(distance, threshold)
        # if falls_within:
        #     inside[i] = True
            # return city_name
    
    # identify the closest city by index of minimal 
    dists = np.array(dists)
    #print(f"dists = {dists}")
    min_idx = np.argmin(dists)
    #print(f"min_idx = {min_idx} with dist = {dists[min_idx]}")
    #min_idx = dists.index(min(dists))
    min_dist = dists[min_idx]
    closest_city = list(metro_coords.keys())[min_idx]

    print(f"closest metro to ({test_lat }, {test_lon}) is {closest_city} with distance {min_dist} mi")

    return min_dist, closest_city

def get_str_from_coord(lat, lon):
    return ",".join([str(lat), str(lon)])


def run(company_property_dict,
        metro_coords_dict,
        existing_lat_key,
        existing_lon_key,
        construction_lat_key,
        construction_lon_key,
        num_units_key,
        build_threshold=1,
        city_threshold=30,
        variant='company'):
    
    """
        the main entrypoint for the analysis. Reads over the existing and construction
        dataframes and tracks which cities have interferences based on preset thresholds
        this function populates multiple dictionaries of interest, outlined below
    """

    # describes the analysis of interest. Company keeps interferences organized by company
    # total combines all interferences and organizes by city irrespective of company
    assert variant in ['company', 'total']

    print(f"now running property distance analysis variant: {variant}")

    total_overall_interferences = 0

    all_company_analysis_results = {}

    for company_name, property_df_dict in company_property_dict.items():

        # company name string
        # property_df_dict = { 'construction': df, 'existing': df }

        print(f"analyzing {company_name}")

        # top level data entry for each company
        all_company_analysis_results[company_name] = {
            'total_company_interferences': 0,  # rolling sum across all property owned by company
            'construction_sites_counted': {},  # {(lat, lon) : bool is_counted } prevent double counting properties
            'units_wip_by_city': {},  # {city: int}
            'interferences_by_city': {},  # track interferences by city { city: { lat_lon (of construction site): [((elat, elon), dist, num_units)]}}
            'all_distances': [],  # list of all distances between construction and existing sites
            'interference_count_by_city': {}, # track the number of interferences by city { city: int }
            'total_units_wip': 0 # total units under construction for company
        }


        # init interferences by city and total wip units by city
        for city_name, coords in metro_coords_dict.items():

            all_company_analysis_results[company_name]['units_wip_by_city'][city_name] = 0
            all_company_analysis_results[company_name]['interferences_by_city'][city_name] = {}
            all_company_analysis_results[company_name]['interference_count_by_city'][city_name] = 0

        construction_df = property_df_dict['construction']
        existing_df = property_df_dict['existing']

        # initialize the construction sites counted dictionary
        for ctup in construction_df.itertuples():
            #print(f"row tuple: {ctup} type row: {ctup.CLat}")
            construction_lat = ctup.CLat
            construction_lon = ctup.CLon

            construction_coord_str = ",".join([str(construction_lat), str(construction_lon)])

            all_company_analysis_results[company_name]['construction_sites_counted'][construction_coord_str] = False
    
        # iterate over the actual construction and existing building data pairwise to get distances
        for cxn_index, cxn_row in construction_df.iterrows():

            construction_lat = cxn_row[construction_lat_key]
            construction_lon = cxn_row[construction_lon_key]
            
            construction_coord_str = get_str_from_coord(construction_lat, construction_lon)

            construction_site_was_counted = all_company_analysis_results[company_name]['construction_sites_counted'][construction_coord_str]
        
            # only make the comparison if the construction site hasn't been counted
            if construction_site_was_counted is False:

                # get the # construction units wip
                num_units_wip = cxn_row[num_units_key]
                print(f"num units wip: {num_units_wip}")

                # the construction has not been counted, so look at the existing units nearby
                print(f"construction site {construction_coord_str} has not been counted yet, and will be checked now")
                units_counted = False
                for exst_index, exst_row in existing_df.iterrows():
                    
                    #print(f"existing {exst_row}")
                    # obtain the coordinates from current df location
                    existing_lat = exst_row[existing_lat_key]
                    existing_lon = exst_row[existing_lon_key]

                    #existing_coord = (existing_lat, existing_lon)

                    # get the location of the city closest to the average of the existing and construction locations
                    avg_lat = (construction_lat + existing_lat) / 2
                    avg_lon = (construction_lon + existing_lon) / 2

                    # get the closest city based on the average of the existing and construction locations
                    min_dist, closest_city = get_city_from_coords(metro_coords_dict, avg_lat, avg_lon)
                    is_within_city = is_within_threshold(min_dist, city_threshold)
                    print(f"is within city: {is_within_city} with distance {min_dist} and threshold {city_threshold}")
                    if is_within_city:  # we are in a city of interest
                    
                        print(f"existing lat {existing_lat} lon {existing_lon} is closest to {closest_city}")
                        print(f"construction lat {construction_lat} lon {construction_lon} is closest to {closest_city} with threshold {city_threshold}")
                        distance_btwn_construction_and_existing = get_distance_between_points(
                            existing_lat,
                            existing_lon,
                            construction_lat,
                            construction_lon
                        )

                        is_within_construction = is_within_threshold(distance_btwn_construction_and_existing, build_threshold)
                        print(f"is_within_construction: {is_within_construction} with distance {distance_btwn_construction_and_existing} and threshold {build_threshold}")

                        if is_within_construction:  #and all_company_analysis_results[company_name]['construction_sites_counted'][construction_coord_str] is False:  # we have a construction interference with an existing building

                            print(f"interference in city: {closest_city}")

                            # mark construction site as visited to prevent double counting of units in progress
                            all_company_analysis_results[company_name]['construction_sites_counted'][construction_coord_str] = True

                            # all construction coords that are already counted
                            interf_by_coord_keys = all_company_analysis_results[company_name]['interferences_by_city'][closest_city].keys()
                            
                            existing_coord_str = get_str_from_coord(existing_lat, existing_lon)

                            coord_units_dist_entry_str = ":".join([existing_coord_str, str(int(num_units_wip)), str(distance_btwn_construction_and_existing)])

                            if construction_coord_str not in interf_by_coord_keys:  # check if intereference list exists
                                all_company_analysis_results[company_name]['interferences_by_city'][closest_city][construction_coord_str] = [coord_units_dist_entry_str]
                            else:  # the list of interferences already exists, add to it
                                all_company_analysis_results[company_name]['interferences_by_city'][closest_city][construction_coord_str].append(coord_units_dist_entry_str)

                            # update the overall and citywise units interfering count
                            total_overall_interferences += 1
                            all_company_analysis_results[company_name]['total_company_interferences'] += 1

                            # add the distance to the list of all distances
                            all_company_analysis_results[company_name]['all_distances'].append(distance_btwn_construction_and_existing)

                            # update the number of interferences and units wip by city 
                            all_company_analysis_results[company_name]['interference_count_by_city'][closest_city] += 1
                            #if construction_coord_str in units_wip_by_city_keys:
                            
                            # update the interfering units for the city
                            if not units_counted:
                                all_company_analysis_results[company_name]['total_units_wip'] += num_units_wip
                                all_company_analysis_results[company_name]['units_wip_by_city'][closest_city] += int(num_units_wip)
                                units_counted = True
                            else:
                                print("units already counted, skipping")
                        else:
                            print("in city but not a construction interference")
                    else:
                        print(f"skipping existing unit: ({existing_lat}, {existing_lon}) since it is not in the city threshold")

            else:
                print(f"skipping construction site: ({construction_lat}, {construction_lon}) since it was already counted")
                continue
    print("analysis complete")

    return all_company_analysis_results


def summarize_analysis(all_company_analysis_results):
    """
        get the average distance between existing and construction sites, sort by city

        all_company_analysis_results[company_name] = {
            'total_company_interferences': 0,  # rolling sum across all property owned by company
            'construction_sites_counted': {},  # {(lat, lon) : bool is_counted } prevent double counting properties
            'units_wip_by_city': {},  # track units in progress for company by city
            'interferences_by_city': {},  # track interferences by city { city: { lat_lon (of construction site): [((elat, elon), dist, num_units)]}}
            'all_distances': [],  # list of all distances between construction and existing sites
            'interference_count_by_city': {} # track the number of interferences by city { city: int }
        }

    """
    summary_lines = []

    for company, company_results in all_company_analysis_results.items():

        summary_lines.append(f"======== results for company: {company} ========")
        summary_lines.append("total interferences: " + str(company_results['total_company_interferences']))
        #summary_lines.append("total units in progress: " + str(sum(company_results['units_wip_by_city'].values())))
        summary_lines.append("average distance between existing and construction sites: " + str(np.average(np.asarray(company_results['all_distances']))) + " miles")
        summary_lines.append("standard deviation of distance between existing and construction sites: " + str(np.std(np.asarray(company_results['all_distances']))) + " miles")
        summary_lines.append("city with most interferences: " + max(company_results['interference_count_by_city'], key=company_results['interference_count_by_city'].get))
        summary_lines.append("city with least interferences: " + min(company_results['interference_count_by_city'], key=company_results['interference_count_by_city'].get))
        #city_to_cton_sites = {k: v for k, v in company_results['units_wip_by_city'].items()}
        # print(f"city to cton sites: {city_to_cton_sites} ")
        # city_to_total_units = {k: sum(v.values()) for k, v in city_to_cton_sites.items()}
        # print(f"city to total units: {city_to_total_units} ")
        summary_lines.append("city with most units in progress: " + max(company_results['units_wip_by_city'], key=company_results['units_wip_by_city'].get))
        summary_lines.append("city with least units in progress: " + min(company_results['units_wip_by_city'], key=company_results['units_wip_by_city'].get))
        summary_lines.append("\n\n")
    
    # write summary lines to text file
    fname = "./analysis_summary.txt"
    with open(fname, 'w') as f:
        f.write("\n".join(summary_lines))
    print(f"wrote to {fname}")


def write_results_to_json(all_company_analysis_results):
    import json
    # write each company's results to json named after the company with indent of 4
    for company, company_results in all_company_analysis_results.items():
        fname = f"./companies/{company}_analysis_results.json"
        with open(fname, 'w') as f:
            json.dump(company_results, f, indent=4)
        print(f"wrote to {fname}")


def map_all_results(metro_coord_dict,
                    company_locs_dict,
                    construction_lat_key,
                    construction_lon_key, 
                    existing_lat_key, 
                    existing_lon_key,
                    build_threshold=1,
                    city_threshold=30):
    """
        This function uses information produced from the run function in order
        to visualize the distances between the cities of interest;
        Make sure to plot all construction and all existing draw small circles around
    """
    print("in map all results function")

    m = folium.Map(zoom_start=8, tiles='OpenStreetMap', csr="EPSG4326")

    for city, coord in metro_coord_dict.items():
        city_lat = coord[0]
        city_lon = coord[1]
        # plot 1mi radius around location
        folium.Circle(
            location= [city_lat, city_lon],
            radius=1609 * city_threshold,
            popup= f"{city_threshold} mi radius",
            color='green',
            fill=False,
        ).add_to(m)

    for company, company_locs in company_locs_dict.items():

        construction_df = company_locs['construction']
        for c_index, crow in construction_df.iterrows():
            construction_lat = crow[construction_lat_key]
            construction_lon = crow[construction_lon_key]
            folium.Marker(
                location= [round(construction_lat, 3), round(construction_lon, 3)],
                #radius=build_limit,
                fill=True,
                icon=folium.Icon(color='red', icon=''),
                popup= f"construction location ({construction_lat},{construction_lon})"   # f"{unit_count} units in progress",
            ).add_to(m)

        existing_df = company_locs['existing']
        for e_index, erow in existing_df.iterrows():

            # obtain the coordinates from current df location
            existing_lat = erow[existing_lat_key]
            existing_lon = erow[existing_lon_key]

            folium.Circle(
                location= [existing_lat, existing_lon],
                radius=1609 * build_threshold,
                popup= f"{build_threshold} mi radius",
                color='blue',
                fill=False,
            ).add_to(m)

    m.save("./all_analysis_map.html")
    
    return m

def zoom_save_map_by_location(map, metro_coords_dict):
    """ zoom the overall map to each of the metro coordinates in the metro_coords dict and save each snapshot
        by city name
    """
    print(metro_coords_dict)
    # for each city in metro_coords_dict, zoom the map to that location and save the map
    # for city, coord in metro_coords_dict.items():
    #     city_lat = float(coord[0])
    #     city_lon = float(coord[1])
    #     map.zoom_start = 12
    #     map.location = [city_lat, city_lon]
    #     map.save(f"./maps/{city}_analysis_map.html")








if __name__ == "__main__":

    """
        REPLACE THE NAMES OF THE EXCEL COLUMNS HERE AS NEEDED
    """
    # variable names to identify columns in the dataframes
    existing_lat_key = 'ELat' # existing latitudes column
    existing_lon_key = 'ELon' # existing longitudes column

    construction_lat_key = 'CLat' # construction latitudes column
    construction_lon_key = 'CLon'  # construction longitude key
    num_units_key = 'num units'

    build_threshold = 3  # distance from construction to any existing site to be considered an interference
    city_threshold = 50  # distance from current location to closest city to be considered further

    # replace with your filename
    filename = "./cities_locations.xlsx"

    # convert the excel file into a dataframe that is easier to process
    # the `company_locs_dict` is a dictionary of the form {company_name : {'construction': df, 'existing': df}}
    # each company has its own entry in this dictionary and each company entry has a construction and existing dataframe associated to it
    company_locs_dict = read_excel_file_to_dataframe(
        filename,
        existing_lat_key,
        existing_lon_key,
        construction_lat_key,
        construction_lon_key,
        num_units_key)

    # obtain the coordinates of each of 30 major metro cities (add to this list as needed)
    # format of the metro_coords_dict is {(lat, lon) : city} track city locations by their coordinates
    # this is used later as a cheap reference to other city locations without 3rd party dependencies
    metro_coords_dict = get_metro_coords_dict()

    # run the analysis 
    all_company_analysis_results = run(
        company_locs_dict,
        metro_coords_dict,
        existing_lat_key,
        existing_lon_key,
        construction_lat_key,
        construction_lon_key,
        num_units_key,
        build_threshold=build_threshold,
        city_threshold=city_threshold
    )

    summarize_analysis(all_company_analysis_results)

    write_results_to_json(all_company_analysis_results)

    print("mapping results")
    
    # map the locations
    final_map = map_all_results(
        metro_coords_dict,
        company_locs_dict,
        construction_lat_key,
        construction_lon_key, 
        existing_lat_key, 
        existing_lon_key,
        build_threshold=build_threshold,
        city_threshold=city_threshold
    )
    
    # # save each zoomed map by city
    # zoom_save_map_by_location(final_map, metro_coords_dict)

