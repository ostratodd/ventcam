echo "The user name is jetson and the password for this camera system is yahboom"
echo -e "\n\n******WARNING: photo capture will be turned off at startup, until the service is restarted\n\n"
echo "To re-enable the capture service as startup, you can use startcapture.sh"
sudo systemctl stop capture.service
