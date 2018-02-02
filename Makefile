deploy-dev:
	gcloud container clusters get-credentials playground

	docker build -t us.gcr.io/lexical-cider-93918/agias:latest reports

	gcloud docker -a
	docker push us.gcr.io/lexical-cider-93918/agias:latest

	kubectl create -f agias-k8s.yml
	kubectl set image deployments/agias agias=us.gcr.io/lexical-cider-93918/agias:latest

	kubectl expose deployment agias --port=80 --target-port=5000

clean-dev:
	gcloud container clusters get-credentials playground
	kubectl delete deployment agias
	kubectl delete service agias
