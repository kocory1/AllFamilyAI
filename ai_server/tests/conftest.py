"""
pytest fixtures (Clean Architecture 전용)
"""

from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


# ====================
# Hooks: 테스트 실행 전/후 설정
# ====================


def pytest_configure(config):
    """pytest 시작 시 실행"""
    print("\n" + "=" * 50)
    print("🧪 온식구 AI 서버 테스트 시작 (Clean Architecture)")
    print("=" * 50)


def pytest_unconfigure(config):
    """pytest 종료 시 실행"""
    print("\n" + "=" * 50)
    print("✅ 테스트 완료")
    print("=" * 50)
