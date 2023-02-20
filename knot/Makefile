up:
	docker compose create
	docker compose cp knot.conf zonesource:/config/knot.conf
	docker compose cp example.com.zone zonesource:/storage/example.com.zone
	docker compose start

down:
	docker compose down

axfr:
	dig @127.0.0.1 -p 5300 example.com axfr
