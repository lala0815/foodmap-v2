from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 替換為你的隨機密鑰

# CSV 檔案路徑
USERS_CSV_PATH = os.path.join('csv_files', 'users.csv')
RESTAURANTS_CSV_PATH = os.path.join('csv_files', 'restaurant.csv')

# 讀取 CSV 中的用戶資料
def read_users_from_csv():
    users = {}
    if os.path.exists(USERS_CSV_PATH):
        with open(USERS_CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[row['username']] = row['password']
    return users

# 註冊新用戶到 CSV
def register_user_to_csv(username, password):
    users = read_users_from_csv()
    # 若用戶名已存在，返回 False
    if username in users:
        return False
    # 若用戶名不存在，新增用戶到 CSV
    with open(USERS_CSV_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([username, password])
    return True

# 讀取 CSV 中的餐廳資料
def read_restaurants_from_csv():
    restaurants = []
    if os.path.exists(RESTAURANTS_CSV_PATH):
        with open(RESTAURANTS_CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                restaurant = {
                    'name': row['name'],
                    'type': row['type'],
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude'])
                }
                restaurants.append(restaurant)
    return restaurants

# 新增餐廳到 CSV
def add_restaurant_to_csv(name, type, latitude, longitude):
    with open(RESTAURANTS_CSV_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([name, type, latitude, longitude])

@app.route('/')
def index():
    username = session.get('user')
    return render_template('index.html', username=username)

@app.route('/map', methods=['GET', 'POST'])
def map():
    restaurants = read_restaurants_from_csv()  # 讀取餐廳資料
    return render_template('map.html', restaurants=restaurants)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        if username == "" or password == "":
            error_message = '使用者名稱或密碼不可為空'
            return render_template('login.html', error_message=error_message)

        users = read_users_from_csv()  # 讀取 CSV 中的用戶資料
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error_message = '登入失敗，請檢查使用者名稱或密碼'
            return render_template('login.html', error_message=error_message)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        if username == "" or password == "":
            error_message = '使用者名稱或密碼不可為空'
            return render_template('register.html', error_message=error_message)

        if register_user_to_csv(username, password):  # 嘗試註冊用戶
            return redirect(url_for('login'))
        else:
            error_message = '使用者名稱已被註冊'
            return render_template('register.html', error_message=error_message)
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/add_restaurant', methods=['GET', 'POST'])
def add_restaurant():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        type = request.form.get('type').strip()
        latitude = float(request.form.get('latitude').strip())
        longitude = float(request.form.get('longitude').strip())

        add_restaurant_to_csv(name, type, latitude, longitude)
        return redirect(url_for('map'))  # 重定向到地圖頁面

    return render_template('add_restaurant.html')  # 顯示新增餐廳的表單

if __name__ == '__main__':
    app.run(debug=True)
