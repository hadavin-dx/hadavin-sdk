note () 
{ 
    echo "$(date -u +%FT%TZ) UTC | $(TZ=Asia/Kolkata date +%FT%T%z) IST | B: $1" >> /home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-B.txt
}
