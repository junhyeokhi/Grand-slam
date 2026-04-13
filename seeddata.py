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
        
        db.session.commit()

        print("2. 티켓 랜덤 데이터 300개 생성 중...")
        # 불필요한 sub_categories 리스트 삭제 완료!
        
        for i in range(300):
            selected_teams = random.sample(KBO_TEAMS, 2)
            home_team_dict = selected_teams[0]
            
            # 홈팀의 실제 sub_options 데이터를 활용
            detailed_category = random.choice(home_team_dict.get('sub_options', ['기타 구역']))

            # 사용자가 직접 입력한 듯한 좌석 상세 정보 생성
            block = random.randint(101, 315)
            row = random.randint(1, 20)
            num = random.randint(1, 25)
            seat_detail = f"{block}블록 {row}열 {num}번"

            ticket = Ticket(
                seller_id=random.choice(user_list).id,
                Hometeam_name=home_team_dict['name'],
                awayteam_name=selected_teams[1]['name'],
                sub_category=detailed_category, # 구단-구장 정보가 들어감
                seat=seat_detail,               # 상세 좌석 번호가 들어감
                quantity=random.randint(1, 4),
                price=random.choice([12000, 15000, 25000, 35000]),
                pin=f"PIN-{random.randint(1000, 9999)}",
                status='판매중',
                game_date=datetime.now() + timedelta(days=random.randint(1, 30))
            )
            db.session.add(ticket)

        db.session.commit()
        print(f'성공: 유저 {len(user_list)}명과 티켓 300개가 생성되었습니다.')

if __name__ == '__main__':
    insert_all_test_data()