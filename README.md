# Talking History - AWS Lambda Web Application

A Python web application for managing history items, running on AWS Lambda with API Gateway and DynamoDB.

## Features

- **Google OAuth2 Login**: User authentication via Google with email authorization
- **Data Management**: Create, read, update, and delete history items
- **Date-based Views**: Default 2-week data view with next/previous navigation
- **Search Functionality**: Search by date range, name, or across all fields
- **Two-stage Deployment**: Support for dev and op (production) environments

## Architecture

- **Backend**: Python Flask application
- **Deployment**: AWS Lambda via Serverless Framework
- **API**: AWS API Gateway
- **Database**: AWS DynamoDB
- **Authentication**: Session-based with Kakao login integration

## Setup

### Prerequisites

- Node.js and npm (for Serverless Framework)
- Python 3.11
- AWS CLI configured with appropriate credentials
- Serverless Framework

### Installation

1. Install Serverless Framework and plugins:
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google OAuth2:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials (Web application)
   - Add authorized JavaScript origins (your API Gateway URL)
   - Add authorized redirect URIs
   - Copy the Client ID

4. Set environment variables:
```bash
export GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
export SECRET_KEY="your-secret-key-for-sessions"
```

### Deployment

Deploy to dev stage:
```bash
serverless deploy --stage dev
```

Deploy to op (production) stage:
```bash
serverless deploy --stage op
```

### Adding Authorized Users

To authorize users, add their email addresses to the DynamoDB users table:

```bash
aws dynamodb put-item \
    --table-name talking-history-users-dev \
    --item '{"email": {"S": "user@example.com"}}'
```

## API Endpoints

- `GET /` - Redirect to login or data page
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout user
- `GET /data` - Data management page
- `GET /search` - Search page
- `GET /api/history` - Get history items (with date range)
- `POST /api/history` - Create new history item
- `PUT /api/history/<id>` - Update history item
- `DELETE /api/history/<id>` - Delete history item
- `GET /api/search` - Search history items

## DynamoDB Tables

### Users Table
- Primary Key: `email` (String)

### History Table
- Primary Key: `id` (String)
- Sort Key: `createdAt` (Number - Unix timestamp)
- GSI: `name-createdAt-index` for name-based queries

## Development

To test locally, you can use:
```bash
serverless wsgi serve
```

## Configuration

Stage selection is done via the `--stage` flag during deployment. The application automatically configures:
- Table names with stage suffix
- Environment variables
- IAM roles and permissions

## Security Notes

- Set `GOOGLE_CLIENT_ID` environment variable before deployment
- Set `SECRET_KEY` environment variable for production
- Add your domain to Google OAuth authorized origins
- Only authorized email addresses in DynamoDB users table can access the app
- Use AWS Secrets Manager for sensitive credentials in production
# talkingHistory
