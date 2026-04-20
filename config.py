import os

#  프로젝트의 루트 디렉토리 경로
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 2. DB 파일명 market.db
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'market.db'))

# 3. 이벤트 처리 옵션 (메모리 절약을 위해 False 유지)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 4. 세션 보안 키
SECRET_KEY = "class"

# 5. 카카오로그인 키
CLIENT_ID = "a711eec72538ae54213fd68cf8162b29"
CLIENT_SECRET = "pcqgtGFTiS3KIyQ3RcgIzKEzryPdgr5k"
REDIRECT_URI = "http://127.0.0.1:5000/auth/kakao/callback"