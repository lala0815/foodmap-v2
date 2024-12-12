from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 替換為你的隨機密鑰

# 假設 restaurants.csv 檔案結構包含 name, type, latitude, longitude, address 等資訊
df = pd.read_csv('restaurants.csv')

# 模擬使用者資料庫
users = {}

@app.route('/')
def index():
    # 首頁顯示標題、跳轉按鈕以及登入按鈕
    return render_template('index.html')

@app.route('/map', methods=['GET', 'POST'])
def map():
    filtered_restaurants = df

    if request.method == 'POST':
        # 獲取關鍵字
        keyword = request.form.get('keyword', '').strip()

        if keyword:
            # 根據關鍵字篩選餐廳，對餐廳名稱、類型和地址進行模糊匹配
            filtered_restaurants = filtered_restaurants[
                filtered_restaurants['name'].str.contains(keyword, case=False, na=False) |
                filtered_restaurants['type'].str.contains(keyword, case=False, na=False) |
                filtered_restaurants['address'].str.contains(keyword, case=False, na=False)
            ]

    # 將篩選後的餐廳資料傳遞到前端
    restaurants = filtered_restaurants[['name', 'latitude', 'longitude']].to_dict(orient='records')
    return render_template('map.html', restaurants=restaurants)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['user'] = username  # 設置會話
            return redirect(url_for('index'))
        else:
            error_message = '登入失敗，請檢查使用者名稱或密碼'
            return render_template('login.html', error_message=error_message)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username not in users:
            users[username] = password
            # 註冊成功後，傳遞訊息到前端
            success_message = '註冊成功！請返回登入頁面'
            return render_template('register.html', success_message=success_message)
        else:
            # 傳遞錯誤訊息
            error_message = '使用者名稱已被註冊'
            return render_template('register.html', error_message=error_message)
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # 清除會話
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)