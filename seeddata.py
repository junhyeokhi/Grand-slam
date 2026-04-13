import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Ticket
from constants import KBO_TEAMS

def insert_all_test_data():
    app = create_app()
    with app.app_context():
        print("1. 테스트 유저 10명 생성 중...")
        user_list = []
        for i in range(1, 11):
            email = f'user{i}@test.com'
            # 중복 체크 (이미 있으면 스킵)
            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                user = User(
                    username=f'테스터{i}',
                    nickname=f'티켓매니아{i}',
                    email=email,
                    password=generate_password_hash('1234'),
                    phone=f'010-1234-567{i-1}',
                    address=f'경기도 수원시 팔달구 테스트로 {i}길'
                )
                db.session.add(user)
                user_list.append(user)
            else:
                user_list.append(existing_user)
        
        db.session.commit() # 유저 먼저 저장 (ID 생성을 위해)

        print("2. 티켓 랜덤 데이터 300개 생성 중...")
        sub_categories = ['중앙지정석', '1루 내야석', '3루 내야석', '외야 자유석', '테이블석', '블루석']
        
        for i in range(300):
            # 1. 딕셔너리 리스트에서 랜덤하게 2팀을 뽑습니다.
            selected_teams = random.sample(KBO_TEAMS, 2)
            
            # 2. 각 딕셔너리에서 'name' 키에 해당하는 글자만 추출합니다.
            home_team_name = selected_teams[0]['name']
            away_team_name = selected_teams[1]['name']

            ticket = Ticket(
                seller_id=random.choice(user_list).id,
                Hometeam_name=home_team_name, # '한화 이글스' 같은 글자만 들어감
                awayteam_name=away_team_name, # 'KIA 타이거즈' 같은 글자만 들어감
                sub_category=random.choice(sub_categories),
                seat=f"{random.randint(1, 20)}구역 {random.randint(1, 15)}열",
                quantity=random.randint(1, 4),
                price=random.choice([12000, 15000, 25000, 35000, 50000]),
                pin=f"PIN-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                status='판매중',
                game_date=datetime.now() + timedelta(days=random.randint(1, 30))
            )
            db.session.add(ticket)

        db.session.commit()
        print(f'성공: 유저 {len(user_list)}명과 티켓 300개가 생성되었습니다.')

if __name__ == '__main__':
    insert_all_test_data()