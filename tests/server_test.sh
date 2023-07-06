functions-framework --target=main &
pid=$!
echo "run [$pid]"
sleep 1
curl http://localhost:8080/ -X POST -H "Content-Type: application/json" \
	-d '{"product": "MVNO"}'
echo
echo "kill [$pid]"
kill -9 $pid
