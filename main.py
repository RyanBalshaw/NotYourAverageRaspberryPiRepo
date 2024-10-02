# Copyright 2023-present Ryan Balshaw
"""
Main file for testing.
"""

import os
import webbrowser
from datetime import datetime

import matplotlib.font_manager as fm
import numpy as np
import scipy.stats as scistats
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

import NYARPR.StravaVisualiser as strava_vis

if __name__ == "__main__":
    env_path = os.path.join(os.getcwd(), "user_information.env")

    # Check to see if the environment variable file is fully defined

    if len(strava_vis.get_env_variables(env_path)) < 4:  # Four variables are expected
        # Ask user for the client id
        client_id = strava_vis.get_client_id(env_path)

        # Ask the user for the client secret
        client_secret = strava_vis.get_client_secret(
            env_path
        )  # Don't actually need it, but oh well

        # Basic loading for client information
        try:
            webbrowser.get()
            webbrowser.open(
                rf"https://www.strava.com/oauth/authorize?client_id={client_id}"
                "&response_type=code&redirect_uri=http://localhost/"
                "exchange_token&approval_prompt=force&scope=profile:"
                "read_all,activity:read_all"
            )

        except Exception:
            oauth_url = (
                rf"https://www.strava.com/oauth/authorize?client_id={client_id}"
                "&response_type=code&redirect_uri=http://localhost/"
                "exchange_token&approval_prompt=force&scope=profile:"
                "read_all,activity:read_all"
            )

            print("Please open the following URL in your web browser to authorize:")
            print(oauth_url)

        # Ask the user for their client id
        access_code_url = input("Please input the access code url\n--->:")

        # Get the important tokens used to access the user information
        strava_vis.get_important_tokens(
            env_path,
            access_code_url=access_code_url,
            overwrite_old=True,
        )

        # Check the tokens
        strava_vis.check_tokens(env_path)

    else:
        # Check the tokens
        strava_vis.check_tokens(env_path)

    # print(strava_vis.get_env_variables(env_path))

    # df = strava_vis.get_activities(env_path)

    # df.to_cstrava_vis('strava_activities.cstrava_vis')

    # TODO
    # Create a get_latest_activity_code function - done
    # Create a get all user information function - done
    # Visualise it all on one grid - use matplotlib!

    df_cumulative_info = strava_vis.get_cumulative_information(env_path)

    recent_activity_id = strava_vis.get_latest_activity_code(
        env_path, activity_type="Run"
    )

    df_recent_activity_stream = strava_vis.get_activity_stream(
        env_path, recent_activity_id
    )
    df_recent_activity_info = strava_vis.get_activity_info(env_path, recent_activity_id)

    t = np.array(df_recent_activity_stream["time.data"].iloc[0]) / 60
    hrt = df_recent_activity_stream["heartrate.data"].iloc[0]
    lat_lng = np.array(df_recent_activity_stream["latlng.data"].iloc[0])
    alt = df_recent_activity_stream["altitude.data"].iloc[0]

    # Visualise heart rate trend
    # fig, ax = plt.subplots(2, 1)
    # ax[0].plot(t, hrt, color="b")
    # ax[0].set_ylabel("heartrate (BPM)")
    #
    # ax[1].plot(t, alt, color="k")
    # ax[1].set_ylabel("Altitude (metres)")
    #
    # for axs in ax:
    #     axs.grid()
    #     axs.set_xlabel("Time (minutes)")
    # plt.show()
    #
    # plt.figure()
    #
    # counts, bins = np.histogram(hrt, density=True, bins=50)
    # plt.hist(bins[:-1], bins, weights=counts, color="b", alpha=0.6)
    #
    # kde = scistats.gaussian_kde(hrt)
    # xx = np.linspace(np.min(hrt), np.max(hrt), 100)
    # plt.plot(xx, kde(xx), color="r", linestyle="--")
    # plt.xlabel("heartrate (BPM)")
    # plt.ylabel("Density")
    # plt.grid()
    # plt.show()
    #
    # plt.figure()
    # plt.plot(lat_lng[:, 0], lat_lng[:, 1], color="b")
    # plt.grid()
    # plt.xlabel("Latitude")
    # plt.ylabel("Longitude")
    # plt.show()

    # Calculate gradient
    gradient = np.gradient(alt, t)

    # Set up Roboto font
    roboto_regular = fm.FontProperties(
        fname=os.path.join(os.getcwd(), "fonts", "roboto", "Roboto-Regular.ttf")
    )
    roboto_bold = fm.FontProperties(
        fname=os.path.join(os.getcwd(), "fonts", "roboto", "Roboto-Bold.ttf")
    )
    font_awesome = fm.FontProperties(
        fname=os.path.join(
            os.getcwd(), "icons", "font-awesome", "Font Awesome 6 Free-Regular-400.otf"
        )
    )
    font_awesome_brands = fm.FontProperties(
        fname=os.path.join(
            os.getcwd(),
            "icons",
            "font-awesome",
            "Font Awesome 6 Brands-Regular-400.otf",
        )
    )

    # Dracula-inspired color scheme
    bg_color = "#282a36"
    text_color = "#f8f8f2"
    accent_color = "#ff79c6"
    secondary_color = "#8be9fd"

    plt.rcParams.update(
        {
            "figure.facecolor": bg_color,
            "text.color": text_color,
            "axes.facecolor": bg_color,
            "axes.edgecolor": text_color,
            "axes.labelcolor": text_color,
            "xtick.color": text_color,
            "ytick.color": text_color,
        }
    )

    # Create the plot
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(
        2, 2, width_ratios=[4, 1], height_ratios=[2, 1], hspace=0.3, wspace=0.3
    )

    # Run path colored by gradient
    ax_path = fig.add_subplot(gs[0, :])
    scatter = ax_path.scatter(
        lat_lng[:, 1], lat_lng[:, 0], c=gradient, cmap="viridis", s=3, alpha=0.7
    )
    ax_path.set_xlabel("Longitude", fontproperties=roboto_regular, fontsize=12)
    ax_path.set_ylabel("Latitude", fontproperties=roboto_regular, fontsize=12)
    ax_path.set_title(
        "Run df_recent_activity_stream", fontproperties=roboto_bold, fontsize=14
    )
    ax_path.tick_params(axis="both", which="major", labelsize=10)

    # Add colorbar
    divider = make_axes_locatable(ax_path)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = plt.colorbar(scatter, cax=cax)
    cbar.set_label("Gradient", fontproperties=roboto_regular, fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    # Add distance and date to legend
    recent_distance = df_cumulative_info["recent_run_totals.distance"].iloc[0] / 1000
    recent_timestamp = df_recent_activity_info["start_date_local"].iloc[0]
    recent_gear = df_recent_activity_info["gear.name"].iloc[0]
    recent_calories = df_recent_activity_info["calories"].iloc[0]

    dt = datetime.strptime(recent_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    formatted_recent_timestamp = dt.strftime("%d %b %Y, %I:%M %p")

    ax_path.text(
        0.02,
        0.98,
        f"Latest Run: {formatted_recent_timestamp}\nDistance: {recent_distance:.2f} km\nGear: {recent_gear}\nCalories: {recent_calories}",
        transform=ax_path.transAxes,
        fontproperties=roboto_regular,
        fontsize=10,
        verticalalignment="top",
        color=text_color,
        bbox=dict(facecolor=bg_color, edgecolor=accent_color, alpha=0.7),
    )

    # Heart rate KDE and histogram
    ax_hr = fig.add_subplot(gs[1, 0])
    counts, bins, _ = ax_hr.hist(
        hrt,
        density=True,
        bins=50,
        alpha=0.6,
        color=secondary_color,
        edgecolor=accent_color,
    )
    kde = scistats.gaussian_kde(hrt)
    xx = np.linspace(np.min(hrt), np.max(hrt), 100)
    ax_hr.plot(xx, kde(xx), color=accent_color, linestyle="--", linewidth=2)
    ax_hr.set_xlabel("Heart Rate (BPM)", fontproperties=roboto_regular, fontsize=12)
    ax_hr.set_ylabel("Density", fontproperties=roboto_regular, fontsize=12)
    ax_hr.set_title("Heart Rate Distribution", fontproperties=roboto_bold, fontsize=14)
    ax_hr.tick_params(axis="both", which="major", labelsize=10)

    # Stats bar
    ax_stats = fig.add_subplot(gs[1, 1])
    ax_stats.text(
        0.5,
        0.8,
        "Yearly Statistics:",
        va="center",
        ha="center",
        fontproperties=roboto_bold,
        fontsize=12,
        color=text_color,
    )
    stats = [
        f"Runs: {df_cumulative_info['ytd_run_totals.count'].iloc[0]}",
        f"Distance: {df_cumulative_info['ytd_run_totals.distance'].iloc[0] / 1000:.1f} km",
        f"Time spent: {df_cumulative_info['ytd_run_totals.moving_time'].iloc[0] / 3600:.1f} hours",
    ]
    ax_stats.text(
        0.5,
        0.5,
        "\n".join(stats),
        va="center",
        ha="center",
        fontproperties=roboto_regular,
        fontsize=12,
        color=text_color,
    )
    ax_stats.text(0.6, 0.4, "\uf428", fontproperties=font_awesome_brands)
    ax_stats.axis("off")

    # Add a border to the stats box
    ax_stats.patch.set_edgecolor(accent_color)
    ax_stats.patch.set_linewidth(2)
    ax_stats.patch.set_facecolor(bg_color)
    ax_stats.patch.set_alpha(0.3)

    # Add main title
    fig.suptitle(
        "Strava Run Analysis",
        fontproperties=roboto_bold,
        fontsize=16,
        y=0.98,
        color=text_color,
    )

    plt.tight_layout()
    plt.show()
