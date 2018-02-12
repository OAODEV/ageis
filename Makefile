deploy:
	docker build -f Testenv -t testenv .
	docker run -it testenv pytest test_agias.py
	gcloud app deploy

