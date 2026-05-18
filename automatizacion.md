sudo nano /etc/systemd/system/karen-proyecto.service

[Unit]
Description=Ejecutar proyecto Karen cuarto
After=network-online.target systemd-udev-settle.service bluetooth.service
Wants=network-online.target systemd-udev-settle.service bluetooth.service

[Service]
Type=simple
WorkingDirectory=/home/pi/karen_cuarto_de_proyecto

ExecStartPre=/bin/sleep 10
ExecStart=/home/pi/karen_cuarto_de_proyecto/venv/bin/python /home/pi/karen_cuarto_de_proyecto/work.py

Restart=always
RestartSec=5
TimeoutStartSec=360

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload

sudo systemctl enable karen-proyecto.service

sudo systemctl status karen-proyecto.service

journalctl -u karen-proyecto.service -n 100 --no-pager
