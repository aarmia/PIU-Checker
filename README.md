# PIU-Checker App 
- - - 
> Pump it up 유저 플레이 데이터 시각화 어플리케이션
>> 개인 사용 목적 개발


### 👨‍🏫 프로젝트 소개
- - -
아케이드 리듬게임 "Pump It Up"의 사용자 데이터를 이용자의 모바일 기기에서 간편하게 확인할 수 있도록 제작된 어플리케이션입니다.
> 확인 가능한 정보
- 닉네임
- 칭호
- **모든 레벨의 레이팅 / 클리어 곡 개수**
- 각각의 레벨의 클리어 플레이트
- **펌빌리티**
- 펌빌리티에 영향을 미치는 상위 50곡의 데이터
- **최근 플레이 50곡**
- **사용자의 곡 클리어 체크리스트**
  - 각 레벨 별 클리어 리스트 제공
  - 싱글 / 더블 구분
  - 클리어 점수 내림차순으로 곡 리스트 제공

 
### 📌 프로젝트 설명

| ![](https://github.com/aarmia/PIU-Checker/blob/master/login_page.png) | ![](https://github.com/aarmia/PIU-Checker/blob/master/home_page.png) | ![](https://github.com/aarmia/PIU-Checker/blob/master/pumbility_page.png) | ![](https://github.com/aarmia/PIU-Checker/blob/master/recent_page.png) | ![](https://github.com/aarmia/PIU-Checker/blob/master/checklist_page.png) |
|------------------------------------------------------------------|-----------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------|----------------------------------------------------------------------|
| **로그인 페이지**                                                    | **홈페이지**                                                        | **펌빌리티 페이지**                                                      | **최근 플레이 페이지**                                                | **체크리스트 페이지**                                                    |

### 📝 디렉토리 구조
- - -
```bash
Checkers
│  login.py
│  main.py
│  piugame.crt
│  requirements.txt
│  scraper.py 
│  test_main.http
|
├─ certificates 
│  | USERTrust RSA Certification Authority.crt
|  └─Sectigo RSA Domain Validation Secure Server CA.crt
|
├─.idea
│        
└─ api
   ├─routes
   │  │  all_data.py
   │  │  auth.py
   │  │  levels.py
   │  │  pumbility.py
   │  │  recently.py
   │  │  songs.py
   │  │  user.py
   │  └─ __init__.py
   │          
   └─services
       │  db.py
       │  limiter.py
       └─ __init__.py
```             

### 💻 개발 환경 
- - -
- 개발 기간
  - 2024.11.20 (수) ~ 2025.1.18 (토)
 
#### 프론트엔드
- **Version** : Flutter 3.24.2
- **IDE** : Flutter Flow 5.0.26

#### 백엔드
- **Version** : Python 3.10
- **IDE** : PyCharm
- **Framework** : FastAPI

- - - 

### ⚙️ 기술 스택
- 서버 : **AWS EC2**

- 데이터베이스 : **AWS RDS, PostgreSQL**
  > 곡 데이터 저장용 / 추후 기능 추가시 활용 예정
