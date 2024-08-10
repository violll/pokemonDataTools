from pathlib import Path

def getAbsPath(f, depth):
    res = f
    while depth != 0:
        res = Path(res).parent.absolute()
        depth -= 1
    
    return str(res)
