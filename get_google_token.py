from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    print("=" * 50)
    print("리프레시 토큰을 GitHub 시크릿 'GOOGLE_REFRESH_TOKEN'에 등록하세요:")
    print(creds.refresh_token)
    print("=" * 50)

if __name__ == '__main__':
    main()
