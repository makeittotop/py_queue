var fs = require('fs')

fs.readFile(process.argv[2], function(err, data) {
    if(err) {
        console.error(err)
    }
    else {
        var s = data.toString().split('\n')
        console.log(s.length - 1)
    }
})
