import numpy as np

# ori_data = {"0x0": 1, "0xff": 1}

ori_data = {f"0x{hex_value:02x}": 1 for hex_value in range(256)}

# 결과를 저장할 리스트 초기화
# result = []

# # 데이터 처리
# for hex_value, count in ori_data.items():
#     # 16진수 값을 10진수로 변환
#     decimal_value = int(hex_value, 16)
#     # 10진수 값을 3자리 이진수 배열로 변환
#     binary_array = np.array([int(x) for x in f"{decimal_value:03b}"])
#     # 지정된 횟수만큼 배열을 반복하여 결과 리스트에 추가
#     for _ in range(count):
#         result.append(binary_array)

# # 결과 출력 (예제로 인해 많은 양의 출력을 피하고, 처음 10개만 출력)
# print(result)


def convert_counts_to_samples(count_datas, wires):
    import numpy as np

    # 결과를 저장할 리스트 초기화
    result = []
    for hex_value, count in count_datas.items():
        # 16진수 값을 10진수로 변환
        decimal_value = int(hex_value, 16)

        if decimal_value >= 2**wires:
            decimal_value = 2**wires - 1
        # 10진수 값을 지정된 자릿수의 이진수 배열로 변환
        binary_array = np.array([int(x) for x in f"{decimal_value:0{wires}b}"])
        # 지정된 횟수만큼 배열을 반복하여 결과 리스트에 추가
        for _ in range(count):
            result.append(binary_array)
    return result


def convert_hex_to_binary_arrays(ori_data, wires):
    # 결과를 저장할 리스트 초기화
    result = []

    # 데이터 처리
    for hex_value, count in ori_data.items():
        # 16진수 값을 10진수로 변환
        decimal_value = int(hex_value, 16)
        # 10진수 값을 이진수 문자열로 변환하고, 필요하다면 자릿수 조절
        binary_str = f"{decimal_value:b}"  # 먼저 이진수로 변환
        binary_str_padded = binary_str.zfill(wires)  # 필요한 경우 앞을 0으로 채움
        if len(binary_str_padded) > wires:
            binary_str_padded = binary_str_padded[-wires:]  # 길이 조절

        # 문자열을 이진수 배열로 변환
        binary_array = np.array([int(x) for x in binary_str_padded])
        # 지정된 횟수만큼 배열을 반복하여 결과 리스트에 추가
        for _ in range(count):
            result.append(binary_array)


result1 = convert_counts_to_samples(ori_data, 12)
# result2 = convert_counts_to_samples(ori_data, 3)

print(result1)
# print(result2)
