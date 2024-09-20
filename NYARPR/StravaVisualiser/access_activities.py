# Copyright 2023-present Ryan Balshaw
"""
Functions used to get a list of all Strava activities
"""

import json
import os

import pandas as pd
import requests

from .access_information import get_env_variables

# def get_activities(env_file_path):
#     """
#     A function that gets the activities for a spec
#     Parameters
#     ----------
#     env_file_path :
#
#     Returns
#     -------
#
#     """
#     # Get user tokens
#     env_dict = get_env_variables(env_file_path)
#
#     url = "https://www.strava.com/api/v3/activities"
#
#     # Get first page of activities with all fields
#     r = requests.get(f"{url}?access_token={env_dict['ACCESS_TOKEN']}")
#
#     # Columns that I want
#
#     return pd.json_normalize(r.json())


def get_cumulative_information(env_file_path: str):
    """
    A function that gets the rolled-up statistics and totals for an athlete.

    Parameters
    ----------
    env_file_path : str
        Path to the 'user_information.env' file.
    Returns
    -------
    pandas.DataFrame instance
    """

    tmp_dir_path = os.path.join(os.getcwd(), "tmp")
    json_path = os.path.join(tmp_dir_path, "strava_tokens.json")
    env_dict = get_env_variables(env_file_path)

    header_dict = {"Authorization": f"Bearer {env_dict['ACCESS_TOKEN']}"}

    with open(json_path) as check:
        user_tokens = json.load(check)

    url = f"https://www.strava.com/api/v3/athletes/{user_tokens['athlete']['id']}/stats"

    # Get the response
    response = requests.get(url, headers=header_dict)

    return pd.json_normalize(response.json())


def get_latest_activity_code(env_file_path: str, activity_type: str = ""):
    """
    A function that returns the latest activity code for a specific activity.

    Parameters
    ----------
    env_file_path : str
        Path to the 'user_information.env' file.

    activity_type : str
        Code that needs to match an ActivityType from StravaAPI

    Returns
    -------
    The most recent activity code from the specified type.
    """
    # Get the environment variables
    env_dict = get_env_variables(env_file_path)

    # Taken from the Strava website
    available_activities = (
        "AlpineSki, BackcountrySki, Canoeing, Crossfit, "
        "EBikeRide, Elliptical, Golf, Handcycle, Hike, "
        "IceSkate, InlineSkate, Kayaking, Kitesurf, "
        "NordicSki, Ride, RockClimbing, RollerSki, "
        "Rowing, Run, Sail, Skateboard, Snowboard, "
        "Snowshoe, Soccer, StairStepper, StandUpPaddling, "
        "Surfing, Swim, Velomobile, VirtualRide, VirtualRun, "
        "Walk, WeightTraining, Wheelchair, Windsurf, Workout, Yoga"
    )

    act_list = available_activities.strip().split(",")
    act_list = [act_list[i].strip() for i in range(len(act_list))]

    url = "https://www.strava.com/api/v3/athlete/activities"

    if activity_type in act_list:
        header_dict = {"Authorization": f"Bearer {env_dict['ACCESS_TOKEN']}"}

        page_cnt = 1
        found_flag = False

        while not found_flag:
            param_dict = {"activity": "read_all", "page": page_cnt, "per_page": 200}

            response = requests.get(url, headers=header_dict, params=param_dict)

            df_iter = pd.json_normalize(response.json())

            searched_df = df_iter.loc[df_iter["sport_type"] == activity_type]

            if searched_df.index.__len__() != 0:
                found_flag = True

            else:
                page_cnt += 1

            if page_cnt >= 5:
                print(
                    f"The search has looked through 1000 activities and has not found one record for activity={activity_type}. Stopping."
                )
                raise SystemExit

    else:
        print(f"Activity entered ({activity_type}) not recognised. Exiting.")
        raise SystemExit

    return searched_df["id"].iloc[0]


def get_activity_stream(env_file_path: str, activity_id: int):
    """
    A function that gets the activity stream for a specific activity code.

    Parameters
    ----------
    env_file_path : str
        Path to the 'user_information.env' file.

    activity_id : int
        The activity code to search for.

    Returns
    -------
    Pandas.DataFrame instance
    """
    # Get user tokens
    env_dict = get_env_variables(env_file_path)

    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    param_dict = {
        "keys": "distance,latlng,time,altitude,heartrate",
        "key_by_type": "true",
    }
    header_dict = {"Authorization": f"Bearer {env_dict['ACCESS_TOKEN']}"}

    # Get the response
    r = requests.get(url, headers=header_dict, params=param_dict)

    return pd.json_normalize(r.json())

    # lat_lng = np.array(Path['latlng.data'].iloc[0])
