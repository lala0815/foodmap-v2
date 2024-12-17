from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import pandas as pd
import uuid  # 用於生成唯一的圖片名稱
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 替換為你的隨機密鑰

# 設置圖片儲存路徑
IMAGE_FOLDER = os.path.join(os.getcwd(), 'static', 'images')
# 設置 CSV 資料夾路徑
CSV_FOLDER = os.path.join(os.getcwd(), 'csv_files')

# 檢查資料夾是否存在
if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

# CSV 文件路徑
RESTAURANT_DATA_FILE = os.path.join(CSV_FOLDER, 'restaurants.csv')
REVIEWS_FILE = os.path.join(CSV_FOLDER, 'reviews.csv')
USER_DATA_FILE = os.path.join(CSV_FOLDER, 'users.csv')

# 檢查用戶資料文件是否存在，若不存在則初始化
if not os.path.exists(USER_DATA_FILE):
    pd.DataFrame(columns=['username', 'password']).to_csv(USER_DATA_FILE, index=False)
# 檢查餐廳評論文件是否存在，若不存在則初始化
if not os.path.exists(REVIEWS_FILE):
    pd.DataFrame(columns=['restaurant_name', 'username', 'rating', 'comment']).to_csv(REVIEWS_FILE, index=False)
# 檢查餐廳資料文件是否存在，若不存在則初始化
if not os.path.exists(RESTAURANT_DATA_FILE):
    pd.DateFrame(columns= ['name','type','latitude','longitude','address','phone','owner','rating','image','description']).to_csv(RESTAURANT_DATA_FILE, index=False)
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(imgaes)

@app.route('/')
def index():
    # 檢查用戶是否已登入
    logged_in = 'user' in session
    username = session.get('user') if logged_in else None
    return render_template('index.html', logged_in=logged_in, username=username)

@app.route('/register-restaurant', methods=['GET', 'POST'])
def register_restaurant():
    if request.method == 'POST':
        # 獲取表單資料
        name = request.form.get('name').strip()
        type = request.form.get('type').strip()
        latitude = request.form.get('latitude').strip()
        longitude = request.form.get('longitude').strip()
        address = request.form.get('address').strip()
        phone = request.form.get('phone').strip()
        owner = request.form.get('owner').strip()
        description = request.form.get('description', '').strip()

        # 處理圖片上傳
        images = request.files.getlist('images')  # 獲取多個圖片文件
        image_filenames = []

        # 上傳每個圖片
        for image in images:
            if image.filename:  # 確保圖片名稱存在
                # 確保圖片名稱是安全的
                filename = secure_filename(image.filename)
                # 生成唯一名稱
                unique_filename = str(uuid.uuid4()) + '_' + filename
                image_path = os.path.join(IMAGE_FOLDER, unique_filename)
                image.save(image_path)
                image_filenames.append(unique_filename)

        # 如果沒有上傳圖片，使用預設值或留空
        image_str = ','.join(image_filenames) if image_filenames else ''  # 空值

        # 數據驗證：檢查必填欄位
        if not name or not type or not latitude or not longitude or not address or not phone:
            error_message = 'All required fields (excluding image and description) are mandatory.！'
            return render_template('register-restaurant.html', error_message=error_message)

        # 儲存餐廳資料至 CSV
        new_restaurant = pd.DataFrame({
            'name': [name],
            'type': [type],
            'latitude': [latitude],
            'longitude': [longitude],
            'address': [address],
            'phone': [phone],
            'owner': [owner],  # 儲存負責人名稱
            'rating': [0],  # 初始評分為 0
            'image': [image_str],  # 儲存圖片路徑字符串或空值
            'description': [description]
        })

        # 讀取現有餐廳資料並合併新資料
        restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)
        restaurant_df = pd.concat([restaurant_df, new_restaurant], ignore_index=True)
        restaurant_df.to_csv(RESTAURANT_DATA_FILE, index=False)  # 儲存更新後的 CSV
        
        # 註冊成功後，跳轉到map頁面並聚焦該餐廳的位置
        return redirect(url_for('map', restaurant_name=name, latitude=latitude, longitude=longitude))

    return render_template('register-restaurant.html')

@app.route('/map', methods=['GET'])
def map():
    # 從最新的 restaurants.csv 讀取餐廳資料
    restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)

    # 只選取需要的欄位，並將資料轉換為字典格式
    restaurants = restaurant_df[['name', 'latitude', 'longitude', 'type', 'address', 'phone', 'owner', 'rating', 'image', 'description']].fillna('').to_dict(orient='records')

    # 獲取 URL 參數中的餐廳名稱、緯度和經度
    restaurant_name = request.args.get('restaurant_name')
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)

    restaurant = None

    # 找到對應的餐廳資料
    if restaurant_name:
        restaurant = next((r for r in restaurants if r['name'] == restaurant_name), None)

    # 將餐廳資料傳遞給前端模板
    return render_template('map.html', restaurants=restaurants, restaurant=restaurant, latitude=latitude, longitude=longitude)

@app.route('/restaurant/<restaurant_name>', methods=['GET', 'POST'])
def restaurant_details(restaurant_name):
    restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)

    restaurant = restaurant_df[restaurant_df['name'] == restaurant_name].iloc[0]
    name = restaurant['name']
    type = restaurant['type']
    address = restaurant['address']
    phone = restaurant['phone']
    owner = restaurant['owner']
    rating = restaurant['rating']
    image = str(restaurant['image']) if pd.notna(restaurant['image']) else ''
    description = restaurant['description'] if pd.notna(restaurant['description']) else 'No description'

    reviews_df = pd.read_csv(REVIEWS_FILE)
    reviews = reviews_df[reviews_df['restaurant_name'] == restaurant_name].to_dict(orient='records')

    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login'))

        username = session['user']
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()

        # 如果評論是空白，將其設為 None
        if not comment:
            comment = None

        new_review = pd.DataFrame({
            'restaurant_name': [restaurant_name],
            'username': [username],
            'rating': [rating],
            'comment': [comment]
        })

        reviews_df = pd.concat([reviews_df, new_review], ignore_index=True)
        reviews_df.to_csv(REVIEWS_FILE, index=False)

        updated_rating = reviews_df[reviews_df['restaurant_name'] == restaurant_name]['rating'].mean()
        restaurant_df.loc[restaurant_df['name'] == restaurant_name, 'rating'] = updated_rating
        restaurant_df.to_csv(RESTAURANT_DATA_FILE, index=False)

        return redirect(url_for('restaurant_details', restaurant_name=restaurant_name))

    return render_template(
        'restaurant_details.html',
        name=name,
        type=type,
        address=address,
        phone=phone,
        rating=rating,
        owner=owner,
        image=image,
        description=description,
        reviews=reviews
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password').strip()

        # 讀取用戶資料
        users = pd.read_csv(USER_DATA_FILE)
        # 清理用戶名與密碼
        users['username'] = users['username'].fillna('').astype(str).str.strip().str.lower()
        users['password'] = users['password'].fillna('').astype(str).str.strip()

        # 驗證用戶名和密碼
        if username in users['username'].values:
            stored_password = users.loc[users['username'] == username, 'password'].values[0]
            if password == stored_password:
                session['user'] = username
                return redirect(url_for('index'))

        # 錯誤處理
        error_message = 'Login failed, please check your username or password.'
        return render_template('login.html', error_message=error_message)

    return render_template('login.html')

# 註冊路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        
        # 檢查密碼複雜度
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$', password):
            error_message = '"Password must contain both uppercase and lowercase letters, as well as numbers, and be at least 6 characters long."'
            return render_template('register.html', error_message=error_message)
        
        # 檢查密碼和確認密碼是否匹配
        if password != confirm_password:
            error_message = 'The password and confirmation password do not match.'
            return render_template('register.html', error_message=error_message)

        # 讀取用戶資料
        users = pd.read_csv(USER_DATA_FILE)

        # 清理數據：將 username 欄位轉換為字串，處理空值
        users['username'] = users['username'].fillna('').astype(str).str.strip().str.lower()

        # 檢查用戶是否已存在
        if username in users['username'].values:
            error_message = 'The username is already taken.'
            return render_template('register.html', error_message=error_message)

        # 新增用戶
        new_user = pd.DataFrame({'username': [username], 'password': [password]})
        users = pd.concat([users, new_user], ignore_index=True)

        # 儲存至 CSV
        users.to_csv(USER_DATA_FILE, index=False)

        # 註冊成功，顯示成功訊息並跳轉到登入頁面
        flash('Registration successful! Please return to the login page.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # 清除會話
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')