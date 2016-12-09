gource aggrepo --stop-at-end -s 0.05 -c 1.0 -p 0.8 --max-file-lag 0.1 -o /media/tfoote/Seagate\ Backup\ Plus\ Drive/gource_output.ppm --title "Historical ROS Activity" --hide filenames -1920x1080 
avconv -y -b 6000K -r 60 -f image2pipe -vcodec ppm -i /media/tfoote/Seagate\ Backup\ Plus\ Drive/gource_output.ppm -vcodec libx264 ROS_Historymp4
