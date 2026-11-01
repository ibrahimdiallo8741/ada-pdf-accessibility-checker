#!/usr/bin/env fish

set OUR_SYSTEM "https://adacheck.deltadizzy.org/system"
set OUR_TESTER "https://adacheck.deltadizzy.org/tester"

set PEER_SYSTEM "https://api.potentiate.club/system"
set PEER_TESTER "https://api.potentiate.club/tester"

# Default to OUR URLs
set target_system $OUR_SYSTEM
set target_tester $OUR_TESTER

argparse -n test.fish 'h/help' 's/peer-system' 't/peer-tester' 'p/peer' 'system=' 'tester=' -- $argv
or exit 1

if set -q _flag_help
    echo "Usage: ./test.fish [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --peer-system    Use PEER system URL ($PEER_SYSTEM)"
    echo "  -t, --peer-tester    Use PEER tester URL ($PEER_TESTER)"
    echo "  -p, --peer           Use PEER for both system and tester"
    echo "      --system=TARGET  Set system: 'our', 'peer', or custom URL"
    echo "      --tester=TARGET  Set tester: 'our', 'peer', or custom URL"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Defaults:"
    echo "  System: OUR ($OUR_SYSTEM)"
    echo "  Tester: OUR ($OUR_TESTER)"
    exit 0
end

if set -q _flag_peer
    set target_system $PEER_SYSTEM
    set target_tester $PEER_TESTER
end

if set -q _flag_peer_system
    set target_system $PEER_SYSTEM
end

if set -q _flag_peer_tester
    set target_tester $PEER_TESTER
end

if set -q _flag_system
    switch $_flag_system
        case our
            set target_system $OUR_SYSTEM
        case peer
            set target_system $PEER_SYSTEM
        case '*'
            set target_system $_flag_system
    end
end

if set -q _flag_tester
    switch $_flag_tester
        case our
            set target_tester $OUR_TESTER
        case peer
            set target_tester $PEER_TESTER
        case '*'
            set target_tester $_flag_tester
    end
end

echo "Using System: $target_system"
echo "Using Tester: $target_tester"

# Send the setup request to get the session id, use jq to extract it from the json response
set SESSION_ID $(curl -s -X POST "$target_tester/test/setup" -H "Content-Type: application/json" -d "{\"target_url\": \"$target_system\"}" | jq -r '.session_id')

echo "Active Session: $SESSION_ID"

# Issue run request using the session id
echo -e "\nRun Test - session $SESSION_ID"
curl -s -X POST "$target_tester/test/run" -H "Content-Type: application/json" -d "{\"session_id\": \"$SESSION_ID\"}" | jq .

echo -e "\nTest Report - session $SESSION_ID"
curl -s -X GET "$target_tester/test/report?session_id=$SESSION_ID" | jq .
