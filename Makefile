APP=tinypass-export
NS=texastribune

build:
	docker build --tag=${NS}/${APP} .

run:
	docker run --name=${APP} --env-file=env --link=smtp:smtp ${NS}/${APP}

clean:
	docker stop ${APP} && docker rm ${APP}
