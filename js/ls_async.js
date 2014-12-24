var fs = require('fs')
var path = require('path')

fs.readdir(process.argv[2], function(err, list) {
    if (err) {
        console.error(err)
    }
    else {
        for(i=0; i < list.length; i++) {
            //console.log(path.extname(list[i]).split('.')[1])
            if(path.extname(list[i]).split('.')[1] == process.argv[3]) {
                console.log(list[i])
            }
        }
    }
})
