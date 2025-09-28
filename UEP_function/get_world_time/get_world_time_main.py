from datetime import datetime
from zoneinfo import ZoneInfo
import get_world_time.time_zone as time_zone


def get_local_time():
    now = datetime.now()
    print("Local time:",now)

def set_timezone(tz):
    tz_key = time_zone.timezone_map[tz]
    assign_time = datetime.now(ZoneInfo(tz_key))
    print(f"{tz_key} is {assign_time}")

def main():
    num = int(input("1.輸出標準時間, 2.輸出指定區域的時間 "))
    if num == 1:
        get_local_time()
    elif num == 2:
        timezone = input("輸入時區:")
        set_timezone(timezone)


if __name__ == "__main__":
    main()