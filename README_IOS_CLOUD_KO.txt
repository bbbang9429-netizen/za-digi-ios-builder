ZA-DIGI Rouge v14 - Mac 없이 iOS 빌드하기 (GitHub Actions)
============================================================

목표
----
이 폴더 자체를 작은 GitHub 저장소로 올리면 GitHub의 macOS runner가:
1) 원본 ZA-DIGI Rouge 저장소를 clone
2) assets/locales submodule까지 자동 다운로드
3) v14 오프라인/커스텀 패치 적용
4) Capacitor iOS 프로젝트 생성
5) iPhone용 unsigned IPA 생성
6) Actions Artifact로 업로드
합니다.

중요
----
- 사용자 PC에 Mac/Xcode가 없어도 됩니다.
- 약 794MB assets를 직접 GitHub에 업로드할 필요가 없습니다.
  workflow가 원본 저장소의 assets/locales submodule을 직접 받습니다.
- 생성되는 IPA는 'unsigned' 입니다. iPhone에 바로 탭해서 설치하는 파일은 아닙니다.
  Windows에서 본인 Apple ID로 서명/설치하는 사이드로딩 도구가 별도로 필요합니다.
- 처음 iOS 런타임 테스트라 Android v14와 완전히 동일하게 동작한다고 아직 단정하지 않습니다.
  파일 불러오기, 터치, 화면 safe-area는 실제 iPhone 테스트 후 보정할 수 있습니다.

GitHub에 올릴 파일
------------------
이 ZIP의 최상위 내용 전체:
  .github/
  patch/
  README_IOS_CLOUD_KO.txt

처음 실행 순서
--------------
1. GitHub에서 새 저장소를 하나 만듭니다. (예: za-digi-ios-builder)
2. 이 ZIP의 내용 전체를 그 저장소 루트에 업로드/commit 합니다.
3. 저장소 상단의 Actions 탭으로 들어갑니다.
4. 왼쪽에서 "Build ZA-DIGI Rouge iOS (Unsigned IPA)" 선택
5. "Run workflow" 버튼을 눌러 실행합니다.
6. 완료 후 해당 실행(run)을 열고 맨 아래 Artifacts에서
   "ZA-DIGI-Rouge-v14-iOS-unsigned"를 다운로드합니다.
7. Artifact ZIP 안에 ZA-DIGI-Rouge-v14-unsigned.ipa가 있습니다.

workflow가 중간에 실패하면
----------------------------
실패한 빨간 단계 이름을 누르고 마지막 오류 부분을 ChatGPT에 보내주세요.
특히 아래 단계의 로그가 중요합니다.
- Clone ZA-DIGI Rouge with assets/locales submodules
- Add Capacitor iOS platform using Swift Package Manager
- Resolve Swift packages
- Build unsigned iPhone app

현재 iOS 기본 설정
------------------
- Bundle ID: net.pokerogue.allinone
- App name: PokeRogue AIO
- 가로모드 Landscape Left/Right
- Full screen
- Capacitor 7.4.2
- Swift Package Manager 사용
- iOS 기기용 Release 빌드
- 코드서명은 클라우드에서 하지 않음

v14 누적 기능
--------------
Android v14에서 적용한 웹/게임 패치는 patch/ 폴더에 그대로 포함되어 있습니다.
- 완전 오프라인 assets
- 서버/API 차단
- .prsv 데이터 호환
- Digimon 스타터 29종 해금
- 특성/패시브/알기술 에디터
- 진화/메가/G-Max 이후 커스텀 특성/패시브 유지
- 아이템 가중치 및 티어 확률 패치
- 스타터 메뉴 스크롤
- 검색 자동완성
- 검색 UI cleanup

첫 iPhone 테스트 권장 항목
--------------------------
1. 실행/홈 화면/가로모드
2. 터치 가상키
3. 새 게임 및 전투
4. BGM/효과음
5. .prsv 파일 불러오기
6. 스타터 특성/패시브/알기술 변경
7. 자동완성 및 검색창 닫힘
8. 저장 후 앱 완전 종료 -> 이어하기
9. 노치/Dynamic Island/Home Indicator와 게임 UI 겹침 여부
