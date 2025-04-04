import mysql.connector
from typing import List, Dict
import httpx

class RecommenderService:
    def __init__(self):
        self.recommendation_api = "http://127.0.0.1:5000"
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'csdl_phim'
        }

    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    async def get_recommendations(self, user_id: str, preferences: Dict) -> List[Dict]:
        """Lấy gợi ý phim"""
        # Thử tìm theo preferences trước
        results = await self.search_movies_by_preferences(preferences)
        
        # Nếu không có kết quả, lấy phim mới nhất
        if not results:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                
                query = """
                    SELECT DISTINCT
                        p.id,
                        p.ten_phim AS title,
                        p.mo_ta AS description,
                        p.slug_phim AS slug,
                        GROUP_CONCAT(DISTINCT tl.ten_the_loai) AS genres
                    FROM phims p
                    LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
                    LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
                    GROUP BY p.id
                    ORDER BY p.id DESC
                    LIMIT 5
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error getting fallback recommendations: {str(e)}")
                return []
                
        return results

    async def get_user_recently_watched(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Lấy danh sách phim user đã xem gần đây"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    p.id,
                    p.ten_phim AS title,
                    p.mo_ta AS description,
                    p.nam_san_xuat AS year,
                    GROUP_CONCAT(DISTINCT tl.ten_the_loai SEPARATOR ', ') AS genres,
                    lx.ngay_xem
                FROM luot_xems lx
                JOIN phims p ON lx.id_phim = p.id
                LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
                LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
                WHERE lx.id_khach_hang = %s
                AND lx.ngay_xem >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY p.id, p.ten_phim, lx.ngay_xem
                ORDER BY lx.ngay_xem DESC
                LIMIT %s
            """

            cursor.execute(query, (user_id, limit))
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            return results

        except Exception as e:
            print(f"Error getting user recently watched: {str(e)}")
            return []

    async def search_movies_by_preferences(self, preferences: Dict) -> List[Dict]:
        """Tìm phim theo preferences"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # In ra preferences để debug
            print(f"Searching with preferences: {preferences}")

            # Query cơ bản
            query = """
                SELECT DISTINCT
                    p.id,
                    p.ten_phim AS title,
                    p.mo_ta AS description,
                    p.slug_phim AS slug,
                    GROUP_CONCAT(DISTINCT tl.ten_the_loai) AS genres
                FROM phims p
                LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
                LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
            """

            conditions = []
            params = []

            # Nếu có thể loại
            if preferences.get('genres'):
                genre_conditions = []
                for genre in preferences['genres']:
                    genre_conditions.append("tl.ten_the_loai LIKE %s")
                    params.append(f"%{genre}%")
                if genre_conditions:
                    conditions.append(f"({' OR '.join(genre_conditions)})")

            # Nếu có từ khóa tìm kiếm
            if preferences.get('message'):
                message = preferences['message']
                if "phim" in message:
                    conditions.append("(p.ten_phim LIKE %s OR p.mo_ta LIKE %s)")
                    params.extend([f"%{message}%", f"%{message}%"])

            # Thêm điều kiện WHERE nếu có
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Group by và limit
            query += " GROUP BY p.id LIMIT 5"

            # In ra query và params để debug
            print("Query:", query)
            print("Params:", params)

            cursor.execute(query, tuple(params))
            results = cursor.fetchall()

            # In ra kết quả để debug
            print(f"Found {len(results)} results")

            cursor.close()
            conn.close()

            return results

        except Exception as e:
            print(f"Error in search_movies_by_preferences: {str(e)}")
            return []

    async def get_fallback_recommendations(self) -> List[Dict]:
        """Lấy phim đề xuất mặc định (mới nhất)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    p.id,
                    p.ten_phim AS title,
                    p.mo_ta AS description,
                    p.nam_san_xuat AS year,
                    GROUP_CONCAT(DISTINCT tl.ten_the_loai SEPARATOR ', ') AS genres
                FROM phims p
                LEFT JOIN chi_tiet_the_loais ctl ON p.id = ctl.id_phim
                LEFT JOIN the_loais tl ON ctl.id_the_loai = tl.id
                GROUP BY p.id
                ORDER BY p.nam_san_xuat DESC
                LIMIT 5
            """

            cursor.execute(query)
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            return results

        except Exception as e:
            print(f"Error getting fallback recommendations: {str(e)}")
            return [] 