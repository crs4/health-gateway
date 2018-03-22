build:
	../../images/common/base/build.sh
	docker build -t crs4/web_base ../../images/common/web_base/
	docker-compose build

run:
	docker-compose up

run_no_spid:
	docker-compose -f docker-compose-without-spid.yml -f docker-compose.override.yml up

down:
	docker-compose down

rund:
	docker-compose up -d

rund_no_spid:
	docker-compose -f docker-compose-without-spid.yml -f docker-compose.override.yml up -d

init_db:
	cd ../../../utils && ./create_service_db.sh $(load_dev_data)

init_db_run: init_db run

init_db_rund: init_db rund

init_db_run_no_spid: init_db run_no_spid

init_db_rund_no_spid: init_db rund_no_spid

build_init_db_run: build init_db_run

build_init_db_rund: build init_db_rund

build_init_db_run_no_spid: build init_db_run_no_spid

build_init_db_rund_no_spid: build init_db_rund_no_spid