from typing import Dict, List
import re
import mysql.connector
from datetime import datetime

class NLPService:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'csdl_phim'
        }
        
        # Định nghĩa các pattern cho intent
        self.intent_patterns = {
            "movie_recommendation": [
                r"gợi ý|đề xuất|recommend|suggestion",
                r"phim (hay|tốt|được|nổi tiếng)",
                r"phim (gì|nào) (hay|thú vị)",
                r"muốn xem phim",
            ],
            "movie_search": [
                r"tìm phim",
                r"kiếm phim",
                r"có phim",
                r"phim tên là",
            ],
            "greeting": [
                r"xin chào|hello|hi|hey",
                r"chào (bạn|bot)",
            ],
            "thank": [
                r"cảm ơn|thank|thanks",
                r"cám ơn",
            ],
            "goodbye": [
                r"tạm biệt|bye|goodbye",
                r"hẹn gặp lại",
            ]
        }
        
        # Mapping thể loại phim
        self.genre_mapping = {
            "hành động": "action",
            "kinh dị": "horror",
            "tình cảm": "romance",
            "hài": "comedy",
            "hoạt hình": "animation",
            "khoa học viễn tưởng": "sci-fi",
            "phiêu lưu": "adventure",
            "drama": "drama",
            "tâm lý": "psychological",
            "tội phạm": "crime"
        }

    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    def analyze_intent(self, message: str) -> str:
        """Phân tích ý định từ tin nhắn"""
        message = message.lower().strip()
        
        # Intent patterns đơn giản
        if any(word in message for word in ["tìm", "kiếm", "xem", "có", "gợi ý"]):
            if "phim" in message:
                return "movie_search"
        
        if "chào" in message:
            return "greeting"
            
        if "cảm ơn" in message:
            return "thank"
            
        return "general_chat"

    def extract_preferences(self, message: str) -> Dict:
        """Trích xuất sở thích phim từ tin nhắn"""
        message = message.lower().strip()
        
        # In ra message để debug
        print(f"Extracting preferences from message: {message}")
        
        preferences = {
            "message": message,
            "genres": []
        }
        
        # Thêm các từ khóa thể loại phổ biến
        genre_keywords = {
            "kinh dị": ["kinh dị", "ma", "rùng rợn"],
            "hành động": ["hành động", "action", "đánh nhau"],
            "tình cảm": ["tình cảm", "lãng mạn", "romance"],
            "hoạt hình": ["hoạt hình", "anime", "cartoon"],
            "hài": ["hài", "hài hước", "comedy"]
        }
        
        # Kiểm tra từng từ khóa
        for genre, keywords in genre_keywords.items():
            if any(keyword in message for keyword in keywords):
                preferences["genres"].append(genre)
                print(f"Found genre: {genre}")
        
        return preferences

    async def generate_response(self, message: str) -> str:
        """Tạo câu trả lời cho tin nhắn thông thường"""
        message = message.lower()
        
        # Các mẫu câu trả lời cơ bản
        responses = {
            "greeting": [
                "Xin chào! Tôi có thể giúp gì cho bạn?",
                "Chào bạn! Bạn muốn xem phim gì?",
                "Hi! Tôi có thể gợi ý phim hay cho bạn."
            ],
            "goodbye": [
                "Tạm biệt! Hẹn gặp lại bạn.",
                "Goodbye! Chúc bạn xem phim vui vẻ.",
                "Bye bye! Rất vui được giúp bạn."
            ],
            "thank": [
                "Không có gì! Rất vui được giúp bạn.",
                "Không có chi! Bạn cần gì cứ hỏi nhé.",
                "Đó là nhiệm vụ của tôi!"
            ]
        }
        
        # Kiểm tra intent và trả về câu trả lời phù hợp
        intent = self.analyze_intent(message)
        if intent in responses:
            return responses[intent][0]
                
        return "Xin lỗi, tôi không hiểu ý bạn. Bạn có thể hỏi về gợi ý phim hoặc tìm kiếm phim không?"

    def extract_movie_id(self, message: str) -> int:
        """Trích xuất ID phim từ tin nhắn"""
        # Tìm số thứ tự phim
        number_match = re.search(r"phim (số )?(\d+)", message)
        if number_match:
            return int(number_match.group(2))
            
        # Tìm tên phim trong database
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = "SELECT id FROM phims WHERE LOWER(ten_phim) LIKE %s LIMIT 1"
            cursor.execute(query, (f"%{message.lower()}%",))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
                
        except Exception as e:
            print(f"Error extracting movie ID: {str(e)}")
            
        return None 