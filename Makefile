start-dev-docker: 
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

migrate-db:
	docker-compose exec web alembic revision --autogenerate
	docker-compose exec web alembic upgrade head
