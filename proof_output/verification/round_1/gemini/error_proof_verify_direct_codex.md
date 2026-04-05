1. Error: `sed: /Users/an/Desktop/cm/QED/proof_output/tmp/verify_fib_output.txt: No such file or directory`
   What I was doing: I ran the checker script and attempted to read its output file in the same parallel tool call.
   Workaround: I reran the checker and then read the output sequentially after the script had finished writing the file.
