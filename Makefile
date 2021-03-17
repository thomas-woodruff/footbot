NAME=footbot

.PHONY: bash
bash:
	docker-compose run --service-ports --name $(NAME) $(NAME) bash

.PHONY: black
black:
	docker-compose run --rm $(NAME) black -q -t py38 $(NAME)/ tests/

.PHONY: build
build:
	docker-compose build $(NAME)

.PHONY: clean
clean:
	docker rm -f $(NAME)
	docker image rm $(NAME)_$(NAME)

.PHONY: format
format:
	make black
	make isort
	make lint

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
serve:
	docker-compose run -d --service-ports --name $(NAME) $(NAME)

.PHONY: test
test:
	make pytest
	make lint
