# Copyright 2023-present Ryan Balshaw
"""
Main file for testing.
"""
import json
import os
import sys
import textwrap
import webbrowser
from datetime import datetime
from typing import Dict, Tuple

import matplotlib as mpl
import matplotlib.font_manager as fm
import numpy as np
import scipy.stats as scistats
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm import tqdm

import NYARPR.StravaVisualiser as strava_vis


class StravaVisualizer:
    def __init__(
        self,
        python_path: str,
        tmp_dir_path: str,
        env_file_name: str = "user_information.env",
    ):
        self.python_path = python_path
        self.env_path = os.path.join(os.getcwd(), env_file_name)
        self.tmp_dir_path = tmp_dir_path
        self.script_path = os.path.join(os.getcwd(), "main.py")
        self.generate_animation = False  # TODO: Refactor this out
        self.setup_fonts()
        self.setup_colors()
        self.setup_plot_params()

        self.plot_save_path = os.path.join(
            self.tmp_dir_path,
            "strava_plot__latest.png",
        )

        self.plot_metadata_path = os.path.join(
            self.tmp_dir_path,
            "strava_plot__metadata.json",
        )

        self.display_html_template_path = os.path.join(
            os.getcwd(), "html_templates", "display_template.html"
        )
        self.strava_diplay_html_path = os.path.join(tmp_dir_path, "strava_display.html")
        self.kiosk_script_file_path = os.path.join(
            tmp_dir_path, "launch_strava_kiosk.sh"
        )
        self.shell_script_file_path = os.path.join(tmp_dir_path, "run_strava_script.sh")

    def setup_fonts(self):
        self.roboto_regular = fm.FontProperties(
            fname=os.path.join(os.getcwd(), "fonts", "roboto", "Roboto-Regular.ttf")
        )
        self.roboto_bold = fm.FontProperties(
            fname=os.path.join(os.getcwd(), "fonts", "roboto", "Roboto-Bold.ttf")
        )
        self.font_awesome = fm.FontProperties(
            fname=os.path.join(
                os.getcwd(),
                "icons",
                "font-awesome",
                "Font Awesome 6 Free-Solid-900.otf",
            )
        )

    def setup_colors(self):
        self.bg_color = "#282a36"
        self.text_color = "#f8f8f2"
        self.accent_color = "#ff79c6"
        self.secondary_color = "#8be9fd"
        self.green_color = "#50fa7b"
        self.comment_color = "#6272a4"

    def setup_plot_params(self):
        plt.rcParams.update(
            {
                "figure.facecolor": self.bg_color,
                "text.color": self.text_color,
                "axes.facecolor": self.bg_color,
                "axes.edgecolor": self.text_color,
                "axes.labelcolor": self.text_color,
                "xtick.color": self.text_color,
                "ytick.color": self.text_color,
                "figure.dpi": 300,
                "animation.convert_path": r"/usr/bin/convert",
            }
        )
        self._label_fontsize = 22
        self._title_fontsize = 26
        self._text_fontsize = 20
        self._icon_fontsize = 24
        self._tick_size = 16

    @staticmethod
    def scale_max_min(
        data_array: np.ndarray, min_scale: float = 0.2, max_scale: float = 0.2
    ) -> Tuple[float, float]:
        min_val, max_val = np.min(data_array), np.max(data_array)
        data_range = max_val - min_val
        padding_min, padding_max = data_range * min_scale, data_range * max_scale
        return min_val - padding_min, max_val + padding_max

    def setup_strava_auth(self):
        if len(strava_vis.get_env_variables(self.env_path)) < 4:
            client_id = strava_vis.get_client_id(self.env_path)
            strava_vis.get_client_secret(self.env_path)

            oauth_url = (
                f"https://www.strava.com/oauth/authorize?client_id={client_id}"
                "&response_type=code&redirect_uri=http://localhost/"
                "exchange_token&approval_prompt=force&scope=profile:"
                "read_all,activity:read_all"
            )

            try:
                webbrowser.get()
                webbrowser.open(oauth_url)
            except Exception:
                print("Please open the following URL in your web browser to authorize:")
                print(oauth_url)

            access_code_url = input("Please input the access code url\n--->:")
            strava_vis.get_important_tokens(
                self.env_path,
                self.tmp_dir_path,
                access_code_url=access_code_url,
                overwrite_old=True,
            )

        strava_vis.check_tokens(self.env_path)

    def get_strava_data(self, recent_activity_id: int):
        # Create the plot information
        self.df_recent_activity_stream = strava_vis.get_activity_stream(
            self.env_path, recent_activity_id
        )
        self.df_recent_activity_info = strava_vis.get_activity_info(
            self.env_path, recent_activity_id
        )

        self.t = np.array(self.df_recent_activity_stream["time.data"].iloc[0]) / 60
        self.hrt = self.df_recent_activity_stream["heartrate.data"].iloc[0]
        self.lat_lng = np.array(self.df_recent_activity_stream["latlng.data"].iloc[0])
        self.alt = self.df_recent_activity_stream["altitude.data"].iloc[0]
        self.rel_alt = np.array(self.alt)
        self.rel_alt -= self.rel_alt[0]

    def get_recent_activity_id(self) -> int:
        self.df_cumulative_info = strava_vis.get_cumulative_information(self.env_path)
        recent_activity_id = strava_vis.get_latest_activity_code(
            self.env_path, activity_type="Run"
        )
        return recent_activity_id

    def check_strava_plot_metadata(self, activity_dictionary: Dict[str, int]) -> bool:
        """
        A simple method to check the plot metadata.
        """

        # Check whether the metadata json file exists
        metadata_file_name = os.path.split(self.plot_metadata_path)[-1]

        if metadata_file_name in os.listdir(self.tmp_dir_path):
            with open(self.plot_metadata_path) as f:
                activity_json_dict = json.load(f)

            if (
                activity_json_dict["recent_activity_id"]
                == activity_dictionary["recent_activity_id"]
            ):
                print("Metadata file indicates that the plot is up to date.")

                return True

        # If this runs, either the json does not exist or the recent_activity_id is
        # not right
        # Serialise the json
        json_object = json.dumps(activity_dictionary, indent=4)

        # Writing to the metadata file
        with open(self.plot_metadata_path, "w") as outfile:
            outfile.write(json_object)

        print("Metadata file indicates that the plot is NOT up to date.")

        return False

    def create_plot(self):
        self.fig = plt.figure(figsize=(16, 12))
        gs = self.fig.add_gridspec(
            2, 2, width_ratios=[3, 1], height_ratios=[2, 1], hspace=0.3, wspace=0.3
        )

        self.create_path_plot(gs[0, :])
        self.create_hr_plot(gs[1, 0])
        self.create_stats_plot(gs[1, 1])

        self.fig.tight_layout()

    def create_path_plot(self, gs):
        self.ax_path = self.fig.add_subplot(gs)
        self.ax_path_cmap = mpl.colormaps["magma"]
        self.ax_path.plot(
            self.lat_lng[:, 0], self.lat_lng[:, 1], "--", color=self.comment_color
        )

        if self.generate_animation:
            self.scatter = self.ax_path.scatter(
                [], [], c=[], cmap=self.ax_path_cmap, s=30, alpha=0.7, zorder=2.5
            )
        else:
            self.scatter = self.ax_path.scatter(
                self.lat_lng[:, 0],
                self.lat_lng[:, 1],
                c=self.rel_alt,
                cmap=self.ax_path_cmap,
                s=30,
                alpha=0.7,
                zorder=2.5,
            )

        self.ax_path.set_xlim(self.scale_max_min(self.lat_lng[:, 0], 0.4, 0.2))
        self.ax_path.set_ylim(self.scale_max_min(self.lat_lng[:, 1], 0.2, 0.2))

        self.ax_path.set_xlabel(
            "Longitude",
            fontproperties=self.roboto_regular,
            fontsize=self._label_fontsize,
        )
        self.ax_path.set_ylabel(
            "Latitude",
            fontproperties=self.roboto_regular,
            fontsize=self._label_fontsize,
        )
        self.ax_path.set_title(
            "Latest run", fontproperties=self.roboto_bold, fontsize=self._title_fontsize
        )
        self.ax_path.axis("off")

        self.add_colorbar()
        self.add_run_details()

    def add_colorbar(self):
        divider = make_axes_locatable(self.ax_path)
        cax = divider.append_axes("right", size="5%", pad=0.1)

        norm = mpl.colors.Normalize(
            vmin=np.min(self.rel_alt), vmax=np.max(self.rel_alt)
        )
        mpl.cm.ScalarMappable(norm=norm, cmap=self.ax_path_cmap)
        cbar = self.fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=self.ax_path_cmap), cax=cax
        )
        cbar.set_label(
            "Altitude (relative)",
            fontproperties=self.roboto_regular,
            fontsize=self._label_fontsize,
        )
        cbar.ax.tick_params(labelsize=self._tick_size)

    def add_run_details(self):
        recent_distance = self.df_recent_activity_info["distance"].iloc[0] / 1000
        recent_timestamp = self.df_recent_activity_info["start_date_local"].iloc[0]
        recent_gear = self.df_recent_activity_info["gear.name"].iloc[0]
        recent_calories = self.df_recent_activity_info["calories"].iloc[0]
        recent_moving_time = self.df_recent_activity_info["moving_time"].iloc[0] / 60

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
            self.ax_path.text(
                -0.1,
                0.98 - i * 0.15,
                icon,
                transform=self.ax_path.transAxes,
                fontproperties=self.font_awesome,
                fontsize=self._icon_fontsize,
                va="top",
                ha="center",
                color=self.accent_color,
            )
            self.ax_path.text(
                -0.04,
                0.98 - i * 0.15,
                value,
                transform=self.ax_path.transAxes,
                va="top",
                ha="left",
                fontproperties=self.roboto_bold,
                fontsize=self._text_fontsize,
                color=self.text_color,
            )
            self.ax_path.text(
                -0.04,
                0.9 - i * 0.15,
                label,
                transform=self.ax_path.transAxes,
                va="top",
                ha="left",
                fontproperties=self.roboto_regular,
                fontsize=self._text_fontsize - 2,
                color=self.secondary_color,
            )

    def create_hr_plot(self, gs):
        self.ax_hr = self.fig.add_subplot(gs)
        _ = self.ax_hr.hist(
            self.hrt[0] if self.generate_animation else self.hrt,
            density=True,
            bins=50,
            alpha=0.6,
            color=self.secondary_color,
            edgecolor=self.accent_color,
        )

        min_hr, max_hr = np.min(self.hrt), np.max(self.hrt)
        self.ax_hr.set_xlim((min_hr, max_hr))

        kde = scistats.gaussian_kde(self.hrt)
        xx = np.linspace(min_hr, max_hr, 100)
        yy = kde(xx)

        (self.line_hr,) = self.ax_hr.plot(
            xx, yy, linestyle="--", linewidth=2, color=self.accent_color
        )

        self.ax_hr.set_xlabel(
            "Heart rate (BPM)",
            fontproperties=self.roboto_regular,
            fontsize=self._label_fontsize,
        )
        self.ax_hr.set_ylabel(
            "Density", fontproperties=self.roboto_regular, fontsize=self._label_fontsize
        )
        self.ax_hr.set_title(
            "Heart rate distribution",
            fontproperties=self.roboto_bold,
            fontsize=self._title_fontsize,
        )
        self.ax_hr.tick_params(axis="both", which="major", labelsize=self._tick_size)
        self.ax_hr.yaxis.set_major_locator(MaxNLocator(nbins=3))
        self.ax_hr.xaxis.set_major_locator(MaxNLocator(nbins=5))

    def create_stats_plot(self, gs):
        self.ax_stats = self.fig.add_subplot(gs)

        x_start, x_delta = -0.3, 0.5
        y_annual, y_last_4, y_stats = 0.2, 0.5, 0.9
        current_year = datetime.now().strftime("%Y")

        self.ax_stats.text(
            x_start + 2 * x_delta,
            y_stats,
            "Statistics",
            va="center",
            ha="center",
            fontproperties=self.roboto_bold,
            fontsize=self._text_fontsize + 2,
            color=self.text_color,
        )
        self.ax_stats.text(
            x_start,
            y_last_4,
            "Last 4 \nweeks",
            va="center",
            ha="center",
            fontproperties=self.roboto_bold,
            fontsize=self._text_fontsize,
            color=self.green_color,
        )
        self.ax_stats.text(
            x_start,
            y_annual,
            f"{current_year}",
            va="center",
            ha="center",
            fontproperties=self.roboto_bold,
            fontsize=self._text_fontsize,
            color=self.green_color,
        )

        stats = [
            (
                "\uf1ec",
                "Runs",
                f"{self.df_cumulative_info['ytd_run_totals.count'].iloc[0]}",
                f"{self.df_cumulative_info['recent_run_totals.count'].iloc[0]}",
            ),
            (
                "\uf547",
                "Distance",
                f"{self.df_cumulative_info['ytd_run_totals.distance'].iloc[0] / 1000:.1f} km",
                f"{self.df_cumulative_info['recent_run_totals.distance'].iloc[0] / 1000:.1f} km",
            ),
            (
                "\uf017",
                "Time spent",
                f"{self.df_cumulative_info['ytd_run_totals.moving_time'].iloc[0] / 3600:.1f} hrs",
                f"{self.df_cumulative_info['recent_run_totals.moving_time'].iloc[0] / 3600:.1f} hrs",
            ),
        ]

        for i, (icon, label, value_4weeks, value_annual) in enumerate(stats):
            x_pos = x_start + (i + 1) * x_delta
            self.ax_stats.text(
                x_pos,
                y_last_4 + 0.25,
                icon,
                fontproperties=self.font_awesome,
                fontsize=self._icon_fontsize * 1.2,
                va="center",
                ha="center",
                color=self.accent_color,
            )
            self.ax_stats.text(
                x_pos,
                y_annual - 0.2,
                label,
                va="center",
                ha="center",
                fontproperties=self.roboto_regular,
                fontsize=self._text_fontsize - 2,
                color=self.secondary_color,
            )
            self.ax_stats.text(
                x_pos,
                y_annual,
                value_4weeks,
                va="center",
                ha="center",
                fontproperties=self.roboto_bold,
                fontsize=self._text_fontsize,
                color=self.text_color,
            )
            self.ax_stats.text(
                x_pos,
                y_last_4,
                value_annual,
                va="center",
                ha="center",
                fontproperties=self.roboto_bold,
                fontsize=self._text_fontsize,
                color=self.text_color,
            )

        self.ax_stats.axis("off")
        self.ax_stats.patch.set_edgecolor(self.accent_color)
        self.ax_stats.patch.set_linewidth(2)
        self.ax_stats.patch.set_facecolor(self.bg_color)
        self.ax_stats.patch.set_alpha(0.3)

    def generate_animation_frames(self):
        if not self.generate_animation:
            return

        pbar = tqdm(total=len(self.lat_lng))

        def init():
            self.scatter.set_offsets(self.lat_lng[:1])
            self.scatter.set_array(self.rel_alt[:1])
            self.scatter.set_clim(np.min(self.rel_alt), np.max(self.rel_alt))
            return [self.scatter]

        def update(frame):
            pbar.update(1)
            self.scatter.set_offsets(self.lat_lng[:frame])
            self.scatter.set_array(self.rel_alt[:frame])
            self.scatter.set_clim(np.min(self.rel_alt), np.max(self.rel_alt))
            return [self.scatter]

        anim = FuncAnimation(
            self.fig,
            update,
            frames=len(self.lat_lng),
            init_func=init,
            repeat=False,
            interval=10000 / len(self.lat_lng),
            blit=False,
        )
        anim.save(filename="plot.mp4")
        pbar.close()

    def save_plot(self):
        self.fig.savefig(self.plot_save_path)
        plt.close()

    @staticmethod
    def make_executable(path):
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2  # copy R bits to X
        os.chmod(path, mode)

    def create_shell_script(self):
        script_directory = os.path.dirname(self.script_path)

        with open(self.shell_script_file_path, "w") as rsh:
            rsh.write(
                textwrap.dedent(
                    f"""\
                    #!/bin/bash
                    cd {script_directory}
                    {self.python_path} {os.path.basename(self.script_path)}
                    """
                )
            )

        # Change permissions
        self.make_executable(self.shell_script_file_path)

        print(
            textwrap.dedent(
                f"""Please follow these steps to make the script run every hour:
                ```
                crontab -e
                ```
                Add this line to run the script every hour:
                ```
                0 * * * * {self.shell_script_file_path}
                ```"""
            )
        )

    def create_kiosk(self):
        with open(self.kiosk_script_file_path, "w") as rsh:
            rsh.write(
                textwrap.dedent(
                    f"""\
                #! /bin/bash
                chromium-browser --kiosk --incognito file://{self.strava_diplay_html_path}
                """
                )
            )

        # Change permissions
        self.make_executable(self.kiosk_script_file_path)

        print(
            textwrap.dedent(
                f"""
                Create a .desktop file in ~/.config/autostart/:
                ```
                mkdir -p ~/.config/autostart
                nano ~/.config/autostart/kiosk.desktop
                ```
                Add the following content:
                ```
                [Desktop Entry]
                Type=Application
                Name=Strava Kiosk
                Exec={self.kiosk_script_file_path}
                ```
                """
            )
        )

    def run(self):
        # Check the auth
        self.setup_strava_auth()

        # Get the ID for the most recent activity
        recent_activity_id = self.get_recent_activity_id()

        # Create the activity_dictionary
        activity_dictionary = {"recent_activity_id": recent_activity_id}

        # Create the figure if the metadata shows the plot is outdated.
        if not self.check_strava_plot_metadata(activity_dictionary):
            self.get_strava_data(recent_activity_id)
            self.create_plot()
            self.generate_animation_frames()
            self.save_plot()

    def create_scripts(self):
        expected_file_paths = [
            self.shell_script_file_path,
            self.strava_diplay_html_path,
            self.kiosk_script_file_path,
        ]
        expected_file_names = [
            os.path.split(file_path)[-1] for file_path in expected_file_paths
        ]
        expected_file_root_path = [
            os.path.join(*os.path.split(file_path)[:-1])
            for file_path in expected_file_paths
        ]

        # Check if all script files exist
        if not all(
            file_name in os.listdir(file_root_path)
            for file_root_path, file_name in zip(
                expected_file_root_path, expected_file_names
            )
        ):
            self.create_shell_script()
            self.update_html()
            self.create_kiosk()

            print("Generated files indicate that the necessary files must be created.")

        else:
            print("Generated files indicate that the necessary files already exist.")

    def update_html(self):
        # Check if display file exists
        split_html_path = os.path.split(self.strava_diplay_html_path)

        display_file_root_path = os.path.join(*split_html_path[:-1])
        display_file_name = split_html_path[-1]

        if display_file_name not in os.listdir(display_file_root_path):
            # Read the template
            with open(self.display_html_template_path, "r") as f:
                template = f.read()

            # Replace the placeholder with the actual image path
            plot_save_name = os.path.split(self.plot_save_path)[-1]
            html_content = template.replace("IMAGE_PATH_PLACEHOLDER", plot_save_name)

            # Write the final HTML
            with open(self.strava_diplay_html_path, "w") as f:
                f.write(html_content)

            print(f"File {self.strava_diplay_html_path} has been generated.")

        else:
            print(f"File {self.strava_diplay_html_path} already exists.")


if __name__ == "__main__":
    visualizer = StravaVisualizer(
        python_path=os.path.join(
            os.getcwd(),
            sys.executable,
        ),
        tmp_dir_path=os.path.join(os.getcwd(), "tmp"),
    )

    # Run the visualisation code
    visualizer.run()

    # Create the scripts
    visualizer.create_scripts()
