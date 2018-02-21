IMAGE_REPO = us.gcr.io/lexical-cider-93918
SERVICE_NAME = $(shell basename $$(pwd))
COMMIT = $(shell git rev-parse --short HEAD)
IMAGE_NAME = $(IMAGE_REPO)/$(SERVICE_NAME):$(COMMIT)
TEST_COMMAND = pytest .
TARGET_PORT = 5000
PATCH_FILE = patch.json


.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .


.PHONY: local-test
test: build
	docker run -it $(IMAGE_NAME) $(TEST_COMMAND)


.PHONY: deploy
deploy: test cluster
	gcloud docker -- push $(IMAGE_NAME)
	kubectl run $(SERVICE_NAME) --image=$(IMAGE_NAME) --port=$(TARGET_PORT)
ifdef PATCH_FILE
	kubectl patch deployment $(SERVICE_NAME) --patch '$(subst {{service_name}},$(SERVICE_NAME),$(shell cat $(PATCH_FILE)))'
endif
	kubectl expose deployment $(SERVICE_NAME) --port=80 --target-port=$(TARGET_PORT)


.PHONY: clean
clean: cluster
	-docker rmi $(IMAGE_NAME)
	-kubectl delete deployment $(SERVICE_NAME)
	-kubectl delete service $(SERVICE_NAME)


.PHONY: cluster
cluster:
ifndef CLUSTER
	$(error CLUSTER is undefined)
endif
	-gcloud container clusters create $(CLUSTER) \
		--preemptible \
		--enable-autoscaling \
		--num-nodes 1 \
		--min-nodes 0 \
		--max-nodes 5
	gcloud container clusters get-credentials $(CLUSTER)


# Pipenv commands
.PHONY: install
install: build
	docker run -it -v $(shell pwd):$(shell docker run $(IMAGE_NAME) pwd) $(IMAGE_NAME) pipenv install $(PACKAGE)


.PHONY: uninstall
uninstall: build
	docker run -it -v $(shell pwd):$(shell docker run $(IMAGE_NAME) pwd) $(IMAGE_NAME) pipenv uninstall $(PACKAGE)


.PHONY: lock
lock: build
	docker run -it -v $(shell pwd):$(shell docker run $(IMAGE_NAME) pwd) $(IMAGE_NAME) pipenv lock


.venv: build
	docker run -it -v $(shell pwd):$(shell docker run $(IMAGE_NAME) pwd) $(IMAGE_NAME) pipenv --three


# httpie command
.PHONY: http
http: cluster
	kubectl run -it --rm httpie-$(shell whoami)-$$RANDOM --image=clue/httpie --restart=Never --command bash
