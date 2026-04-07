### 📊 우리 프로젝트 DB 설계도 (ERD)

```mermaid
erDiagram
    USER ||--o{ TICKET : "판매"
    USER ||--o{ ORDER : "구매"
    TICKET ||--|| ORDER : "성립"


    USER {
        int id PK "고유번호"
        string nickname "닉네임"
        string kakao_id "카카오ID"
        string email "이메일"
        string pw "비밀번호"
        string number "전화번호"
        string birth_date "생년월일"
        string address "주소"
    }
    TICKET {
        int id PK "티켓번호"
        int seller_id FK "판매자ID"
        string team_name "구단명"
        string sub_category "상세구간"
        int price "가격"
        string pin "PIN번호"
        string status "상태"
    }
    ORDER {
        int id PK "주문번호"
        int ticket_id FK "티켓ID"
        int buyer_id FK "구매자ID"
        datetime created_at "거래시간"
    }