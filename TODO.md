# TODO:
For the next version we need to update some things to make sure that the lambda function cannot run into memory issues:

- [ ] Change the temp directory to read files each and add them to the zip by string;
- [ ] Send the string of the zip to the server by file, to not overload memory;
- [ ] Keep response open until full zip is sent;