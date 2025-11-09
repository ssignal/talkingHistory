# Talking History - AWS Lambda Web Application

A Python web application for managing encrypted history items, running on AWS Lambda with API Gateway and DynamoDB.

## Features

- **Google OAuth2 Login**: User authentication via Google with email authorization
- **Client-Side Encryption**: All data encrypted with user's secret key before storing in DynamoDB
- **User-Specific Data**: Each user can only see their own encrypted data
- **Secret Key Management**: Secret key stored securely in browser localStorage
- **Data Management**: Create, read, update, and delete history items
- **Date-based Views**: Default 2-week data view with next/previous navigation
- **Advanced Search**: Search with AND/OR logic, case sensitivity options
- **Two-stage Deployment**: Support for dev and op (production) environments
- **Admin Features**: User management page for admins only

## Security Model

### Encryption
- **Client-Side**: All sensitive data (name, text/description) is encrypted using AES encryption in the browser before sending to the server
- **Secret Key**: User-provided secret key stored only in browser localStorage (never sent to server)
- **DynamoDB**: Stores only encrypted data
- **Search**: Performed client-side after decrypting data (for security)

### Access Control
- Users can only access their own data
- Admin can manage user permissions
- Email-based authorization in DynamoDB users table

## Architecture

- **Backend**: Python Flask application
- **Deployment**: AWS Lambda via Serverless Framework
- **API**: AWS API Gateway
- **Database**: AWS DynamoDB
- **Authentication**: Session-based with Kakao login integration

## Setup

### Prerequisites

- Node.js and npm (for Serverless Framework)
- Python 3.10
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

4. Set environment variables in `resource/env.json` for each stage:
```json
{
  "dev": {
    "GOOGLE_CLIENT_ID": "your-dev-google-client-id.apps.googleusercontent.com",
    "SECRET_KEY": "your-dev-secret-key",
    "ADMIN_EMAIL": "admin@example.com"
  },
  "op": {
    "GOOGLE_CLIENT_ID": "your-op-google-client-id.apps.googleusercontent.com",
    "SECRET_KEY": "your-op-secret-key",
    "ADMIN_EMAIL": "admin@example.com"
  }
}
```

Note: 
- You can use the same Google Client ID for both stages or create separate OAuth credentials for each environment.
- The ADMIN_EMAIL will be automatically added to the allowed users table when the Lambda function initializes.

### Deployment

Deploy to dev stage:
```bash
npm run deploy:dev
# or
serverless deploy --stage dev
```

Deploy to op (production) stage:
```bash
npm run deploy:op
# or
serverless deploy --stage op
```

Remove deployments:
```bash
npm run remove:dev  # Remove dev
npm run remove:op   # Remove production
```

### Adding Authorized Users

The admin email from `resource/env.json` is automatically added to the users table when the Lambda function initializes.

To add additional authorized users, add their email addresses to the DynamoDB users table:

```bash
aws dynamodb put-item \
    --table-name talking-history-users-dev \
    --item '{"email": {"S": "user@example.com"}}'
```

## API Endpoints

- `GET /` - Redirect to login or secret page
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout user
- `GET /secret` - Secret key entry page
- `GET /data` - Data management page
- `GET /add` - Add new item page
- `GET /search` - Search page
- `GET /users` - User management page (admin only)
- `GET /api/users` - Get all users (admin only)
- `POST /api/users` - Add new user (admin only)
- `DELETE /api/users/<email>` - Remove user (admin only)
- `GET /api/history` - Get history items (user-specific, with date range)
- `POST /api/history` - Create new history item (encrypted)
- `PUT /api/history/<id>` - Update history item (encrypted)
- `DELETE /api/history/<id>` - Delete history item

## DynamoDB Tables

### Users Table
- Primary Key: `email` (String)

### History Table
- Primary Key: `id` (String)
- Sort Key: `createdAt` (Number - Unix timestamp)
- Additional Fields:
  - `userId` (String) - User's email
  - `name` (String) - Encrypted
  - `description` (String) - Encrypted
  - `text` (String) - Encrypted
- GSI: `name-createdAt-index` for name-based queries
- **Note**: All user data fields are encrypted client-side before storage

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
- Set `SECRET_KEY` environment variable for Flask sessions (different from user secret keys)
- Add your domain to Google OAuth authorized origins
- Only authorized email addresses in DynamoDB users table can access the app
- User secret keys are stored only in browser localStorage
- All sensitive data is encrypted client-side using AES encryption (CryptoJS library)
- Data in DynamoDB is encrypted and can only be decrypted by the user with their secret key
- **Important**: If a user loses their secret key, their data cannot be recovered
- Use AWS Secrets Manager for sensitive credentials in production
# talkingHistory
