

reformat:
	poetry run black .
	poetry run isort .

test:
	poetry run pytest --black --isort --pylama
