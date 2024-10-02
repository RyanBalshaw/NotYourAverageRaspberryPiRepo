# NotYourAverageRaspberryPiRepo
Definitely an average raspberry pi repository.

## A simple list of projects is as follows:
- Strava latest activity map plotter

### TODO
- Initialise environment variable for new user on new PC.
- Play around with plotting so that you can create the image you would 'display' on a screen.

4. Set up Nginx:
   - Install Nginx if you haven't already: `sudo apt-get install nginx`
   - Start Nginx: `sudo systemctl start nginx`
   - Enable Nginx to start on boot: `sudo systemctl enable nginx`

5. Set up a cron job to update the display daily:
   ```
   crontab -e
   ```
   Add this line to run the script daily at 1 AM:
   ```
   0 1 * * * python /path/to/your/update_strava_display.py
   ```

6. Configure your Raspberry Pi to open the web page on startup:
   - Install a lightweight browser like Chromium: `sudo apt-get install chromium-browser`
   - Create a startup script (e.g., `start_display.sh`):
     ```bash
     #!/bin/bash
     chromium-browser --kiosk --incognito http://localhost
     ```
   - Make the script executable: `chmod +x start_display.sh`
   - Add the script to autostart:
     ```
     mkdir -p ~/.config/autostart
     echo "[Desktop Entry]
     Type=Application
     Name=Strava Display
     Exec=/path/to/your/start_display.sh" > ~/.config/autostart/strava_display.desktop
     ```