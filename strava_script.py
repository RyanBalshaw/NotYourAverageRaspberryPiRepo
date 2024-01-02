# Copyright 2023-present Ryan Balshaw
"""
Main file for testing.
"""

import os
import webbrowser

import numpy as np
import scipy.stats as scistats
from matplotlib import pyplot as plt

import NYARPR.StravaVisualiser as SV

if __name__ == "__main__":
    env_path = os.path.join(os.getcwd(), "user_information.env")

    # Check to see if the environment variable file is fully defined

    if len(SV.get_env_variables(env_path)) < 4:  # Four variables are expected
        # Ask user for the client id
        client_id = SV.get_client_id(env_path)

        # Ask the user for the client secret
        client_secret = SV.get_client_secret(
            env_path
        )  # Don't actually need it, but oh well

        # Basic loading for client information
        webbrowser.open(
            rf"https://www.strava.com/oauth/authorize?client_id={client_id}"
            "&response_type=code&redirect_uri=http://localhost/"
            "exchange_token&approval_prompt=force&scope=profile:"
            "read_all,activity:read_all"
        )

        # Ask the user for their client id
        access_code_url = input("Please input the access code url\n--->:")

        # Get the important tokens used to access the user information
        SV.get_important_tokens(
            env_path,
            access_code_url=access_code_url,
            overwrite_old=True,
        )

        # Check the tokens
        SV.check_tokens(env_path)

    else:
        # Check the tokens
        SV.check_tokens(env_path)

    # print(SV.get_env_variables(env_path))

    # df = SV.get_activities(env_path)

    # df.to_csv('strava_activities.csv')

    # TODO
    # Create a get_latest_activity_code function - done
    # Create a get all user information function - done
    # Visualise it all on one grid - use matplotlib!

    # SV.get_cumulative_information(env_path)

    act_recent = SV.get_latest_activity_code(env_path, activity_type="Run")

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
