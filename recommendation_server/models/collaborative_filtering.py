from surprise import SVD, Dataset, Reader
import pandas as pd

class CollaborativeRecommender:
    def __init__(self):
        self.model = SVD(n_factors=100)
        
    def train(self, ratings_df):
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(ratings_df[['user_id', 'movie_id', 'rating']], reader)
        self.model.fit(data.build_full_trainset())
        
    def predict(self, user_id, movie_ids):
        predictions = [self.model.predict(user_id, movie_id) for movie_id in movie_ids]
        return predictions 