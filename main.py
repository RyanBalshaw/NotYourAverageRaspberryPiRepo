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
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable

import NYARPR.StravaVisualiser as strava_vis
from tqdm import tqdm

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
    rel_alt = np.array(alt)
    rel_alt -= rel_alt[0]

    # Set up Roboto font and Font Awesome
    roboto_regular = fm.FontProperties(
        fname=os.path.join(os.getcwd(), "fonts", "roboto", "Roboto-Regular.ttf")
    )
    roboto_bold = fm.FontProperties(
        fname=os.path.join(os.getcwd(), "fonts", "roboto", "Roboto-Bold.ttf")
    )
    font_awesome = fm.FontProperties(
        fname=os.path.join(
            os.getcwd(), "icons", "font-awesome", "Font Awesome 6 Free-Solid-900.otf"
        )
    )

    # Dracula-inspired color scheme
    bg_color = "#282a36"
    text_color = "#f8f8f2"
    accent_color = "#ff79c6"
    secondary_color = "#8be9fd"
    green_color = "#50fa7b"
    comment_color = "#6272a4"

    plt.rcParams.update(
        {
            "figure.facecolor": bg_color,
            "text.color": text_color,
            "axes.facecolor": bg_color,
            "axes.edgecolor": text_color,
            "axes.labelcolor": text_color,
            "xtick.color": text_color,
            "ytick.color": text_color,
            "figure.dpi": 300,
            "animation.convert_path": r"/usr/bin/convert",
        }
    )

    _label_fontsize = 16
    _title_fontsize = 20
    _text_fontsize = 14
    _icon_fontsize = 18
    _tick_size = 12

    # Create the plot
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(
        2, 2, width_ratios=[3, 1], height_ratios=[2, 1], hspace=0.3, wspace=0.3
    )

    # Run path colored by heart rate
    ax_path = fig.add_subplot(gs[0, :])
    ax_path_cmap = mpl.colormaps["magma"]
    ax_path.plot(lat_lng[:, 0], lat_lng[:, 1], "--", color=comment_color)
    scatter = ax_path.scatter([], [], c=[], cmap=ax_path_cmap, s=30, alpha=0.7, zorder=2.5)

    # Set limits
    # ax_path.set_xlim(lat_lng[:, 0].min() * 0.8, lat_lng[:, 0].max() * 1.2)
    # ax_path.set_ylim(lat_lng[:, 1].min() * 0.8, lat_lng[:, 1].max() * 1.2)

    ax_path.set_xlabel(
        "Longitude", fontproperties=roboto_regular, fontsize=_label_fontsize
    )
    ax_path.set_ylabel(
        "Latitude", fontproperties=roboto_regular, fontsize=_label_fontsize
    )
    ax_path.set_title(
        "Latest run", fontproperties=roboto_bold, fontsize=_title_fontsize
    )
    ax_path.axis("off")

    # Add colorbar
    divider = make_axes_locatable(ax_path)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    norm = mpl.colors.Normalize(vmin=np.min(rel_alt), vmax=np.max(rel_alt))
    mpl.cm.ScalarMappable(norm=norm, cmap=ax_path_cmap)
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=ax_path_cmap), cax=cax)
    cbar.set_label(
        "Altitude (relative)", fontproperties=roboto_regular, fontsize=_label_fontsize
    )
    cbar.ax.tick_params(labelsize=_tick_size)

    # Add run details to legend
    recent_distance = df_recent_activity_info["distance"].iloc[0] / 1000
    recent_timestamp = df_recent_activity_info["start_date_local"].iloc[0]
    recent_gear = df_recent_activity_info["gear.name"].iloc[0]
    recent_calories = df_recent_activity_info["calories"].iloc[0]
    recent_moving_time = df_recent_activity_info["moving_time"].iloc[0] / 60

    current_year = datetime.now().strftime("%Y")
    dt = datetime.strptime(recent_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    formatted_recent_timestamp = dt.strftime("%d %b %Y, %I:%M %p")

    details = [
        ("\uf073", f"{formatted_recent_timestamp}", "Date"),
        ("\uf70c", f"{recent_distance:.2f} km", "Distance"),
        ("\uf013", f" {recent_gear}", "Gear"),
        ("\uf06d", f"{recent_calories:.0f} kcal", "Calories"),
        ("\uf017", f"{recent_moving_time:.2f} min.", "Moving time"),
    ]

    for i, (icon, value, label) in enumerate(details):
        ax_path.text(
            0.02,
            0.98 - i * 0.1,
            icon,
            transform=ax_path.transAxes,
            fontproperties=font_awesome,
            fontsize=_icon_fontsize,
            va="top",
            ha="center",
            color=accent_color,
        )
        ax_path.text(
            0.06,
            0.98 - i * 0.1,
            value,
            transform=ax_path.transAxes,
            va="top",
            ha="left",
            fontproperties=roboto_bold,
            fontsize=_text_fontsize,
            color=text_color,
        )
        ax_path.text(
            0.06,
            0.94 - i * 0.1,
            label,
            transform=ax_path.transAxes,
            va="top",
            ha="left",
            fontproperties=roboto_regular,
            fontsize=_text_fontsize - 2,
            color=secondary_color,
        )

    # Heart rate KDE and histogram
    ax_hr = fig.add_subplot(gs[1, 0])
    counts, bins, _ = ax_hr.hist(
        hrt[0],
        density=True,
        bins=50,
        alpha=0.6,
        color=secondary_color,
        edgecolor=accent_color,
    )

    min_hr = np.min(hrt)
    max_hr = np.max(hrt)
    ax_hr.set_xlim((min_hr, max_hr))

    _ = ax_hr.hist(
        hrt,
        density=True,
        bins=50,
        alpha=0.6,
        color=secondary_color,
        edgecolor=accent_color,
    )
    kde = scistats.gaussian_kde(hrt)
    xx = np.linspace(min_hr, max_hr, 100)
    yy = kde(xx)

    line_hr, = ax_hr.plot(xx, yy, linestyle="--", linewidth=2, color=accent_color)

    pbar = tqdm(total=len(lat_lng))

    def init():

        # line_hr.set_data([min_hr, max_hr], [0.1] * 2)

        scatter.set_offsets(lat_lng[:1])
        scatter.set_array(rel_alt[:1])  # Set initial color
        scatter.set_clim(np.min(rel_alt), np.max(rel_alt))  # Set color limits

        return [scatter]

    def update(frame):
        pbar.update(1)

        # ax_path updates
        scatter.set_offsets(lat_lng[:frame])
        scatter.set_array(rel_alt[:frame])  # Update the color array

        # Set the color limits to match the full range of rel_alt
        scatter.set_clim(np.min(rel_alt), np.max(rel_alt))
        #
        # # ax_hr updates
        # if frame % 300 == 0:
        #     # Clear the frame
        #     ax_hr.cla()
        #
        #     if frame < 3:
        #         hrt_frame = hrt[:3]
        #     else:
        #         hrt_frame = hrt[:frame]
        #     pdf, bins, _ = ax_hr.hist(
        #         hrt_frame,
        #         density=True,
        #         bins=50,
        #         alpha=0.6,
        #         color=secondary_color,
        #         edgecolor=accent_color,
        #     )
        #     kde = scistats.gaussian_kde(hrt_frame)
        #     xx = np.linspace(min_hr, max_hr, 100)
        #     yy = kde(xx)
        #
        #     line_hr.set_data(xx, yy)
        #
        #     ax_hr.set_ylim((-0.005, np.max(kde) * 1.5))

        return [scatter]


    ax_hr.set_xlabel(
        "Heart rate (BPM)", fontproperties=roboto_regular, fontsize=_label_fontsize
    )
    ax_hr.set_ylabel("Density", fontproperties=roboto_regular, fontsize=_label_fontsize)
    ax_hr.set_title(
        "Heart rate distribution", fontproperties=roboto_bold, fontsize=_title_fontsize
    )
    ax_hr.tick_params(axis="both", which="major", labelsize=_tick_size)
    ax_hr.yaxis.set_major_locator(MaxNLocator(nbins=3))
    ax_hr.xaxis.set_major_locator(MaxNLocator(nbins=5))

    # Stats bar
    # Past 4 weeks

    # \uf073
    # Statistics section
    ax_stats = fig.add_subplot(gs[1, 1])

    # Icon and main title
    ax_stats.text(
        0.58,
        0.7,
        "Statistics",
        va="center",
        ha="center",
        fontproperties=roboto_bold,
        fontsize=_text_fontsize + 2,
        color=text_color,
    )

    # Column titles
    y_annual = 0.25
    y_last_4 = 0.4
    ax_stats.text(
        -0.1,
        y_last_4,
        "Last 4 weeks",
        va="center",
        ha="center",
        fontproperties=roboto_bold,
        fontsize=_text_fontsize,
        color=green_color,
    )
    ax_stats.text(
        -0.1,
        y_annual,
        f"{current_year}",
        va="center",
        ha="center",
        fontproperties=roboto_bold,
        fontsize=_text_fontsize,
        color=green_color,
    )

    # Statistics data
    stats = [
        (
            "\uf1ec",
            "Runs",
            f"{df_cumulative_info['ytd_run_totals.count'].iloc[0]}",
            f"{df_cumulative_info['recent_run_totals.count'].iloc[0]}",
        ),
        (
            "\uf547",
            "Distance",
            f"{df_cumulative_info['ytd_run_totals.distance'].iloc[0] / 1000:.1f} km",
            f"{df_cumulative_info['recent_run_totals.distance'].iloc[0] / 1000:.1f} km",
        ),
        (
            "\uf017",
            "Time spent",
            f"{df_cumulative_info['ytd_run_totals.moving_time'].iloc[0] / 3600:.1f} hours",
            f"{df_cumulative_info['recent_run_totals.moving_time'].iloc[0] / 3600:.1f} hours",
        ),
    ]

    for i, (icon, label, value_4weeks, value_annual) in enumerate(stats):
        x_pos = 0.2 + i * 0.38

        # Icon
        ax_stats.text(
            x_pos,
            y_last_4 + 0.15,
            icon,
            fontproperties=font_awesome,
            fontsize=_icon_fontsize * 1.2,
            va="center",
            ha="center",
            color=accent_color,
        )

        # Label
        ax_stats.text(
            x_pos,
            y_annual - 0.1,
            label,
            va="center",
            ha="center",
            fontproperties=roboto_regular,
            fontsize=_text_fontsize - 2,
            color=secondary_color,
        )

        # 4-week value
        ax_stats.text(
            x_pos,
            y_annual,
            value_4weeks,
            va="center",
            ha="center",
            fontproperties=roboto_bold,
            fontsize=_text_fontsize,
            color=text_color,
        )

        # Annual value
        ax_stats.text(
            x_pos,
            y_last_4,
            value_annual,
            va="center",
            ha="center",
            fontproperties=roboto_bold,
            fontsize=_text_fontsize,
            color=text_color,
        )

    ax_stats.axis("off")

    # Add a border to the stats box
    ax_stats.patch.set_edgecolor(accent_color)
    ax_stats.patch.set_linewidth(2)
    ax_stats.patch.set_facecolor(bg_color)
    ax_stats.patch.set_alpha(0.3)

    fig.tight_layout()

    anim = FuncAnimation( #len(lat_lng)
        fig, update, frames=len(lat_lng), init_func=init, repeat=False, interval=10000/len(lat_lng), blit=True
    )

    anim.save(filename="plot.mp4")

    pbar.close()

