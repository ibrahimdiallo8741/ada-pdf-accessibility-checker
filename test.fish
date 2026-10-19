#!/usr/bin/env fish

set OUR_SYSTEM "https://adacheck.deltadizzy.org/system"
set OUR_TESTER "https://adacheck.deltadizzy.org/tester"

# Send the setup request to get the session id, use jq to extract it from the json response
set SESSION_ID $(curl -s -X POST "$OUR_TESTER/test/setup" -H "Content-Type: application/json" -d "{\"target_url\": \"$OUR_SYSTEM\"}" | jq -r '.session_id')

echo "Active Session: $SESSION_ID"

# Issue run request using the session id
echo -e "\nRun Test - session $SESSION_ID"
curl -s -X POST "$OUR_TESTER/test/run" -H "Content-Type: application/json" -d "{\"session_id\": \"$SESSION_ID\"}" | jq .

echo -e "\nTest Report - session $SESSION_ID"
curl -s -X GET "$OUR_TESTER/test/report?session_id=$SESSION_ID" | jq .