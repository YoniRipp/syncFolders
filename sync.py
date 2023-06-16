import sys 
import os
import argparse
import time
import logging
import shutil
import filecmp

class Sync:

    def __init__(self, sourcePath, replicaPath, logFile, interval):

        self.source = sourcePath
        self.replica = replicaPath 
        self.interval = interval
        self.logFile = logFile
        self.initLoggers()

    ## Create a replica of the source directory.
    def createRootReplica(self):
        if not os.path.isdir(self.replica):
            os.makedirs(self.replica)
            logging.debug(f"Directory {self.replica} is created")
        
    ## Create Loggers
    def initLoggers(self):
        try:
            logging.basicConfig(filename=self.logFile, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', filemode='w')
            handler = logging.StreamHandler()
            formater = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formater)
            logging.getLogger('').addHandler(handler)
            print(f"Syncing...")
        except Exception as e:
            print(f"Unexpected error occurred while creating logging: {e}")
            sys.exit(1)
    
    def runRecurse(self,sourceSubPath,replicaSubPath):
        ## Compare Files top down.
        ## Find all files and directories of both paths.
        ## 1) Remove all Items and files that are replica and not in source.
        ## 2) Create all items and files that are in source and nost in replica.
        ## 3) Copy all items that are in source but are changed in replica.

        ##Init params 
        sourceItems =  set(os.listdir(sourceSubPath))
        replicaItems =  set(os.listdir(replicaSubPath))

        ## Items in source/replica, replica/source and in both.
        sourceItemsDiff = sourceItems - replicaItems
        replicaItemsDiff = replicaItems - sourceItems
        itemsInBoth = sourceItems.intersection(replicaItems)

        ## Items in source but not in replica
        for item in sourceItemsDiff:
            sourcePath = os.path.join(sourceSubPath, item)
            replicaPath = os.path.join(replicaSubPath, item)
            ## Create subdir/files of source in replica
            if(os.path.isdir(sourcePath)):
                self.copyDir(sourcePath,replicaPath)
            else:
                self.copyFile(sourcePath,replicaPath,True)
                

        ## Items in replica but not in source.
        for item in replicaItemsDiff:
            replicaPath = os.path.join(replicaSubPath, item)

            ## remove dir that is not in source from replica
            if(os.path.isdir(replicaPath)):
                self.removeDir(replicaPath)
            else:
                try:
                    ## remove file that is not in source from replica
                    os.remove(replicaPath)
                    logging.debug(f"File      {replicaPath} is removed")
                except Exception as e:
                    logging.error(f"Unexpected error occurred while removing file {replicaPath}: {e}")
                    sys.exit(1)

        ## Items in both.
        for item in itemsInBoth:
            sourcePath = os.path.join(sourceSubPath, item)
            replicaPath = os.path.join(replicaSubPath, item)

            ## compare both are dirs, recurse.
            if(os.path.isdir(sourcePath) and os.path.isdir(replicaPath)):
                self.runRecurse(sourcePath,replicaPath)
             ## compare both files, if they are not the same from source to replica.   
            elif(os.path.isfile(sourcePath) and os.path.isfile(replicaPath)):
                if not self.compareFiles(sourcePath,replicaPath):
                    self.copyFile(sourcePath,replicaPath)
       
    ## Check if both files are the same
    def compareFiles(self,sourceFile,replicaFile):
        try:
            return filecmp.cmp(sourceFile, replicaFile, shallow=False)
        except Exception as e:
            logging.error(f"Unexpected error occurred while comparing files {sourceFile} with {replicaFile}: {e}")
            sys.exit(1)

    def removeDir(self,replicaPath):
        try:
            shutil.rmtree(replicaPath)
            logging.debug(f"Directory {replicaPath} is removed")
        except Exception as e:
            logging.error(f"Unexpected error occurred while removing directory {replicaPath}: {e}")
            sys.exit(1)

    ## copy/replace file from replica by source
    def copyFile(self,sourcePath,replicaPath,create=False):
        try:
            shutil.copy2(sourcePath,replicaPath)
            if(create):
                logging.debug(f"File      {replicaPath} is created")
            else:
                logging.debug(f"File      {replicaPath} is updated")
        except Exception as e:
            logging.error(f"Unexpected error occurred while copying file from {sourcePath} to {replicaPath}: {e}")
            sys.exit(1)

    ## Copy Dir from source to replica
    def copyDir(self,sourcePath,replicaPath):
        try:
            shutil.copytree(sourcePath,replicaPath)
            logging.debug(f"Directory {replicaPath} is created")
        except Exception as e:
            logging.error(f"Unexpected error occurred while copying directory from {sourcePath} to {replicaPath}: {e}")
            sys.exit(1)

    ## Run sync until stopped.
    def run(self):
        while True:
            self.createRootReplica()
            self.runRecurse(self.source, self.replica)
            time.sleep(self.interval)
    
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Sync folders')
        parser.add_argument('--source', type=str, default='source', help='Source path.')
        parser.add_argument('--replica', type=str, default='replica', help='Replica path.')
        parser.add_argument('--interval', type=int, default=1, help='Synchronization interval.')
        parser.add_argument('--log', type=str, default='log', help='Log file path.')
        args = parser.parse_args()
        s = Sync(args.source, args.replica, args.log, args.interval)
        s.run()
        
    except KeyboardInterrupt:
        print('Stopping sync...')