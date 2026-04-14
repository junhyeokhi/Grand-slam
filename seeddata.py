import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Ticket, Order # ✨ Order 모델 추가 임포트
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
        ticket_list = [] # 생성된 티켓을 담아둘 리스트 (주문 생성에 사용)
        
        for i in range(300):
            selected_teams = random.sample(KBO_TEAMS, 2)
            home_team_dict = selected_teams[0]
            
            detailed_category = random.choice(home_team_dict.get('sub_options', ['기타 구역']))

            block = random.randint(101, 315)
            row = random.randint(1, 20)
            num = random.randint(1, 25)
            seat_detail = f"{block}블록 {row}열 {num}번"

            ticket = Ticket(
                seller_id=random.choice(user_list).id,
                Hometeam_name=home_team_dict['name'],
                awayteam_name=selected_teams[1]['name'],
                sub_category=detailed_category, 
                seat=seat_detail,               
                quantity=random.randint(1, 4),
                price=random.choice([12000, 15000, 25000, 35000]),
                pin=f"PIN-{random.randint(1000, 9999)}",
                status='판매중',
                game_date=datetime.now() + timedelta(days=random.randint(1, 30))
            )
            db.session.add(ticket)
            ticket_list.append(ticket) # 리스트에 추가

        db.session.commit() # 티켓 먼저 저장 (ID 발급을 위해)
        print(f"   -> 티켓 300개 생성 완료.")

        print("3. 주문(Order) 랜덤 데이터 100개 생성 중...")
        # 300개의 티켓 중 무작위로 100개를 골라서 판매완료 처리합니다.
        ordered_tickets = random.sample(ticket_list, 100)
        
        for ticket in ordered_tickets:
            # 자기가 올린 티켓을 자기가 살 수는 없으므로 판매자 제외
            possible_buyers = [u for u in user_list if u.id != ticket.seller_id]
            buyer = random.choice(possible_buyers)
            
            # 주문 객체 생성
            order = Order(
                ticket_id=ticket.id,
                buyer_id=buyer.id,
                # 주문 시간은 현재 기준으로 최근 1~5일 사이로 랜덤하게 세팅
                created_at=datetime.now() - timedelta(days=random.randint(0, 5), hours=random.randint(1, 23))
            )
            db.session.add(order)
            
            # ✨ 디테일 2: 팔린 티켓이므로 상태를 '판매완료'로 변경
            ticket.status = '판매완료'

        db.session.commit()
        print(f'✅ 성공: 유저 {len(user_list)}명, 티켓 300개, 주문 100건이 생성되었습니다.')

if __name__ == '__main__':
    insert_all_test_data()