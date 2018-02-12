deploy:
	docker build -f Testenv -t agiastestenv .
	docker run -it agiastestenv pytest test_agias.py
	gcloud app deploy

