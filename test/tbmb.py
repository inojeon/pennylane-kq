import time
from tqdm import tqdm
import itertools


def check_api_status():
    # 초기 API 요청

    # for i in range(3000):
    # 200 상태 코드가 나올 때까지 반복
    # time.sleep(0.1)  # 5초 대기
    # 진행 상황 표시
    # tqdm.write("API 상태 확인 중...")

    return 200


def main():
    print("API 요청을 진행 중입니다. 잠시만 기다려주세요...")
    for _ in tqdm(itertools.count(), desc="API 상태 확인"):
        status = check_api_status()
        # if status == 200:
        #     break
        time.sleep(1)  # 5초 대기
    print("API 요청이 완료되었습니다.")
    # 결과 출력
    print(status)


if __name__ == "__main__":
    main()
