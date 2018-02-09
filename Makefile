deploy:
	docker build -t localtest .
	docker run -it localtest pytest
	gcloud app deploy
