NAME=footbot

.PHONY: bash
bash: clean build
	docker-compose run --service-ports --name $(NAME) $(NAME) bash

.PHONY: black
black:
	docker-compose run --rm $(NAME) black -q -t py38 $(NAME)/ tests/

.PHONY: build
build:
	docker-compose build $(NAME)

.PHONY: clean
clean: clean-container clean-image

.PHONY: clean-container
clean-container:
	docker rm -f $(NAME)

.PHONY: clean-image
clean-image:
	docker image rm $(NAME)_$(NAME)

.PHONY: format
format: black isort lint

.PHONY: isort
isort:
	docker-compose run --rm $(NAME) isort -sl -rc -p $(NAME) $(NAME)/ tests/

.PHONY: lint
lint:
	docker-compose run --rm $(NAME) flake8 --max-line-length 100 $(NAME)

.PHONY: pytest
pytest:
	docker-compose run --rm $(NAME) python -m pytest

.PHONY: serve
serve: clean build
	docker-compose run --service-ports --name $(NAME) $(NAME)

.PHONY: test
test: pytest lint
