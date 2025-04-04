from typing import List, Dict
import mysql.connector
from datetime import datetime
from app.models.chat import ChatMessage
from app.services.nlp_service import NLPService
from app.services.recommender_service import RecommenderService

class ChatService:
    def __init__(self):
        self.nlp_service = NLPService()
        self.recommender_service = RecommenderService()
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'csdl_phim'
        }
    
    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    async def process_message(self, message: str, user_id: str) -> Dict:
        try:
            # Phân tích intent
            intent = self.nlp_service.analyze_intent(message)
            
            # Xử lý các intent khác nhau
            if intent == "greeting":
                return {
                    "message": "Xin chào! Tôi có thể giúp bạn tìm phim. Bạn muốn xem thể loại phim gì?",
                    "recommendations": None
                }
                
            elif intent == "thank":
                return {
                    "message": "Không có gì! Bạn cần tìm thêm phim nào không?",
                    "recommendations": None
                }
                
            elif intent == "movie_search" or "phim" in message.lower():
                # Trích xuất preferences
                preferences = self.nlp_service.extract_preferences(message)
                
                # Tìm phim theo preferences
                movies = await self.recommender_service.search_movies_by_preferences(preferences)
                
                if not movies:
                    return {
                        "message": "Xin lỗi, tôi không tìm thấy phim phù hợp. Bạn có thể thử tìm phim khác không?",
                        "recommendations": None
                    }
                    
                # Format response với danh sách phim
                response = "Đây là những phim phù hợp với yêu cầu của bạn:\n\n"
                for i, movie in enumerate(movies, 1):
                    response += f"{i}. {movie['title']}\n"
                    if movie.get('genres'):
                        response += f"   Thể loại: {movie['genres']}\n"
                    if movie.get('description'):
                        response += f"   Mô tả: {movie['description'][:150]}...\n"
                    if movie.get('slug'):
                        response += f"   Link: /phim/{movie['slug']}\n"
                    response += "\n"
                
                response += "\nBạn muốn xem chi tiết phim nào? (Nhập số thứ tự hoặc tên phim)"
                
                return {
                    "message": response,
                    "recommendations": movies
                }
                
            else:
                # Fallback response
                return {
                    "message": "Tôi có thể giúp bạn tìm phim theo thể loại hoặc tên phim. Bạn muốn xem phim gì?",
                    "recommendations": None
                }

        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            return {
                "message": "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
                "recommendations": None
            }

    async def search_movies(self, query: str) -> List[Dict]:
        """Tìm kiếm phim trong database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            search_query = """
                SELECT 
                    p.id,
                    p.ten_phim AS title,
                    p.mo_ta AS description,
                    GROUP_CONCAT(DISTINCT tl.ten_the_loai SEPARATOR ', ') AS genres
                FROM phims p
                LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
                LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
                WHERE p.ten_phim LIKE %s
                GROUP BY p.id
                LIMIT 5
            """
            
            cursor.execute(search_query, (f"%{query}%",))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return results
        except Exception as e:
            print(f"Error in search_movies: {str(e)}")
            return []

    async def get_movie_detail(self, movie_id: int) -> Dict:
        """Lấy chi tiết phim từ database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    p.*,
                    GROUP_CONCAT(DISTINCT tl.ten_the_loai SEPARATOR ', ') AS genres,
                    GROUP_CONCAT(DISTINCT dd.ten_dao_dien SEPARATOR ', ') AS directors,
                    GROUP_CONCAT(DISTINCT dl.ten_dien_vien SEPARATOR ', ') AS actors
                FROM phims p
                LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
                LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
                LEFT JOIN chi_tiet_dao_diens ctdd ON p.id = ctdd.id_phim
                LEFT JOIN dao_diens dd ON ctdd.id_dao_dien = dd.id
                LEFT JOIN chi_tiet_dien_viens ctdl ON p.id = ctdl.id_phim
                LEFT JOIN dien_viens dl ON ctdl.id_dien_vien = dl.id
                WHERE p.id = %s
                GROUP BY p.id
            """
            
            cursor.execute(query, (movie_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result if result else {}
        except Exception as e:
            print(f"Error in get_movie_detail: {str(e)}")
            return {}

    def format_movie_recommendations(self, movies: List[Dict]) -> str:
        """Format danh sách phim đề xuất"""
        if not movies:
            return "Xin lỗi, tôi không tìm thấy phim phù hợp với yêu cầu của bạn."
            
        response = "Đây là một số phim bạn có thể thích:\n\n"
        for i, movie in enumerate(movies, 1):
            response += f"{i}. {movie['title']}\n"
            if movie.get('genres'):
                response += f"   Thể loại: {movie['genres']}\n"
            if movie.get('description'):
                response += f"   Mô tả: {movie['description'][:100]}...\n"
            response += "\n"
        
        response += "\nBạn muốn xem chi tiết phim nào? (Nhập số thứ tự hoặc tên phim)"
        return response

    def format_movie_search_results(self, movies: List[Dict]) -> str:
        """Format kết quả tìm kiếm phim"""
        if not movies:
            return "Không tìm thấy phim nào phù hợp với yêu cầu của bạn."
            
        response = "Kết quả tìm kiếm:\n\n"
        for i, movie in enumerate(movies, 1):
            response += f"{i}. {movie['title']}\n"
            if movie.get('genres'):
                response += f"   Thể loại: {movie['genres']}\n"
            if movie.get('description'):
                response += f"   Mô tả: {movie['description'][:100]}...\n"
            response += "\n"
            
        response += "\nBạn muốn xem chi tiết phim nào?"
        return response

    def format_movie_detail(self, movie: Dict) -> str:
        """Format chi tiết phim"""
        if not movie:
            return "Không tìm thấy thông tin phim."
            
        response = f"Chi tiết phim: {movie['ten_phim']}\n\n"
        if movie['genres']:
            response += f"Thể loại: {movie['genres']}\n"
        if movie['directors']:
            response += f"Đạo diễn: {movie['directors']}\n"
        if movie['actors']:
            response += f"Diễn viên: {movie['actors']}\n"
        if movie['mo_ta']:
            response += f"\nTóm tắt: {movie['mo_ta']}\n"
            
        return response

    async def save_chat_history(self, chat_message: ChatMessage):
        """Lưu lịch sử chat vào database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO lich_su_chat 
                (id_khach_hang, message, response, intent, created_at) 
                VALUES (%s, %s, %s, %s, %s)
            """
            
            values = (
                chat_message.user_id,
                chat_message.message,
                chat_message.response,
                chat_message.intent,
                datetime.now()
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Error saving chat history: {str(e)}") 