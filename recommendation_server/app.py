from flask import Flask, request, jsonify
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

# Kết nối MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="csdl_phim"
    )

# Load dữ liệu từ MySQL
def load_data():
    conn = get_db_connection()
    
    # Lấy thông tin phim và thể loại
    query = """
     SELECT 
    p.id, 
    p.ten_phim AS title, 
    MAX(p.mo_ta) AS description, 
    GROUP_CONCAT(DISTINCT tl.ten_the_loai SEPARATOR ', ') AS genres
FROM 
    phims p
LEFT JOIN 
    chi_tiet_the_loais ctl ON p.id = ctl.id_phim
LEFT JOIN 
    the_loais tl ON ctl.id_the_loai = tl.id
GROUP BY 
    p.id, p.ten_phim;
    """
    
    movies_df = pd.read_sql(query, conn)
    conn.close()
    return movies_df

def create_feature_matrix(movies_df):
    # Xử lý text features
    movies_df['combined_features'] = movies_df['genres'].fillna('') + ' ' + movies_df['description'].fillna('')
    
    # Tạo TF-IDF matrix
    tfidf = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2
    )
    feature_matrix = tfidf.fit_transform(movies_df['combined_features'])
    return feature_matrix

def get_recommendations(movie_id, feature_matrix, movies_df, n=5):
    try:
        # Tính similarity matrix
        similarity = cosine_similarity(feature_matrix)
        
        # Lấy index của phim đầu vào
        movie_idx = movies_df[movies_df['id'] == movie_id].index[0]
        
        # Tính điểm similarity với tất cả phim khác
        sim_scores = list(enumerate(similarity[movie_idx]))
        
        # Sắp xếp theo điểm similarity
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Lấy n phim có điểm cao nhất (bỏ qua phim đầu vì là chính nó)
        sim_scores = sim_scores[1:n+1]
        movie_indices = [i[0] for i in sim_scores] 
        
        # Trả về thông tin các phim được recommend
        recommendations = movies_df.iloc[movie_indices][['id', 'title', 'genres']].to_dict('records')
        
        # Thêm điểm similarity vào kết quả
        for idx, rec in enumerate(recommendations):
            rec['similarity_score'] = float(sim_scores[idx][1])
        return recommendations
        
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        return []

def get_user_recently_watched(user_id, limit=5):
    """Lấy danh sách phim user đã xem gần đây"""
    conn = get_db_connection()
    query = """
        SELECT 
            p.id,
            p.ten_phim AS title,
            MAX(p.mo_ta) AS description,
            GROUP_CONCAT(DISTINCT tl.ten_the_loai SEPARATOR ', ') AS genres,
            lx.ngay_xem
        FROM 
            luot_xems lx
            JOIN phims p ON lx.id_phim = p.id
            LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
            LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
        WHERE 
            lx.id_khach_hang = %s
            AND lx.ngay_xem >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY 
            p.id, p.ten_phim, lx.ngay_xem
        ORDER BY 
            lx.ngay_xem DESC
        LIMIT %s
    """
    
    recently_watched_df = pd.read_sql(query, conn, params=(user_id, limit))
    conn.close()
    return recently_watched_df

def get_recommendations_from_multiple_movies(movie_ids, feature_matrix, movies_df, n=5):
    """Lấy recommendations dựa trên nhiều phim"""
    try:
        # Tính similarity matrix
        similarity = cosine_similarity(feature_matrix)
        
        # Tính điểm similarity trung bình với tất cả phim đầu vào
        combined_scores = np.zeros(len(movies_df))
        for movie_id in movie_ids:
            movie_idx = movies_df[movies_df['id'] == movie_id].index[0]
            combined_scores += similarity[movie_idx]
        
        combined_scores = combined_scores / len(movie_ids)
        
        # Tạo list (index, score)
        sim_scores = list(enumerate(combined_scores))
        
        # Loại bỏ các phim đầu vào
        sim_scores = [s for s in sim_scores if movies_df.iloc[s[0]]['id'] not in movie_ids]
        
        # Sắp xếp theo điểm similarity
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Lấy n phim có điểm cao nhất
        sim_scores = sim_scores[:n]
        movie_indices = [i[0] for i in sim_scores]
        
        # Trả về thông tin các phim được recommend
        recommendations = movies_df.iloc[movie_indices][['id', 'title', 'genres']].to_dict('records')
        
        # Thêm điểm similarity
        for idx, rec in enumerate(recommendations):
            rec['similarity_score'] = float(sim_scores[idx][1])
        return recommendations
        
    except Exception as e:
        print(f"Error in get_recommendations_from_multiple_movies: {str(e)}")
        return []

@app.route('/recommend', methods=['POST'])
def recommend_movies():
    try:
        data = request.get_json()
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return jsonify({
                'status': 'error',
                'message': 'Movie ID is required'
            }), 400
            
        # Load và xử lý dữ liệu
        movies_df = load_data()
        feature_matrix = create_feature_matrix(movies_df)
        
        # Lấy recommendations
        recommendations = get_recommendations(
            movie_id=movie_id,
            feature_matrix=feature_matrix,
            movies_df=movies_df,
            n=5
        )
        print(recommendations)
        return jsonify({
            'status': 'success',
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/recommend/history', methods=['POST'])
def recommend_from_history():
    try:
        print("Received request for /recommend/history")
        data = request.get_json()
        print(f"Request data: {data}")
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        # Lấy lịch sử xem gần đây
        recently_watched = get_user_recently_watched(user_id)
        
        if recently_watched.empty:
            return jsonify({
                'status': 'error',
                'message': 'No watching history found'
            }), 404
            
        # Load toàn bộ dữ liệu phim
        movies_df = load_data()
        feature_matrix = create_feature_matrix(movies_df)
        
        # Lấy recommendations dựa trên các phim đã xem
        recent_movie_ids = recently_watched['id'].tolist()
        recommendations = get_recommendations_from_multiple_movies(
            movie_ids=recent_movie_ids,
            feature_matrix=feature_matrix,
            movies_df=movies_df,
            n=5
        )
        print(recommendations)
        return jsonify({
            'status': 'success',
            'recently_watched': recently_watched[['id', 'title', 'genres']].to_dict('records'),
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test_db_connection', methods=['GET'])
def test_db_connection():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    print(f"404 Error: {request.url}")
    return jsonify({
        'status': 'error',
        'message': f'URL not found: {request.url}',
        'method': request.method
    }), 404

# @app.before_request
# def log_request_info():
#     print('Headers:', dict(request.headers))
#     print('Body:', request.get_json() if request.is_json else 'No JSON')
#     print('URL:', request.url)
#     print('Method:', request.method)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)