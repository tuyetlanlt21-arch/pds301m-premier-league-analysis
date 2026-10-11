# Giải thích chi tiết phần lấy dữ liệu Premier League

## Phiên bản được phân tích

Tài liệu này mô tả phần data collection đã được merge vào nhánh `main` tại commit `049e80a` (Merge pull request #6). Phần mới gồm:

1. Xác minh và chốt nguồn dữ liệu.
2. Collector tải CSV từ Football-Data.
3. Ba file raw data cho các mùa 2023/24, 2024/25 và 2025/26.
4. Test cho collector và các quy tắc bảo vệ raw data.

Project hiện đã có raw data, nhưng chưa thực hiện cleaning, feature engineering, phân tích hoặc trực quan hóa.

## Luồng dữ liệu tổng thể

```text
scripts/collect_data.py
  -> chọn mùa hợp lệ
  -> collect_season(season)
  -> fetch_page(url)
  -> parse_matches(csv_text, season)
  -> gắn metadata nguồn cho từng dòng
  -> inspect_records(records)
  -> save_raw_data(records, data/raw/epl_xxxx_raw.csv)
```

Luồng lớn của project là:

```text
Web source
  -> Raw CSV (data/raw, bất biến)
  -> Validate
  -> Clean
  -> Normalize team names
  -> Feature engineering
  -> Analysis
  -> Charts / notebook / report
```

Collector chỉ phụ trách phần trước validation. Nó cố ý không làm sạch, không thay giá trị thiếu và không tạo kết luận phân tích.

## Chọn nguồn dữ liệu

Nguồn chính là Football-Data. Mỗi mùa Premier League có CSV theo pattern:

```text
https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv
```

`E0` là mã Premier League. Mapping mùa được cố định như sau:

| Mùa trong project | Mã Football-Data | File raw tạo ra |
| --- | --- | --- |
| `2023/24` | `2324` | `data/raw/epl_2324_raw.csv` |
| `2024/25` | `2425` | `data/raw/epl_2425_raw.csv` |
| `2025/26` | `2526` | `data/raw/epl_2526_raw.csv` |

Football-Data được chọn vì ba CSV đã audit đều có 380 trận và chứa các field cần cho năm research questions: kết quả, bàn thắng, kết quả hiệp một, shots, shots on target, corners và cards.

FBref chỉ là nguồn tham khảo/cross-check thủ công. Browser có thể mở một match report đã kiểm tra, nhưng automated inspection từng nhận HTTP 403; vì vậy FBref không được dùng làm nguồn tự động chính.

## File `src/data_collection.py`

Đây là module trung tâm của phần thu thập dữ liệu.

### Hằng số cấu hình

```python
SOURCE_NAME = "Football-Data"
SOURCE_URL_TEMPLATE = "https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv"
SEASON_CODES = {"2023/24": "2324", "2024/25": "2425", "2025/26": "2526"}
```

Các hằng số này giới hạn collector vào nguồn và mùa đã kiểm tra. Người dùng không thể vô tình tải một giải hoặc mùa khác chỉ vì truyền URL sai.

`REQUIRED_COLUMNS` là tập các cột cốt lõi:

| Field | Ý nghĩa |
| --- | --- |
| `Date` | Ngày thi đấu |
| `HomeTeam`, `AwayTeam` | Đội nhà và đội khách |
| `FTHG`, `FTAG` | Bàn thắng cả trận của đội nhà/khách |
| `FTR` | Kết quả cả trận: `H`, `D`, `A` |
| `HTHG`, `HTAG`, `HTR` | Bàn thắng/kết quả hiệp một |
| `HS`, `AS` | Số cú sút |
| `HST`, `AST` | Số sút trúng đích |
| `HC`, `AC` | Số phạt góc |

Các cards là optional trong data contract nên không nằm trong required set, dù raw data hiện có các cột `HY`, `AY`, `HR`, `AR`.

`PROVENANCE_COLUMNS` yêu cầu mọi raw row phải có `Season`, `Source`, `CollectionMethod`, `SourceURL`, và `RetrievedAt`. Đây là nền tảng để truy vết nguồn gốc dữ liệu.

### Rate limiting: `_wait_for_request_slot()`

Collector đặt khoảng cách tối thiểu một giây giữa thời điểm bắt đầu các request:

```python
MIN_REQUEST_INTERVAL_SECONDS = 1.0
_REQUEST_LOCK = threading.Lock()
_last_request_started: float | None = None
```

Hàm dùng `threading.Lock()` để tránh nhiều caller cùng đọc/ghi `_last_request_started`, và dùng `time.monotonic()` vì loại đồng hồ này không bị ảnh hưởng bởi thay đổi giờ hệ thống.

Ví dụ request cũ bắt đầu ở giây 100.00 và request mới đến ở 100.25:

```text
Khoảng đã chờ = 100.25 - 100.00 = 0.25 giây
Khoảng cần có = 1.00 giây
sleep = 0.75 giây
```

Biến thời gian được cập nhật trước khi gửi HTTP request, nên request thất bại vẫn được tính vào giới hạn tốc độ. Đây là cách tránh spam server khi mạng hoặc server đang lỗi.

### `fetch_page(url)`

```python
def fetch_page(url: str) -> str:
```

Hàm này tải text CSV từ Football-Data.

Nó thực hiện theo thứ tự:

1. Gọi `_wait_for_request_slot()`.
2. Gọi `requests.get()` với user agent và timeout 20 giây.
3. Gọi `raise_for_status()` để HTTP 4xx/5xx không bị coi là dữ liệu hợp lệ.
4. Chuyển mọi `requests.RequestException` thành `RuntimeError` có chứa URL và lỗi gốc.
5. Từ chối response body rỗng hoặc toàn khoảng trắng.

```python
response = requests.get(
    url,
    headers={"User-Agent": "PremierLeagueCoursework/1.0"},
    timeout=20,
)
```

User agent làm request minh bạch hơn với nguồn dữ liệu. Timeout tránh chương trình treo vô hạn khi server hoặc mạng gặp vấn đề.

Hàm mới chỉ tải text; nó chưa khẳng định nội dung là CSV hợp lệ. Việc đó thuộc `parse_matches()`.

### `parse_matches(page_html, season)`

Tên tham số `page_html` còn từ interface ban đầu, nhưng nội dung thực tế là CSV text.

#### Chặn season ngoài scope

```python
if season not in SEASON_CODES:
    raise ValueError(...)
```

Chỉ các mùa đã được source audit mới được parse. Ví dụ `2022/23` bị từ chối.

#### Đọc CSV và xử lý BOM

```python
reader = csv.DictReader(io.StringIO(page_html.lstrip("\ufeff")))
```

Một số CSV bắt đầu bằng UTF-8 BOM. `lstrip("\ufeff")` bỏ ký tự đó để tên header đầu tiên không bị biến thành `\ufeffDiv`.

`csv.DictReader` chuyển mỗi row thành dict. Tại raw stage, mọi giá trị vẫn là chuỗi; chưa convert goals thành `int` hoặc date thành `datetime`.

#### Kiểm tra header

```python
reader.fieldnames = [field.strip() for field in reader.fieldnames]
missing_columns = sorted(REQUIRED_COLUMNS - set(reader.fieldnames))
```

Khoảng trắng thừa quanh header được bỏ. Nếu thiếu một cột cốt lõi, collector dừng với `ValueError`, thay vì tạo raw file không đủ điều kiện trả lời research questions.

#### Kiểm tra từng row

```python
if None in row or any(value is None for value in row.values()):
    raise ValueError(...)
```

Điều này phát hiện row có số cột không khớp header, thường do CSV hỏng hoặc lệch delimiter.

```python
if any(not row[field].strip() for field in ("Date", "HomeTeam", "AwayTeam")):
    raise ValueError(...)
```

Date, đội nhà và đội khách tạo thành phần cốt lõi của match identity. Thiếu chúng thì row không thể định danh trận.

#### Bảo toàn fixture chưa hoàn tất

```python
row["Season"] = season
records.append(row)
```

Code chỉ thêm `Season`; không fill `FTHG`, `FTAG` hoặc `FTR`. Nếu source có trận chưa đá, các ô đó vẫn để trống. Điều này tuân thủ rule: không được biến fixture chưa hoàn tất thành trận hòa 0-0 giả.

CSV có header nhưng không có row nào cũng bị từ chối.

### `collect_season(season)`

Hàm này điều phối một mùa:

```python
source_url = SOURCE_URL_TEMPLATE.format(season_code=SEASON_CODES[season])
page_text = fetch_page(source_url)
records = parse_matches(page_text, season)
```

Sau đó nó tạo một timestamp UTC cho toàn bộ lần tải:

```python
retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
```

Và thêm cùng provenance vào từng record:

```python
record.update({
    "Source": SOURCE_NAME,
    "CollectionMethod": "HTTP CSV download via requests",
    "SourceURL": source_url,
    "RetrievedAt": retrieved_at,
})
```

Nhờ đó, mỗi dòng có thể trả lời: trận thuộc mùa nào, lấy từ nguồn nào, qua URL nào và được tải lúc nào.

### `inspect_records(records)`

Đây là hàm audit không làm thay đổi records. Nó trả về:

```python
{
    "row_count": ...,
    "incomplete_fixtures": ...,
    "duplicate_keys": ...,
    "blank_values": ...,
}
```

#### Duplicate key

Key được tạo là:

```text
(Season, Date, HomeTeam, AwayTeam)
```

`Counter` đếm số lần từng key xuất hiện. Key nào xuất hiện trên một lần được report, nhưng chưa bị xóa. Raw phase chỉ ghi nhận vấn đề; validation/cleaning phase mới quyết định cách xử lý.

#### Incomplete fixture

Một trận bị tính incomplete khi thiếu `FTHG`, thiếu `FTAG`, hoặc `FTR` không thuộc `H`, `D`, `A`.

Hàm chỉ đếm, không drop row và không thay giá trị thiếu bằng số 0.

#### Blank values

Hàm đếm ô trống của mọi cột, bao gồm các cột bookmaker odds. Điều này cho phép minh bạch chất lượng source dù odds nằm ngoài research scope hiện tại.

### `save_raw_data(records, destination)`

Hàm xuất raw CSV và có ba lớp bảo vệ:

1. Không cho ghi list records rỗng.
2. Không cho ghi nếu thiếu provenance columns.
3. Không cho ghi nếu các record có schema khác nhau.

```python
with destination.open("x", encoding="utf-8", newline="") as output_file:
```

Mode `"x"` là exclusive creation:

- File chưa tồn tại: tạo và ghi.
- File đã tồn tại: ném `FileExistsError`.

Nó không ghi đè raw file cũ. Đây là implementation trực tiếp của quy tắc raw data immutable.

`newline=""` là cách chuẩn khi ghi CSV trên Windows để tránh dòng trống thừa.

## File `scripts/collect_data.py`

Đây là CLI cho người dùng.

Chạy toàn bộ ba mùa:

```powershell
.venv\Scripts\python.exe scripts\collect_data.py
```

Chạy một mùa:

```powershell
.venv\Scripts\python.exe scripts\collect_data.py --seasons 2025/26
```

`argparse` giới hạn `--seasons` bằng `choices=tuple(SEASON_CODES)`, nên mùa sai bị chặn trước khi gọi network.

Mỗi mùa, script:

1. Tạo destination `data/raw/epl_{season_code}_raw.csv`.
2. Gọi `collect_season()`.
3. Gọi `inspect_records()`.
4. Gọi `save_raw_data()`.
5. In row count, incomplete fixtures, duplicate keys và các cột có blank.

Nếu lỗi file system, network, validation hoặc target file đã tồn tại, script in lỗi ra `stderr`, trả exit code 1 và dừng. Nếu chạy nhiều mùa và lỗi ở mùa sau, các file đã lưu của mùa trước được giữ nguyên; collector không overwrite hay rollback raw evidence.

## Raw datasets đã có

Ba file trong `data/raw/` là:

- `epl_2324_raw.csv`
- `epl_2425_raw.csv`
- `epl_2526_raw.csv`

Mỗi file có 380 match rows. Ngoài các field phân tích, raw source còn giữ thông tin referee, fouls, cards và nhiều bookmaker odds columns. Odds được giữ để bảo toàn source nhưng nằm ngoài scope research questions, không được tự ý impute hoặc phân tích.

Mỗi row được thêm năm cột provenance:

| Cột | Ý nghĩa |
| --- | --- |
| `Season` | Mùa do project gán từ mapping URL |
| `Source` | `Football-Data` |
| `CollectionMethod` | `HTTP CSV download via requests` |
| `SourceURL` | URL CSV gốc |
| `RetrievedAt` | Thời điểm tải theo UTC |

Theo audit được ghi trong `DATA_SOURCES.md`, ba file đều có 380 row, không có incomplete fixture, không có duplicate match key, và không có blank ở canonical analysis fields. Một vài cột odds có blank, nhưng đây không phải field nghiên cứu.

## Tests trong `tests/test_data_collection.py`

Tests dùng CSV synthetic thay vì dữ liệu trận thật. Các test kiểm tra:

| Nhóm test | Điều được bảo đảm |
| --- | --- |
| Incomplete fixture | Giá trị thiếu vẫn là chuỗi rỗng, không đổi thành 0 |
| Required columns | Thiếu cột cốt lõi phải raise lỗi |
| Season scope | Mùa không được hỗ trợ phải raise lỗi |
| Input malformed | CSV rỗng, không row, sai số cột hoặc thiếu identity phải fail |
| HTTP failure | Lỗi từ `requests` được bọc thành `RuntimeError` rõ ràng |
| Request interval | Request sau phải sleep đúng thời gian cần thiết |
| Provenance | Mọi row có source metadata chính xác và timestamp chung |
| Audit | Duplicate, blank và incomplete fixture được đếm đúng |
| Save once | File raw tồn tại không bị ghi đè |

## Những gì collector chưa làm

Các việc sau chưa được thực hiện và thuộc phase sau:

- Parse `Date` sang datetime.
- Chuyển goals/shots từ string sang numeric.
- Kiểm tra `FTR` có khớp với `FTHG` và `FTAG` không.
- Chuẩn hóa tên đội.
- Xử lý duplicate.
- Chọn/lọc cột phục vụ analysis.
- Tạo feature như `total_goals`, `goal_difference`, `result_label`.
- Merge nhiều nguồn.
- Phân tích, biểu đồ và report.

Các bước này sẽ thuộc `FootballDataProcessor` trong `src/processor.py`, sau raw collection.

## Đánh giá thiết kế

Phần collector đang làm tốt các điểm quan trọng cho data workflow học thuật:

- nguồn và mùa được kiểm tra trước;
- request có timeout, user agent và rate limiting;
- schema cốt lõi được kiểm tra trước khi ghi file;
- incomplete fixtures được bảo toàn;
- provenance có trên từng row;
- raw data không bị overwrite;
- audit quan sát chất lượng mà không sửa dữ liệu;
- test bao phủ các đường lỗi quan trọng.

Giới hạn hiện tại là collector chỉ kiểm tra cấu trúc và identity cơ bản, chưa kiểm tra semantic validity như goal không âm, FTR có nhất quán với score, hoặc team-name normalization. Đây là ranh giới hợp lý giữa collection và processing, miễn là phase tiếp theo thực sự thực hiện validation trước analysis.
