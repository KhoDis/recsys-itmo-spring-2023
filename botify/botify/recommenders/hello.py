from .random import Random
from .recommender import Recommender
import random


class HelloRec(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog, user_history):
        self.tracks_redis = tracks_redis
        self.fallback = Random(tracks_redis)
        self.catalog = catalog
        self.user_history = user_history
        self.top_track_popularity = {}
        for i, track_id in enumerate(catalog.top_tracks):
            self.top_track_popularity[track_id] = (1 - i / len(catalog.top_tracks))

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if not recommendations:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        # Get user history and subtract from recommendations
        user_history_tracks = self.user_history.get(user, [])
        filtered_recommendations = set(recommendations) - set(user_history_tracks)

        # Calculate popularity of recommended tracks
        popularity = []
        for track_id in filtered_recommendations:
            if track_id in self.top_track_popularity:
                popularity.append(self.top_track_popularity[track_id])
            else:
                popularity.append(0.0)

        # Choose track with highest popularity
        if popularity:
            max_popularity = max(popularity)
            max_popularity_tracks = [t for t, p in zip(filtered_recommendations, popularity) if p == max_popularity]
            recommended_track = random.choice(max_popularity_tracks)
        else:
            recommended_track = self.fallback.recommend_next(user, prev_track, prev_track_time)

        # Add recommended track to user history
        user_history_tracks.append(recommended_track)
        self.user_history[user] = user_history_tracks

        return recommended_track
