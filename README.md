## Set up conda environment

- make sure conda is installed
- clone this repo
- cd into this repo `cd real-estate-jk`
- run `conda env create --file=env.yaml` to create the conda env and install dependencies
- run `conda activate re-study`. After running this, you should see '(re-study)' in the left side of the Git Bash prompt.
- now the environment is set up with the software packages we need to run the code

## Run code 
`python map-viz/main.py` the result should be cities and lat/long values in a python dictionary printed to the terminal, as well as a map of the US States outlined in blue.
