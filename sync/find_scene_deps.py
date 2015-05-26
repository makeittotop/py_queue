#!/usr/bin/env python

from pymel.core import *
def gen2(scn_file):
    scn_file = str(scn_file)

    txFiles = ls(type='file')
    abcs = ls(type='bs_alembicNode')
    refs = ls(type='reference')
    ASSs = ls(type='aiStandIn')
    dynGlobals = ls(type='dynGlobals')
    
    deps = []
    
    # appending scene name:
    #deps.append('%s'%sceneName()+'\n')
    deps.append(scn_file+'\n')
    
    # processing refs:
    for ref in refs:
        try:
            deps.append(referenceQuery(ref, f=True)+'\n')
        except:
            print ("Warning: scene has unknow ref nodes that doesn't relate to files")
    
    # processing texutres:
    '''
    TODO: Add support for image texture sequence
    '''
    for tx in txFiles:
        tmpName = '%s'%getAttr('%s.fileTextureName'%tx)
        tmpName = tmpName.replace('////', '/')
        tmpName = tmpName.replace('///', '/')
        tmpName = tmpName.replace('//', '/')
        tmpName = tmpName.replace('<udim>', '*')
        shaveTex = False

        # check if connected to a shave node (yes.. go as it is, otherwise send the .tx version)
        connections = listConnections(tx, p=True, s=False, d=True)
        for conn in connections:
            if 'shaveTex' in '%s'%conn:
                shaveTex = True
                break

        if not shaveTex:
            tmpName = tmpName.replace('.tiff', '.tx')
            tmpName = tmpName.replace('.tif', '.tx')
            tmpName = tmpName.replace('.tga', '.tx')
            tmpName = tmpName.replace('.jpg', '.tx')
            tmpName = tmpName.replace('.png', '.tx')
            tmpName = tmpName.replace('.hdr', '.tx')
            tmpName = tmpName.replace('.exr', '.tx')
        
        deps.append(tmpName+'\n')
    
    # processing alembics:
    for abc in abcs:
        tmpName = getAttr('%s.abc_File'%abc)+'\n'
        tmpName = tmpName.replace('//', '/')
        tmpName = tmpName.replace('///', '/')
        tmpName = tmpName.replace('////', '/')
        deps.append(tmpName)
    
    # processing ASSs and/or assAttrNode:
    for ass in ASSs:
        ass_path=""
        fxd_path=""
        
        try:
            ass_path=getAttr("%s.assAttrNodePath" % ass)
        except:
            ass_path=getAttr("%s.dso" % ass)
            pass

        if ass_path != "":
            ass_path = ass_path.replace('#', '*')+'\n'
            ass_path = ass_path.replace('////', '/')
            ass_path = ass_path.replace('///', '/')
            ass_path = ass_path.replace('//', '/')
            deps.append(ass_path)
        
        # processing fxd FumeFx cache    
        nodes=listConnections(ass, type="assAttrNode")
        if len(nodes) > 0:
            try:
                fxd_path=getAttr("%s.render_output_path" % nodes[0])
            except: pass
            if fxd_path != "":
                fxd_path = fxd_path.replace('#', '*')+'\n'
                fxd_path = fxd_path.replace('////', '/')
                fxd_path = fxd_path.replace('///', '/')
                fxd_path = fxd_path.replace('//', '/')
                deps.append(fxd_path)
                
        
    # processing particle caches:
    for dyn in dynGlobals:
        deps.append(getAttr('%s.cacheDirectory'%dyn)+'\n')
        
    # processing Yeti caches:
    yetiShapes = ls(type='pgYetiMaya')
    for yeti in yetiShapes:
        yetiCache = getAttr('%s.cacheFileName'%yeti)
        if yetiCache:
            yetiCache = yetiCache.replace('%04d', '*') + '\n'
            deps.append(yetiCache)

    # cleaning up deps by removing duplicates
    deps = list(set(deps))

    # Ensuring that dep items DO NOT have double forward slashes at all
    deps = map(lambda x: x.replace('//', '/'), deps)
    
    #depsFile = '/nas/projects/Tactic/bilal/render/.depsTemp/%s_filtered.lst'%os.path.basename(sceneName())
    depsFile = '/nas/projects/Tactic/bilal/render/.depsTemp/%s_filtered.lst'%os.path.basename(scn_file)
    resultFile = depsFile
    
    depsFile = open(depsFile,'w')
    depsFile.writelines(deps)
    depsFile.close()
    
    print '\n\n#################################################################'
    print '####               SCENE DEPENDENCIES FOUND                 #####'
    print '#################################################################'
    for dep in deps:
        print dep[:-1]
    print '#################################################################'
    print 'Deps file generated successfully.'
    print 'file: %s'%resultFile
    
    return (resultFile, deps)

def gen():
    txFiles = ls(type='file')
    abcs = ls(type='bs_alembicNode')
    refs = ls(type='reference')
    ASSs = ls(type='aiStandIn')
    dynGlobals = ls(type='dynGlobals')
    
    deps = []
    
    # appending scene name:
    deps.append('%s'%sceneName()+'\n')
    
    # processing refs:
    for ref in refs:
        try:
            deps.append(referenceQuery(ref, f=True)+'\n')
        except:
            print ("Warning: scene has unknow ref nodes that doesn't relate to files")
    
    # processing texutres:
    '''
    TODO: Add support for image texture sequence
    '''
    for tx in txFiles:
        tmpName = '%s'%getAttr('%s.fileTextureName'%tx)
        tmpName = tmpName.replace('//', '/')
        tmpName = tmpName.replace('///', '/')
        tmpName = tmpName.replace('////', '/')
        tmpName = tmpName.replace('.tiff', '.tx')
        tmpName = tmpName.replace('.tif', '.tx')
        tmpName = tmpName.replace('.tga', '.tx')
        tmpName = tmpName.replace('.jpg', '.tx')
        tmpName = tmpName.replace('.png', '.tx')
        tmpName = tmpName.replace('.hdr', '.tx')
        tmpName = tmpName.replace('.exr', '.tx')
        tmpName = tmpName.replace('<udim>', '*')
        
        deps.append(tmpName+'\n')
    
    # processing alembics:
    for abc in abcs:
        tmpName = getAttr('%s.abc_File'%abc)+'\n'
        tmpName = tmpName.replace('//', '/')
        tmpName = tmpName.replace('///', '/')
        tmpName = tmpName.replace('////', '/')
        deps.append(tmpName)
    
    # processing ASSs and/or assAttrNode:
    for ass in ASSs:
        ass_path=""
        node=ls(ass, type="assAttrNode", dag=True)
        if len(node) > 0:
            ass_path=getAttr("%s.assAttrNodePath" % ass)
        else:
            ass_path=getAttr("%s.dso" % ass)

        if ass_path != "":
            ass_path = ass_path.replace('#', '*')
            ass_path = ass_path.replace('////', '/')
            ass_path = ass_path.replace('///', '/')
            ass_path = ass_path.replace('//', '/')
            deps.append(ass_path)
        
    # processing particle caches:
    for dyn in dynGlobals:
        deps.append(getAttr('%s.cacheDirectory'%dyn)+'\n')
        
    # processing Yeti caches:
    yetiShapes = ls(type='pgYetiMaya')
    for yeti in yetiShapes:
        yetiCache = getAttr('%s.cacheFileName'%yeti)
        if yetiCache:
            yetiCache = yetiCache.replace('%04d', '*') + '\n'
            deps.append(yetiCache)

    # cleaning up deps by removing duplicates
    deps = list(set(deps))

    # Ensuring that dep items DO NOT have double forward slashes at all
    deps = map(lambda x: x.replace('//', '/'), deps)
    
    depsFile = '/nas/projects/Tactic/bilal/render/.depsTemp/%s_filtered.lst'%os.path.basename(sceneName())
    resultFile = depsFile
    
    depsFile = open(depsFile,'w')
    depsFile.writelines(deps)
    depsFile.close()
    
    print '\n\n#################################################################'
    print '####               SCENE DEPENDENCIES FOUND                 #####'
    print '#################################################################'
    for dep in deps:
        print dep[:-1]
    print '#################################################################'
    print 'Deps file generated successfully.'
    print 'file: %s'%resultFile
    
    return (resultFile, deps)

    '''
    deps = []
    
    for dep in depsList:
        deps.append(dep[:-1])
    
    cleanDeps = list(set(deps))
    
    cpList=''
    print '--------------------------------------------------------'
    print 'These scene dependencies will be uploaded to vendor nas:'
    print 'Note: deps coming from "asset" will not be uploaded'
    print '      To upload them, please request that from Admin'
    print 'Evaluating from lst file: %s'%filteredFile
    print '--------------------------------------------------------'
    for dep in cleanDeps:
        print dep
        cpList = cpList + dep + ' '
    print '--------------------------------------------------------'
    
    # eval the ascp command:
    print     'ascp -P 33001 -O 33001 -l 15M -p --overwrite=diff -d --src-base=/nas/projects %s render@113.107.235.11:/'%cpList
    os.system('ascp -P 33001 -O 33001 -l 15M -p --overwrite=diff -d --src-base=/nas/projects %s render@113.107.235.11:/'%cpList)
    '''
