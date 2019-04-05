#!/usr/bin/env bash

docker run -d -p 4567:4567 gkmr/jumanpp-api

curl -X POST -H 'Content-Type: application/json' --data '{"string":"この道をゆけばどうなるものか危ぶむなかれ危ぶめば道はなし踏み出せばその一足が道となり  その一足が道となる迷わず行けよ行けば分かるさ"}' http://localhost:4567/parse
curl -X POST -H 'Content-Type: application/json' --data '{"string":"この道をゆけばどうなるものか危ぶむなかれ危ぶめば道はなし踏み出せばその一足が道となり  その一足が道となる迷わず行けよ行けば分かるさ"}' http://localhost:4567/split