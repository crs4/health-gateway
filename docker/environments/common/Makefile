build:
	bash ../../images/generate_images.sh

run:
	docker-compose up

run_with_spid:
	docker-compose -f docker-compose-with-spid.yml -f docker-compose.override.yml up

run_with_tscns:
	docker-compose -f docker-compose-with-tscns.yml -f docker-compose.override.yml up

down:
	docker-compose down

down_with_spid:
	docker-compose -f docker-compose-with-spid.yml -f docker-compose.override.yml down

down_with_tscns:
	docker-compose -f docker-compose-with-tscns.yml -f docker-compose.override.yml down

rund:
	docker-compose up -d

rund_with_spid:
	docker-compose -f docker-compose-with-spid.yml -f docker-compose.override.yml up -d

rund_with_tscns:
	docker-compose -f docker-compose-with-tscns.yml -f docker-compose.override.yml up -d

clear_data:
	rm -rf ./kafka-logs/* ./zookeeper/*
	find ../../../ -name *.sqlite3 -delete
	
clear_data_run: clear_data run

clear_data_rund: clear_data rund

clear_data_run_with_spid: clear_data run_with_spid

clear_data_rund_with_spid: clear_data rund_with_spid

clear_data_run_with_tscns: clear_data run_with_tscns

clear_data_rund_with_tscns: clear_data rund_with_tscns

build_clear_data_run: build clear_data_run

build_clear_data_rund: build clear_data_rund

build_clear_data_run_with_spid: build clear_data_run_with_spid

build_clear_data_rund_with_spid: build clear_data_rund_with_spid

build_clear_data_run_with_tscns: build clear_data_run_with_tscns

build_clear_data_rund_with_tscns: build clear_data_rund_with_tscns