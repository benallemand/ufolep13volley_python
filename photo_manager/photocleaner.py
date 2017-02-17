import sql_manager
import data_manager


def cleanup_players_photo_path():
    unused_photos = sql_manager.sql_get_unused_photo_paths()
    for unused_photo in unused_photos:
        data_manager.remove_photo(unused_photo['path_photo'])
        sql_manager.delete_photo(unused_photo['id'])
