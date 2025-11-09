# Troubleshooting Login Issues

## Issue: 403 Forbidden and CORS errors with Google OAuth

### Steps to Fix:

1. **Update Google OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to: APIs & Services > Credentials
   - Select your OAuth 2.0 Client ID
   - Under "Authorized JavaScript origins", add:
     ```
     https://ep4xixdyhj.execute-api.ap-northeast-2.amazonaws.com
     ```
   - Under "Authorized redirect URIs", add:
     ```
     https://ep4xixdyhj.execute-api.ap-northeast-2.amazonaws.com/dev/login
     https://ep4xixdyhj.execute-api.ap-northeast-2.amazonaws.com/dev/
     https://ep4xixdyhj.execute-api.ap-northeast-2.amazonaws.com/op/login
     https://ep4xixdyhj.execute-api.ap-northeast-2.amazonaws.com/op/
     ```
   - Click Save

2. **Redeploy the application**
   ```bash
   npm run deploy:dev
   ```

3. **Test the login**
   - Clear browser cache and cookies for the site
   - Try logging in again

### Additional Notes:

- The CORS policy has been updated in both `app.py` and `serverless.yml`
- The admin email is set to: `ssignalckh@gmail.com`
- Admin can login without being in the users table
- Make sure you're using the correct Google Client ID that matches the authorized origins

### If issue persists:

Check the Lambda logs:
```bash
npm run logs:dev
```

Or manually:
```bash
serverless logs -f app --stage dev --tail
```
