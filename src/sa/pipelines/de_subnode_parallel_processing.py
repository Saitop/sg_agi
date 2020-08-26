import logging

import pandas as pd
from typing import Dict
from kedro.pipeline import Pipeline, node

from sa.nodes.temperature_nodes import get_temp_data, choose_station
from multiprocessing.dummy import Pool


def generate_data_range(
        start_date: str,
        end_date: str,
):
    dates_to_download = {
        str(dt.date()): True
        for dt in pd.date_range(start_date, end_date)
    }
    return dates_to_download


def parallel_get_temp_data(dates_to_download: Dict[str, bool]) -> Dict[str, Dict]:
    logger = logging.getLogger('parallel_get_temp_data')

    def _get_temp_data(dt):
        logger.info(f"Start Download {dt}")
        try:
            date_data = get_temp_data(dt)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Failed Download {e}")
            date_data = None
        logger.info(f"Finish Download {dt}")
        return dt, date_data

    with Pool(10) as p:
        downloaded_data = p.map(_get_temp_data, dates_to_download.keys())

    downloaded_data_dict = dict(downloaded_data)

    return downloaded_data_dict


def parallel_choose_station(
        downloaded_data_dict: Dict,
        station_id: str,
):
    logger = logging.getLogger('parallel_get_temp_data')

    def _choose_station(item):
        dt = item[0]
        dt_data = item[1]
        logger.info(f"Start Choose Station {dt}")
        station_data = choose_station(dt_data, station_id)
        logger.info(f"Finish Choose Station {dt}")
        return dt, station_data

    with Pool(10) as p:
        downloaded_station_data = p.map(_choose_station, downloaded_data_dict.items())

    return dict(downloaded_station_data)


def create_pipeline():
    return Pipeline([
        node(
            generate_data_range,
            inputs=['params:start_date', 'params:end_date'],
            outputs='dates_to_download'
        ),
        node(
            parallel_get_temp_data,
            inputs='dates_to_download',
            outputs='downloaded_dates'
        ),
        node(
            parallel_choose_station,
            inputs=['downloaded_dates', 'params:station_id'],
            outputs='downloaded_station_data'
        )
    ])
