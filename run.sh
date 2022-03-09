
sudo docker run \
    --mount type=bind,source=$(pwd)/videos,target=/usr/src/app/videos \
    --mount type=bind,source=$(pwd)/db,target=/usr/src/app/db \
    youtube/tgbot 