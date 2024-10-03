import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

def split_playlist(sp, original_playlist_id, chunk_size=50):
    # Get the original playlist's tracks
    results = sp.playlist_tracks(original_playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Get the original playlist's details
    original_playlist = sp.playlist(original_playlist_id)
    original_name = original_playlist['name']

    # Split tracks into chunks
    for i in range(0, len(tracks), chunk_size):
        chunk = tracks[i:i+chunk_size]
        
        # Create a new playlist
        new_playlist_name = f"{original_name} (Part {i//chunk_size + 1})"
        new_playlist = sp.user_playlist_create(sp.me()['id'], new_playlist_name, public=False)
        
        # Add tracks to the new playlist
        successful_tracks = []
        failed_tracks = []

        for track in chunk:
            if track['track'] is None or 'uri' not in track['track']:
                failed_tracks.append((track['track']['name'] if track['track'] and 'name' in track['track'] else "Unknown Track", "Missing track data"))
                continue

            if track['track']['uri'].startswith('spotify:local:'):
                failed_tracks.append((track['track']['name'], "Local file, cannot be added via API"))
                continue

            try:
                sp.user_playlist_add_tracks(sp.me()['id'], new_playlist['id'], [track['track']['uri']])
                successful_tracks.append(track['track']['name'])
            except SpotifyException as e:
                failed_tracks.append((track['track']['name'], f"Error: {str(e)}"))

        print(f"Created playlist: {new_playlist_name}")
        print(f"Successfully added {len(successful_tracks)} tracks")
        
        if failed_tracks:
            print("The following tracks couldn't be added:")
            for track_name, reason in failed_tracks:
                print(f"  - {track_name}: {reason}")

def main():
    # Set up authentication
    scope = "playlist-read-private playlist-modify-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    # Get user's playlists
    playlists = sp.current_user_playlists()
    
    print("Your playlists:")
    for i, playlist in enumerate(playlists['items']):
        print(f"{i+1}. {playlist['name']} (Tracks: {playlist['tracks']['total']})")
    
    # Ask user to select a playlist
    selection = int(input("Enter the number of the playlist you want to split: ")) - 1
    selected_playlist = playlists['items'][selection]
    
    # Split the selected playlist
    split_playlist(sp, selected_playlist['id'])
    
    print(f"Playlist '{selected_playlist['name']}' has been split into smaller playlists of 50 songs each.")

if __name__ == "__main__":
    main()
