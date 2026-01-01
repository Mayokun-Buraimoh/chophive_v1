# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for ChopHive.

## Required Environment Variables

You need to create `.env` files in both the backend and frontend directories with your Google OAuth credentials.

## Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Configure the OAuth consent screen if prompted
6. Choose **Web application** as the application type
7. Add authorized JavaScript origins:
   - For development: `http://localhost:5173` and `http://127.0.0.1:5173`
   - For production: Add your production domain
8. Copy your **Client ID** (it will look like: `123456789-abcdefghijklmnop.apps.googleusercontent.com`)

## Step 2: Create Backend .env File

Create a file named `.env` in the `chophive_v1/backend/` directory with the following content:

```env
# Django Settings
SECRET_KEY=django-insecure-y(m4ssw(juk#6-@yl3xxw)7mg0m)jai%f2y$ifqug0t1#(csge
DEBUG=True

# Google OAuth Settings
# Replace YOUR_GOOGLE_CLIENT_ID with your actual Google Client ID
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com

# Email Settings (Optional)
# FROM_EMAIL=chophive01@gmail.com
# MAILER_SEND_API_TOKEN=your_mailer_send_token_here
```

**Important:** Replace `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com` with your actual Google Client ID.

## Step 3: Create Frontend .env File

Create a file named `.env` in the `chophive_v1/frontend/` directory with the following content:

```env
# Google OAuth Client ID
# Replace YOUR_GOOGLE_CLIENT_ID with your actual Google Client ID
VITE_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com

# API Base URL (if needed to change)
# VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

**Important:** Replace `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com` with your actual Google Client ID.

## Step 4: Restart Your Development Servers

After creating the `.env` files:

1. **Backend**: Restart your Django development server
   ```bash
   cd chophive_v1/backend
   python manage.py runserver
   ```

2. **Frontend**: Restart your Vite development server
   ```bash
   cd chophive_v1/frontend
   npm run dev
   ```

## Verification

1. Navigate to the login page in your frontend application
2. You should see a Google Sign-In button
3. Click it and you should be able to sign in with your Google account
4. After successful authentication, you should be redirected to the food menu page

## Troubleshooting

### Google Sign-In button not appearing
- Check that `VITE_GOOGLE_CLIENT_ID` is set correctly in your frontend `.env` file
- Make sure you've restarted your frontend development server after creating the `.env` file
- Verify that the Google Sign-In script is loaded (check browser console for errors)

### "Invalid token format" error
- Ensure your Google Client ID is correct
- Verify that the authorized JavaScript origins in Google Cloud Console match your development URL
- Check that the credential token is being sent correctly from the frontend

### User not being created
- Check the backend logs for any errors
- Verify that the email from Google token is valid
- Ensure the database is accessible and migrations are up to date

## Security Notes

- **Never commit `.env` files to version control** - they are already in `.gitignore`
- Use different Client IDs for development and production
- In production, use environment variables from your hosting platform instead of `.env` files
- Consider implementing proper token verification using Google's public keys for production use

