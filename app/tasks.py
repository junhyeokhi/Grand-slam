from datetime import datetime, timedelta
from app import db, scheduler
from app.models import Order, Ticket, Notification

# 매일 새벽 1시에 실행되도록 설정 (cron 방식)
# @scheduler.task('cron', id='auto_confirm_job', hour=1, minute=0)
# 1분마다 실행되도록 설정 (테스트용도)
@scheduler.task('interval', id='test_job', seconds=60)
def auto_confirm_purchases():
    # 스케줄러가 DB에 접근하기 위해 app_context를 엽니다.
    with scheduler.app.app_context():
        print(f"[{datetime.now()}] 자동 구매확정 스케줄러 실행 중...")
        
        # 7일 전의 시간 계산
        # seven_days_ago = datetime.now() - timedelta(days=7)
        # 1분 전의 주문 조희
        seven_days_ago = datetime.now() - timedelta(seconds=60)
        # 1. 7일이 지났고 (created_at <= seven_days_ago)
        # 2. 티켓 상태가 '판매완료'인 주문들을 모두 찾습니다.
        target_orders = Order.query.join(Ticket).filter(
            Order.created_at <= seven_days_ago,
            Ticket.status == '판매완료'
        ).all()

        if not target_orders:
            print("업데이트할 대상이 없습니다.")
            return

        # 찾은 주문들의 티켓 상태를 '거래완료'로 변경
        count = 0
        for order in target_orders:
            order.ticket.status = '거래완료'
            
            # 판매자에게 자동 구매 확정 알림 전송
            seller_noti = Notification(
                user_id=order.ticket.seller_id,
                message=f"등록하신 '{order.ticket.Hometeam_name}전' 티켓의 자동 구매확정 및 정산이 진행됩니다.",
                link='/ticket/history/?tab=sales' # 스케줄러 환경이므로 url_for 대신 직접 경로 입력
            )
            db.session.add(seller_noti)
            count += 1
            
        try:
            db.session.commit()
            print(f"총 {count}건의 주문이 자동 구매확정 처리되었습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"스케줄러 DB 저장 에러: {e}")

# 경기 날짜가 지난 방치된 티켓을 '기간만료'로 변경하는 스케줄러
@scheduler.task('interval', id='expire_tickets_job', seconds=60)
def expire_past_tickets():
    with scheduler.app.app_context():
        now = datetime.now()
        
        # 현재 시간보다 game_date가 과거이고, 아직 '판매중'인 티켓 조회
        expired_tickets = Ticket.query.filter(
            Ticket.game_date < now,
            Ticket.status == '판매중'
        ).all()

        if not expired_tickets:
            return
        
        count = 0
        for ticket in expired_tickets:
            ticket.status = '기간만료'
            count += 1
        
        try:
            db.session.commit()
            print(f"[{now}] 총 {count}건의 지난 경기 티켓이 '기간만료' 처리되었습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"스케줄러 DB 저장 에러 (기간만료 처리): {e}")