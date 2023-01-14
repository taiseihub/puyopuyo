import pytube


def download_videos_in(play_list_url, resolution='360p', output_path='video/'):
    for url in pytube.Playlist(play_list_url):
        video = pytube.YouTube(url).streams.filter(res=resolution).first()
        if not video:
            print(f'{pytube.YouTube(url).streams.first().title} with {resolution} was not found.')
            continue
        print(video)
        video.download(output_path=output_path)
        print(video.default_filename, 'is downloaded')


if __name__ == '__main__':
    download_videos_in('https://www.youtube.com/watch?v=xGn-bBKebfA&list=PLmDQwMwneImGzRkN5neXNg9rF45ELGjhF')

