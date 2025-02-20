class RecommenderMetrics:
    def calculate_metrics(self, predictions, actual):
        metrics = {
            'precision': self.precision_at_k(predictions, actual, k=5),
            'recall': self.recall_at_k(predictions, actual, k=5),
            'ndcg': self.ndcg_at_k(predictions, actual, k=5),
            'diversity': self.diversity_score(predictions),
            'novelty': self.novelty_score(predictions, user_history)
        }
        return metrics 