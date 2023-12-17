""" YouTubeの文字起こしを取得する """
import youtube_transcript_api

video_id = "DIL82INALDI"
a = youtube_transcript_api.YouTubeTranscriptApi.get_transcripts(
    [video_id], languages=["ja"]
)

b = "".join([x["text"] for x in a[0][video_id]])
print(b)
