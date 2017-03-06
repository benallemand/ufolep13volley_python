import sql_manager
import data_manager


def cleanup_players_photo_path():
    unused_photos = sql_manager.sql_get_unused_photo_paths()
    for unused_photo in unused_photos:
        sql_manager.delete_photo(unused_photo['id'])
    existing_photo_paths = data_manager.get_existing_photo_paths()
    for existing_photo_path in existing_photo_paths:
        if not sql_manager.is_photo_path_in_database(existing_photo_path):
            data_manager.remove_photo(existing_photo_path)
