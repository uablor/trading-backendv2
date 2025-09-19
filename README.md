


# install requirements.txt 
# use everytime push to git

run : pip freeze > requirements.txt

# install virtualenv 

run : pip install virtualenv

# install .venv

run : virtualenv .venv

# use .venv


run : . .venv/Scripts/activate || ro || source .venv/Scripts/activate

## Start project

run : pip install -r requ.txt

## migrate you modal 
 run : python manage.py migrations
 and run : python manage.py migrate

## start redis server
# run redis server in  port 127.0.0.1:6379 here for shutdown redis-cli shutdown
run : redis-server


# seeder

python seed_admin.py
## start Socket server

run : daphne -p 9000 Core.asgi:application

## start Project

run : python manage.py runserver



# for next แท่งเทียน

  # url = 'https://api.binance.com/api/v3/klines'
            # params = {
            #     'symbol': "BTCUSDT",
            #     'interval': '1m',
            #     'limit': 1,  # ดึงข้อมูลแท่งเทียนล่าสุด
            # }

            # latest_candlestick_id = None  # ใช้เพื่อตรวจสอบแท่งเทียนล่าสุด
            # is_button_enter_last = None  # เก็บสถานะล่าสุดของปุ่ม

            # while True:
            #     response = requests.get(url, params=params)
            #     response.raise_for_status()
            #     data = response.json()

            #     latest_candlestick = data[0]
            #     latest_timestamp = latest_candlestick[0]  # เวลาของแท่งเทียนปัจจุบัน

            #     # คำนวณเวลาแท่งเทียนถัดไป
            #     next_candlestick_time = datetime.utcfromtimestamp(latest_timestamp / 1000) + timedelta(minutes=1)

            #     current_time = datetime.utcnow()
            #     time_diff = next_candlestick_time - current_time
            #     seconds_remaining = int(time_diff.total_seconds())

            #     # ดึงสถานะปัจจุบันของปุ่มจาก Cache
            #     is_button_enter = cache.get('is_button_enter', False)

            #     # ตรวจสอบแท่งเทียนใหม่และเปลี่ยนสถานะ
            #     if latest_candlestick_id != latest_timestamp:
            #         latest_candlestick_id = latest_timestamp  # อัปเดต ID ของแท่งเทียนล่าสุด
            #         if is_button_enter_last is None or is_button_enter != is_button_enter_last:
            #             # เปลี่ยนสถานะปุ่ม
            #             is_button_enter = not is_button_enter
            #             cache.set('is_button_enter', is_button_enter)  # บันทึกสถานะใหม่
            #             cache.set('last_toggled', current_time)  # บันทึกเวลาที่เปลี่ยนสถานะ
            #             is_button_enter_last = is_button_enter  # อัปเดตสถานะล่าสุด