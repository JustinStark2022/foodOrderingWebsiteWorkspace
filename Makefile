run:
	docker run -p 5000:5000 -v static:/app/static -v templates:/app/templates dev/groupies
build:
	docker build --no-cache -t dev/groupies .