from music_controller.music_cache_controller import MusicCacheManager

if __name__ == "__main__":
    manager = MusicCacheManager()
    manager.check_and_update_cache()