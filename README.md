# bf-native

A brainf*ck compiler written using [llvm-lite](https://github.com/numba/llvmlite) as a compiler backend

## Example

**run.sh**

```bash
#!/bin/bash

set -xe
python "bf-native" hello.bf hello.ll && clang hello.ll -o hello.exe && ./hello.exe
```

```bash
$ ./run.sh 
+ python bf-native hello.bf hello.ll
+ clang hello.ll -o hello.exe
+ ./hello.exe
Hello World!
```
