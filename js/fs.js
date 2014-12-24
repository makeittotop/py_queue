var fs = require('fs')

var file = process.argv[2]
var buf = fs.readFileSync(file)
var lines = buf.toString().split('\n')

console.log(lines.length - 1)


