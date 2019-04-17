import argparse
import os

from backup import BackUpUtil

parser = argparse.ArgumentParser()
parser.add_argument("method", nargs="?", help="a[dd], m[odify], d[elete] s[ync] run(sync and delete expire files in trashbin)")

if __name__ == "__main__":
    buu = BackUpUtil()
    args = parser.parse_args()
    os.system("clear")

    if args.method == 'a':
        buu.addNewReference()
    elif args.method == 'm':
        buu.modifyRenference()
    elif args.method == 'd':
        buu.delRenference()
    elif args.method == 's':
        buu.sync()
    elif args.method == 'run':
        buu.run()
    else:
        buu.display()