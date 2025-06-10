echo "The user name is jetson and the password for this camera system is yahboom"
echo -e "\n\nPhoto capture will now begin at startup, until the service is restarted\n\n"
sudo systemctl daemon-reload
sudo systemctl enable capture.service

sudo systemctl start capture.service
