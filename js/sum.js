var sum = 0, i;

for(i = 2; i < process.argv.length; i++) {
    sum += Number(process.argv[i]);
}

console.log(sum)
