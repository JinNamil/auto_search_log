import os
import fnmatch
import configparser
from collections import Counter, defaultdict
import sys
from concurrent.futures import ProcessPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "log_config.ini")

def print_progress(current, total, bar_length=40):
    percent = current / total
    arrow = '#' * int(percent * bar_length)
    spaces = '-' * (bar_length - len(arrow))
    sys.stdout.write(f"\r진행 중: [{arrow}{spaces}] {percent*100:.1f}% ({current}/{total})")
    sys.stdout.flush()

def process_file(filepath, keywords):
    file_counter = Counter()
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
            lowered = data.lower()
            for keyword in keywords:
                count = lowered.count(keyword.lower())
                if count > 0:
                    file_counter[keyword] += count
            # 라인별 결과 저장 (필요시 사용)
            for idx, line in enumerate(data.splitlines(), start=1):
                line_lower = line.lower()
                for keyword in keywords:
                    if keyword.lower() in line_lower:
                        results.append(f"{filepath}:{idx}: {line.strip()}")
                        break
    except Exception as e:
        print(f"\n파일 열기 실패: {filepath} ({e})")
    return filepath, file_counter, results

from concurrent.futures import ProcessPoolExecutor, as_completed

def search_logs(log_dir, patterns_str, keywords):
    all_files = []
    patterns = [p.strip() for p in patterns_str.split(',') if p.strip()]
    
    for root, _, files in os.walk(log_dir):
        matched_files = set()
        for pattern in patterns:
            matched_files.update(fnmatch.filter(files, pattern))
        for filename in matched_files:
            all_files.append(os.path.join(root, filename))

    total_files = len(all_files)

    results = []
    keyword_counter = Counter()
    file_keyword_counter = defaultdict(Counter)

    with ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(process_file, f, keywords): f for f in all_files}
        for idx, future in enumerate(as_completed(futures), start=1):
            filepath, file_counter, file_results = future.result()
            print_progress(idx, total_files)
            results.extend(file_results)
            for k, v in file_counter.items():
                keyword_counter[k] += v
                file_keyword_counter[filepath][k] += v
    print()
    return results, keyword_counter, file_keyword_counter

def print_table(keywords, file_keyword_counter):
    files = sorted(file_keyword_counter.keys())
    header = ["파일명"] + keywords

    max_file_len = max(len(os.path.basename(f)) for f in files) if files else 0
    file_col_width = max(max_file_len, len(header[0])) + 2  # 데이터 열 너비

    num_col_widths = []
    for keyword in keywords:
        max_num_len = max((len(str(file_keyword_counter[f].get(keyword, 0))) for f in files), default=1)
        num_col_widths.append(max(max_num_len, len(keyword)) + 2)

    # 헤더용: 파일명 열만 3칸 줄임 (최소 1 이상)
    header_file_col_width = max(1, file_col_width - 3)

    header_format = f"{{:^{header_file_col_width}}}" + " | " + " | ".join(f"{{:^{w}}}" for w in num_col_widths)
    row_format = f"{{:<{file_col_width}}}" + " | " + " | ".join(f"{{:>{w}}}" for w in num_col_widths)

    total_width = file_col_width + sum(num_col_widths) + 3 * len(num_col_widths)

    title = "=== 파일별 키워드 통계 ==="
    print("\n" + title.center(total_width))

    # 헤더 출력 (파일명 컬럼만 3칸 줄여서 중앙 정렬)
    print(header_format.format(header[0], *header[1:]))

    print("-" * total_width)

    # 데이터 출력 (파일명 왼쪽 정렬, 숫자 오른쪽 정렬)
    for filepath in files:
        row = [os.path.basename(filepath)] + [file_keyword_counter[filepath].get(k, 0) for k in keywords]
        print(row_format.format(*row))

    print("=" * total_width + "\n")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')

    if not config.has_section('LOG'):
        raise RuntimeError(f"[LOG] 섹션을 {CONFIG_PATH}에서 찾을 수 없습니다!")

    log_dir = config.get('LOG', 'log_dir')
    file_pattern = config.get('LOG', 'file_pattern')

    # log_dir이 존재하지 않으면 생성
    if not os.path.exists(log_dir):
        print(f"'{log_dir}' 경로가 존재하지 않아 생성합니다.")
        os.makedirs(log_dir, exist_ok=True)

    keywords = [config.get('SEARCH', key).strip('"').strip() for key in config['SEARCH']]

    output_file = os.path.join(BASE_DIR, config.get('OUTPUT', 'output_file'))

    results, keyword_counter, file_keyword_counter = search_logs(log_dir, file_pattern, keywords)

    print("\n=== 키워드 검색 통계 ===")
    for keyword in keywords:
        print(f"{keyword}: {keyword_counter.get(keyword, 0)} 회")
    print("=======================\n")

    if file_keyword_counter:
        print_table(keywords, file_keyword_counter)

    if results:
        save_choice = input(f"{len(results)}개의 결과가 검색되었습니다. 결과를 '{output_file}'에 저장할까요? (y/n): ").strip().lower()
        if save_choice == 'y':
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write("\n".join(results))
            print(f"검색 결과가 {output_file}에 저장되었습니다.")
        else:
            print("검색 결과를 저장하지 않았습니다.")
    else:
        print("검색 결과가 없습니다.")

