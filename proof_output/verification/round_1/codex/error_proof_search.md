Initial shell listing command used `sed 's#^#/##'`, which failed on the local BSD `sed` with the message:

`sed: 1: "s#^#/##": bad flag in substitute command: '#'`

Context: I was trying to normalize file-list output while inspecting the input directories at the start of the round.

Workaround: I dropped that substitution and used simpler listing/read commands instead. No proof content was affected.
