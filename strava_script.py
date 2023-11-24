# Copyright 2023-present Ryan Balshaw
"""
Main file for testing.
"""

import os

import numpy as np
import scipy.stats as scistats
from matplotlib import pyplot as plt

import NYARPR.StravaVisualiser as SV

if __name__ == "__main__":
    # https: // www.strava.com / oauth / authorize?client_id = 87007 & response_type = code & redirect_uri = http: // localhost / exchange_token & approval_prompt = force & scope = profile:read_all, activity: read_all

    env_path = os.path.join(os.getcwd(), "user_information.env")

    SV.get_important_tokens(
        env_path,
        access_code="c3e97fa74143d9326a0ed5010805dfb971e8d22f",
        overwrite_old=False,
    )

    # print(SV.get_env_variables(env_path))

    # df = SV.get_activities(env_path)

    # df.to_csv('strava_activities.csv')

    # TODO
    # Create a get_latest_activity_code function - done
    # Create a get all user information function - done
    # Visualise it all on one grid - use matplotlib!

    SV.check_tokens(env_path)

    # SV.get_cumulative_information(env_path)

    act_recent = SV.get_latest_activity_code(
        env_path, activity_type="Run", date_range=[]
    )
    Path = SV.get_activity_stream(env_path, act_recent)

    t = np.array(Path["time.data"].iloc[0]) / 60
    hrt = Path["heartrate.data"].iloc[0]
    lat_lng = np.array(Path["latlng.data"].iloc[0])
    alt = Path["altitude.data"].iloc[0]

    # Visualise heart rate trend
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(t, hrt, color="b")
    ax[0].set_ylabel("heartrate (BPM)")

    ax[1].plot(t, alt, color="k")
    ax[1].set_ylabel("Altitude (metres)")

    for axs in ax:
        axs.grid()
        axs.set_xlabel("Time (minutes)")
    plt.show()

    plt.figure()

    counts, bins = np.histogram(hrt, density=True, bins=50)
    plt.hist(bins[:-1], bins, weights=counts, color="b", alpha=0.6)

    kde = scistats.gaussian_kde(hrt)
    xx = np.linspace(np.min(hrt), np.max(hrt), 100)
    plt.plot(xx, kde(xx), color="r", linestyle="--")
    plt.xlabel("heartrate (BPM)")
    plt.ylabel("Density")
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(lat_lng[:, 0], lat_lng[:, 1], color="b")
    plt.grid()
    plt.xlabel("Latitude")
    plt.ylabel("Longitude")
    plt.show()
