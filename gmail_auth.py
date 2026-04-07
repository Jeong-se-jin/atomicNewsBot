# Gmail API OAuth2 인증 헬퍼

# -*- coding: utf-8 -*-
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def setup_gmail_auth():
    """Gmail API 인증 설정 (최초 1회 브라우저 인증 필요)"""
    creds = None

    # 기존 토큰 파일 확인
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # 토큰이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 최초 인증 (브라우저 열림)
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 토큰 저장
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


if __name__ == '__main__':
    creds = setup_gmail_auth()
    print('[OK] Gmail 인증 완료. token.json 저장됨.')
