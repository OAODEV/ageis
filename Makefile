IMAGE_REPO=us.gcr.io/lexical-cider-93918
PRODUCT=$(shell basename pwd)
TAG=$(shell git rev-parse --short HEAD)
IMAGE_NAME=$(IMAGE_REPO)/$(PRODUCT):$(TAG)
PORT=80
TARGET_PORT=5000


.PHONY: deploy
deploy: cluster
	docker build -t $(IMAGE_NAME) .

	gcloud docker -a
	docker push $(IMAGE_NAME)

	kubectl create -f agias-k8s.yml
	kubectl set image deployments/agias agias=$(IMAGE_NAME)

	kubectl expose deployment agias --port=$(PORT) --target-port=$(TARGET_PORT)


.PHONY: clean
clean: cluster
	kubectl delete deployment agias
	kubectl delete service agias


.PHONY: cluster
cluster:
ifndef CLUSTER
	$(error CLUSTER is undefined)
endif
	gcloud container clusters get-credentials $(CLUSTER)
