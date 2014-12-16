#!/usr/bin/env python

import ldap
import sys
import os

def main():
    keyword = sys.argv[1]
     
    server = '172.16.10.10'
    port = 389

    l = ldap.open(server, port)
    l.simple_bind("abhishek@barajoun.local", "qwerty")

    base = 'OU=barajounusers,DC=barajoun,DC=local'
    scope = ldap.SCOPE_SUBTREE
    filter = "cn=" + "*" + keyword + "*"
    retrieve_attributes = None

    count = 0
    result_set = []
    timeout = 0

    result_id = l.search(base, scope, filter, retrieve_attributes)
    result_type, result_data = l.result(result_id, timeout)
    if result_type == ldap.RES_SEARCH_ENTRY:
        result_set.append(result_data)

    if len(result_set) == 0:
        print "No Results."
        return
     
    for i in range(len(result_set)):
        for entry in result_set[i]:
            name = entry[1]['cn'][0]
            email = entry[1]['mail'][0]
            #phone = entry[1]['telephonenumber'][0]
            #desc = entry[1]['description'][0]
            count = count + 1
        
            print "%d.\nName: %s: \nE-mail: %s\n" %(count, name, email)
        
    pass

if __name__=='__main__':
    main()

