# Talking History Deployment Scripts

## Deploy to Dev
deploy-dev:
	serverless deploy --stage dev

## Deploy to Production (op)
deploy-op:
	serverless deploy --stage op

## Remove Dev deployment
remove-dev:
	serverless remove --stage dev

## Remove Production deployment
remove-op:
	serverless remove --stage op

## Install dependencies
install:
	npm install
	pip install -r requirements.txt

## Local development server
serve:
	serverless wsgi serve

## Add test user (dev)
add-test-user:
	aws dynamodb put-item \
		--table-name talking-history-users-dev \
		--item '{"email": {"S": "user@example.com"}}'

## Logs (dev)
logs-dev:
	serverless logs -f app --stage dev --tail

## Logs (op)
logs-op:
	serverless logs -f app --stage op --tail

.PHONY: deploy-dev deploy-op remove-dev remove-op install serve add-test-user logs-dev logs-op
