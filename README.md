# HTTP Server Derived from
https://esp32tutorials.com/esp32-cam-esp-idf-live-streaming-web-server/

This is run with the ESP32-S3-EYE on ESP IDF V5.4+ on Ubuntu 22.04. The specific release for the IDF can be found here: https://github.com/espressif/esp-idf/releases/tag/v5.4.1
The command line idf.py was used (not the IDF terminal via vscode or platformio).


# How it works
1. Image taken by glasses (served in an esp32-s3-eye web server). SERVER DOESNT NEED TO BE CONNECTED TO COMPUTER; IT JUST NEEDS POWER. CAN ALSO USE ESP32 SERVER TO LOG DIAGNOSTICS DATA IN SD CARD (OPTIONAL)
2. on button press, send a GET request VIA WIFI to the ESP32 to get the image onto a computer
3. run tesseract-ocr to get text from an image. We get 5 images, and any text that appears once or less gets filtered out
4. spellcheck and regex out text (remove symbols)
5. (optional) Translation layer (via google translate)
6. output result via text-to-speech

# How to Run
It is assumed you have access to the idf.py command line tool. Once the IDF release repo is cloned (e.g. to ~/esp/esp-v5.4.1), run the install.sh and . ./export.sh scripts. Note that idf.py will only be active for the terminal session.
1. Clone this repo
2. cd into the repo into main, and replace the connect_wifi.c file with your SSID (wi-fi name) and password
3. run idf.py set-target esp32s3
4. run idf.py menuconfig, and set the parameters to your needs. It is recommended use PSRAM where possible.
5. cd back to root of the repo, and run idf.py /dev/yourport flash monitor
6. in monitor, you should get an IP address. To test that the web server is running, view this in your browser at IP.ADDRESS.YES.YES/image.
7. in another terminal, go into the ml directory and run ml.py.

# Contributors
Rhett: Spellchecking and Designer
Cielo: Text Recognition, translation and text-to-speech
Jackie: Presentation, backup camera
Ryan: HTTP Web server and Camera
