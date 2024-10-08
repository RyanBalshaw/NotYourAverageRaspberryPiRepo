# Copyright 2023-present Ryan Balshaw
"""
A Simple script that loads in the user information and creates a JSON file with their information.
"""
import json
import os
import time

import requests
from dotenv import dotenv_values, set_key


def get_client_id(env_file_path: str) -> str:
    """
    A function that gets the client id from a user.

    Parameters
    ----------
    env_file_path : str
        df_recent_activity_stream of the environment file.

    Returns
    -------
    client_id : str
        The client id for the user.
    """
    env_file = get_env_variables(env_file_path)

    if len(env_file) < 4:  # Only expect four inputs in the env file.
        client_id = input("Please enter in your client id:\n-->:")

        set_key(
            dotenv_path=env_file_path,
            key_to_set="CLIENT_ID",
            value_to_set=client_id,
            quote_mode="never",
        )

    else:
        client_id = env_file["CLIENT_ID"]

    return client_id


def get_client_secret(env_file_path: str) -> str:
    """
    A function that gets the client secret from a user.

    Parameters
    ----------
    env_file_path : str
        df_recent_activity_stream of the environment file.

    Returns
    -------
    client_secret : str
        The client secret for the user.
    """
    env_file = get_env_variables(env_file_path)

    if len(env_file) < 4:  # Only expect four inputs in the env file.
        client_secret = input(
            "Please enter in your client secret (Settings -> "
            "My API Application):\n-->:"
        )

        set_key(
            dotenv_path=env_file_path,
            key_to_set="CLIENT_SECRET",
            value_to_set=client_secret,
            quote_mode="never",
        )

    else:
        client_secret = env_file["CLIENT_SECRET"]

    return client_secret


def set_env_tokens(env_file_path: str, json_data: dict):
    """
    A function to set the important environment variables (REFRESH_TOKEN and ACCESS_TOKEN)

    Parameters
    ----------
    env_file_path : str
        df_recent_activity_stream of the environment file.

    json_data :
        Dict with the request json data.

    Returns
    -------
        None
    """
    # Store refresh and access token in .env file
    set_key(
        dotenv_path=env_file_path,
        key_to_set="REFRESH_TOKEN",
        value_to_set=json_data["refresh_token"],
        quote_mode="never",
    )

    set_key(
        dotenv_path=env_file_path,
        key_to_set="ACCESS_TOKEN",
        value_to_set=json_data["access_token"],
        quote_mode="never",
    )


def get_env_variables(env_file_path: str):
    """
    A function to get the environment variables

    Parameters
    ----------
    env_file_path : str
        df_recent_activity_stream to the user_information.env file.

    Returns
    -------
    user_env : dict
        The user environment files
    """

    # Check and update the env file information
    user_env = dotenv_values(env_file_path)

    return user_env


def check_tokens(env_file_path: str):
    """
    A function to check the current tokens and update if necessary.

    Parameters
    ----------
    env_file_path : str
        df_recent_activity_stream to the user environment file.

    Returns
    -------
    None

    """

    tmp_dir_path = os.path.join(os.getcwd(), "tmp")
    json_path = os.path.join(tmp_dir_path, "strava_tokens.json")

    # Get the current env information
    env_file = get_env_variables(env_file_path)

    # Access the json file
    with open(json_path) as json_file:
        strava_data = json.load(json_file)

    # Check the expiry time
    if time.time() > strava_data["expires_at"]:
        print("Current tokens have expired. Refreshing tokens now...")

        # Make a Strava auth API call with the current refresh token
        response = requests.post(
            url="https://www.strava.com/api/v3/oauth/token",
            data={
                "client_id": int(env_file["CLIENT_ID"]),
                "client_secret": env_file["CLIENT_SECRET"],
                "grant_type": "refresh_token",
                "refresh_token": env_file["REFRESH_TOKEN"],
            },
        )

        # Save the new tokens and update the env file.
        new_tokens = response.json()

        # Access the old tokens
        with open(json_path) as check:
            old_tokens = json.load(check)

        # Update old_tokens
        for key in new_tokens.keys():
            old_tokens[key] = new_tokens[key]

        # Save updated old_tokens to .json file
        with open(json_path, "w") as outfile:
            json.dump(old_tokens, outfile)

        # Open JSON file and store contents
        with open(json_path) as check:
            json_data = json.load(check)

        # Set the environment variables
        set_env_tokens(env_file_path, json_data)

    else:
        remaining_time = strava_data["expires_at"] - time.time()
        print(
            f"Tokens work just fine. They expire in {time.strftime('%M min, %S sec.', time.gmtime(remaining_time))}"
        )


def get_important_tokens(
    env_file_path: str, tmp_dir_path, access_code_url: str, overwrite_old: bool = False
):
    """

    Parameters
    ----------
    env_file_path : str
        df_recent_activity_stream to the 'user_information.env' file.

    tmp_dir_path : str
        The path to the temporary directory.

    access_code_url : str
        The url containing the access code used to access user information.

    overwrite_old : bool
        A flag to specify whether the user environment variable file should be
        overwritten (default = False).

    Returns
    -------
    None
    """

    json_path = os.path.join(tmp_dir_path, "strava_tokens.json")

    # Create a tmp file to store the .json file
    try:
        os.mkdir(tmp_dir_path)
    except FileExistsError:
        pass

    if os.path.isfile(json_path) and not overwrite_old:
        print(
            "JSON file already exists in the tmp directory, and you have opted "
            "not to create it."
        )

    elif not os.path.isfile(json_path) or overwrite_old:
        # Access the user environment variables
        user_env = get_env_variables(env_file_path)

        # Extract the access code from the URL (hard-coded, might be problematic later)
        access_code = access_code_url.split("&")[1].split("=")[1]

        # Make the Strava auth API call your client code, client secret and code
        response = requests.post(
            url="https://www.strava.com/oauth/token",
            data={
                "client_id": int(user_env["CLIENT_ID"]),
                "client_secret": user_env["CLIENT_SECRET"],
                "code": access_code,
                "grant_type": "authorization_code",
            },
        )

        # Save json response as a variable
        strava_tokens = response.json()

        # Check to see that code was valid
        if strava_tokens.__contains__("errors"):
            print("The access code generated is not valid. Please re-enter.")
            raise SystemExit

        else:
            print("The access code generated is valid.")

            # Save tokens to .json file
            with open(json_path, "w") as outfile:
                json.dump(strava_tokens, outfile)

            # Open JSON file and store contents
            with open(json_path) as check:
                json_data = json.load(check)

            # Set the environment variables
            set_env_tokens(env_file_path, json_data)
