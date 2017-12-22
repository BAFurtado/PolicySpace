import json
import pandas as pd
from osgeo import ogr
from shapely.geometry import shape


def prepare_shapes(geo):
    """Loads shape data for municipalities"""

    # list of States codes in Brazil
    states_codes = pd.read_csv('input/STATES_ID_NUM.csv', sep=';', header=0, decimal=',')

    # creating a list of code number for each state to use in municipalities selection
    processing_states_code_list = []
    for item in geo.states_on_process:
        processing_states_code_list.append((states_codes['nummun'].loc[states_codes['codmun'] == item]).values[0])

    # load the shapefiles
    full_region = ogr.Open('input/shapes/mun_ibge_2014_latlong_wgs1984_fixed.shp')
    urban_region = ogr.Open('input/shapes/URBAN_IBGE_ACPs.shp')

    urban = []
    urban_mun_codes = []
    # selecting the urban areas for each municipality
    for state in processing_states_code_list:
        for acp in geo.processing_acps:
            # for all states different from Federal district (53 code)
            for mun_reg in range(urban_region.GetLayer(0).GetFeatureCount()):
                if urban_region.GetLayer(0).GetFeature(mun_reg).GetField(5) == str(acp) and \
                                urban_region.GetLayer(0).GetFeature(mun_reg).GetField(3) == str(state) :
                    urban.append(urban_region.GetLayer(0).GetFeature(mun_reg))
                    urban_mun_codes.append(urban_region.GetLayer(0).GetFeature(mun_reg).GetField(1))

    urban = {
        item.GetField(1): shape(json.loads(item.geometry().ExportToJson()))
        for item in urban
    }

    my_shapes = []
    # selection of municipalities boundaries
    # running over the states in the list
    for mun_id in urban_mun_codes:
        # for all states different from Federal district (53 code)
        for mun_reg in range(full_region.GetLayer(0).GetFeatureCount()):
            if full_region.GetLayer(0).GetFeature(mun_reg).GetField(1) == mun_id:
                my_shapes.append(full_region.GetLayer(0).GetFeature(mun_reg))

    return urban, my_shapes
