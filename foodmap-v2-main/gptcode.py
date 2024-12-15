from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import pandas as pd
import uuid  # 用於生成唯一的圖片名稱
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 替換為你的隨機密鑰

# 設置圖片儲存路徑
IMAGE_FOLDER = os.path.join(os.getcwd(), 'static', 'images')
# 設置 CSV 資料夾路徑
CSV_FOLDER = os.path.join(os.getcwd(), 'csv_files')

# 檢查資料夾是否存在
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)
if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

# CSV 文件路徑
RESTAURANT_DATA_FILE = os.path.join(CSV_FOLDER, 'restaurants.csv')
REVIEWS_FILE = os.path.join(CSV_FOLDER, 'reviews.csv')
USER_DATA_FILE = os.path.join(CSV_FOLDER, 'users.csv')

# 初始化評論文件
if not os.path.exists(REVIEWS_FILE):
    pd.DataFrame(columns=['restaurant_name', 'username', 'rating', 'comment']).to_csv(REVIEWS_FILE, index=False)

# 初始化用戶文件
if not os.path.exists(USER_DATA_FILE):
    pd.DataFrame(columns=['username', 'password']).to_csv(USER_DATA_FILE, index=False)

@app.route('/')
def index():
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
        description = request.form.get('description', '').strip()

        # 處理圖片上傳
        images = request.files.getlist('images')
        image_filenames = []

        if images:
            for image in images:
                if image.filename:
                    filename = secure_filename(image.filename)
                    unique_filename = str(uuid.uuid4()) + '_' + filename
                    image_path = os.path.join(IMAGE_FOLDER, unique_filename)
                    image.save(image_path)
                    image_filenames.append(unique_filename)

        image_str = ','.join(image_filenames) if image_filenames else ''

        # 數據驗證：檢查必填欄位
        if not name or not type or not latitude or not longitude or not address or not phone:
            error_message = '所有必填欄位（不包含圖片和描述）都是必填的！'
            return render_template('register-restaurant.html', error_message=error_message)

        # 儲存餐廳資料至 CSV
        new_restaurant = pd.DataFrame({
            'name': [name],
            'type': [type],
            'latitude': [latitude],
            'longitude': [longitude],
            'address': [address],
            'phone': [phone],
            'rating': [0],  # 初始評分為 0
            'image': [image_str],
            'description': [description]
        })

        restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)
        restaurant_df = pd.concat([restaurant_df, new_restaurant], ignore_index=True)
        restaurant_df.to_csv(RESTAURANT_DATA_FILE, index=False)

        return redirect(url_for('map', restaurant_name=name, latitude=latitude, longitude=longitude))

    return render_template('register-restaurant.html')

@app.route('/restaurant/<restaurant_name>', methods=['GET', 'POST'])
def restaurant_details(restaurant_name):
    restaurant_df = pd.read_csv(RESTAURANT_DATA_FILE)
    if restaurant_name not in restaurant_df['name'].values:
        return "餐廳不存在", 404

    restaurant = restaurant_df[restaurant_df['name'] == restaurant_name].iloc[0]
    name = restaurant['name']
    type = restaurant['type']
    address = restaurant['address']
    phone = restaurant['phone']
    rating = restaurant['rating']
    image = str(restaurant['image']) if pd.notna(restaurant['image']) else ''
    description = restaurant['description'] if pd.notna(restaurant['description']) else '無介紹'

    reviews_df = pd.read_csv(REVIEWS_FILE)
    reviews = reviews_df[reviews_df['restaurant_name'] == restaurant_name].to_dict(orient='records')

    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login'))

        username = session['user']
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()

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
        image=image,
        description=description,
        reviews=reviews
    )

# 其他路由與功能維持不變

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
