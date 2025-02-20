class HybridRecommender:
    def __init__(self):
        self.content_based = ContentBasedRecommender()
        self.collaborative = CollaborativeRecommender()
        self.deep_learning = DeepRecommender()
        
    def get_recommendations(self, user_id, movie_id):
        # Kết hợp kết quả từ các model khác nhau
        content_scores = self.content_based.predict(movie_id)
        collab_scores = self.collaborative.predict(user_id)
        deep_scores = self.deep_learning.predict(user_id, movie_id)
        
        # Weighted ensemble
        final_scores = (0.4 * content_scores + 
                       0.4 * collab_scores + 
                       0.2 * deep_scores)
        return final_scores 