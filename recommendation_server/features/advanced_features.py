class FeatureExtractor:
    def extract_temporal_features(self, user_history):
        # Thêm features về thời gian xem
        time_features = {
            'time_of_day': user_history['timestamp'].dt.hour,
            'day_of_week': user_history['timestamp'].dt.dayofweek,
            'season': user_history['timestamp'].dt.quarter
        }
        return time_features
        
    def extract_context_features(self, user_data):
        # Features về context của user
        return {
            'device_type': user_data['device'],
            'location': user_data['location'],
            'connection_type': user_data['connection']
        } 