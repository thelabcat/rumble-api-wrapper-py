"""
UploadPHP

Interact with Rumble's Upload.PHP API to upload videos.
S.D.G."""

raise NotImplementedError("See TODOs in code")
import mimetypes
import os
import requests
from . import static
from . import utils

class UploadPHP:
    """Upload videos to Rumble"""
    def __init__(self, servicephp):
        """Pass a ServicePHP object"""
        self.servicephp = servicephp

    @property
    def session_cookie(self):
        """Our Rumble session cookie to authenticate requests"""
        return self.servicephp.session_cookie

    def uphp_request(self, additional_params, method = "PUT", data: dict = None):
        """Make a request to Upload.PHP with common settings
        additional_params: Query string parameters to add to the base ones
        method: What method to use for the request.
            Defaults to PUT.
        data: Form data for the request.
            Defaults to None."""
        params = {"api": static.Upload.api_ver}
        params.update(additional_params)
        r = requests.request(
                method,
                static.URI.uploadphp,
                params = params,
                data = data,
                headers = static.RequestHeaders.user_agent,
                cookies = self.session_cookie if logged_in else None,
                timeout = static.Delays.request_timeout,
                )
        assert r.status_code == 200, f"Upload.PHP request failed: {r}\n{r.text}"
        #If the request json has a data -> success value, make sure it is True

        return r

    def chunked_file_upload(self, file_path):
        """Upload a video file to Rumble in chunks"""
        #Get video upload ID, for example 1734105774078-167771, TODO

        #Number of chunks we will need to do, rounded up
        num_chunks = self.__cur_filesize // static.Upload.chunksz + 1

        #Base upload params
        upload_params = {
            "chunkSz": static.Upload.chunksz,
            "chunkQty": num_chunks,
            }

        with open(file_path, "rb") as f:
            for i in range(num_chunks):
                #Parameters for this chunk upload
                chunk_params = upload_params.copy()
                chunk_params.update({
                    "chunk": f"{i}_{upload_id}.mp4",
                    })

                #Get permission to upload the chunk
                assert utils.options_check(
                    static.URI.uploadphp,
                    "PUT",
                    cookies = self.session_cookie,
                    prams = chunk_params,
                    ), f"Chunk {i} upload failed at OPTIONS request."
                #Upload the chunk
                self.uphp_request(chunk_params, data = f.read(static.Upload.chunksz))

        #Params for the merge request
        merge_params = upload_params.copy()
        merge_params.update({
            "merge": i,
            "chunk": f"{upload_id}.mp4",
            })

        #Tell the server to merge the chunks
        r = self.uphp_request(merge_params)
        merged_video_fn = r.text

        return merged_video_fn, upload_id

    def unchunked_file_upload(self, file_path):
        """Upload a video file to Rumble all at once"""
        #Get video upload ID, for example 1734105774078-167771, TODO

        with open(file_path, "rb") as f:
            #Get permission to upload the file
            assert utils.options_check(
                static.URI.uploadphp,
                "PUT",
                cookies = self.session_cookie,
                prams = {"api": static.Upload.api_ver},
                ), f"File upload failed at OPTIONS request."
            #Upload the file
            r = self.uphp_request({}, data = f.read())

        uploaded_fn = r.text

        return uploaded_fn, upload_id

    def upload_video(self, file_path, title: str, **kwargs):
        """Upload a video to Rumble
        file_path: Path to video file
        title: The video title
        info_who, _when, _where, _ext_user: Metadata about the video
        tags: String of comma-separated tags
        channel_id: Numeric ID of the channel to upload to
        visibility: Public, unlisted, private
            Defaults to public
        availability: TODO
            Defaults to free.
        scheduled_publish: Time to publish the video to public in seconds since epoch.
            Defaults to publish immediately.
        """
        assert os.path.exists(file_path), "Video file does not exist on disk"

        self.__cur_filesize = os.path.size(file_path)

        assert self.__cur_filesize < static.Upload.max_filesize, "File is too big"

        start_time = int(time.time() * 1000)

        #Is the file large enough that it needs to be chunked
        if self.__cur_file_size > static.Upload.chunksz:
            server_filename, upload_id = self.chunked_file_upload(file_path)
        else:
            server_filename, upload_id = self.unchunked_file_upload(file_path)

        end_time = int(time.time() * 1000)

        #Get the uploaded duration
        #r = self.uphp_request({"duration": merged_video_fn})
        #checked_duration = int(r.text)
        #print("Server says video duration is", checked_duration)

        #Skipping thumbnails get

        self.uphp_request(
            {"form" : 1},
            data = {
                "title": title,
                "description": kwargs.get("description"),
                "video[]": server_filename,
                "featured": 6, #Never seems to change
                "rights": 1,
                "terms": 1,
                "facebookUpload": None,
                "vimeoUpload": None,
                "infoWho": kwargs.get("info_who"),
                "infoWhen": kwargs.get("info_when"),
                "infoWhere": kwargs.get("info_where"),
                "infoExtUser": kwargs.get("info_ext_user"),
                "tags": kwargs.get("tags"),
                "channelId": utils.ensure_b10(kwargs.get("channel_id", 0)),
                "siteChannelId": 7, #Does not change between user and Marswide BGL TODO
                "mediaChannelId": None,
                "isGamblingRelated": False,
                "set_default_channel_id": 0, #Set to 1 to "Set this channel as default" on Rumble
                #Scheduled visibility takes precedent over visibility setting
                "visibility": kwargs.get("visibility", "public") if not kwargs.get("scheduled_publish") else "private",
                "availability": kwargs.get("availability", "free"),
                "file_meta": {
                    "name": os.path.basename(file_path), #File name
                    "modified": int(os.path.getmtime(file_path) * 1000), #Timestamp file was modified, miliseconds
                    "size": self.__cur_file_size, #Exact length of entire MP4 file in bytes
                    "type": mimetypes.guess_file_type(file_path)[0],
                    "time_start": start_time, #Timestamp file started uploading, miliseconds
                    "speed": 0, #5460521, #TODO
                    "num_chunks": len(chunks),
                    "time_end": end_time, #Timestamp we finished uploading, miliseconds
                    },
                "schedulerDatetime": utils.form_timestamp(kwargs.get("scheduled_publish")) if kwargs.get("scheduled_publish") else None,
                thumb: 4 #Key of thumbnail to use from auto-generated ones, TODO
